"""AI Service for chat and AI operations with local JSON file integration."""

import logging
import re
from typing import Optional, Dict, Any, List, Iterator
from django.conf import settings
from django.core.cache import cache

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except (ImportError, ValueError):
    GEMINI_AVAILABLE = False
    genai = None

from apps.core.services.api_client import APIClient
from apps.core.config import Config
from apps.ai_agent.services.media_loader import MediaFileLoaderService
from apps.ai_agent.services.semantic_search import SemanticSearchService
from apps.ai_agent.services.postman_parser import PostmanCollectionParser
from apps.ai_agent.services.project_docs_loader import ProjectDocsLoader

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI operations using OpenAI, Gemini, and Lambda AI API."""
    
    def __init__(self):
        """Initialize AI service."""
        # OpenAI client
        if OPENAI_AVAILABLE and Config.is_openai_enabled():
            try:
                openai.api_key = settings.OPENAI_API_KEY
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        # Gemini AI client
        self.gemini_model = None
        if GEMINI_AVAILABLE and Config.is_gemini_enabled():
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini AI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
        
        # Lambda AI API client
        self.lambda_client = None
        if Config.is_lambda_enabled():
            try:
                self.lambda_client = APIClient(
                    base_url=settings.LAMBDA_AI_API_URL,
                    api_key=settings.LAMBDA_AI_API_KEY
                )
                logger.info("Lambda AI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Lambda AI client: {e}")
        
        # Media file services
        self.media_loader = MediaFileLoaderService()
        self.semantic_search = SemanticSearchService(self.media_loader)
        self.postman_parser = PostmanCollectionParser(self.media_loader)
        self.project_docs_loader = ProjectDocsLoader(self.media_loader)
        
        # System context about available documentation
        self.system_context = self._build_system_context()
    
    def _build_system_context(self) -> str:
        """Build system context about available documentation.
        
        Returns:
            System context string
        """
        try:
            pages_index = self.media_loader.local_storage.get_index('pages')
            endpoints_index = self.media_loader.local_storage.get_index('endpoints')
            
            total_pages = pages_index.get('total', 0)
            total_endpoints = endpoints_index.get('total', 0)
            
            context = f"""You are an AI assistant for a documentation system.
Available documentation:
- {total_pages} pages (routes, metadata, endpoint relationships)
- {total_endpoints} API endpoints (GraphQL queries and mutations)
- Postman collections with API examples
- Project documentation and architecture files

