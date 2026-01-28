# Relationships Matrix: Page-to-Endpoint and Endpoint-to-Page

**Generated:** 2026-01-20  
**Total Relationships:** 95

## Overview

This matrix provides a complete view of all relationships between pages and endpoints, showing both page-to-endpoint and endpoint-to-page perspectives.

---

## Page-to-Endpoint Matrix

### Dashboard Pages

#### `/companies`
**Endpoints Used:**
- `graphql/QueryCompanies` (QUERY) - Primary, data_fetching, via `companiesService`, hook `useCompaniesPage`
- `graphql/GetCompany` (QUERY) - Secondary, data_fetching, via `companiesService`, hook `useCompaniesPage`
- `graphql/GetCompanyFilters` (QUERY) - Secondary, data_fetching, via `companiesService`, hook `useCompaniesPage`
- `graphql/GetCompanyContacts` (QUERY) - Secondary, data_fetching, via `companiesService`, hook `useCompaniesPage`

#### `/contacts`
**Endpoints Used:**
- `graphql/QueryContacts` (QUERY) - Primary, data_fetching, via `contactsService`, hook `useContactsPage`
- `graphql/GetContact` (QUERY) - Secondary, data_fetching, via `contactsService`, hook `useContactsPage`
- `graphql/GetContactFilters` (QUERY) - Secondary, data_fetching, via `contactsService`, hook `useContactsPage`
- `graphql/ListSavedSearches` (QUERY) - Secondary, data_fetching, via `savedSearchesService`, hook `useContactsPage`
- `graphql/CreateSavedSearch` (MUTATION) - Secondary, data_mutation, via `savedSearchesService`, hook `useContactsPage`
- `graphql/UpdateSavedSearch` (MUTATION) - Secondary, data_mutation, via `savedSearchesService`, hook `useContactsPage`
- `graphql/DeleteSavedSearch` (MUTATION) - Secondary, data_mutation, via `savedSearchesService`, hook `useContactsPage`

#### `/profile`
**Endpoints Used:**
- `graphql/GetMe` (QUERY) - Primary, data_fetching, via `authService`, hook `useProfilePage`
- `graphql/UpdateProfile` (MUTATION) - Secondary, data_mutation, via `profileService`, hook `useProfilePage`
- `graphql/UploadAvatar` (MUTATION) - Secondary, data_mutation, via `profileService`, hook `useProfilePage`
- `graphql/ListAPIKeys` (QUERY) - Secondary, data_fetching, via `profileService`, hook `useProfilePage`
- `graphql/CreateAPIKey` (MUTATION) - Secondary, data_mutation, via `profileService`, hook `useProfilePage`
- `graphql/DeleteAPIKey` (MUTATION) - Secondary, data_mutation, via `profileService`, hook `useProfilePage`
- `graphql/ListSessions` (QUERY) - Secondary, data_fetching, via `profileService`, hook `useProfilePage`
- `graphql/RevokeSession` (MUTATION) - Secondary, data_mutation, via `profileService`, hook `useProfilePage`
- `graphql/ListTeamMembers` (QUERY) - Secondary, data_fetching, via `profileService`, hook `useProfilePage`
- `graphql/Get2FAStatus` (QUERY) - Secondary, data_fetching, via `twoFactorService`, hook `useProfilePage`
- `graphql/Setup2FA` (MUTATION) - Secondary, data_mutation, via `twoFactorService`, hook `useProfilePage`
- `graphql/Verify2FA` (MUTATION) - Secondary, data_mutation, via `twoFactorService`, hook `useProfilePage`
- `graphql/Disable2FA` (MUTATION) - Secondary, data_mutation, via `twoFactorService`, hook `useProfilePage`

#### `/billing`
**Endpoints Used:**
- `graphql/GetBilling` (QUERY) - Primary, data_fetching, via `billingService`, hook `useBilling`
- `graphql/GetPlans` (QUERY) - Secondary, data_fetching, via `billingService`, hook `useBilling`
- `graphql/GetAddons` (QUERY) - Secondary, data_fetching, via `billingService`, hook `useBilling`
- `graphql/GetInvoices` (QUERY) - Secondary, data_fetching, via `billingService`, hook `useBilling`
- `graphql/Subscribe` (MUTATION) - Secondary, data_mutation, via `billingService`, hook `useBilling`
- `graphql/PurchaseAddon` (MUTATION) - Secondary, data_mutation, via `billingService`, hook `useBilling`
- `graphql/CancelSubscription` (MUTATION) - Secondary, data_mutation, via `billingService`, hook `useBilling`
- `graphql/GetAdminPlans` (QUERY) - Secondary, data_fetching, via `billingService`, hook `useBilling` (admin only)
- `graphql/GetAdminAddons` (QUERY) - Secondary, data_fetching, via `billingService`, hook `useBilling` (admin only)

