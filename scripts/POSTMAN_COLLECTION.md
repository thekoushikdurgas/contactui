# Contact360 GraphQL API - Postman Collection

> **Note**: This file was renamed from `README (2).md` to `POSTMAN_COLLECTION.md` to better reflect its content.

Complete Postman collection for the Contact360 GraphQL API with all 25 modules.

> **📚 For comprehensive module documentation**, see [GraphQL Modules Documentation](../GraphQL/README.md) which includes detailed queries, mutations, validation rules, error handling, and implementation details for each module.

## Files

- **Contact360_GraphQL_API.postman_collection.json** - Main collection with all requests
- **Contact360_Local.postman_environment.json** - Local development environment
- **Contact360_Production.postman_environment.json** - Production environment

## Quick Start

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Import both:
   - `Contact360_GraphQL_API.postman_collection.json`
   - `Contact360_Local.postman_environment.json` (or Production)
4. Select the imported environment from the environment dropdown

### 2. Authenticate

1. Go to **Auth** folder
2. Run **Login** or **Register** request
3. Tokens are automatically saved to environment variables
4. All other requests will use the saved `accessToken`

### 3. Use the API

- Browse requests by module folder
- Modify variables as needed
- Check responses and error messages

## Collection Structure

The collection is organized into module folders:

### Core Modules

- **Auth** - Authentication, login, registration, token management
- **Users** - User management, profiles, avatars, role promotion (SuperAdmin only)
- **Health** - Health checks, API metadata, performance stats, logging health (includes REST endpoints)
- **Saved Searches** - Save and manage search queries with filters and sorting
- **Two-Factor Authentication** - 2FA setup, verification, and backup codes
- **Profile** - API keys, sessions, and team management

### Data Modules

- **Contacts** - Contact queries, VQL queries, filtering, filter metadata
- **Companies** - Company queries, VQL queries, company contacts, filter metadata
- **Activities** - Activity tracking and statistics

### Communication Modules

- **Email** - Email finder, verification, bulk operations
- **Notifications** - Notification management, preferences
- **AI Chats** - AI chat conversations and Gemini AI operations (email risk analysis, company summaries, filter parsing)

### File & Storage Modules

- **Jobs** - Background job management (exports, generic jobs), S3 upload URLs, export download URLs
- **Imports** - CSV import job management for contacts and companies
- **S3** - S3 file operations, CSV reading
- **Upload** - Multipart file uploads to S3
- **Exports** - Export job management

### Business Modules

- **Billing** - Subscriptions, plans, addons, invoices
- **Usage** - Feature usage tracking
- **Analytics** - Performance metrics tracking

### Integration Modules

- **LinkedIn** - LinkedIn URL search and export
- **Sales Navigator** - Sales Navigator profile saving to Connectra

### Content Management Modules

- **Dashboard Pages** - Dashboard page management with RBAC
- **Documentation** - Documentation page management
- **Marketing** - Marketing page management

### Administration Modules

- **Admin** - User management, statistics, logs (Admin/SuperAdmin only)

### User Account Modules

- **Saved Searches** - Save and manage search queries with filters and sorting
- **Two-Factor Authentication** - 2FA setup, verification, and backup codes
- **Profile** - API keys, sessions, and team management

## Environment Variables

### Required Variables

- `baseUrl` - API base URL (e.g., `http://localhost:8000`)
- `accessToken` - JWT access token (auto-populated after login)
- `refreshToken` - JWT refresh token (auto-populated after login)
- `userId` - Current user UUID (auto-populated after login)

### Optional Variables

- `email` - User email for login/register
- `password` - User password for login/register
- `name` - User name for registration
- `contactUuid` - Contact UUID for contact operations
- `companyUuid` - Company UUID for company operations
- `exportId` - Export ID for export operations
- `jobUuid` - Job UUID for Connectra job operations
- `notificationId` - Notification ID for notification operations
- `chatId` - AI Chat ID for chat operations
- `uploadId` - Upload ID for upload operations

## Authentication Flow

1. **Login or Register** → Gets `accessToken` and `refreshToken`
2. Tokens are automatically saved to environment
3. All subsequent requests use `Bearer {{accessToken}}` header
4. **Refresh Token** → Use when access token expires
5. **Logout** → Invalidates current token

## Public Endpoints

These endpoints don't require authentication:

### GraphQL Queries

- `health.apiMetadata`
- `health.apiHealth`
- `billing.plans`
- `billing.addons`
- `documentation.*` (all queries)
- `marketing.marketingPage` (published pages only)
- `marketing.marketingPages`

### REST Endpoints

- `GET /health` - Basic API health check
- `GET /health/db` - Database health check
- `GET /health/logging` - Logging system health and metrics

## Admin/SuperAdmin Endpoints