You can help users understand:
- How pages connect to endpoints
- API endpoint details and usage
- Code examples from Postman collections
- System architecture and structure
"""
            return context
        except Exception as e:
            logger.warning(f"Error building system context: {e}")
            return "You are an AI assistant for a documentation system."
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        context: Optional[List[str]] = None,
        model: str = 'gpt-3.5-turbo',
        stream: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get chat completion from AI.
        
        Priority: OpenAI → Gemini → Lambda AI
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            context: Additional context strings to include
            model: AI model to use
            stream: Whether to stream the response
            
        Returns:
            Response dictionary with 'content' and 'metadata', or None if error
        """
        try:
            # Add system context about available documentation
            if self.system_context:
                system_message = {
                    'role': 'system',
                    'content': self.system_context
                }
                messages = [system_message] + messages
            
            # Add context if provided
            if context:
                context_message = {
                    'role': 'system',
                    'content': f"Additional context:\n" + "\n".join(context)
                }
                messages = [context_message] + messages
            
            # Try OpenAI first
            if OPENAI_AVAILABLE and Config.is_openai_enabled():
                if stream:
                    return self._openai_stream(messages, model)
                else:
                    try:
                        response = openai.ChatCompletion.create(
                            model=model,
                            messages=messages,
                            temperature=0.7
                        )
                        return {
                            'content': response.choices[0].message.content,
                            'metadata': {
                                'model': model,
                                'usage': response.usage,
                                'provider': 'openai'
                            }
                        }
                    except Exception as e:
                        logger.warning(f"OpenAI failed, trying Gemini: {e}")
            
            # Try Gemini AI
            if self.gemini_model:
                try:
                    # Get the last user message
                    user_message = messages[-1].get('content', '') if messages else ''
                    
                    # Use generate_content with Google Search tool for grounding sources
                    try:
                        # Try with googleSearch tool (requires newer Gemini API)
                        from google.generativeai import types
                        response = self.gemini_model.generate_content(
                            user_message,
                            generation_config=types.GenerationConfig(
                                temperature=0.7,
                            ),
                            tools=[types.Tool.from_google_search_retrieval(
                                types.GoogleSearchRetrieval()
                            )]
                        )
                    except (ImportError, AttributeError, TypeError):
                        # Fallback to basic generate_content if tool not available
                        response = self.gemini_model.generate_content(
                            user_message,
                            generation_config={
                                'temperature': 0.7,
                            }
                        )
                    
                    # Extract grounding sources from response
                    grounding_sources = []
                    try:
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'grounding_metadata'):
                                grounding_metadata = candidate.grounding_metadata
                                if hasattr(grounding_metadata, 'grounding_chunks'):
                                    for chunk in grounding_metadata.grounding_chunks:
                                        if hasattr(chunk, 'web'):
                                            web = chunk.web
                                            grounding_sources.append({
                                                'title': getattr(web, 'title', 'Reference'),
                                                'uri': getattr(web, 'uri', '#')
                                            })
                    except Exception as e:
                        logger.debug(f"Could not extract grounding sources: {e}")
                    
                    return {
                        'content': response.text,
                        'metadata': {
                            'model': 'gemini-pro',
                            'provider': 'gemini'
                        },
                        'groundingSources': grounding_sources
                    }
                except Exception as e:
                    logger.warning(f"Gemini AI failed, falling back to Lambda: {e}")
            
            # Fallback to Lambda AI API
            return self._lambda_chat(messages, context)
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return None
    
    def _openai_stream(self, messages: List[Dict[str, str]], model: str) -> Iterator[str]:
        """Stream OpenAI chat completion.
        
        Args:
            messages: List of messages
            model: Model name
            
        Yields:
            Response chunks
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.7,
                stream=True
            )
            for chunk in response:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        yield delta['content']
        except Exception as e:
            logger.error(f"Error in OpenAI streaming: {str(e)}")
            yield f"Error: {str(e)}"
    
    def _lambda_chat(
        self,
        messages: List[Dict[str, str]],
        context: Optional[List[str]]
    ) -> Optional[Dict[str, Any]]:
        """Get chat completion from Lambda AI API.
        
        Args:
            messages: List of messages
            context: Optional context
            
        Returns:
            Response dictionary, or None if error
        """
        if not self.lambda_client:
            return None
        
        try:
            response = self.lambda_client.post("/chat", json_data={
                'messages': messages,
                'context': context or []
            })
            return {
                'content': response.get('content', ''),
                'metadata': {
                    'provider': 'lambda'
                }
            }
        except Exception as e:
            logger.error(f"Error in Lambda chat: {str(e)}")
            return None
    
    def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        use_media_files: bool = True
    ) -> List[str]:
        """
        Retrieve relevant context from knowledge base and media files.
        
        Args:
            query: Search query
            limit: Maximum number of results per source
            use_media_files: Whether to include media file context (default: True)
            
        Returns:
            List of context strings
        """
        context = []
        max_context_length = 3000  # Limit total context size
        
        # Search Pages
        if use_media_files:
            try:
                page_results = self.semantic_search.search_pages(query, limit=limit)
                for result in page_results:
                    page_data = result['data']
                    metadata = page_data.get('metadata', {})
                    route = metadata.get('route', '')
                    purpose = metadata.get('purpose', '')
                    endpoints = metadata.get('uses_endpoints', [])
                    endpoint_names = [ep.get('endpoint_path', '').split('/')[-1] for ep in endpoints[:3]]
                    
                    context_str = f"Page: {route} - Purpose: {purpose[:200]}"
                    if endpoint_names:
                        context_str += f" - Uses endpoints: {', '.join(endpoint_names)}"
                    
                    if len('\n'.join(context)) + len(context_str) < max_context_length:
                        context.append(context_str)
            except Exception as e:
                logger.error(f"Error retrieving page context: {e}")
            
            # Search Endpoints
            try:
                endpoint_results = self.semantic_search.search_endpoints(query, limit=limit)
                for result in endpoint_results:
                    endpoint_data = result['data']
                    endpoint_path = endpoint_data.get('endpoint_path', '')
                    method = endpoint_data.get('method', '')
                    description = endpoint_data.get('description', '')
                    
                    context_str = f"Endpoint: {endpoint_path} ({method}) - {description[:200]}"
                    
                    if len('\n'.join(context)) + len(context_str) < max_context_length:
                        context.append(context_str)
            except Exception as e:
                logger.error(f"Error retrieving endpoint context: {e}")
        
        return context
    
    def explain_code(self, code: str, language: str = 'python') -> Optional[str]:
        """
        Explain code using AI with media file context.
        
        Priority: Gemini → OpenAI → Lambda AI
        
        Args:
            code: Code to explain
            language: Programming language
            
        Returns:
            Explanation text, or None if error
        """
        # Detect references in code
        code_context = self._extract_code_references(code)
        
        # Try Gemini first if available
        if self.gemini_model:
            try:
                prompt = f"Explain the following {language} code clearly and concisely:\n\n{code}"
                if code_context:
                    prompt += f"\n\nRelevant Documentation:\n{code_context}"
                
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.warning(f"Gemini explain_code failed, falling back: {e}")
        
        # Fallback to chat completion
        system_prompt = f'You are a code explanation assistant. Explain the following {language} code clearly and concisely.'
        if code_context:
            system_prompt += f'\n\nRelevant documentation:\n{code_context}'
        
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': code
            }
        ]
        
        response = self.chat_completion(messages)
        if response:
            return response.get('content')
        return None
    
    def _extract_code_references(self, code: str) -> str:
        """Extract page/endpoint references from code and get relevant context."""
        context_parts = []
        
        # Detect page routes (e.g., '/companies', '/dashboard')
        route_pattern = r'["\'](/[a-zA-Z0-9\-_/]+)["\']'
        routes = re.findall(route_pattern, code)
        for route in set(routes):
            page = self.media_loader.load_page(route.lstrip('/').replace('/', '_'))
            if not page:
                # Try to find by route in metadata
                pages = self.media_loader.load_all_pages()
                for p in pages:
                    metadata = p.get('metadata', {})
                    if metadata.get('route') == route:
                        page = p
                        break
            
            if page:
                metadata = page.get('metadata', {})
                purpose = metadata.get('purpose', '')
                context_parts.append(f"Page {route}: {purpose[:150]}")
        
        # Detect endpoint paths
        endpoint_patterns = [
            r'graphql[/"\' ]+([A-Z][a-zA-Z0-9]+)',
            r'["\']([A-Z][a-zA-Z0-9]+)["\']',
        ]
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, code)
            for match in set(matches):
                if len(match) > 5:
                    endpoint = self.media_loader.load_endpoint(f"{match.lower()}_graphql")
                    if not endpoint:
                        endpoint = self.media_loader.load_endpoint(match.lower())
                    if endpoint:
                        desc = endpoint.get('description', '')
                        context_parts.append(f"Endpoint {match}: {desc[:150]}")
        
        return '\n'.join(context_parts) if context_parts else ''
    
    def generate_documentation(self, code: str, language: str = 'python') -> Optional[str]:
        """
        Generate documentation for code.
        
        Priority: Gemini → OpenAI → Lambda AI
        
        Args:
            code: Code to document
            language: Programming language
            
        Returns:
            Generated documentation, or None if error
        """
        # Find similar pages/endpoints
        similar_context = self._find_similar_documentation(code)
        
        # Try Gemini first if available
        if self.gemini_model:
            try:
                prompt = f"Generate clear, comprehensive documentation for the following {language} code in Markdown format:\n\n{code}"
                if similar_context:
                    prompt += f"\n\nSimilar existing documentation patterns:\n{similar_context}"
                
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.warning(f"Gemini generate_documentation failed, falling back: {e}")
        
        # Fallback to chat completion
        system_prompt = f'You are a documentation generator. Generate clear, comprehensive documentation for the following {language} code in Markdown format.'
        if similar_context:
            system_prompt += f'\n\nSimilar existing documentation patterns:\n{similar_context}'
        
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': code
            }
        ]
        
        response = self.chat_completion(messages)
        if response:
            return response.get('content')
        return None
    
    def _find_similar_documentation(self, code: str) -> str:
        """Find similar pages/endpoints for documentation generation."""
        context_parts = []
        
        # Extract keywords from code
        keywords = re.findall(r'[a-zA-Z]{4,}', code.lower())
        query = ' '.join(set(keywords[:5]))
        
        if query:
            # Search for similar pages
            page_results = self.semantic_search.search_pages(query, limit=2)
            for result in page_results:
                page_data = result['data']
                metadata = page_data.get('metadata', {})
                route = metadata.get('route', '')
                purpose = metadata.get('purpose', '')
                context_parts.append(f"Similar page: {route} - {purpose[:100]}")
            
            # Search for similar endpoints
            endpoint_results = self.semantic_search.search_endpoints(query, limit=2)
            for result in endpoint_results:
                endpoint_data = result['data']
                endpoint_path = endpoint_data.get('endpoint_path', '')
                description = endpoint_data.get('description', '')
                context_parts.append(f"Similar endpoint: {endpoint_path} - {description[:100]}")
        
        return '\n'.join(context_parts) if context_parts else ''
    
    def suggest_best_practices(self, code: str, language: str = 'python') -> Optional[str]:
        """
        Suggest best practices for code.
        
        Args:
            code: Code to analyze
            language: Programming language
            
        Returns:
            Suggestions text, or None if error
        """
        system_prompt = f'You are a code review assistant. Analyze the following {language} code and suggest best practices, improvements, and potential issues.'
        
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': code
            }
        ]
        
        response = self.chat_completion(messages)
        if response:
            return response.get('content')
        return None
    
    def generate_chat_response(
        self,
        prompt: str,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI chat response (backward compatibility).
        
        Args:
            prompt: User prompt
            history: Chat history
            
        Returns:
            Dictionary with 'text' and optional 'groundingSources'
        """
        messages = (history or []) + [{'role': 'user', 'content': prompt}]
        
        # Retrieve context
        context = self.retrieve_context(prompt, limit=3)
        
        response = self.chat_completion(messages, context=context)
        if response:
            # Use grounding sources from response if available, otherwise use context
            grounding_sources = response.get('groundingSources', [])
            if not grounding_sources:
                # Convert context to grounding sources format
                grounding_sources = [
                    {'title': ctx[:100], 'uri': '#'} for ctx in context[:5]
                ]
            
            return {
                'text': response.get('content', ''),
                'groundingSources': grounding_sources
            }
        
        return {
            'text': 'Sorry, I encountered an error generating a response. Please try again.',
            'groundingSources': []
        }
    
    def analyze_project_structure(self, file_names: List[str]) -> str:
        """
        Analyze project structure from file names.
        
        Args:
            file_names: List of file paths/names
            
        Returns:
            Analysis text
        """
        if self.gemini_model:
            try:
                prompt = f"""Based on the following list of files in a repository, provide a concise senior engineer's overview of the project architecture, likely tech stack, and key modules.

Files:
{chr(10).join(file_names[:100])}

Format your response as a professional executive summary."""
                
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Project analysis failed: {e}")
        
        # Fallback to chat completion
        file_list = '\n'.join(file_names[:100])
        messages = [
            {
                'role': 'system',
                'content': 'You are a senior software engineer. Analyze the project structure and provide an overview.'
            },
            {
                'role': 'user',
                'content': f"Analyze this project structure:\n\n{file_list}"
            }
        ]
        
        response = self.chat_completion(messages)
        if response:
            return response.get('content', 'Analysis failed to generate.')
        
        return "Analysis failed to generate."