#### `/dashboard`
**Endpoints Used:**
- `graphql/GetUserStats` (QUERY) - Conditional, analytics, via `adminService`, hook `useDashboardPage`
- `graphql/GetActivities` (QUERY) - Primary, data_fetching, via `activitiesService`, hook `useDashboardPage`
- `graphql/ListExports` (QUERY) - Primary, data_fetching, via `exportsService`, hook `useDashboardPage`
- `graphql/GetDashboardPage` (QUERY) - Primary, data_fetching, via `dashboardPagesService`, hook `useDashboardPage`
- `graphql/GetUsage` (QUERY) - Secondary, analytics, via `usageService`, hook `useDashboardPage`

#### `/app`
**Endpoints Used:**
- `graphql/FindSingleEmail` (MUTATION) - Primary, data_mutation, via `emailService`, hook null

#### `/app/data-search`
**Endpoints Used:**
- `graphql/QueryCompanies` (QUERY) - Primary, data_fetching, via `companiesService`, hook null
- `graphql/QueryContacts` (QUERY) - Primary, data_fetching, via `contactsService`, hook null

#### `/verifier`
**Endpoints Used:**
- `graphql/VerifySingleEmail` (MUTATION) - Primary, data_mutation, via `emailService`, hook `useVerifier`
- `graphql/VerifyBulkEmails` (MUTATION) - Primary, data_mutation, via `emailService`, hook `useVerifier`
- `graphql/GetActivities` (QUERY) - Secondary, data_fetching, via `activitiesService`, hook `useVerifier`

#### `/ai-chat`
**Endpoints Used:**
- `graphql/ListAIChats` (QUERY) - Primary, data_fetching, via `aiChatsService`, hook `useAiChat`
- `graphql/GetAIChat` (QUERY) - Primary, data_fetching, via `aiChatsService`, hook `useAiChat`
- `graphql/CreateAIChat` (MUTATION) - Secondary, data_mutation, via `aiChatsService`, hook `useAiChat`
- `graphql/UpdateAIChat` (MUTATION) - Secondary, data_mutation, via `aiChatsService`, hook `useAiChat`
- `graphql/DeleteAIChat` (MUTATION) - Secondary, data_mutation, via `aiChatsService`, hook `useAiChat`
- `graphql/SendMessage` (MUTATION) - Primary, data_mutation, via `aiChatsService`, hook `useAiChat`

#### `/linkedin`
**Endpoints Used:**
- `graphql/SearchLinkedIn` (MUTATION) - Primary, data_mutation, via `linkedinService`, hook `useLinkedIn`
- `graphql/UpsertByLinkedInUrl` (MUTATION) - Primary, data_mutation, via `linkedinService`, hook `useLinkedIn`
- `graphql/ExportLinkedIn` (MUTATION) - Secondary, data_mutation, via `linkedinService`, hook `useLinkedIn`

#### `/export`
**Endpoints Used:**
- `graphql/ListExports` (QUERY) - Primary, data_fetching, via `exportsService`, hook `useExportPage`
- `graphql/GetExport` (QUERY) - Primary, data_fetching, via `exportsService`, hook `useExportPage`
- `graphql/CancelExport` (MUTATION) - Secondary, data_mutation, via `exportsService`, hook `useExportPage`
- `graphql/CreateContactExport` (MUTATION) - Secondary, data_mutation, via `exportsService`, hook `useCompanyExport`
- `graphql/CreateCompanyExport` (MUTATION) - Secondary, data_mutation, via `exportsService`, hook `useCompanyExport`

#### `/activities`
**Endpoints Used:**
- `graphql/GetActivities` (QUERY) - Primary, data_fetching, via `activitiesService`, hook `useActivitiesPage`
- `graphql/GetActivityStats` (QUERY) - Secondary, analytics, via `activitiesService`, hook `useActivitiesPage`

#### `/analytics`
**Endpoints Used:**
- `graphql/GetPerformanceMetrics` (QUERY) - Primary, analytics, via `analyticsService`, hook `useAnalyticsPage`
- `graphql/AggregateMetrics` (QUERY) - Primary, analytics, via `analyticsService`, hook `useAnalyticsPage`
- `graphql/GetActivityStats` (QUERY) - Secondary, analytics, via `activitiesService`, hook `useAnalyticsPage`
- `graphql/GetUsage` (QUERY) - Secondary, analytics, via `usageService`, hook `useAnalyticsPage`
- `graphql/GetUserStats` (QUERY) - Secondary, analytics, via `adminService`, hook `useAnalyticsPage`

