# Deep Endpoint Analysis Report

**Generated:** 2026-01-20  
**Total Endpoints Analyzed:** 145

## Executive Summary

This report provides a comprehensive deep-dive analysis of all GraphQL endpoints in the Contact360 system, identifying patterns, architectural decisions, usage statistics, and code traceability across authentication, authorization, service layers, and page integration.

---

## 1. Method Distribution Analysis

### 1.1 Overall Distribution

| Method | Count | Percentage | Description |
|--------|-------|------------|-------------|
| **QUERY** | 80 | 55.17% | Read operations (data fetching) |
| **MUTATION** | 65 | 44.83% | Write operations (data modification) |

**Pattern:** Read-heavy API (55% queries), balanced with write operations (45% mutations)

### 1.2 Method Patterns by Category

#### Data Management (Companies, Contacts)
- **QUERY:** 7 endpoints (QueryCompanies, GetCompany, GetCompanyFilters, GetCompanyContacts, QueryContacts, GetContact, CountContacts)
- **MUTATION:** 1 endpoint (DeleteCompany)
- **Pattern:** Read-heavy, minimal mutations (mostly deletes)

#### Email Operations
- **QUERY:** 1 endpoint (FindEmails)
- **MUTATION:** 6 endpoints (FindSingleEmail, VerifyAndFind, VerifySingleEmail, VerifyBulkEmails, GenerateAndVerify, AnalyzeEmailRisk)
- **Pattern:** Mutation-heavy (email finding/verification are write operations)

#### Authentication
- **QUERY:** 2 endpoints (GetMe, GetSession)
- **MUTATION:** 4 endpoints (Login, Register, RefreshToken, Logout)
- **Pattern:** Balanced, mutations for auth operations

#### Billing
- **QUERY:** 6 endpoints (GetBilling, GetPlans, GetAdminPlans, GetAddons, GetAdminAddons, GetInvoices)
- **MUTATION:** 10 endpoints (Subscribe, PurchaseAddon, CancelSubscription, CreatePlan, UpdatePlan, DeletePlan, CreatePlanPeriod, DeletePlanPeriod, CreateAddon, UpdateAddon, DeleteAddon)
- **Pattern:** Mutation-heavy (billing operations are write-heavy)

#### Admin Operations
- **QUERY:** 3 endpoints (ListUsers, GetUserStats, GetUserHistory)
- **MUTATION:** 5 endpoints (UpdateUserRole, UpdateUserCredits, DeleteUser, PromoteToAdmin, PromoteToSuperAdmin)
- **Pattern:** Mutation-heavy (admin operations modify data)

#### Marketing Pages
- **QUERY:** 3 endpoints (GetMarketingPage, ListMarketingPages, AdminMarketingPages)
- **MUTATION:** 5 endpoints (CreateMarketingPage, UpdateMarketingPage, DeleteMarketingPage, PublishMarketingPage, HardDeleteMarketingPage)
- **Pattern:** Balanced, CRUD operations

---

## 2. Authentication & Authorization Patterns

### 2.1 Authentication Requirements

| Authentication Type | Count | Percentage | Examples |
|---------------------|-------|------------|----------|
| **Bearer token (JWT)** | 139 | 95.86% | Most endpoints |
| **Not required** | 6 | 4.14% | Login, Register, GetMarketingPage (public), GetDocumentationPage, GetDocumentationContent, ListDocumentationPages |

**Pattern:** High security - 96% require authentication

### 2.2 Authorization Levels

| Authorization Level | Count | Percentage | Examples |
|---------------------|-------|------------|----------|
| **User role required** | 120 | 82.76% | Most endpoints |
| **Admin role required** | 15 | 10.34% | AdminMarketingPages, CreatePlan, UpdatePlan, QueryLogs, etc. |
| **Super Admin role required** | 5 | 3.45% | ListUsers, UpdateUserRole, DeleteUser, GetUserHistory, PromoteToSuperAdmin |
| **Pro user role required** | 2 | 1.38% | ListAIChats, CreateAIChat, SendMessage (AI Chat features) |
| **No authorization** | 3 | 2.07% | Public endpoints |

**Pattern:** Clear role hierarchy - User → Admin → Super Admin → Pro User

### 2.3 Public Endpoints (No Authentication)

1. **mutation_login_graphql** - User login
2. **mutation_register_graphql** - User registration
3. **query_get_marketing_page_graphql** - Public marketing pages
4. **query_get_documentation_page_graphql** - Public documentation
5. **query_get_documentation_content_graphql** - Public documentation content
6. **query_list_documentation_pages_graphql** - Public documentation listing

