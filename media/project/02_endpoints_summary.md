# Endpoints Collection Summary Report

**Generated:** 2026-01-20  
**Total Endpoints:** 145

## Overview

This report provides a comprehensive summary of all GraphQL API endpoints in the Contact360 system, including their methods, authentication requirements, usage patterns, and relationships to pages.

## Method Distribution

| Method | Count | Percentage |
|--------|-------|------------|
| **QUERY** | 80 | 55.17% |
| **MUTATION** | 65 | 44.83% |

## API Version

- **GraphQL:** 145 endpoints (100%)
- All endpoints use GraphQL API

## Authentication Distribution

| Authentication Type | Count | Percentage |
|---------------------|-------|------------|
| **Bearer token (JWT)** | 139 | 95.86% |
| **Not required** | 6 | 4.14% |

### Public Endpoints (No Authentication)
- `mutation_login_graphql`
- `mutation_register_graphql`
- `query_get_marketing_page_graphql` (for public pages)
- `query_get_documentation_page_graphql` (for public docs)
- `query_get_documentation_content_graphql`
- `query_list_documentation_pages_graphql`

## Authorization Distribution

| Authorization Level | Count | Percentage |
|---------------------|-------|------------|
| **User role required** | 120 | 82.76% |
| **Admin role required** | 15 | 10.34% |
| **Super Admin role required** | 5 | 3.45% |
| **Pro user role required** | 2 | 1.38% |
| **No authorization** | 3 | 2.07% |

## Endpoint Usage

### Endpoints with Pages
- **Total:** 95 endpoints (65.52%)
- **Average pages per endpoint:** 1.2

### Endpoints without Pages
- **Total:** 50 endpoints (34.48%)
- These may be:
  - Internal/admin-only endpoints
  - Recently added endpoints not yet integrated
  - Utility endpoints used programmatically

### Most Used Endpoints

1. **`query_get_marketing_page_graphql`** - 14 pages
   - Used by all marketing pages and admin marketing editor
   
2. **`query_get_activities_graphql`** - 3 pages
   - Used by activities page, dashboard, and verifier
   
3. **`query_get_dashboard_page_graphql`** - 2 pages
   - Used by dynamic dashboard and admin editor

## Endpoint Categories

### Authentication & User Management (6 endpoints)
- Login, Register, GetMe, GetSession, RefreshToken, Logout

### Companies (5 endpoints)
- QueryCompanies, GetCompany, GetCompanyFilters, GetCompanyContacts, DeleteCompany

### Contacts (3 endpoints)
- QueryContacts, GetContact, CountContacts

### Email Operations (7 endpoints)
- FindSingleEmail, VerifyAndFind, VerifySingleEmail, VerifyBulkEmails, GenerateAndVerify, AnalyzeEmailRisk, FindEmails

### Dashboard Pages (5 endpoints)
- GetDashboardPage, ListDashboardPages, CreateDashboardPage, UpdateDashboardPage, DeleteDashboardPage

### Marketing Pages (8 endpoints)
- GetMarketingPage, ListMarketingPages, AdminMarketingPages, CreateMarketingPage, UpdateMarketingPage, DeleteMarketingPage, PublishMarketingPage, HardDeleteMarketingPage

### Activities (2 endpoints)
- GetActivities, GetActivityStats

### Exports (7 endpoints)
- ListExports, GetExport, CancelExport, CreateContactExport, CreateCompanyExport, ExportEmails, ExportLinkedIn

### Billing (16 endpoints)
- GetBilling, GetPlans, GetAdminPlans, GetAddons, GetAdminAddons, GetInvoices, Subscribe, PurchaseAddon, CancelSubscription, CreatePlan, UpdatePlan, DeletePlan, CreatePlanPeriod, DeletePlanPeriod, CreateAddon, UpdateAddon, DeleteAddon

### Profile & Settings (9 endpoints)
- GetUser, UpdateProfile, UploadAvatar, ListAPIKeys, CreateAPIKey, DeleteAPIKey, ListSessions, RevokeSession, ListTeamMembers

### Two-Factor Authentication (5 endpoints)
- Get2FAStatus, Setup2FA, Verify2FA, Disable2FA, RegenerateBackupCodes

### Saved Searches (6 endpoints)
- ListSavedSearches, GetSavedSearch, CreateSavedSearch, UpdateSavedSearch, DeleteSavedSearch, UpdateSavedSearchUsage

### Usage Tracking (3 endpoints)
- GetUsage, TrackUsage, ResetUsage

### AI Chat (6 endpoints)
- ListAIChats, GetAIChat, CreateAIChat, UpdateAIChat, DeleteAIChat, SendMessage

### LinkedIn Integration (4 endpoints)
- SearchLinkedIn, UpsertByLinkedInUrl, SaveProfiles, ListScrapingRecords

### Admin Operations (8 endpoints)
- ListUsers, GetUserStats, UpdateUserRole, UpdateUserCredits, DeleteUser, GetUserHistory, PromoteToAdmin, PromoteToSuperAdmin

### System Logs (8 endpoints)
- QueryLogs, SearchLogs, GetLogStatistics, CreateLog, CreateLogsBatch, UpdateLog, DeleteLog, DeleteLogsBulk

### Notifications (5 endpoints)
- ListNotifications, GetUnreadCount, MarkAsRead, DeleteNotifications, UpdatePreferences

### S3 File Management (9 endpoints)
- ListS3Files, GetS3FileData, GetS3FileDownloadUrl, GetUploadStatus, GetPresignedUrl, InitiateUpload, RegisterPart, CompleteUpload, AbortUpload

### Job Management (8 endpoints)
- ListJobs, GetJob, CreateJob, ListImportJobs, GetImportJob, CreateImportJob, CreateExportJob, GetUploadUrl, GetExportDownloadUrl

### Documentation (6 endpoints)
- GetDocumentationPage, GetDocumentationContent, ListDocumentationPages, CreateDocumentationPage, UpdateDocumentationPage, DeleteDocumentationPage

### Health & Monitoring (4 endpoints)
- GetHealth, GetAPIMetadata, GetVQLHealth, GetVQLStats

### Analytics (3 endpoints)
- GetPerformanceMetrics, AggregateMetrics, SubmitMetric

### Company Operations (2 endpoints)
- GenerateCompanySummary, ParseFilters

## Key Insights

1. **Query-Heavy API:** 55% of endpoints are queries (read operations), 45% are mutations (write operations)
2. **High Security:** 96% of endpoints require JWT authentication
3. **Role-Based Access:** 15% of endpoints require admin/super admin roles
4. **Page Integration:** 66% of endpoints are used by pages, 34% are standalone/internal
5. **Marketing Page Endpoint:** `GetMarketingPage` is the most used endpoint (14 pages)
6. **Comprehensive Coverage:** Endpoints cover all major features: data management, billing, admin, AI, integrations

## Service Layer Patterns

### Service Methods
- Most endpoints have 1-2 service methods
- Service methods follow naming conventions: `get*`, `list*`, `create*`, `update*`, `delete*`
- Services are organized by domain: `emailService`, `companiesService`, `contactsService`, `billingService`, etc.

### Repository Methods
- Most GraphQL endpoints don't have repository_methods (direct service calls)
- Repository layer is abstracted in service layer

## Rate Limiting

- **Most endpoints:** No rate limit specified (null)
- Rate limits would be enforced at API gateway level

## Next Steps

1. Complete detailed endpoint analysis
2. Map all service and repository methods
3. Analyze endpoint usage patterns
4. Identify unused endpoints
5. Generate endpoint dependency graph
6. Create relationship mappings