#### `/usage`
**Endpoints Used:**
- `graphql/GetUsage` (QUERY) - Primary, analytics, via `usageService`, hook `useUsageTracking`
- `graphql/TrackUsage` (MUTATION) - Secondary, data_mutation, via `usageService`, hook `useUsageTracking`

### Auth Pages

#### `/login`
**Endpoints Used:**
- `graphql/Login` (MUTATION) - Primary, authentication, via `authService`, hook `useAuth`
- `graphql/GetSession` (QUERY) - Secondary, authentication, via `authService`, hook `useAuth`

#### `/register`
**Endpoints Used:**
- `graphql/Register` (MUTATION) - Primary, authentication, via `authService`, hook `useAuth`

### Admin Pages

#### `/admin/users`
**Endpoints Used:**
- `graphql/ListUsers` (QUERY) - Primary, data_fetching, via `adminService`, hook `useAdminUsers`
- `graphql/GetUserStats` (QUERY) - Secondary, analytics, via `adminService`, hook `useAdminUsers`
- `graphql/UpdateUserRole` (MUTATION) - Secondary, data_mutation, via `adminService`, hook `useAdminUsers`
- `graphql/UpdateUserCredits` (MUTATION) - Secondary, data_mutation, via `adminService`, hook `useAdminUsers`
- `graphql/DeleteUser` (MUTATION) - Secondary, data_mutation, via `adminService`, hook `useAdminUsers`

#### `/admin/marketing`
**Endpoints Used:**
- `graphql/AdminMarketingPages` (QUERY) - Primary, data_fetching, via `marketingService`, hook `useAdminMarketingPages`
- `graphql/CreateMarketingPage` (MUTATION) - Secondary, data_mutation, via `marketingService`, hook `useAdminMarketingPages`
- `graphql/UpdateMarketingPage` (MUTATION) - Secondary, data_mutation, via `marketingService`, hook `useAdminMarketingPages`
- `graphql/DeleteMarketingPage` (MUTATION) - Secondary, data_mutation, via `marketingService`, hook `useAdminMarketingPages`
- `graphql/PublishMarketingPage` (MUTATION) - Secondary, data_mutation, via `marketingService`, hook `useAdminMarketingPages`

#### `/admin/marketing/new`
**Endpoints Used:**
- `graphql/CreateMarketingPage` (MUTATION) - Primary, data_mutation, via `marketingService`, hook `useMarketingPageEditor`

#### `/admin/marketing/[uuid]`
**Endpoints Used:**
- `graphql/GetMarketingPage` (QUERY) - Primary, data_fetching, via `marketingService`, hook `useMarketingPageEditor`
- `graphql/UpdateMarketingPage` (MUTATION) - Secondary, data_mutation, via `marketingService`, hook `useMarketingPageEditor`

#### `/admin/dashboard-pages`
**Endpoints Used:**
- `graphql/ListDashboardPages` (QUERY) - Primary, data_fetching, via `dashboardPagesService`, hook `useAdminDashboardPages`
- `graphql/CreateDashboardPage` (MUTATION) - Secondary, data_mutation, via `dashboardPagesService`, hook `useAdminDashboardPages`
- `graphql/UpdateDashboardPage` (MUTATION) - Secondary, data_mutation, via `dashboardPagesService`, hook `useAdminDashboardPages`

#### `/admin/dashboard-pages/[uuid]`
**Endpoints Used:**
- `graphql/GetDashboardPage` (QUERY) - Primary, data_fetching, via `dashboardPagesService`, hook `useDashboardPageEditor`
- `graphql/UpdateDashboardPage` (MUTATION) - Secondary, data_mutation, via `dashboardPagesService`, hook `useDashboardPageEditor`

#### `/admin/user-history`
**Endpoints Used:**
- `graphql/GetUserHistory` (QUERY) - Primary, data_fetching, via `adminService`, hook `useAdminUserHistory`

#### `/admin/logs`
**Endpoints Used:**
- `graphql/QueryLogs` (QUERY) - Primary, data_fetching, via `adminService`, hook `useAdminLogs`
- `graphql/SearchLogs` (QUERY) - Primary, data_fetching, via `adminService`, hook `useAdminLogs`
- `graphql/GetLogStatistics` (QUERY) - Secondary, analytics, via `adminService`, hook `useAdminLogs`
- `graphql/CreateLog` (MUTATION) - Secondary, data_mutation, via `adminService`, hook `useAdminLogs`