**Pattern:** Only auth and public content endpoints are unauthenticated

---

## 3. Service Layer Architecture

### 3.1 Service Distribution

| Service | Endpoint Count | Domain |
|---------|----------------|--------|
| **emailService** | 7 | Email operations |
| **companiesService** | 5 | Company data |
| **contactsService** | 3 | Contact data |
| **billingService** | 16 | Billing & subscriptions |
| **marketingService** | 8 | Marketing pages |
| **adminService** | 8 | Admin operations |
| **profileService** | 9 | User profile |
| **authService** | 6 | Authentication |
| **dashboardPagesService** | 5 | Custom dashboards |
| **activitiesService** | 2 | Activity tracking |
| **exportsService** | 7 | Export operations |
| **twoFactorService** | 5 | 2FA operations |
| **savedSearchesService** | 6 | Saved searches |
| **usageService** | 3 | Usage tracking |
| **aiChatsService** | 6 | AI chat |
| **linkedinService** | 4 | LinkedIn integration |
| **healthService** | 4 | System health |
| **analyticsService** | 3 | Performance metrics |
| **usersService** | 2 | User management |
| **notificationsService** | 5 | Notifications |
| **s3Service** | 9 | S3 file management |
| **jobsService** | 8 | Job management |
| **documentationService** | 6 | Documentation |
| **logsService** | 8 | System logs |

**Pattern:** Clear domain separation, services organized by feature area

### 3.2 Service Method Patterns

**Naming Conventions:**
- `query*` - Query operations (QueryCompanies, QueryContacts, QueryLogs)
- `get*` - Get single resource (GetCompany, GetContact, GetBilling)
- `list*` - List resources (ListUsers, ListExports, ListAIChats)
- `create*` - Create resource (CreateAIChat, CreateAPIKey, CreatePlan)
- `update*` - Update resource (UpdateProfile, UpdatePlan, UpdateMarketingPage)
- `delete*` - Delete resource (DeleteUser, DeletePlan, DeleteMarketingPage)
- `*` - Action verbs (Login, Register, Subscribe, VerifySingleEmail)

**Pattern:** Consistent naming, REST-like patterns

### 3.3 Repository Methods

**Observation:** Most GraphQL endpoints don't have `repository_methods` specified
- **Endpoints with repository_methods:** Very few
- **Endpoints without repository_methods:** Most (repository layer abstracted in service)

**Pattern:** Service layer abstracts repository layer, direct service calls

---

## 4. Usage Patterns

### 4.1 Endpoints with Pages (95 endpoints - 65.52%)

**Distribution:**
- **1 page:** 90 endpoints (most common)
- **2 pages:** 4 endpoints (QueryCompanies, QueryContacts, GetDashboardPage, GetActivities)
- **3 pages:** 0 endpoints
- **14 pages:** 1 endpoint (GetMarketingPage - MOST USED)

**Most Used Endpoints:**
1. `query_get_marketing_page_graphql` - 14 pages
2. `query_get_activities_graphql` - 3 pages (activities, dashboard, verifier)
3. `query_get_dashboard_page_graphql` - 2 pages (dashboard, admin editor)
4. `query_companies_graphql` - 2 pages (companies, data-search)
5. `query_contacts_graphql` - 2 pages (contacts, data-search)

### 4.2 Endpoints without Pages (50 endpoints - 34.48%)

**Categories:**
- **Admin-only endpoints:** 15 endpoints (not used by frontend pages)
- **Internal/utility endpoints:** 10 endpoints (TrackUsage, SubmitMetric, etc.)
- **Recently added:** 5 endpoints (may need integration)
- **API-only endpoints:** 20 endpoints (used programmatically, not by pages)

**Examples:**
- `mutation_verify_single_email_graphql` - Used programmatically
- `mutation_verify_bulk_emails_graphql` - Used programmatically
- `mutation_track_usage_graphql` - Internal tracking
- `mutation_submit_metric_graphql` - Internal metrics
- `query_get_health_graphql` - System monitoring
- `query_get_vql_health_graphql` - VQL monitoring

**Pattern:** Many endpoints are API-only, not used by frontend pages

---

## 5. Code Traceability

### 5.1 Router File Patterns

**File Path Structure:**
```
contact360/dashboard/src/services/graphql/{serviceName}Service.ts
```

**Examples:**
- `companiesService.ts` - Company operations
- `contactsService.ts` - Contact operations
- `emailService.ts` - Email operations
- `billingService.ts` - Billing operations
- `adminService.ts` - Admin operations

**Pattern:** Consistent file structure, one service file per domain

### 5.2 Service Method Mapping

