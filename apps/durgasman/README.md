# Durgasman API Testing App

Durgasman is a Postman-like API testing application integrated with the DocsAI documentation system. It allows users to browse API documentation files and seamlessly open them for testing.

## Features

- **Postman Collection Import**: Import Postman v2.1 collections with full folder support
- **Environment Management**: Variable replacement with `{{variable}}` syntax
- **GraphQL Support**: Native support for GraphQL queries and mutations
- **AI-Powered Analysis**: Response analysis and intelligent request generation
- **Request History**: Automatic tracking of all API calls
- **Mock Server**: Local mock endpoints for testing
- **Modern UI**: Dark theme, responsive design

## Quick Start

### 1. Import from Media Manager

1. Go to Media Manager: `/docs/media-manager/`
2. Find Postman collections or endpoint JSON files
3. Click "Open in Durgasman" button
4. Collections are automatically imported and ready to test

### 2. Manual Import

```bash
# Test imports
python manage.py import_test

# Create demo data
python manage.py demo_data
```

### 3. Using Durgasman

1. Navigate to `/durgasman/`
2. Select a collection from the sidebar
3. Choose a request to test
4. Configure parameters, headers, and body
5. Click "Send" to execute the request
6. View response with AI analysis

## Architecture

### Models

- **Collection**: Groups API requests
- **ApiRequest**: Individual API requests with method, URL, headers, body
- **Environment**: Variable management with key-value pairs
- **RequestHistory**: Execution tracking and responses
- **MockEndpoint**: Local mock server endpoints

### Services

- **postman_importer.py**: Imports Postman collections and environments
- **endpoint_importer.py**: Converts endpoint JSON to API requests
- **executor.py**: HTTP request execution with variable resolution
- **ai_service.py**: AI-powered analysis and generation

### Frontend Components

- **request-builder.js**: API request construction interface
- **response-viewer.js**: Response display with JSON highlighting
- **sidebar.js**: Collections and environments navigation
- **durgasman-controller.js**: Main application state management

## API Endpoints

- `GET /durgasman/api/collections/` - List user collections
- `GET /durgasman/api/collections/{id}/requests/` - Get collection requests
- `POST /durgasman/api/execute/` - Execute API request
- `POST /durgasman/api/analyze/` - AI response analysis
- `GET /durgasman/api/environments/` - List environments

## Import Formats

### Postman Collections

Durgasman imports Postman v2.1 collections with:
- Nested folders and requests
- Authentication settings
- Query parameters and headers
- Request bodies (raw JSON)

### Endpoint JSON

Converts DocsAI endpoint metadata to executable requests:
- GraphQL operations with variables
- Authentication headers
- Response schemas

### Environment Variables

Supports Postman environment format:
```json
{
  "name": "Production",
  "values": [
    {"key": "baseUrl", "value": "https://api.example.com", "enabled": true}
  ]
}
```

## Variable Syntax

Use `{{variableName}}` in URLs, headers, and request bodies:

```
URL: {{baseUrl}}/api/v1/users/{{userId}}
Header: Authorization: Bearer {{accessToken}}
Body: {"email": "{{userEmail}}"}
```

## AI Features

### Response Analysis
- Automatic success/error detection
- Performance analysis (response time)
- Schema validation
- Error pattern recognition

### Request Generation
- Natural language to API request conversion
- Schema-aware request building
- Authentication setup

## Development

### Running Tests

```bash
# Django system checks
python manage.py check durgasman

# Import testing
python manage.py import_test

# Demo data creation
python manage.py demo_data
```

### Adding New Features

1. **Models**: Add new fields to models.py, create migrations
2. **Services**: Add business logic to services/
3. **Views**: Add API endpoints to views.py
4. **Frontend**: Add components to static/js/components/durgasman/
5. **Templates**: Update templates in templates/durgasman/

## Integration Points

### Media Manager
- Automatic "Open in Durgasman" buttons for compatible files
- URL-based import workflow

### DocsAI Relationships
- Link API requests to documented endpoints
- Visualize API usage in relationship graphs

### Authentication
- Uses Django user system
- User-scoped collections and environments

## Troubleshooting

### Import Issues
- Check file paths in media directory
- Verify JSON format validity
- Check Django user permissions

### Request Execution
- Verify environment variables are set
- Check network connectivity
- Review request configuration

### UI Issues
- Check browser console for JavaScript errors
- Verify static files are served correctly
- Check CSRF token validity

## Security

- File path validation for imports
- User-scoped data isolation
- CSRF protection on all forms
- Input sanitization and validation

## Performance

- Asynchronous request execution
- Database indexing on frequently queried fields
- Response caching for repeated requests
- Efficient JSON handling

## Future Enhancements

- WebSocket testing support
- Bulk request execution
- Request chaining (use response data in next request)
- Code snippet generation (cURL, Python, JavaScript)
- Team collaboration features
- Advanced mocking with dynamic responses