#### `/admin/statistics`
**Endpoints Used:**
- `graphql/GetUserStats` (QUERY) - Primary, analytics, via `adminService`, hook `useSystemStatus`
- `graphql/GetActivityStats` (QUERY) - Secondary, analytics, via `activitiesService`, hook `useSystemStatus`

#### `/admin/system-status`
**Endpoints Used:**
- `graphql/GetHealth` (QUERY) - Primary, data_fetching, via `healthService`, hook `useSystemStatus`
- `graphql/GetAPIMetadata` (QUERY) - Primary, data_fetching, via `healthService`, hook `useSystemStatus`
- `graphql/GetVQLHealth` (QUERY) - Secondary, data_fetching, via `healthService`, hook `useSystemStatus`
- `graphql/GetVQLStats` (QUERY) - Secondary, analytics, via `healthService`, hook `useSystemStatus`

### Marketing Pages

All marketing pages (14 total) use:
- `graphql/GetMarketingPage` (QUERY) - Primary, data_fetching, via `marketingService`, hook `useMarketingPage`

---

## Endpoint-to-Page Matrix

### Most Used Endpoints

#### `graphql/GetMarketingPage` (QUERY)
**Used By:** 14 pages
- All marketing pages (landing, about, careers, products, etc.)
- Admin marketing edit page

#### `graphql/GetActivities` (QUERY)
**Used By:** 3 pages
- `/activities` - Primary, data_fetching
- `/dashboard` - Primary, data_fetching
- `/verifier` - Secondary, data_fetching

#### `graphql/GetDashboardPage` (QUERY)
**Used By:** 2 pages
- `/dashboard` - Primary, data_fetching
- `/dashboard/[uuid]` - Primary, data_fetching

#### `graphql/QueryCompanies` (QUERY)
**Used By:** 2 pages
- `/companies` - Primary, data_fetching
- `/app/data-search` - Primary, data_fetching

#### `graphql/QueryContacts` (QUERY)
**Used By:** 2 pages
- `/contacts` - Primary, data_fetching
- `/app/data-search` - Primary, data_fetching

#### `graphql/ListExports` (QUERY)
**Used By:** 2 pages
- `/export` - Primary, data_fetching
- `/dashboard` - Primary, data_fetching

### Single-Use Endpoints

Most endpoints are used by only one page. Examples:
- `graphql/GetMe` → `/profile`
- `graphql/GetBilling` → `/billing`
- `graphql/Login` → `/login`
- `graphql/Register` → `/register`
- `graphql/ListUsers` → `/admin/users`

---

## Service Usage Matrix

### Top Services by Relationship Count

1. **marketingService** - 15 relationships
   - Used by: All marketing pages, admin marketing pages

2. **billingService** - 9 relationships
   - Used by: `/billing` page

3. **adminService** - 8 relationships
   - Used by: Admin pages, dashboard, analytics

4. **profileService** - 8 relationships
   - Used by: `/profile` page

5. **companiesService** - 6 relationships
   - Used by: `/companies`, `/app/data-search`

6. **savedSearchesService** - 6 relationships
   - Used by: `/contacts` page

7. **aiChatsService** - 6 relationships
   - Used by: `/ai-chat` page

8. **contactsService** - 4 relationships
   - Used by: `/contacts`, `/app/data-search`

9. **emailService** - 5 relationships
   - Used by: `/app`, `/verifier`

10. **activitiesService** - 3 relationships
    - Used by: `/activities`, `/dashboard`, `/verifier`

---

## Hook Usage Matrix

### Most Used Hooks

1. **useMarketingPage** - 14 pages (all marketing pages)
2. **useCompaniesPage** - 1 page (`/companies`)
3. **useContactsPage** - 1 page (`/contacts`)
4. **useProfilePage** - 1 page (`/profile`)
5. **useBillingPage** - 1 page (`/billing`)
6. **useAuth** - 2 pages (`/login`, `/register`)
7. **useDashboardPage** - 1 page (`/dashboard`)

### Pages Without Hooks

Some pages use services directly without hooks:
- `/app` - Direct service calls
- `/app/data-search` - Direct service calls

---

## Usage Type Distribution

- **Primary:** 60 relationships (63.16%)
- **Secondary:** 30 relationships (31.58%)
- **Conditional:** 5 relationships (5.26%)

## Usage Context Distribution

- **data_fetching:** 50 relationships (52.63%)
- **data_mutation:** 35 relationships (36.84%)
- **authentication:** 3 relationships (3.16%)
- **analytics:** 5 relationships (5.26%)
- **reporting:** 2 relationships (2.11%)

---

**Last Updated:** 2026-01-20  
**Total Relationships:** 95
