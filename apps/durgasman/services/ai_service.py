"""AI Service for Durgasman API Testing App."""

import json
from typing import Dict, Any, Optional
from django.conf import settings


class AIService:
    """AI-powered features for API testing."""

    def __init__(self):
        # For now, use a simple implementation without external APIs
        # This can be extended to use Gemini, OpenAI, etc.
        self.gemini_available = hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY

    def analyze_response(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> str:
        """Analyze API response and provide insights."""

        if not self.gemini_available:
            return self._basic_response_analysis(request_data, response_data)

        # TODO: Implement actual Gemini API call
        return self._basic_response_analysis(request_data, response_data)

    def generate_request_from_description(self, description: str, schema_hint: str = None) -> Optional[Dict[str, Any]]:
        """Generate API request from natural language description."""

        if not self.gemini_available:
            return self._basic_request_generation(description, schema_hint)

        # TODO: Implement actual Gemini API call
        return self._basic_request_generation(description, schema_hint)

    def generate_documentation(self, collection_name: str, requests: list) -> str:
        """Generate API documentation for a collection."""

        if not self.gemini_available:
            return self._basic_documentation_generation(collection_name, requests)

        # TODO: Implement actual Gemini API call
        return self._basic_documentation_generation(collection_name, requests)

    def _basic_response_analysis(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> str:
        """Basic response analysis without AI."""

        status = response_data.get('status', 0)
        time = response_data.get('time', 0)

        analysis = []

        # Status analysis
        if status >= 200 and status < 300:
            analysis.append("✅ **Success**: The API returned a successful response.")
        elif status >= 400 and status < 500:
            analysis.append("❌ **Client Error**: There might be an issue with the request (check parameters, authentication, etc.).")
        elif status >= 500:
            analysis.append("🔴 **Server Error**: The API server encountered an error.")
        else:
            analysis.append("⚠️ **Unexpected Status**: The response status is unusual.")

        # Performance analysis
        if time > 5000:
            analysis.append("🐌 **Slow Response**: The request took longer than 5 seconds. Consider optimizing or checking network connectivity.")
        elif time > 1000:
            analysis.append("⚠️ **Moderate Response Time**: The request took over 1 second, which might indicate performance issues.")

        # Content analysis
        data = response_data.get('data')
        if data:
            if isinstance(data, dict):
                field_count = len(data)
                analysis.append(f"📊 **Response Structure**: The response contains {field_count} top-level fields.")

                # Check for common error patterns
                if 'error' in data or 'errors' in data:
                    analysis.append("⚠️ **Possible Error**: The response contains error fields.")
                if 'message' in data:
                    analysis.append("💬 **Message Field**: Check the message field for additional information.")
            elif isinstance(data, list):
                analysis.append(f"📋 **List Response**: The response contains {len(data)} items.")
        else:
            analysis.append("📭 **Empty Response**: The response body is empty.")

        # Request method analysis
        method = request_data.get('method', '').upper()
        if method == 'GET' and status >= 400:
            analysis.append("🔍 **GET Request Failed**: For read operations, ensure the resource exists and you have proper permissions.")
        elif method == 'POST' and status == 201:
            analysis.append("✨ **Resource Created**: The POST request successfully created a new resource.")
        elif method in ['PUT', 'PATCH'] and status == 204:
            analysis.append("📝 **Resource Updated**: The request successfully modified the resource.")

        if not analysis:
            analysis.append("🤔 **Basic Analysis**: The response appears normal, but consider reviewing the full response details.")

        return "\n\n".join(analysis)

    def _basic_request_generation(self, description: str, schema_hint: str = None) -> Optional[Dict[str, Any]]:
        """Basic request generation without AI."""

        # Simple keyword-based request generation
        description_lower = description.lower()

        request = {
            'name': 'Generated Request',
            'method': 'GET',
            'url': 'https://api.example.com/v1/resource',
            'headers': [
                {'key': 'Accept', 'value': 'application/json', 'enabled': True},
                {'key': 'Content-Type', 'value': 'application/json', 'enabled': True}
            ],
            'params': [],
            'body': '',
            'auth_type': 'None',
            'response_schema': schema_hint or ''
        }

        # Method detection
        if any(word in description_lower for word in ['create', 'add', 'insert', 'new']):
            request['method'] = 'POST'
            request['body'] = '{"key": "value"}'
        elif any(word in description_lower for word in ['update', 'modify', 'change', 'edit']):
            request['method'] = 'PUT'
            request['body'] = '{"key": "updated_value"}'
        elif any(word in description_lower for word in ['delete', 'remove', 'destroy']):
            request['method'] = 'DELETE'

        # Authentication detection
        if any(word in description_lower for word in ['auth', 'login', 'token', 'bearer']):
            request['auth_type'] = 'Bearer Token'
            request['headers'].append({
                'key': 'Authorization',
                'value': 'Bearer {{accessToken}}',
                'enabled': True
            })

        return request

    def _basic_documentation_generation(self, collection_name: str, requests: list) -> str:
        """Basic documentation generation without AI."""

        doc_lines = [
            f"# {collection_name}",
            "",
            "## Overview",
            f"This collection contains {len(requests)} API requests for testing {collection_name}.",
            "",
            "## Endpoints",
            ""
        ]

        for req in requests[:10]:  # Limit to first 10 requests
            doc_lines.extend([
                f"### {req.get('method', 'GET')} {req.get('name', 'Unnamed Request')}",
                f"- **URL**: {req.get('url', '')}",
                f"- **Method**: {req.get('method', 'GET')}",
            ])

            if req.get('headers'):
                headers = [h for h in req.get('headers', []) if h.get('enabled', True)]
                if headers:
                    doc_lines.append("- **Headers**:")
                    for header in headers[:3]:  # Show first 3 headers
                        doc_lines.append(f"  - {header.get('key', '')}: {header.get('value', '')}")

            if req.get('body') and req['body'].strip():
                doc_lines.extend([
                    "- **Request Body**:",
                    f"  ```json\n  {req['body']}\n  ```"
                ])

            doc_lines.append("")

        return "\n".join(doc_lines)


# Singleton instance
ai_service = AIService()