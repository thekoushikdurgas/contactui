"""
Agent Nodes - AI-powered workflow nodes

These nodes integrate AI capabilities into workflows.
"""

import json
import logging
from typing import Dict, Any
from ..services.node_registry import NodeRegistry, BaseNodeHandler

logger = logging.getLogger(__name__)


@NodeRegistry.register
class ChatCompletionNode(BaseNodeHandler):
    """Chat completion node - uses AI to generate responses"""
    node_type = "ai/chat_completion"
    title = "AI Chat Completion"
    category = "ai_agent"
    description = "Generate AI responses using chat models"
    color = "#aa44ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "response", "type": "object"}]
    properties = [
        {
            "name": "model",
            "type": "select",
            "options": ["gpt-4", "gpt-3.5-turbo", "gemini-pro"],
            "default": "gpt-3.5-turbo"
        },
        {"name": "system_prompt", "type": "textarea", "default": "You are a helpful assistant."},
        {"name": "user_prompt", "type": "textarea", "default": ""},
        {"name": "temperature", "type": "number", "default": 0.7},
        {"name": "max_tokens", "type": "number", "default": 1000},
        {"name": "use_input_as_prompt", "type": "boolean", "default": False}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.ai_agent.services.ai_service import AIService
        
        # Build prompt
        if config.get('use_input_as_prompt') and input_data:
            if isinstance(input_data, dict):
                user_prompt = json.dumps(input_data)
            else:
                user_prompt = str(input_data)
        else:
            user_prompt = config.get('user_prompt', '')
        
        system_prompt = config.get('system_prompt', 'You are a helpful assistant.')
        
        # Call AI service
        ai_service = AIService()
        
        try:
            response = ai_service.get_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=config.get('temperature', 0.7),
                max_tokens=config.get('max_tokens', 1000)
            )
            
            return {
                'response': response,
                'model': config.get('model', 'gpt-3.5-turbo'),
                'input_data': input_data
            }
        except Exception as e:
            logger.error(f"AI Chat Completion failed: {e}")
            raise


@NodeRegistry.register
class CodeGeneratorNode(BaseNodeHandler):
    """Code generator node - generates code using AI"""
    node_type = "ai/code_generator"
    title = "AI Code Generator"
    category = "ai_agent"
    description = "Generate code using AI models"
    color = "#aa44ff"
    
    inputs = [{"name": "context", "type": "object"}]
    outputs = [{"name": "code", "type": "object"}]
    properties = [
        {
            "name": "language",
            "type": "select",
            "options": ["python", "javascript", "typescript", "sql", "bash", "other"],
            "default": "python"
        },
        {"name": "task_description", "type": "textarea", "default": ""},
        {"name": "include_comments", "type": "boolean", "default": True}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.ai_agent.services.ai_service import AIService
        
        language = config.get('language', 'python')
        task = config.get('task_description', '')
        include_comments = config.get('include_comments', True)
        
        prompt = f"""Generate {language} code for the following task:
{task}

{"Include helpful comments explaining the code." if include_comments else ""}

Context data:
{json.dumps(input_data) if input_data else "No additional context"}

Return only the code, no explanations."""
        
        ai_service = AIService()
        
        try:
            code = ai_service.get_completion(
                prompt=prompt,
                system_prompt=f"You are an expert {language} developer. Generate clean, production-ready code.",
                temperature=0.3
            )
            
            return {
                'code': code,
                'language': language,
                'task': task
            }
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise


@NodeRegistry.register
class SummarizerNode(BaseNodeHandler):
    """Summarizer node - summarizes text using AI"""
    node_type = "ai/summarizer"
    title = "AI Summarizer"
    category = "ai_agent"
    description = "Summarize text content using AI"
    color = "#aa44ff"
    
    inputs = [{"name": "text", "type": "object"}]
    outputs = [{"name": "summary", "type": "object"}]
    properties = [
        {
            "name": "summary_type",
            "type": "select",
            "options": ["brief", "detailed", "bullet_points", "key_takeaways"],
            "default": "brief"
        },
        {"name": "max_length", "type": "number", "default": 200},
        {"name": "text_field", "type": "string", "default": "text"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.ai_agent.services.ai_service import AIService
        
        # Extract text from input
        text_field = config.get('text_field', 'text')
        if isinstance(input_data, dict):
            text = input_data.get(text_field, str(input_data))
        else:
            text = str(input_data)
        
        summary_type = config.get('summary_type', 'brief')
        max_length = config.get('max_length', 200)
        
        type_instructions = {
            'brief': f'Provide a brief summary in under {max_length} words.',
            'detailed': f'Provide a detailed summary covering all main points.',
            'bullet_points': 'Summarize as bullet points, highlighting key information.',
            'key_takeaways': 'List the key takeaways from this content.'
        }
        
        prompt = f"""Summarize the following text:

{text}

{type_instructions.get(summary_type, type_instructions['brief'])}"""
        
        ai_service = AIService()
        
        try:
            summary = ai_service.get_completion(
                prompt=prompt,
                system_prompt="You are an expert at summarizing content clearly and concisely.",
                temperature=0.3
            )
            
            return {
                'summary': summary,
                'summary_type': summary_type,
                'original_length': len(text),
                'summary_length': len(summary)
            }
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise


@NodeRegistry.register
class DataExtractorNode(BaseNodeHandler):
    """Data extractor node - extracts structured data using AI"""
    node_type = "ai/data_extractor"
    title = "AI Data Extractor"
    category = "ai_agent"
    description = "Extract structured data from text using AI"
    color = "#aa44ff"
    
    inputs = [{"name": "text", "type": "object"}]
    outputs = [{"name": "extracted", "type": "object"}]
    properties = [
        {"name": "schema", "type": "json", "default": '{"fields": ["name", "email", "phone"]}'},
        {"name": "instructions", "type": "textarea", "default": "Extract the specified fields from the text."}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.ai_agent.services.ai_service import AIService
        
        schema = config.get('schema', {})
        if isinstance(schema, str):
            schema = json.loads(schema)
        
        instructions = config.get('instructions', 'Extract the specified fields.')
        
        # Get text from input
        if isinstance(input_data, dict):
            text = input_data.get('text', json.dumps(input_data))
        else:
            text = str(input_data)
        
        fields = schema.get('fields', [])
        
        prompt = f"""Extract the following information from the text below:
Fields to extract: {', '.join(fields)}

Text:
{text}

{instructions}

Return the extracted data as JSON with the field names as keys."""
        
        ai_service = AIService()
        
        try:
            result = ai_service.get_completion(
                prompt=prompt,
                system_prompt="You are a data extraction expert. Return only valid JSON.",
                temperature=0.1
            )
            
            # Try to parse as JSON
            try:
                extracted = json.loads(result)
            except json.JSONDecodeError:
                extracted = {'raw_result': result}
            
            return {
                'extracted': extracted,
                'fields_requested': fields
            }
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            raise