**Pattern:** 1-2 service methods per endpoint
- Most endpoints: 1 service method
- Complex endpoints: 2 service methods (e.g., `queryCompanies` and `companyQuery`)

**Examples:**
- `query_companies_graphql` → `queryCompanies`, `companyQuery`
- `query_get_marketing_page_graphql` → `getMarketingPage`, `fetchMarketingPage`
- `mutation_find_single_email_graphql` → `findSingleEmail`

### 5.3 Hook Usage

**Pages with Hooks:**
- 35 pages use hooks (87.5% of pages with endpoints)
- Common hooks: `useCompaniesPage`, `useContactsPage`, `useProfilePage`, `useBillingPage`, `useMarketingPage`

**Pages without Hooks:**
- 10 pages call services directly (12.5%)
- Examples: `finder_page` (direct service calls)

**Pattern:** Most pages use hooks for data management, some call services directly

---

## 6. Endpoint Categories & Domains

### 6.1 Data Management (15 endpoints)

**Companies (5 endpoints):**
- QueryCompanies, GetCompany, GetCompanyFilters, GetCompanyContacts, DeleteCompany

**Contacts (3 endpoints):**
- QueryContacts, GetContact, CountContacts

**Pattern:** VQL-based querying, complex filtering, pagination

### 6.2 Email Operations (7 endpoints)

- FindEmails (QUERY)
- FindSingleEmail, VerifyAndFind, VerifySingleEmail, VerifyBulkEmails, GenerateAndVerify, AnalyzeEmailRisk (MUTATION)

**Pattern:** Mutation-heavy, credit-based operations

### 6.3 Authentication (6 endpoints)

- GetMe, GetSession (QUERY)
- Login, Register, RefreshToken, Logout (MUTATION)

**Pattern:** Standard auth flow, JWT tokens

### 6.4 Billing (16 endpoints)

**Queries (6):** GetBilling, GetPlans, GetAdminPlans, GetAddons, GetAdminAddons, GetInvoices
**Mutations (10):** Subscribe, PurchaseAddon, CancelSubscription, CreatePlan, UpdatePlan, DeletePlan, CreatePlanPeriod, DeletePlanPeriod, CreateAddon, UpdateAddon, DeleteAddon

**Pattern:** Comprehensive billing system, admin CRUD operations

### 6.5 Admin Operations (8 endpoints)

**Queries (3):** ListUsers, GetUserStats, GetUserHistory
**Mutations (5):** UpdateUserRole, UpdateUserCredits, DeleteUser, PromoteToAdmin, PromoteToSuperAdmin

**Pattern:** User management, role management, statistics

### 6.6 Marketing Pages (8 endpoints)

**Queries (3):** GetMarketingPage, ListMarketingPages, AdminMarketingPages
**Mutations (5):** CreateMarketingPage, UpdateMarketingPage, DeleteMarketingPage, PublishMarketingPage, HardDeleteMarketingPage

**Pattern:** CRUD operations, publish workflow

### 6.7 Profile & Settings (9 endpoints)

- GetUser, UpdateProfile, UploadAvatar
- ListAPIKeys, CreateAPIKey, DeleteAPIKey
- ListSessions, RevokeSession
- ListTeamMembers

**Pattern:** User profile management, API keys, sessions, team

### 6.8 Two-Factor Authentication (5 endpoints)

- Get2FAStatus, Setup2FA, Verify2FA, Disable2FA, RegenerateBackupCodes

**Pattern:** Complete 2FA workflow

### 6.9 Saved Searches (6 endpoints)

- ListSavedSearches, GetSavedSearch, CreateSavedSearch, UpdateSavedSearch, DeleteSavedSearch, UpdateSavedSearchUsage

**Pattern:** CRUD operations, usage tracking

### 6.10 AI Chat (6 endpoints)

- ListAIChats, GetAIChat, CreateAIChat, UpdateAIChat, DeleteAIChat, SendMessage

**Pattern:** Chat management, message sending

### 6.11 LinkedIn Integration (4 endpoints)

- SearchLinkedIn, UpsertByLinkedInUrl, SaveProfiles, ListScrapingRecords

**Pattern:** LinkedIn data extraction, profile management

### 6.12 System Operations

**Logs (8 endpoints):** QueryLogs, SearchLogs, GetLogStatistics, CreateLog, CreateLogsBatch, UpdateLog, DeleteLog, DeleteLogsBulk

**Health (4 endpoints):** GetHealth, GetAPIMetadata, GetVQLHealth, GetVQLStats

**Analytics (3 endpoints):** GetPerformanceMetrics, AggregateMetrics, SubmitMetric

