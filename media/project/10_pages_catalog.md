# Pages Catalog: Complete Reference Guide

**Generated:** 2026-01-20  
**Total Pages:** 48

## Overview

This catalog provides a complete reference for all 48 pages in the Contact360 documentation system, organized by type and including all metadata, endpoints, and UI components.

---

## Table of Contents

1. [Dashboard Pages (33)](#dashboard-pages)
2. [Marketing Pages (15)](#marketing-pages)
3. [Auth Pages (2)](#auth-pages)
4. [Quick Reference](#quick-reference)

---

## Dashboard Pages (33)

### Core Data Pages

#### `/companies` - Companies Page
- **Page ID:** `companies_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required (protected by AuthGuard)
- **Authorization:** None
- **Endpoints:** 4
- **Components:** 7
- **Purpose:** Company listing and management page with filtering, search, bulk operations, pagination, and AI-powered company summaries.
- **Endpoints Used:**
  - `graphql/QueryCompanies` (QUERY) - Primary, data_fetching
  - `graphql/GetCompany` (QUERY) - Secondary, data_fetching
  - `graphql/GetCompanyFilters` (QUERY) - Secondary, data_fetching
  - `graphql/GetCompanyContacts` (QUERY) - Secondary, data_fetching
- **UI Components:**
  - CompanyTable
  - CompanyFilter
  - CompanySearch
  - CompanyBulkActions
  - CompanyPagination
  - CompanySummary
  - CompanyDetails

#### `/contacts` - Contacts Page
- **Page ID:** `contacts_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 7
- **Components:** 8
- **Purpose:** Contact listing and management page with advanced filtering, search, VQL query builder, saved searches, bulk operations, and pagination.
- **Endpoints Used:**
  - `graphql/QueryContacts` (QUERY) - Primary, data_fetching
  - `graphql/GetContact` (QUERY) - Secondary, data_fetching
  - `graphql/GetContactFilters` (QUERY) - Secondary, data_fetching
  - `graphql/ListSavedSearches` (QUERY) - Secondary, data_fetching
  - `graphql/CreateSavedSearch` (MUTATION) - Secondary, data_mutation
  - `graphql/UpdateSavedSearch` (MUTATION) - Secondary, data_mutation
  - `graphql/DeleteSavedSearch` (MUTATION) - Secondary, data_mutation

#### `/companies/[uuid]` - Company Details Page
- **Page ID:** `companies_id_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 3
- **Components:** 5
- **Purpose:** Individual company details page showing company information, contacts, and related data.

### User Management Pages

#### `/profile` - Profile Page
- **Page ID:** `profile_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 13
- **Components:** 11
- **Purpose:** User profile management page with tabs for profile editing, team management, AI settings, appearance, notifications, security, API keys, and billing.
- **Endpoints Used:**
  - `graphql/GetMe` (QUERY) - Primary, data_fetching
  - `graphql/UpdateProfile` (MUTATION) - Secondary, data_mutation
  - `graphql/UploadAvatar` (MUTATION) - Secondary, data_mutation
  - `graphql/ListAPIKeys` (QUERY) - Secondary, data_fetching
  - `graphql/CreateAPIKey` (MUTATION) - Secondary, data_mutation
  - `graphql/DeleteAPIKey` (MUTATION) - Secondary, data_mutation
  - `graphql/ListSessions` (QUERY) - Secondary, data_fetching
  - `graphql/RevokeSession` (MUTATION) - Secondary, data_mutation
  - `graphql/ListTeamMembers` (QUERY) - Secondary, data_fetching
  - `graphql/Get2FAStatus` (QUERY) - Secondary, data_fetching
  - `graphql/Setup2FA` (MUTATION) - Secondary, data_mutation
  - `graphql/Verify2FA` (MUTATION) - Secondary, data_mutation
  - `graphql/Disable2FA` (MUTATION) - Secondary, data_mutation

#### `/billing` - Billing Page
- **Page ID:** `billing_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 9
- **Components:** 8
- **Purpose:** Billing and subscription management page with current subscription, plans, addons, payment methods, invoices, and admin billing management.

### Feature Pages

#### `/app` - Email Finder
- **Page ID:** `finder_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 1
- **Components:** 3
- **Purpose:** Email finder tool for finding email addresses.

#### `/app/data-search` - Data Search
- **Page ID:** `data_search_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 2
- **Components:** 4
- **Purpose:** Advanced data search interface.

#### `/verifier` - Email Verifier
- **Page ID:** `verifier_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 3
- **Components:** 5
- **Purpose:** Email verification tool for single and bulk email verification.

#### `/ai-chat` - AI Chat
- **Page ID:** `ai_chat_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 6
- **Components:** 4
- **Purpose:** AI-powered chat interface for customer support and assistance.

#### `/linkedin` - LinkedIn Integration
- **Page ID:** `linkedin_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 3
- **Components:** 4
- **Purpose:** LinkedIn profile search and data extraction.

#### `/export` - Export Management
- **Page ID:** `export_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 5
- **Components:** 5
- **Purpose:** Export job management and download interface.

#### `/activities` - Activities Feed
- **Page ID:** `activities_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 2
- **Components:** 3
- **Purpose:** User activity feed and history.

#### `/analytics` - Analytics Dashboard
- **Page ID:** `analytics_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 5
- **Components:** 6
- **Purpose:** Analytics and reporting dashboard.

#### `/usage` - Usage Tracking
- **Page ID:** `usage_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 2
- **Components:** 3
- **Purpose:** Usage statistics and tracking.

#### `/dashboard` - Main Dashboard
- **Page ID:** `dashboard_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 5
- **Components:** 8
- **Purpose:** Main dashboard with overview, stats, and quick actions.

#### `/dashboard/[uuid]` - Custom Dashboard
- **Page ID:** `dashboard_pageid_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 1
- **Components:** 3
- **Purpose:** Custom dashboard page with user-defined widgets.

#### `/icon-generator` - Icon Generator
- **Page ID:** `icon_generator_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** None
- **Endpoints:** 0 (Uses Gemini AI directly)
- **Components:** 2
- **Purpose:** AI-powered icon generation using Google Gemini.

### Admin Pages

#### `/admin/users` - Admin Users
- **Page ID:** `admin_users_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Super Admin role required
- **Endpoints:** 5
- **Components:** 5
- **Purpose:** Admin user management page for viewing, editing, and managing user accounts, roles, and credits.

#### `/admin/settings` - Admin Settings
- **Page ID:** `admin_settings_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin or Super Admin role required
- **Endpoints:** 0
- **Components:** 3
- **Purpose:** Admin settings and configuration page.

#### `/admin/marketing` - Admin Marketing Pages
- **Page ID:** `admin_marketing_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 5
- **Components:** 6
- **Purpose:** Admin interface for managing marketing pages.

#### `/admin/marketing/new` - Create Marketing Page
- **Page ID:** `admin_marketing_new_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 1
- **Components:** 3
- **Purpose:** Create new marketing page interface.

#### `/admin/marketing/[uuid]` - Edit Marketing Page
- **Page ID:** `admin_marketing_pageid_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 2
- **Components:** 4
- **Purpose:** Edit existing marketing page interface.

#### `/admin/dashboard-pages` - Admin Dashboard Pages
- **Page ID:** `admin_dashboard_pages_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 3
- **Components:** 5
- **Purpose:** Admin interface for managing dashboard pages.

#### `/admin/dashboard-pages/[uuid]` - Edit Dashboard Page
- **Page ID:** `admin_dashboard_pages_pageid_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 2
- **Components:** 4
- **Purpose:** Edit existing dashboard page interface.

#### `/admin/user-history` - Admin User History
- **Page ID:** `admin_user_history_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 1
- **Components:** 3
- **Purpose:** View user activity history.

#### `/admin/logs` - Admin Logs
- **Page ID:** `admin_logs_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 4
- **Components:** 5
- **Purpose:** System logs and audit trail.

#### `/admin/statistics` - Admin Statistics
- **Page ID:** `admin_statistics_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 2
- **Components:** 4
- **Purpose:** System statistics and metrics.

#### `/admin/system-status` - Admin System Status
- **Page ID:** `admin_system_status_page`
- **Type:** Dashboard
- **Status:** Published
- **Authentication:** Required
- **Authorization:** Admin role required
- **Endpoints:** 4
- **Components:** 5
- **Purpose:** System health and status monitoring.

---

## Marketing Pages (15)

### Public Pages

#### `/` - Landing Page
- **Page ID:** `landing_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0 (Static content)
- **Components:** 12
- **Purpose:** Main landing page with hero section, features, pricing, and CTA.

#### `/about` - About Page
- **Page ID:** `about_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 5
- **Purpose:** About us page with company information.

#### `/careers` - Careers Page
- **Page ID:** `careers_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** Careers and job listings page.

#### `/api-docs` - API Documentation
- **Page ID:** `api_docs_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 3
- **Purpose:** API documentation and reference.

#### `/privacy` - Privacy Policy
- **Page ID:** `privacy_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 2
- **Purpose:** Privacy policy page.

#### `/terms` - Terms of Service
- **Page ID:** `terms_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 2
- **Purpose:** Terms of service page.

#### `/integrations` - Integrations
- **Page ID:** `integrations_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 3
- **Purpose:** Integrations and third-party connections.

#### `/chrome-extension` - Chrome Extension
- **Page ID:** `chrome_extension_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 3
- **Purpose:** Chrome extension information and download.

### Product Pages

#### `/products/email-finder` - Email Finder Product
- **Page ID:** `products_email_finder_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** Email finder product page.

#### `/products/prospect-finder` - Prospect Finder Product
- **Page ID:** `products_prospect_finder_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** Prospect finder product page.

#### `/products/email-verifier` - Email Verifier Product
- **Page ID:** `products_email_verifier_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** Email verifier product page.

#### `/products/ai-email-writer` - AI Email Writer Product
- **Page ID:** `products_ai_email_writer_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** AI email writer product page.

#### `/products/cfo-email-list` - CFO Email List Product
- **Page ID:** `products_cfo_email_list_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** CFO email list product page.

#### `/products/chrome-extension` - Chrome Extension Product
- **Page ID:** `products_chrome_extension_page`
- **Type:** Marketing
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 0
- **Components:** 4
- **Purpose:** Chrome extension product page.

### Dynamic Marketing Pages

All marketing pages use the `graphql/GetMarketingPage` endpoint (14 pages total).

---

## Auth Pages (2)

#### `/login` - Login Page
- **Page ID:** `login_page`
- **Type:** Auth
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 2
- **Components:** 1
- **Purpose:** User login page with email/password authentication.
- **Endpoints Used:**
  - `graphql/Login` (MUTATION) - Primary, authentication
  - `graphql/GetSession` (QUERY) - Secondary, authentication

#### `/register` - Register Page
- **Page ID:** `register_page`
- **Type:** Auth
- **Status:** Published
- **Authentication:** Not required
- **Authorization:** None
- **Endpoints:** 1
- **Components:** 1
- **Purpose:** User registration page for creating new accounts.
- **Endpoints Used:**
  - `graphql/Register` (MUTATION) - Primary, authentication

---

## Quick Reference

### Pages by Endpoint Count
- **13 endpoints:** profile_page
- **9 endpoints:** billing_page
- **7 endpoints:** contacts_page
- **6 endpoints:** ai_chat_page
- **5 endpoints:** admin_users_page, admin_marketing_page, admin_dashboard_pages_page, admin_logs_page, admin_system_status_page
- **4 endpoints:** companies_page, export_page, analytics_page
- **3 endpoints:** companies_id_page, verifier_page, linkedin_page, activities_page
- **2 endpoints:** login_page, data_search_page
- **1 endpoint:** register_page, finder_page, usage_page, dashboard_pageid_page, admin_marketing_new_page, admin_marketing_pageid_page, admin_dashboard_pages_pageid_page, admin_user_history_page, admin_statistics_page
- **0 endpoints:** 8 pages (static marketing pages, icon_generator, admin_settings)

### Pages by Authentication
- **Required:** 35 pages (72.92%)
- **Not Required:** 13 pages (27.08%)

### Pages by Authorization
- **No authorization:** 43 pages (89.58%)
- **Admin role required:** 4 pages (8.33%)
- **Super Admin role required:** 1 page (2.08%)

### Pages by Status
- **Published:** 48 pages (100%)
- **Draft:** 0 pages
- **Deleted:** 0 pages

---

**Last Updated:** 2026-01-20  
**Total Pages:** 48