These require Admin or SuperAdmin role:

- Most **Admin** module operations
- **Users** promotion operations (`promoteToAdmin`, `promoteToSuperAdmin`) - SuperAdmin only
- **Billing** plan/addon management
- **Dashboard Pages** CRUD operations
- **Documentation** CRUD operations
- **Marketing** CRUD operations

## Request Examples

### Login

```json
{
  "query": "mutation Login($input: LoginInput!) { auth { login(input: $input) { accessToken refreshToken user { uuid email name } } } }",
  "variables": {
    "input": {
      "email": "user@example.com",
      "password": "password123"
    }
  }
}
```

### Get Current User

```json
{
  "query": "query { auth { me { uuid email name profile { role credits } } } }"
}
```

### List Contacts

```json
{
  "query": "query ListContacts($query: VQLQueryInput) { contacts { contacts(query: $query) { items { uuid firstName lastName email } total } } }",
  "variables": {
    "filters": {
      "limit": 50,
      "offset": 0
    }
  }
}
```

## Response Examples

The collection includes comprehensive response examples for each request:

### Success Responses

- All requests include example success responses (200 OK)
- Responses match the actual GraphQL schema structure
- Use these as reference when building your own queries

### Error Responses

Each request includes multiple error response examples:

- **401 Unauthorized** - Authentication required (for non-auth requests)
- **422 Validation Error** - Input validation failed with field-level errors
- **404 Not Found** - Resource not found (for queries with UUIDs)
- **403 Forbidden** - Insufficient permissions (for mutations and admin operations)
- **400 Bad Request** - Invalid request data (for mutations)
- **503 Service Unavailable** - External service unavailable (for service-dependent operations)

All error responses follow the GraphQL error format with `extensions` containing:
- `code`: Error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
- `statusCode`: HTTP status code
- Additional context (e.g., `resourceType`, `identifier`, `fieldErrors`, `serviceName`)

**Example Error Response:**
```json
{
  "errors": [{
    "message": "Resource with identifier '123e4567-e89b-12d3-a456-426614174000' not found",
    "extensions": {
      "code": "NOT_FOUND",
      "statusCode": 404,
      "resourceType": "Resource",
      "identifier": "123e4567-e89b-12d3-a456-426614174000"
    }
  }]
}
```

## Tips

1. **Use Variables** - Always use environment variables for dynamic values
2. **Check Responses** - Review response structure before modifying queries
3. **Error Handling** - Check `errors` array in GraphQL responses - each request includes multiple error examples
4. **Token Refresh** - Use Refresh Token request when access token expires
5. **Environment Switching** - Switch between Local/Production environments as needed
6. **Health Monitoring** - Use REST endpoints (`/health`, `/health/db`, `/health/logging`) for quick health checks
7. **Logging Health** - Monitor logging system via `GET /health/logging` to check metrics and system health
8. **Error Examples** - Review error response examples in each request to understand error handling patterns

## Logging System Health

The collection includes a REST endpoint for monitoring the logging system:

**Endpoint:** `GET /health/logging` (in Health folder)

**Features:**

- No authentication required
- Returns comprehensive metrics:
  - Logs sent/failed counts
  - Queue and fallback buffer sizes
  - API call statistics
  - Success rates
  - Error type breakdown
  - Health check statistics

**Example Response:**
```json
{
  "status": "healthy",
  "metrics": {
    "logs_sent": 10000,
    "logs_failed": 50,
    "logs_in_queue": 25,
    "logs_in_fallback": 0,
    "success_rate": 99.5
  }
}
```

For more details, see [Health Module Documentation](../GraphQL/08_HEALTH_MODULE.md#rest-endpoints).

## Troubleshooting

### 401 Unauthorized

- Check if `accessToken` is set in environment
- Try logging in again
- Check if token has expired (use Refresh Token)

### 403 Forbidden

- Check user role (some operations require Admin/SuperAdmin)
- Verify you have permissions for the operation

### 422 Validation Error

- Check request variables format
- Verify required fields are provided
- Check field types match expected types

### 503 Service Unavailable

- External service (Connectra, Lambda) may be down
- Check health endpoints for service status

## Related Documentation

- **[GraphQL Modules Documentation](../GraphQL/README.md)** - **Comprehensive documentation** for all 22 modules with:
  - Detailed query and mutation documentation
  - Validation rules and limits
  - Error handling patterns
  - Implementation details
  - Usage examples
- [GraphQL API Reference](../GRAPHQL_API.md) - Quick API reference
- [Architecture Documentation](../ARCHITECTURE.md) - System architecture

## Support

For issues or questions:

1. Check the GraphQL module documentation in `docs/GraphQL/`
2. Review error messages in responses
3. Check API health endpoints
4. Verify environment variables are set correctly