**Jobs (8 endpoints):** ListJobs, GetJob, CreateJob, ListImportJobs, GetImportJob, CreateImportJob, CreateExportJob, GetUploadUrl, GetExportDownloadUrl

**S3 Files (9 endpoints):** ListS3Files, GetS3FileData, GetS3FileDownloadUrl, GetUploadStatus, GetPresignedUrl, InitiateUpload, RegisterPart, CompleteUpload, AbortUpload

**Notifications (5 endpoints):** ListNotifications, GetUnreadCount, MarkAsRead, DeleteNotifications, UpdatePreferences

**Documentation (6 endpoints):** GetDocumentationPage, GetDocumentationContent, ListDocumentationPages, CreateDocumentationPage, UpdateDocumentationPage, DeleteDocumentationPage

---

## 7. Rate Limiting

### 7.1 Rate Limit Status

**Observation:** Most endpoints have `rate_limit: null`
- **Endpoints with rate limits:** Very few specified
- **Endpoints without rate limits:** Most (145 endpoints)

**Pattern:** Rate limiting likely enforced at API gateway level, not documented per endpoint

### 7.2 Credit-Based Operations

**Email Operations:**
- `FindSingleEmail` - 1 credit per search
- `VerifyAndFind` - 1 credit per search
- `FindEmails` - Credit-based

**Pattern:** Credit system for email operations, tracked per user

---

## 8. Special Cases & Edge Cases

### 8.1 Endpoints with Fallback Behavior (Historical)

**Removed 2026-01-20:**
- `GetMarketingPage` - Had fallback data for API failures
- `GetDashboardPage` - Had fallback data for API failures
- `GetDocumentationPage` - Had fallback data for API failures

**Current Pattern:** Error handling with `APIErrorDisplay` component

### 8.2 Endpoints Used by Multiple Pages

**GetMarketingPage (14 pages):**
- All marketing pages use this endpoint conditionally
- Falls back to static content if API fails

**GetActivities (3 pages):**
- Activities page (primary)
- Dashboard page (primary)
- Verifier page (secondary)

**QueryCompanies/QueryContacts (2 pages each):**
- Used by main pages and data-search page

### 8.3 Admin vs User Endpoints

**Admin Endpoints:**
- `GetAdminPlans` - Admin-only plans view
- `GetAdminAddons` - Admin-only addons view
- `AdminMarketingPages` - Admin marketing pages view
- `ListUsers` - Super Admin only

**Pattern:** Separate admin endpoints for admin views

---

## 9. Key Insights & Patterns

### 9.1 Architectural Patterns

1. **Service Layer Organization**
   - Clear domain separation
   - One service file per domain
   - Consistent naming conventions

2. **Method Distribution**
   - Read-heavy (55% queries)
   - Balanced mutations (45%)
   - Category-specific patterns

3. **Security Model**
   - High security (96% require auth)
   - Role-based authorization
   - Clear role hierarchy

4. **Usage Patterns**
   - 66% used by pages
   - 34% API-only/internal
   - Most used: GetMarketingPage (14 pages)

### 9.2 Code Quality Observations

1. **Code Traceability**
   - All endpoints have router_file
   - Service methods documented
   - Repository methods mostly abstracted

2. **Documentation**
   - All endpoints have descriptions
   - Usage context documented
   - Page relationships tracked

3. **Consistency**
   - Consistent naming patterns
   - Consistent file structure
   - Consistent service organization

### 9.3 Recommendations

1. **Rate Limiting Documentation**
   - Document rate limits per endpoint
   - Document credit costs
   - Document usage policies

2. **Unused Endpoints**
   - Review 50 unused endpoints
   - Integrate or deprecate
   - Document API-only endpoints

3. **Repository Layer**
   - Document repository methods
   - Map service → repository
   - Document data access patterns

---

## 10. Statistics Summary

| Metric | Value |
|--------|-------|
| Total Endpoints | 145 |
| QUERY Endpoints | 80 (55.17%) |
| MUTATION Endpoints | 65 (44.83%) |
| Endpoints Requiring Auth | 139 (95.86%) |
| Public Endpoints | 6 (4.14%) |
| Endpoints with Pages | 95 (65.52%) |
| Endpoints without Pages | 50 (34.48%) |
| Most Used Endpoint | GetMarketingPage (14 pages) |
| Admin Endpoints | 15 (10.34%) |
| Super Admin Endpoints | 5 (3.45%) |
| Pro User Endpoints | 2 (1.38%) |

---

**Analysis Status:** Complete ✅  
**Next:** Relationship Analysis Report  
**Last Updated:** 2026-01-20
