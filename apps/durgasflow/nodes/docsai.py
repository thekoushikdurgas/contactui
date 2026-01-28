"""
DocsAI Integration Nodes - Nodes for interacting with DocsAI features

These nodes integrate with other DocsAI components like pages, endpoints, and knowledge base.
"""

import json
import logging
from typing import Dict, Any
from ..services.node_registry import NodeRegistry, BaseNodeHandler

logger = logging.getLogger(__name__)


@NodeRegistry.register
class GetPageNode(BaseNodeHandler):
    """Get page node - fetch page from documentation"""
    node_type = "docsai/get_page"
    title = "Get Documentation Page"
    category = "docsai"
    description = "Fetch a documentation page"
    color = "#4488ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "page", "type": "object"}]
    properties = [
        {"name": "page_id", "type": "string", "default": ""},
        {"name": "page_slug", "type": "string", "default": ""},
        {"name": "use_input", "type": "boolean", "default": False}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.documentation.services.pages_service import PagesService
        
        if config.get('use_input') and input_data:
            if isinstance(input_data, dict):
                page_id = input_data.get('page_id') or input_data.get('id')
            else:
                page_id = str(input_data)
        else:
            page_id = config.get('page_id', '')
        
        try:
            page = PagesService.get_page_by_id(page_id)
            return page
        except Exception as e:
            logger.error(f"Failed to get page: {e}")
            return {'error': str(e), 'page_id': page_id}


@NodeRegistry.register
class SearchPagesNode(BaseNodeHandler):
    """Search pages node - search documentation pages"""
    node_type = "docsai/search_pages"
    title = "Search Pages"
    category = "docsai"
    description = "Search documentation pages"
    color = "#4488ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "pages", "type": "array"}]
    properties = [
        {"name": "query", "type": "string", "default": ""},
        {"name": "limit", "type": "number", "default": 10},
        {"name": "category", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.documentation.services.pages_service import PagesService
        
        query = config.get('query', '')
        if input_data and isinstance(input_data, dict):
            query = input_data.get('query', query)
        
        limit = config.get('limit', 10)
        category = config.get('category', '')
        
        try:
            pages = PagesService.search_pages(query=query, limit=limit)
            return {
                'pages': pages,
                'count': len(pages),
                'query': query
            }
        except Exception as e:
            logger.error(f"Failed to search pages: {e}")
            return {'error': str(e), 'pages': []}


@NodeRegistry.register
class GetEndpointNode(BaseNodeHandler):
    """Get endpoint node - fetch API endpoint"""
    node_type = "docsai/get_endpoint"
    title = "Get API Endpoint"
    category = "docsai"
    description = "Fetch an API endpoint definition"
    color = "#4488ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "endpoint", "type": "object"}]
    properties = [
        {"name": "endpoint_id", "type": "string", "default": ""},
        {"name": "use_input", "type": "boolean", "default": False}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.documentation.services.endpoints_service import EndpointsService
        
        if config.get('use_input') and input_data:
            if isinstance(input_data, dict):
                endpoint_id = input_data.get('endpoint_id') or input_data.get('id')
            else:
                endpoint_id = str(input_data)
        else:
            endpoint_id = config.get('endpoint_id', '')
        
        try:
            endpoint = EndpointsService.get_endpoint_by_id(endpoint_id)
            return endpoint
        except Exception as e:
            logger.error(f"Failed to get endpoint: {e}")
            return {'error': str(e), 'endpoint_id': endpoint_id}


@NodeRegistry.register
class SearchKnowledgeNode(BaseNodeHandler):
    """Search knowledge base node"""
    node_type = "docsai/search_knowledge"
    title = "Search Knowledge Base"
    category = "docsai"
    description = "Search the knowledge base"
    color = "#4488ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "results", "type": "array"}]
    properties = [
        {"name": "query", "type": "string", "default": ""},
        {"name": "limit", "type": "number", "default": 5},
        {"name": "semantic", "type": "boolean", "default": True}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.knowledge.services import KnowledgeService
        
        query = config.get('query', '')
        if input_data and isinstance(input_data, dict):
            query = input_data.get('query', query)
        
        limit = config.get('limit', 5)
        
        try:
            results = KnowledgeService.search(query=query, limit=limit)
            return {
                'results': results,
                'count': len(results),
                'query': query
            }
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return {'error': str(e), 'results': []}


@NodeRegistry.register
class CreatePageNode(BaseNodeHandler):
    """Create page node - create a new documentation page"""
    node_type = "docsai/create_page"
    title = "Create Documentation Page"
    category = "docsai"
    description = "Create a new documentation page"
    color = "#4488ff"
    
    inputs = [{"name": "data", "type": "object"}]
    outputs = [{"name": "page", "type": "object"}]
    properties = [
        {"name": "title", "type": "string", "default": ""},
        {"name": "content", "type": "textarea", "default": ""},
        {"name": "category", "type": "string", "default": "general"},
        {"name": "use_input", "type": "boolean", "default": True}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.documentation.services.pages_service import PagesService
        
        if config.get('use_input') and isinstance(input_data, dict):
            title = input_data.get('title', config.get('title', ''))
            content = input_data.get('content', config.get('content', ''))
            category = input_data.get('category', config.get('category', 'general'))
        else:
            title = config.get('title', '')
            content = config.get('content', '')
            category = config.get('category', 'general')
        
        try:
            page = PagesService.create_page(
                title=title,
                content=content,
                category=category
            )
            return page
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            return {'error': str(e)}


@NodeRegistry.register
class UpdatePageNode(BaseNodeHandler):
    """Update page node - update an existing page"""
    node_type = "docsai/update_page"
    title = "Update Documentation Page"
    category = "docsai"
    description = "Update an existing documentation page"
    color = "#4488ff"
    
    inputs = [{"name": "data", "type": "object"}]
    outputs = [{"name": "page", "type": "object"}]
    properties = [
        {"name": "page_id", "type": "string", "default": ""},
        {"name": "title", "type": "string", "default": ""},
        {"name": "content", "type": "textarea", "default": ""},
        {"name": "use_input", "type": "boolean", "default": True}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.documentation.services.pages_service import PagesService
        
        if config.get('use_input') and isinstance(input_data, dict):
            page_id = input_data.get('page_id', config.get('page_id', ''))
            updates = {
                k: v for k, v in input_data.items()
                if k not in ['page_id', 'id']
            }
        else:
            page_id = config.get('page_id', '')
            updates = {}
            if config.get('title'):
                updates['title'] = config['title']
            if config.get('content'):
                updates['content'] = config['content']
        
        try:
            page = PagesService.update_page(page_id, updates)
            return page
        except Exception as e:
            logger.error(f"Failed to update page: {e}")
            return {'error': str(e), 'page_id': page_id}


@NodeRegistry.register
class GenerateDocumentationNode(BaseNodeHandler):
    """Generate documentation node - use AI to generate documentation"""
    node_type = "docsai/generate_docs"
    title = "Generate Documentation"
    category = "docsai"
    description = "Use AI to generate documentation from code or descriptions"
    color = "#4488ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "documentation", "type": "object"}]
    properties = [
        {"name": "doc_type", "type": "select", "options": ["api", "function", "class", "module", "readme"], "default": "api"},
        {"name": "source", "type": "textarea", "default": ""},
        {"name": "style", "type": "select", "options": ["technical", "simple", "detailed"], "default": "technical"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.ai_agent.services.ai_service import AIService
        
        doc_type = config.get('doc_type', 'api')
        style = config.get('style', 'technical')
        
        if input_data:
            if isinstance(input_data, dict):
                source = input_data.get('source', input_data.get('code', json.dumps(input_data)))
            else:
                source = str(input_data)
        else:
            source = config.get('source', '')
        
        prompt = f"""Generate {style} documentation for the following {doc_type}:

{source}

Create comprehensive documentation including:
- Description
- Parameters/Properties (if applicable)
- Return values (if applicable)
- Examples
- Notes or warnings (if applicable)

Format the documentation in Markdown."""
        
        ai_service = AIService()
        
        try:
            documentation = ai_service.get_completion(
                prompt=prompt,
                system_prompt="You are a technical documentation expert. Create clear, comprehensive documentation.",
                temperature=0.3
            )
            
            return {
                'documentation': documentation,
                'doc_type': doc_type,
                'style': style
            }
        except Exception as e:
            logger.error(f"Failed to generate documentation: {e}")
            return {'error': str(e)}


@NodeRegistry.register
class GetRelationshipsNode(BaseNodeHandler):
    """Get relationships node - fetch page relationships"""
    node_type = "docsai/get_relationships"
    title = "Get Page Relationships"
    category = "docsai"
    description = "Fetch relationships for a page"
    color = "#4488ff"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "relationships", "type": "array"}]
    properties = [
        {"name": "page_id", "type": "string", "default": ""},
        {"name": "use_input", "type": "boolean", "default": False}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from apps.documentation.services.relationships_service import RelationshipsService
        
        if config.get('use_input') and input_data:
            if isinstance(input_data, dict):
                page_id = input_data.get('page_id') or input_data.get('id')
            else:
                page_id = str(input_data)
        else:
            page_id = config.get('page_id', '')
        
        try:
            relationships = RelationshipsService.get_relationships_for_page(page_id)
            return {
                'relationships': relationships,
                'count': len(relationships),
                'page_id': page_id
            }
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            return {'error': str(e), 'relationships': []}
