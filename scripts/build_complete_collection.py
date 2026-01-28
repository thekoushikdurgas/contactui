#!/usr/bin/env python3
"""
Build complete Postman collection from GraphQL module documentation.
This script reads the module docs and creates a comprehensive Postman collection.
"""

import json
import re
from pathlib import Path

# Base collection structure
BASE_COLLECTION = {
    "info": {
        "_postman_id": "contact360-graphql-api-complete",
        "name": "Contact360 GraphQL API - Complete",
        "description": "Complete GraphQL API collection for Contact360 Appointment service.\n\n**Setup:**\n1. Import this collection\n2. Create environment with baseUrl\n3. Use Auth > Login to get token\n4. Token auto-saves to environment\n\n**Modules:** All 25 GraphQL modules included\n\n**📚 For comprehensive module documentation**, see docs/GraphQL/README.md which includes detailed queries, mutations, validation rules, error handling, and implementation details for each module.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [],
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
        {"key": "accessToken", "value": "", "type": "string"},
        {"key": "refreshToken", "value": "", "type": "string"},
        {"key": "userId", "value": "", "type": "string"}
    ]
}

# Module requests configuration
MODULE_REQUESTS = {
    "Auth": {
        "module_description": "Authentication and session management with JWT tokens, registration, login, logout, and token refresh. See comprehensive documentation: docs/GraphQL/01_AUTH_MODULE.md",
        "queries": [
            {
                "name": "Get Current User (me)",
                "query": "query { auth { me { uuid email name profile { jobTitle bio role credits } } } }",
                "description": "Get current authenticated user. Returns null if unauthenticated. See docs/GraphQL/01_AUTH_MODULE.md#me for details."
            },
            {
                "name": "Get Session",
                "query": "query { auth { session { userUuid email isAuthenticated lastSignInAt } } }",
                "description": "Get current session information. Requires authentication. See docs/GraphQL/01_AUTH_MODULE.md#session for details."
            }
        ],
        "mutations": [
            {
                "name": "Login",
                "query": "mutation Login($input: LoginInput!) { auth { login(input: $input) { accessToken refreshToken user { uuid email name } } } }",
                "variables": {"input": {"email": "{{email}}", "password": "{{password}}"}},
                "saveTokens": True
            },
            {
                "name": "Register",
                "query": "mutation Register($input: RegisterInput!) { auth { register(input: $input) { accessToken refreshToken user { uuid email name } } } }",
                "variables": {"input": {"email": "{{email}}", "password": "{{password}}", "name": "{{name}}"}},
                "saveTokens": True
            },
            {
                "name": "Logout",
                "query": "mutation { auth { logout } }"
            },
            {
                "name": "Refresh Token",
                "query": "mutation RefreshToken($input: RefreshTokenInput!) { auth { refreshToken(input: $input) { accessToken refreshToken } } }",
                "variables": {"input": {"refreshToken": "{{refreshToken}}"}},
                "saveTokens": True
            }
        ]
    },
    "Users": {
        "module_description": "User profile management, avatar uploads, role promotions, and user statistics. See comprehensive documentation: docs/GraphQL/02_USERS_MODULE.md",
        "queries": [
            {
                "name": "Get User",
                "query": "query GetUser($uuid: ID!) { users { user(uuid: $uuid) { uuid email name isActive profile { jobTitle bio role credits subscriptionPlan } } } }",
                "variables": {"uuid": "{{userId}}"},
                "description": "Get user by UUID. Users can view their own profile; Admins can view any user. See docs/GraphQL/02_USERS_MODULE.md#user for validation rules and role-based access."
            },
            {
                "name": "List Users",
                "query": "query ListUsers($limit: Int, $offset: Int) { users { users(limit: $limit, offset: $offset) { uuid email name isActive createdAt } } }",
                "variables": {"limit": 50, "offset": 0}
            },
            {
                "name": "User Stats",
                "query": "query { users { userStats { totalUsers activeUsers inactiveUsers usersByRole { role count } usersBySubscription { subscriptionPlan count } } } }"
            }
        ],
        "mutations": [
            {
                "name": "Update Profile",
                "query": "mutation UpdateProfile($input: UpdateProfileInput!) { users { updateProfile(input: $input) { userId jobTitle bio timezone } } }",
                "variables": {"input": {"jobTitle": "Software Engineer", "bio": "Developer"}}
            },
            {
                "name": "Upload Avatar",
                "query": "mutation UploadAvatar($input: UploadAvatarInput!) { users { uploadAvatar(input: $input) { userId avatarUrl jobTitle bio timezone role credits subscriptionPlan subscriptionStatus createdAt updatedAt } } }",
                "variables": {
                    "input": {
                        "fileData": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
                    }
                },
                "description": "Uploads a user avatar image. The fileData field should contain base64-encoded image data (without data URI prefix). File requirements: JPEG, PNG, GIF, or WebP; Maximum size: 5MB."
            },
            {
                "name": "Promote To Admin",
                "query": "mutation PromoteToAdmin($input: PromoteToAdminInput!) { users { promoteToAdmin(input: $input) { uuid email name profile { role } } } }",
                "variables": {"input": {"userId": "{{userId}}"}},
                "description": "Promote a user to Admin role. Requires SuperAdmin role."
            },
            {
                "name": "Promote To SuperAdmin",
                "query": "mutation PromoteToSuperAdmin($input: PromoteToSuperAdminInput!) { users { promoteToSuperAdmin(input: $input) { uuid email name profile { role } } } }",
                "variables": {"input": {"userId": "{{userId}}"}},
                "description": "Promote a user to SuperAdmin role. Requires SuperAdmin role."
            }
        ]
    },
    "Health": {
        "module_description": "API health checks, metadata, VQL service status, and performance statistics. See comprehensive documentation: docs/GraphQL/08_HEALTH_MODULE.md",
        "queries": [
            {
                "name": "API Metadata",
                "query": "query { health { apiMetadata { name version docs } } }",
                "auth": False,
                "description": "Get API metadata (name, version, docs URL). Public access. See docs/GraphQL/08_HEALTH_MODULE.md#apimetadata for details."
            },
            {
                "name": "API Health",
                "query": "query { health { apiHealth { status environment } } }",
                "auth": False
            },
            {
                "name": "VQL Health",
                "query": "query { health { vqlHealth { connectraEnabled connectraStatus connectraBaseUrl } } }"
            },
            {
                "name": "Performance Stats",
                "query": "query { health { performanceStats { cache { enabled hits misses hitRate } database { status poolSize activeConnections } } } }"
            }
        ],
        "mutations": []
    },
    "Jobs": {
        "module_description": "Background job management for Connectra operations including export jobs, generic jobs, S3 upload URLs, and export download URLs. See comprehensive documentation: docs/GraphQL/24_JOBS_MODULE.md",
        "queries": [
            {
                "name": "List Jobs",
                "query": "query ListJobs($filters: JobFilterInput) { jobs { jobs(filters: $filters) { items { uuid jobType status data jobResponse { runtimeErrors messages s3Key } createdAt updatedAt } total } } }",
                "variables": {"filters": {"jobType": "export_csv_file", "status": ["completed", "processing"], "limit": 50}},
                "description": "List jobs with filters. See docs/GraphQL/24_JOBS_MODULE.md#jobs for validation rules and implementation details."
            },
            {
                "name": "Get Job",
                "query": "query GetJob($uuid: ID!) { jobs { job(uuid: $uuid) { uuid jobType status data jobResponse { runtimeErrors messages s3Key } retryCount createdAt updatedAt } } }",
                "variables": {"uuid": "{{jobUuid}}"}
            },
            {
                "name": "Get Upload URL",
                "query": "query GetUploadUrl($filename: String!) { jobs { uploadUrl(filename: $filename) { uploadUrl s3Key expiresIn } } }",
                "variables": {"filename": "contacts.csv"}
            },
            {
                "name": "Get Export Download URL",
                "query": "query GetExportDownloadUrl($jobUuid: ID!) { jobs { exportDownloadUrl(jobUuid: $jobUuid) } }",
                "variables": {"jobUuid": "{{jobUuid}}"}
            }
        ],
        "mutations": [
            {
                "name": "Create Job",
                "query": "mutation CreateJob($input: CreateJobInput!) { jobs { createJob(input: $input) { uuid jobType status data } } }",
                "variables": {"input": {"jobType": "insert_csv_file", "jobData": {"s3_key": "uploads/contacts.csv", "s3_bucket": "my-bucket"}, "retryCount": 3}}
            },
            {
                "name": "Create Export Job",
                "query": "mutation CreateExportJob($input: CreateExportJobInput!) { jobs { createExportJob(input: $input) { uuid jobType status data createdAt } } }",
                "variables": {
                    "input": {
                        "service": "contact",
                        "vql": {
                            "where": {
                                "keywordMatch": {
                                    "must": {
                                        "country": ["united states"],
                                        "title": ["VP", "Director"]
                                    }
                                }
                            },
                            "selectColumns": ["first_name", "last_name", "email", "title", "uuid"],
                            "orderBy": [{"orderBy": "created_at", "orderDirection": "desc"}],
                            "limit": 500
                        },
                        "s3Bucket": "my-bucket",
                        "retryCount": 2
                    }
                },
                "description": "Create a CSV export job with VQL query. Poll job status, then get download URL when completed."
            }
        ]
    },
    "Imports": {
        "module_description": "CSV import job management for contacts and companies. Supports unified imports (contact and company data in one file). See comprehensive documentation: docs/GraphQL/25_IMPORTS_MODULE.md",
        "queries": [
            {
                "name": "List Import Jobs",
                "query": "query ListImportJobs($filters: ImportJobFilterInput) { imports { importJobs(filters: $filters) { items { uuid jobType status data jobResponse { runtimeErrors messages s3Key } createdAt updatedAt } total } } }",
                "variables": {"filters": {"status": ["completed", "processing"], "limit": 50}},
                "description": "List import jobs with filters. See docs/GraphQL/25_IMPORTS_MODULE.md#importjobs for validation rules and implementation details."
            },
            {
                "name": "Get Import Job",
                "query": "query GetImportJob($uuid: ID!) { imports { importJob(uuid: $uuid) { uuid jobType status data jobResponse { runtimeErrors messages s3Key } retryCount createdAt updatedAt } } }",
                "variables": {"uuid": "{{jobUuid}}"}
            }
        ],
        "mutations": [
            {
                "name": "Create Import Job",
                "query": "mutation CreateImportJob($input: CreateImportJobInput!) { imports { createImportJob(input: $input) { uuid jobType status data createdAt } } }",
                "variables": {"input": {"s3Key": "uploads/uuid_contacts.csv", "s3Bucket": "my-bucket", "retryCount": 3, "service": "contact"}},
                "description": "Create a CSV import job. First get upload URL from Jobs module, upload file to S3, then create import job with the S3 key. Service can be 'contact' or 'company'."
            }
        ]
    },
    "Contacts": {
        "module_description": "Contact management with advanced VQL queries, filtering, and batch operations. See comprehensive documentation: docs/GraphQL/03_CONTACTS_MODULE.md",
        "queries": [
            {
                "name": "Get Contact",
                "query": "query GetContact($uuid: ID!) { contacts { contact(uuid: $uuid) { uuid firstName lastName email title companyUuid linkedinUrl city country company { uuid name employeesCount industries address annualRevenue website linkedinUrl phoneNumber city state country } } } }",
                "variables": {"uuid": "{{contactUuid}}"},
                "description": "Get contact by UUID with full company data. Requires authentication. See docs/GraphQL/03_CONTACTS_MODULE.md#contact for validation rules and implementation details."
            },
            {
                "name": "List Contacts (Basic)",
                "query": "query ListContacts($query: VQLQueryInput) { contacts { contacts(query: $query) { items { uuid firstName lastName email title } total limit offset } } }",
                "variables": {"query": {"limit": 50, "offset": 0}},
                "description": "Basic contact listing with pagination"
            },
            {
                "name": "Contact Count",
                "query": "query ContactCount($query: VQLQueryInput) { contacts { contactCount(query: $query) } }",
                "variables": {"query": {"filters": {"conditions": [{"field": "email_status", "operator": "eq", "value": "verified"}]}}}
            },
            {
                "name": "Text Search - Name (Shuffle)",
                "query": "query SearchByName($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "first_name", "operator": "contains", "value": "John"},
                                {"field": "last_name", "operator": "contains", "value": "Smith"}
                            ]
                        },
                        "limit": 25,
                        "page": 1
                    }
                },
                "description": "Flexible name search with typo tolerance (shuffle search type)"
            },
            {
                "name": "Text Search - Exact Title",
                "query": "query SearchByExactTitle($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName title email } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "title", "operator": "exact", "value": "software engineer"}
                            ]
                        },
                        "limit": 50
                    }
                },
                "description": "Exact phrase matching for job titles"
            },
            {
                "name": "Keyword Filter - Verified Engineering",
                "query": "query VerifiedEngineering($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title departments emailStatus } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "email_status", "operator": "eq", "value": "verified"},
                                {"field": "departments", "operator": "in", "value": ["Engineering", "Product"]}
                            ]
                        },
                        "limit": 100
                    }
                },
                "description": "Find verified contacts in specific departments"
            },
            {
                "name": "Range Query - Date Range",
                "query": "query RecentContacts($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email createdAt } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "created_at", "operator": "gte", "value": "2024-01-01T00:00:00Z"},
                                {"field": "created_at", "operator": "lte", "value": "2024-12-31T23:59:59Z"}
                            ]
                        },
                        "limit": 100
                    }
                },
                "description": "Find contacts created in a specific date range"
            },
            {
                "name": "Denormalized Company Fields - High Value Companies",
                "query": "query ContactsAtHighValueCompanies($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title seniority companyUuid } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "company_industries", "operator": "in", "value": ["Software", "SaaS", "Technology"]},
                                {"field": "company_annual_revenue", "operator": "gte", "value": 5000000},
                                {"field": "company_employees_count", "operator": "gte", "value": 100},
                                {"field": "company_employees_count", "operator": "lte", "value": 1000},
                                {"field": "seniority", "operator": "in", "value": ["Senior", "Lead", "Principal", "Executive"]},
                                {"field": "email_status", "operator": "eq", "value": "verified"}
                            ]
                        },
                        "orderBy": [{"orderBy": "seniority", "orderDirection": "desc"}],
                        "limit": 100,
                        "page": 1
                    }
                },
                "description": "Filter contacts by company attributes using denormalized company_* fields (single query, no separate company query needed)"
            },
            {
                "name": "Company Config - Populate Company Data",
                "query": "query ContactsWithCompany($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName title companyUuid company { uuid name employeesCount industries annualRevenue website } } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "company_industries", "operator": "in", "value": ["Software", "SaaS"]},
                                {"field": "seniority", "operator": "in", "value": ["Senior", "Lead"]},
                                {"field": "email_status", "operator": "eq", "value": "verified"}
                            ]
                        },
                        "selectColumns": ["uuid", "first_name", "last_name", "title", "company_id"],
                        "companyConfig": {
                            "populate": True,
                            "selectColumns": ["uuid", "name", "employees_count", "industries", "annual_revenue", "website"]
                        },
                        "limit": 25,
                        "page": 1
                    }
                },
                "description": "Get contacts with populated company objects. Use company_* fields for filtering, companyConfig.selectColumns for response data."
            },
            {
                "name": "Cursor Pagination - First Page",
                "query": "query FirstPageContacts($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "country", "operator": "eq", "value": "united states"}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "last_name", "orderDirection": "asc"},
                            {"orderBy": "first_name", "orderDirection": "asc"}
                        ],
                        "limit": 25
                    }
                },
                "description": "Initial request for cursor-based pagination. Extract values from last document for searchAfter."
            },
            {
                "name": "Cursor Pagination - Next Page",
                "query": "query NextPageContacts($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "country", "operator": "eq", "value": "united states"}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "last_name", "orderDirection": "asc"},
                            {"orderBy": "first_name", "orderDirection": "asc"}
                        ],
                        "searchAfter": ["Smith", "John"],
                        "limit": 25
                    }
                },
                "description": "Next page using search_after cursor. Replace values with actual values from last document of previous response."
            },
            {
                "name": "Combined Filters - Text + Keyword + Range",
                "query": "query ComplexContactSearch($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title departments seniority country createdAt } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "title", "operator": "contains", "value": "engineer developer"},
                                {"field": "departments", "operator": "in", "value": ["Engineering", "Product"]},
                                {"field": "seniority", "operator": "in", "value": ["Senior", "Lead", "Principal"]},
                                {"field": "country", "operator": "in", "value": ["united states", "canada", "united kingdom"]},
                                {"field": "email_status", "operator": "eq", "value": "verified"},
                                {"field": "created_at", "operator": "gte", "value": "2023-01-01T00:00:00Z"}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "created_at", "orderDirection": "desc"},
                            {"orderBy": "last_name", "orderDirection": "asc"}
                        ],
                        "limit": 50,
                        "page": 1
                    }
                },
                "description": "Complex filtering combining text search, keyword filters, and date range"
            },
            {
                "name": "Real-World: Lead Generation",
                "query": "query HighQualityLeads($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title seniority departments company { uuid name employeesCount industries annualRevenue website } } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "company_industries", "operator": "in", "value": ["Software", "SaaS", "Technology"]},
                                {"field": "company_annual_revenue", "operator": "gte", "value": 1000000},
                                {"field": "company_employees_count", "operator": "gte", "value": 50},
                                {"field": "company_employees_count", "operator": "lte", "value": 1000},
                                {"field": "seniority", "operator": "in", "value": ["Senior", "Lead", "Principal", "Executive"]},
                                {"field": "departments", "operator": "in", "value": ["Sales", "Marketing", "Business Development"]},
                                {"field": "email_status", "operator": "eq", "value": "verified"},
                                {"field": "country", "operator": "in", "value": ["united states", "canada", "united kingdom"]}
                            ]
                        },
                        "companyConfig": {
                            "populate": True,
                            "selectColumns": ["uuid", "name", "employees_count", "industries", "annual_revenue", "website"]
                        },
                        "orderBy": [{"orderBy": "seniority", "orderDirection": "desc"}],
                        "limit": 200,
                        "page": 1
                    }
                },
                "description": "Find high-quality leads for outreach - combines company and contact filters"
            },
            {
                "name": "Real-World: Account-Based Marketing",
                "query": "query DecisionMakers($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title seniority company { uuid name employeesCount industries annualRevenue } } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "company_id", "operator": "in", "value": ["company-uuid-1", "company-uuid-2", "company-uuid-3"]},
                                {"field": "seniority", "operator": "in", "value": ["Senior", "Lead", "Principal", "Executive"]},
                                {"field": "email_status", "operator": "eq", "value": "verified"}
                            ]
                        },
                        "companyConfig": {
                            "populate": True,
                            "selectColumns": ["uuid", "name", "employees_count", "industries", "annual_revenue"]
                        },
                        "orderBy": [{"orderBy": "seniority", "orderDirection": "desc"}],
                        "limit": 100
                    }
                },
                "description": "Find decision-makers at target companies for account-based marketing"
            },
            {
                "name": "Real-World: Recruiting Search",
                "query": "query EngineeringCandidates($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email title departments seniority companyUuid } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "title", "operator": "contains", "value": "engineer developer architect"},
                                {"field": "departments", "operator": "in", "value": ["Engineering", "Product"]},
                                {"field": "seniority", "operator": "in", "value": ["Senior", "Lead", "Principal"]},
                                {"field": "company_technologies", "operator": "in", "value": ["Python", "Go", "React", "AWS"]},
                                {"field": "company_employees_count", "operator": "gte", "value": 100},
                                {"field": "country", "operator": "in", "value": ["united states", "canada"]}
                            ]
                        },
                        "orderBy": [{"orderBy": "created_at", "orderDirection": "desc"}],
                        "limit": 50,
                        "page": 1
                    }
                },
                "description": "Find engineering candidates with specific skills and company technologies"
            },
            {
                "name": "Contact Query (VQL)",
                "query": "query ContactQuery($query: VQLQueryInput!) { contacts { contactQuery(query: $query) { items { uuid firstName lastName email } total } } }",
                "variables": {"query": {"filters": {"conditions": [{"field": "title", "operator": "contains", "value": "VP"}]}}},
                "description": "Advanced VQL query with custom filters"
            },
            {
                "name": "Get Filters",
                "query": "query GetFilters { contacts { filters { items { id key service filterType displayName directDerived active } total } } }",
                "description": "Get available filters for contacts. Service is automatically set to 'contact'."
            },
            {
                "name": "Get Filter Data",
                "query": "query GetFilterData($input: ContactFilterDataInput!) { contacts { filterData(input: $input) { items { value displayValue } total } } }",
                "variables": {"input": {"filterKey": "title", "searchText": "VP", "page": 1, "limit": 20}},
                "description": "Get filter values for a specific filter key. Service is automatically set to 'contact'. See docs/GraphQL/03_CONTACTS_MODULE.md#filterdata for details."
            }
        ],
        "mutations": [
            {
                "name": "Create Contact",
                "query": "mutation CreateContact($input: CreateContactInput!) { contacts { createContact(input: $input) { uuid firstName lastName email title companyUuid } } }",
                "variables": {
                    "input": {
                        "firstName": "John",
                        "lastName": "Doe",
                        "email": "john.doe@example.com",
                        "title": "Software Engineer"
                    }
                },
                "description": "Create a new contact via Connectra. Requires authentication. See docs/GraphQL/03_CONTACTS_MODULE.md#createcontact for validation rules (email format, max 255 chars for fields) and implementation details."
            },
            {
                "name": "Update Contact",
                "query": "mutation UpdateContact($uuid: ID!, $input: UpdateContactInput!) { contacts { updateContact(uuid: $uuid, input: $input) { uuid firstName lastName email } } }",
                "variables": {
                    "uuid": "{{contactUuid}}",
                    "input": {
                        "firstName": "John",
                        "lastName": "Doe Updated"
                    }
                },
                "description": "Update an existing contact. Currently raises NotImplementedError. See docs/GraphQL/03_CONTACTS_MODULE.md#updatecontact for details."
            },
            {
                "name": "Delete Contact",
                "query": "mutation DeleteContact($uuid: ID!) { contacts { deleteContact(uuid: $uuid) } }",
                "variables": {"uuid": "{{contactUuid}}"},
                "description": "Delete a contact. Currently raises NotImplementedError. See docs/GraphQL/03_CONTACTS_MODULE.md#deletecontact for details."
            },
            {
                "name": "Batch Create Contacts",
                "query": "mutation BatchCreateContacts($input: BatchCreateContactsInput!) { contacts { batchCreateContacts(input: $input) { uuid firstName lastName email } } }",
                "variables": {
                    "input": {
                        "contacts": [
                            {
                                "firstName": "John",
                                "lastName": "Doe",
                                "email": "john.doe@example.com"
                            },
                            {
                                "firstName": "Jane",
                                "lastName": "Smith",
                                "email": "jane.smith@example.com"
                            }
                        ]
                    }
                },
                "description": "Create multiple contacts in batch (max 1000, processed in chunks of 100). Requires authentication. See docs/GraphQL/03_CONTACTS_MODULE.md#batchcreatecontacts for validation rules and batch processing details."
            }
        ]
    },
    "Companies": {
        "module_description": "Company management with advanced VQL queries, filtering, and CRUD operations. See comprehensive documentation: docs/GraphQL/04_COMPANIES_MODULE.md",
        "queries": [
            {
                "name": "Get Company",
                "query": "query GetCompany($uuid: ID!) { companies { company(uuid: $uuid) { uuid name employeesCount industries keywords address linkedinUrl website city country } } }",
                "variables": {"uuid": "{{companyUuid}}"},
                "description": "Get company by UUID. Requires authentication. See docs/GraphQL/04_COMPANIES_MODULE.md#company for validation rules and implementation details."
            },
            {
                "name": "List Companies (Basic)",
                "query": "query ListCompanies($query: VQLQueryInput) { companies { companies(query: $query) { items { uuid name employeesCount industries } total limit offset } } }",
                "variables": {"query": {"limit": 50, "offset": 0}},
                "description": "Basic company listing with pagination"
            },
            {
                "name": "Text Search - Company Name (Shuffle)",
                "query": "query SearchCompanyName($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries website } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "name", "operator": "contains", "value": "acme corporation"}
                            ]
                        },
                        "limit": 25,
                        "page": 1
                    }
                },
                "description": "Flexible company name search with typo tolerance (shuffle search type)"
            },
            {
                "name": "Text Search - Exact Industry",
                "query": "query SearchByExactIndustry($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "exact", "value": "software as a service"}
                            ]
                        },
                        "limit": 50
                    }
                },
                "description": "Exact phrase matching for industries"
            },
            {
                "name": "Keyword Filter - Industries & Technologies",
                "query": "query TechCompanies($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries keywords technologies } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS", "Technology"]},
                                {"field": "technologies", "operator": "in", "value": ["Python", "AWS", "React", "Go"]}
                            ]
                        },
                        "limit": 100
                    }
                },
                "description": "Find companies in specific industries using specific technologies"
            },
            {
                "name": "Range Query - Employee Count",
                "query": "query MidSizeCompanies($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries annualRevenue } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "employees_count", "operator": "gte", "value": 50},
                                {"field": "employees_count", "operator": "lte", "value": 1000}
                            ]
                        },
                        "limit": 100
                    }
                },
                "description": "Find mid-size companies by employee count range"
            },
            {
                "name": "Range Query - Revenue & Funding",
                "query": "query HighValueCompanies($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount annualRevenue totalFunding industries } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "annual_revenue", "operator": "gte", "value": 1000000},
                                {"field": "total_funding", "operator": "gte", "value": 5000000}
                            ]
                        },
                        "orderBy": [{"orderBy": "annual_revenue", "orderDirection": "desc"}],
                        "limit": 50,
                        "page": 1
                    }
                },
                "description": "Find high-value companies by revenue and funding"
            },
            {
                "name": "Combined Filters - Text + Keyword + Range",
                "query": "query ComplexCompanySearch($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries technologies annualRevenue totalFunding city country } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "name", "operator": "contains", "value": "tech software"},
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS", "Technology"]},
                                {"field": "technologies", "operator": "in", "value": ["Python", "Go", "AWS"]},
                                {"field": "employees_count", "operator": "gte", "value": 100},
                                {"field": "employees_count", "operator": "lte", "value": 5000},
                                {"field": "annual_revenue", "operator": "gte", "value": 5000000},
                                {"field": "country", "operator": "in", "value": ["united states", "canada", "united kingdom"]}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "annual_revenue", "orderDirection": "desc"},
                            {"orderBy": "employees_count", "orderDirection": "desc"}
                        ],
                        "limit": 50,
                        "page": 1
                    }
                },
                "description": "Complex filtering combining text search, keyword filters, and numeric ranges"
            },
            {
                "name": "Cursor Pagination - First Page",
                "query": "query FirstPageCompanies($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS"]}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "name", "orderDirection": "asc"},
                            {"orderBy": "employees_count", "orderDirection": "desc"}
                        ],
                        "limit": 25
                    }
                },
                "description": "Initial request for cursor-based pagination. Extract values from last document for searchAfter."
            },
            {
                "name": "Cursor Pagination - Next Page",
                "query": "query NextPageCompanies($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS"]}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "name", "orderDirection": "asc"},
                            {"orderBy": "employees_count", "orderDirection": "desc"}
                        ],
                        "searchAfter": ["Acme Corp", 500],
                        "limit": 25
                    }
                },
                "description": "Next page using search_after cursor. Replace values with actual values from last document of previous response."
            },
            {
                "name": "Real-World: Target Account List",
                "query": "query TargetAccounts($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries annualRevenue totalFunding technologies website city country } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS", "Technology"]},
                                {"field": "employees_count", "operator": "gte", "value": 100},
                                {"field": "employees_count", "operator": "lte", "value": 2000},
                                {"field": "annual_revenue", "operator": "gte", "value": 5000000},
                                {"field": "technologies", "operator": "in", "value": ["AWS", "Python", "React", "Go"]},
                                {"field": "country", "operator": "in", "value": ["united states", "canada"]}
                            ]
                        },
                        "orderBy": [{"orderBy": "annual_revenue", "orderDirection": "desc"}],
                        "limit": 200,
                        "page": 1
                    }
                },
                "description": "Build target account list for account-based marketing - ideal company size, revenue, and tech stack"
            },
            {
                "name": "Real-World: Competitive Analysis",
                "query": "query Competitors($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries annualRevenue totalFunding technologies keywords website } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "name", "operator": "contains", "value": "competitor company names"},
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS"]},
                                {"field": "technologies", "operator": "in", "value": ["Python", "AWS", "React"]}
                            ]
                        },
                        "orderBy": [{"orderBy": "employees_count", "orderDirection": "desc"}],
                        "limit": 100
                    }
                },
                "description": "Find competitors by name, industry, and technology stack for competitive analysis"
            },
            {
                "name": "Real-World: Partnership Opportunities",
                "query": "query PartnershipTargets($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries annualRevenue technologies website city country } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS", "Technology"]},
                                {"field": "employees_count", "operator": "gte", "value": 50},
                                {"field": "employees_count", "operator": "lte", "value": 500},
                                {"field": "annual_revenue", "operator": "gte", "value": 1000000},
                                {"field": "technologies", "operator": "in", "value": ["Python", "Go", "AWS", "React"]},
                                {"field": "country", "operator": "in", "value": ["united states", "canada", "united kingdom"]}
                            ]
                        },
                        "orderBy": [{"orderBy": "annual_revenue", "orderDirection": "desc"}],
                        "limit": 100,
                        "page": 1
                    }
                },
                "description": "Find partnership opportunities - complementary companies in similar industries with compatible tech stacks"
            },
            {
                "name": "Real-World: Geographic Expansion",
                "query": "query GeographicTargets($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount industries city state country website } total } } }",
                "variables": {
                    "query": {
                        "filters": {
                            "conditions": [
                                {"field": "industries", "operator": "in", "value": ["Software", "SaaS"]},
                                {"field": "employees_count", "operator": "gte", "value": 100},
                                {"field": "city", "operator": "in", "value": ["San Francisco", "New York", "Austin", "Seattle"]},
                                {"field": "state", "operator": "in", "value": ["California", "New York", "Texas", "Washington"]},
                                {"field": "country", "operator": "eq", "value": "united states"}
                            ]
                        },
                        "orderBy": [
                            {"orderBy": "employees_count", "orderDirection": "desc"},
                            {"orderBy": "city", "orderDirection": "asc"}
                        ],
                        "limit": 200,
                        "page": 1
                    }
                },
                "description": "Find companies in target geographic regions for expansion planning"
            },
            {
                "name": "Company Query (VQL)",
                "query": "query CompanyQuery($query: VQLQueryInput!) { companies { companyQuery(query: $query) { items { uuid name employeesCount } total } } }",
                "variables": {"query": {"filters": {"conditions": [{"field": "employeesCount", "operator": "gte", "value": 100}]}}},
                "description": "Advanced VQL query with custom filters"
            },
            {
                "name": "Company Contacts",
                "query": "query CompanyContacts($companyUuid: ID!) { companies { companyContacts(companyUuid: $companyUuid) { items { uuid firstName lastName email title } total } } }",
                "variables": {"companyUuid": "{{companyUuid}}"}
            },
            {
                "name": "Get Filters",
                "query": "query GetFilters { companies { filters { items { id key service filterType displayName directDerived active } total } } }",
                "description": "Get available filters for companies. Service is automatically set to 'company'."
            },
            {
                "name": "Get Filter Data",
                "query": "query GetFilterData($input: CompanyFilterDataInput!) { companies { filterData(input: $input) { items { value displayValue } total } } }",
                "variables": {"input": {"filterKey": "industry", "searchText": "tech", "page": 1, "limit": 20}},
                "description": "Get filter values for a specific filter key. Service is automatically set to 'company'. See docs/GraphQL/04_COMPANIES_MODULE.md#filterdata for details."
            }
        ],
        "mutations": [
            {
                "name": "Create Company",
                "query": "mutation CreateCompany($input: CreateCompanyInput!) { companies { createCompany(input: $input) { uuid name employeesCount industries website } } }",
                "variables": {
                    "input": {
                        "name": "Acme Corporation",
                        "website": "https://acme.com",
                        "industries": ["Software", "SaaS"]
                    }
                },
                "description": "Create a new company via Connectra batch upsert. Requires authentication. See docs/GraphQL/04_COMPANIES_MODULE.md#createcompany for validation rules and implementation details."
            },
            {
                "name": "Update Company",
                "query": "mutation UpdateCompany($uuid: ID!, $input: UpdateCompanyInput!) { companies { updateCompany(uuid: $uuid, input: $input) { uuid name employeesCount industries website } } }",
                "variables": {
                    "uuid": "{{companyUuid}}",
                    "input": {
                        "name": "Acme Corporation Updated",
                        "employeesCount": 500
                    }
                },
                "description": "Update an existing company via Connectra batch upsert. Requires authentication. See docs/GraphQL/04_COMPANIES_MODULE.md#updatecompany for validation rules and implementation details."
            },
            {
                "name": "Delete Company",
                "query": "mutation DeleteCompany($uuid: ID!) { companies { deleteCompany(uuid: $uuid) } }",
                "variables": {"uuid": "{{companyUuid}}"},
                "description": "Delete a company. Currently raises NotImplementedError as Connectra API does not support company deletion. See docs/GraphQL/04_COMPANIES_MODULE.md#deletecompany for details."
            }
        ]
    },
    "Notifications": {
        "module_description": "Notification management with user isolation, batch operations, and preference management. See comprehensive documentation: docs/GraphQL/05_NOTIFICATIONS_MODULE.md",
        "queries": [
            {
                "name": "List Notifications",
                "query": "query ListNotifications($filters: NotificationFilterInput) { notifications { notifications(filters: $filters) { items { id title message type priority read createdAt } pageInfo { total } } } }",
                "variables": {"filters": {"unreadOnly": True, "limit": 20}},
                "description": "List user notifications with filters. See docs/GraphQL/05_NOTIFICATIONS_MODULE.md#notifications for validation rules (pagination limits, type enum) and implementation details."
            },
            {
                "name": "Get Notification",
                "query": "query GetNotification($notificationId: ID!) { notifications { notification(notificationId: $notificationId) { id title message type priority read createdAt } } }",
                "variables": {"notificationId": "{{notificationId}}"}
            },
            {
                "name": "Unread Count",
                "query": "query { notifications { unreadCount { count } } }"
            },
            {
                "name": "Notification Preferences",
                "query": "query { notifications { notificationPreferences { emailEnabled pushEnabled } } }"
            }
        ],
        "mutations": [
            {
                "name": "Mark Notification Read",
                "query": "mutation MarkRead($notificationId: ID!) { notifications { markNotificationAsRead(notificationId: $notificationId) { id read } } }",
                "variables": {"notificationId": "{{notificationId}}"}
            },
            {
                "name": "Mark All Read",
                "query": "mutation { notifications { markAllNotificationsAsRead { count } } }"
            },
            {
                "name": "Delete Notification",
                "query": "mutation DeleteNotification($notificationId: ID!) { notifications { deleteNotification(notificationId: $notificationId) } }",
                "variables": {"notificationId": "{{notificationId}}"}
            }
        ]
    },
    "Exports": {
        "module_description": "Export job management for contacts and companies with asynchronous processing, S3 storage, and presigned URLs. See comprehensive documentation: docs/GraphQL/06_EXPORTS_MODULE.md",
        "queries": [
            {
                "name": "Get Export",
                "query": "query GetExport($exportId: ID!) { exports { export(exportId: $exportId) { exportId downloadUrl expiresAt status contactCount companyCount } } }",
                "variables": {"exportId": "{{exportId}}"},
                "description": "Get export by ID. See docs/GraphQL/06_EXPORTS_MODULE.md#export for validation rules (UUID format) and implementation details."
            },
            {
                "name": "List Exports",
                "query": "query ListExports($pagination: ExportPaginationInput) { exports { exports(pagination: $pagination) { items { exportId status createdAt contactCount } total } } }",
                "variables": {"pagination": {"limit": 20, "offset": 0}}
            },
            {
                "name": "Export Status",
                "query": "query ExportStatus($exportId: ID!) { exports { exportStatus(exportId: $exportId) { status progressPercentage downloadUrl } } }",
                "variables": {"exportId": "{{exportId}}"}
            }
        ],
        "mutations": [
            {
                "name": "Create Contact Export",
                "query": "mutation CreateContactExport($input: CreateContactExportInput!) { exports { createContactExport(input: $input) { exportId downloadUrl status } } }",
                "variables": {"input": {"contactUuids": ["{{contactUuid}}"]}}
            },
            {
                "name": "Create Company Export",
                "query": "mutation CreateCompanyExport($input: CreateCompanyExportInput!) { exports { createCompanyExport(input: $input) { exportId downloadUrl status } } }",
                "variables": {"input": {"companyUuids": ["{{companyUuid}}"]}}
            }
        ]
    },
    "S3": {
        "module_description": "S3 file operations for CSV files including listing, reading paginated data, and getting file metadata. See comprehensive documentation: docs/GraphQL/07_S3_MODULE.md",
        "queries": [
            {
                "name": "List S3 Files",
                "query": "query ListS3Files($prefix: String) { s3 { s3Files(prefix: $prefix) { files { key filename size lastModified } total } } }",
                "variables": {"prefix": "exports/"},
                "description": "List CSV files in S3. See docs/GraphQL/07_S3_MODULE.md#s3files for validation rules (prefix max 500 chars) and implementation details."
            },
            {
                "name": "Get S3 File Data",
                "query": "query GetS3FileData($fileKey: String!, $limit: Int!, $offset: Int) { s3 { s3FileData(fileKey: $fileKey, limit: $limit, offset: $offset) { rows { data } total limit offset } } }",
                "variables": {"fileKey": "exports/file.csv", "limit": 100, "offset": 0}
            },
            {
                "name": "Get S3 File Info",
                "query": "query GetS3FileInfo($fileKey: String!) { s3 { s3FileInfo(fileKey: $fileKey) { key filename size lastModified contentType } } }",
                "variables": {"fileKey": "exports/file.csv"}
            }
        ],
        "mutations": []
    },
    "Email": {
        "module_description": "Email finding, verification (single and bulk), email generation, and export functionality with credit-based operations. See comprehensive documentation: docs/GraphQL/15_EMAIL_MODULE.md",
        "queries": [
            {
                "name": "Find Emails",
                "query": "query FindEmails($input: EmailFinderInput!) { email { findEmails(input: $input) { emails { uuid email } total } } }",
                "variables": {"input": {"firstName": "John", "lastName": "Doe", "domain": "example.com"}},
                "description": "Find emails by name and domain. See docs/GraphQL/15_EMAIL_MODULE.md#findemails for validation rules (name max 100 chars, domain max 255 chars) and credit costs."
            }
        ],
        "mutations": [
            {
                "name": "Find Single Email",
                "query": "mutation FindSingleEmail($input: SingleEmailInput!) { email { findSingleEmail(input: $input) { email source } } }",
                "variables": {"input": {"firstName": "John", "lastName": "Doe", "domain": "example.com"}}
            },
            {
                "name": "Verify Single Email",
                "query": "mutation VerifySingle($input: SingleVerifyInput!) { email { verifySingle(input: $input) { email status score reason } } }",
                "variables": {"input": {"email": "john.doe@example.com", "provider": "truelist"}}
            },
            {
                "name": "Verify Bulk Emails",
                "query": "mutation VerifyBulk($input: BulkVerifyInput!) { email { verifyBulk(input: $input) { results { email status score } total validCount invalidCount } } }",
                "variables": {"input": {"emails": ["email1@example.com", "email2@example.com"], "provider": "truelist"}}
            }
        ]
    },
    "Billing": {
        "module_description": "Subscription management, plans, addon packages, invoices, and credit management with role-based access. See comprehensive documentation: docs/GraphQL/14_BILLING_MODULE.md",
        "queries": [
            {
                "name": "Get Billing Info",
                "query": "query { billing { billing { credits creditsUsed creditsLimit subscriptionPlan subscriptionStatus usagePercentage } } }",
                "description": "Get current user billing information. See docs/GraphQL/14_BILLING_MODULE.md#billing for details."
            },
            {
                "name": "Get Plans",
                "query": "query { billing { plans { tier name category periods { monthly { price credits } yearly { price credits savings { percentage } } } } } }",
                "auth": False
            },
            {
                "name": "Get Addons",
                "query": "query { billing { addons { id name credits price } } }",
                "auth": False
            },
            {
                "name": "List Invoices",
                "query": "query ListInvoices($pagination: InvoicePaginationInput) { billing { invoices(pagination: $pagination) { items { id amount status createdAt } total } } }",
                "variables": {"pagination": {"limit": 20, "offset": 0}}
            }
        ],
        "mutations": [
            {
                "name": "Subscribe",
                "query": "mutation Subscribe($input: SubscribeInput!) { billing { subscribe(input: $input) { message subscriptionPlan credits } } }",
                "variables": {"input": {"tier": "pro", "period": "monthly"}}
            },
            {
                "name": "Purchase Addon",
                "query": "mutation PurchaseAddon($input: PurchaseAddonInput!) { billing { purchaseAddon(input: $input) { message creditsAdded totalCredits } } }",
                "variables": {"input": {"packageId": "addon_1000_credits"}}
            },
            {
                "name": "Cancel Subscription",
                "query": "mutation { billing { cancelSubscription { message subscriptionStatus } } }"
            }
        ],
        "admin_mutations": [
            {
                "name": "Create Plan",
                "query": "mutation CreatePlan($input: CreatePlanInput!) { billing { createPlan(input: $input) { message tier } } }",
                "variables": {
                    "input": {
                        "tier": "test",
                        "name": "Test Plan",
                        "category": "STARTER",
                        "periods": [
                            {
                                "period": "monthly",
                                "credits": 1000,
                                "ratePerCredit": 0.001,
                                "price": 10.00
                            }
                        ],
                        "isActive": True
                    }
                }
            },
            {
                "name": "Update Plan",
                "query": "mutation UpdatePlan($tier: String!, $input: UpdatePlanInput!) { billing { updatePlan(tier: $tier, input: $input) { message tier } } }",
                "variables": {
                    "tier": "5k",
                    "input": {
                        "name": "Updated Plan Name",
                        "category": "PROFESSIONAL"
                    }
                }
            },
            {
                "name": "Delete Plan",
                "query": "mutation DeletePlan($tier: String!) { billing { deletePlan(tier: $tier) { message tier } } }",
                "variables": {"tier": "test"}
            },
            {
                "name": "Create Plan Period",
                "query": "mutation CreatePlanPeriod($tier: String!, $input: CreatePlanPeriodInput!) { billing { createPlanPeriod(tier: $tier, input: $input) { message tier period } } }",
                "variables": {
                    "tier": "5k",
                    "input": {
                        "period": "monthly",
                        "credits": 5000,
                        "ratePerCredit": 0.002,
                        "price": 10.00,
                        "savingsAmount": None,
                        "savingsPercentage": None
                    }
                }
            },
            {
                "name": "Update Plan Period",
                "query": "mutation UpdatePlanPeriod($tier: String!, $period: String!, $input: UpdatePlanPeriodInput!) { billing { updatePlanPeriod(tier: $tier, period: $period, input: $input) { message tier period } } }",
                "variables": {
                    "tier": "5k",
                    "period": "monthly",
                    "input": {
                        "credits": 6000,
                        "price": 12.00
                    }
                }
            },
            {
                "name": "Delete Plan Period",
                "query": "mutation DeletePlanPeriod($tier: String!, $period: String!) { billing { deletePlanPeriod(tier: $tier, period: $period) { message tier period } } }",
                "variables": {"tier": "5k", "period": "monthly"}
            },
            {
                "name": "Create Addon",
                "query": "mutation CreateAddon($input: CreateAddonInput!) { billing { createAddon(input: $input) { message id } } }",
                "variables": {
                    "input": {
                        "id": "test_addon",
                        "name": "Test Addon",
                        "credits": 1000,
                        "ratePerCredit": 0.001,
                        "price": 10.00,
                        "isActive": True
                    }
                }
            },
            {
                "name": "Update Addon",
                "query": "mutation UpdateAddon($packageId: String!, $input: UpdateAddonInput!) { billing { updateAddon(packageId: $packageId, input: $input) { message id } } }",
                "variables": {
                    "packageId": "small",
                    "input": {
                        "name": "Updated Addon Name",
                        "credits": 6000,
                        "price": 12.00
                    }
                }
            },
            {
                "name": "Delete Addon",
                "query": "mutation DeleteAddon($packageId: String!) { billing { deleteAddon(packageId: $packageId) { message id } } }",
                "variables": {"packageId": "test_addon"}
            }
        ]
    },
    "Usage": {
        "module_description": "Feature usage tracking with role-based limits, auto-creation of usage records, and monthly period-based resets. See comprehensive documentation: docs/GraphQL/09_USAGE_MODULE.md",
        "queries": [
            {
                "name": "Get Usage",
                "query": "query GetUsage($feature: String) { usage { usage(feature: $feature) { features { feature used limit remaining resetAt } } } }",
                "variables": {"feature": "EMAIL_FINDER"},
                "description": "Get current feature usage. Auto-creates records if missing, performs monthly resets. See docs/GraphQL/09_USAGE_MODULE.md#usage for role-based limits and implementation details."
            }
        ],
        "mutations": [
            {
                "name": "Track Usage",
                "query": "mutation TrackUsage($input: TrackUsageInput!) { usage { trackUsage(input: $input) { feature used limit success } } }",
                "variables": {"input": {"feature": "EMAIL_FINDER", "amount": 1}}
            },
            {
                "name": "Reset Usage",
                "query": "mutation ResetUsage($input: ResetUsageInput!) { usage { resetUsage(input: $input) { feature used limit success } } }",
                "variables": {"input": {"feature": "EMAIL_FINDER"}}
            }
        ]
    },
    "Activities": {
        "module_description": "User activity tracking and statistics with filtering, pagination, and timezone handling. See comprehensive documentation: docs/GraphQL/11_ACTIVITIES_MODULE.md",
        "queries": [
            {
                "name": "List Activities",
                "query": "query ListActivities($filters: ActivityFilterInput) { activities { activities(filters: $filters) { items { id userId serviceType actionType status resultCount createdAt } total limit offset hasNext hasPrevious } } }",
                "variables": {"filters": {"serviceType": "ai_chats", "actionType": "create", "limit": 50, "offset": 0}},
                "description": "List user activities with filters. See docs/GraphQL/11_ACTIVITIES_MODULE.md#activities for validation rules (pagination, enum validation, date ranges) and implementation details."
            },
            {
                "name": "Activity Stats",
                "query": "query ActivityStats($filters: ActivityStatsInput) { activities { activityStats(filters: $filters) { totalActivities byServiceType byActionType byStatus recentActivities } } }",
                "variables": {"filters": {"startDate": "2024-01-01T00:00:00Z", "endDate": "2024-01-31T23:59:59Z"}}
            }
        ],
        "mutations": []
    },
    "AI Chats": {
        "module_description": "AI chat management, message sending, email risk analysis, company summary generation, and contact filter parsing using Google Gemini AI. See comprehensive documentation: docs/GraphQL/17_AI_CHATS_MODULE.md",
        "queries": [
            {
                "name": "List AI Chats",
                "query": "query ListAIChats($filters: AIChatFilterInput) { aiChats { aiChats(filters: $filters) { items { uuid title createdAt } pageInfo { total } } } }",
                "variables": {"filters": {"limit": 20, "offset": 0}},
                "description": "List AI chats with pagination and filters. See docs/GraphQL/17_AI_CHATS_MODULE.md#aichats for validation rules and implementation details."
            },
            {
                "name": "Get AI Chat",
                "query": "query GetAIChat($chatId: String!) { aiChats { aiChat(chatId: $chatId) { uuid title messages { sender text contacts { firstName lastName email } } } } }",
                "variables": {"chatId": "{{chatId}}"}
            }
        ],
        "mutations": [
            {
                "name": "Create AI Chat",
                "query": "mutation CreateAIChat($input: CreateAIChatInput!) { aiChats { createAIChat(input: $input) { uuid title messages { sender text } } } }",
                "variables": {"input": {"title": "New Chat", "messages": []}}
            },
            {
                "name": "Send Message",
                "query": "mutation SendMessage($chatId: String!, $input: SendMessageInput!) { aiChats { sendMessage(chatId: $chatId, input: $input) { uuid messages { sender text contacts { firstName lastName } } } } } }",
                "variables": {"chatId": "{{chatId}}", "input": {"message": "Find VPs at tech companies"}}
            },
            {
                "name": "Analyze Email Risk",
                "query": "mutation AnalyzeEmailRisk($input: AnalyzeEmailRiskInput!) { aiChats { analyzeEmailRisk(input: $input) { riskScore analysis isRoleBased isDisposable } } }",
                "variables": {"input": {"email": "info@example.com"}}
            },
            {
                "name": "Generate Company Summary",
                "query": "mutation GenerateCompanySummary($input: GenerateCompanySummaryInput!) { aiChats { generateCompanySummary(input: $input) { summary } } }",
                "variables": {"input": {"companyName": "Acme Corp", "industry": "Technology"}}
            },
            {
                "name": "Parse Contact Filters",
                "query": "mutation ParseFilters($input: ParseFiltersInput!) { aiChats { parseContactFilters(input: $input) { jobTitles companyNames industry location employees seniority } } }",
                "variables": {"input": {"query": "Find VPs at tech companies in San Francisco"}}
            }
        ]
    },
    "Analytics": {
        "module_description": "Performance metric submission and aggregation (avg, min, max, p50, p75, p95, count) with non-blocking storage and user isolation. See comprehensive documentation: docs/GraphQL/18_ANALYTICS_MODULE.md",
        "queries": [
            {
                "name": "Performance Metrics",
                "query": "query GetPerformanceMetrics($input: GetMetricsInput) { analytics { performanceMetrics(input: $input) { id metricName metricValue timestamp metadata } } }",
                "variables": {"input": {"metricName": "LCP", "limit": 100}},
                "description": "Get performance metrics with filters. See docs/GraphQL/18_ANALYTICS_MODULE.md#performancemetrics for validation rules (limit 1-1000, date range) and implementation details."
            },
            {
                "name": "Aggregate Metrics",
                "query": "query AggregateMetrics($input: AggregateMetricsInput!) { analytics { aggregateMetrics(input: $input) { avg min max p50 p75 p95 count } } }",
                "variables": {"input": {"metricName": "LCP", "startDate": "2024-01-01T00:00:00Z", "endDate": "2024-01-31T23:59:59Z"}}
            }
        ],
        "mutations": [
            {
                "name": "Submit Performance Metric",
                "query": "mutation SubmitMetric($input: SubmitPerformanceMetricInput!) { analytics { submitPerformanceMetric(input: $input) { success message } } }",
                "variables": {"input": {"name": "LCP", "value": 2.5, "timestamp": 1705312200000}}
            }
        ]
    },
    "LinkedIn": {
        "module_description": "LinkedIn URL search for contacts and companies, and export functionality with credit deduction. See comprehensive documentation: docs/GraphQL/21_LINKEDIN_MODULE.md",
        "queries": [],
        "mutations": [
            {
                "name": "Search LinkedIn",
                "query": "mutation SearchLinkedIn($input: LinkedInSearchInput!) { linkedin { search(input: $input) { contacts { contact { uuid firstName lastName email } } totalContacts } } }",
                "variables": {"input": {"url": "https://www.linkedin.com/in/johndoe"}},
                "description": "Search contacts/companies by LinkedIn URL. See docs/GraphQL/21_LINKEDIN_MODULE.md#search for validation rules (URL format, max 2048 chars) and credit costs."
            },
            {
                "name": "Export LinkedIn Results",
                "query": "mutation ExportLinkedIn($input: LinkedInExportInput!) { linkedin { exportLinkedInResults(input: $input) { exportId downloadUrl contactCount companyCount } } }",
                "variables": {"input": {"urls": ["https://www.linkedin.com/in/johndoe"]}}
            }
        ]
    },
    "Sales Navigator": {
        "module_description": "Sales Navigator profile saving to Connectra via bulk upsert operations for contacts and companies. See comprehensive documentation: docs/GraphQL/23_SALES_NAVIGATOR_MODULE.md",
        "queries": [
            {
                "name": "List Scraping Records",
                "query": "query ListScrapingRecords($filters: SalesNavigatorFilterInput) { salesNavigator { salesNavigatorRecords(filters: $filters) { items { id timestamp version source } pageInfo { total } } } }",
                "variables": {"filters": {"limit": 20, "offset": 0}},
                "description": "List Sales Navigator scraping records. See docs/GraphQL/23_SALES_NAVIGATOR_MODULE.md for details."
            }
        ],
        "mutations": [
            {
                "name": "Save Profiles",
                "query": "mutation SaveProfiles($input: SaveProfilesInput!) { salesNavigator { saveSalesNavigatorProfiles(input: $input) { success totalProfiles savedCount errors } } }",
                "variables": {"input": {"profiles": [{"name": "Jane Smith", "title": "Senior Software Engineer", "company": "Tech Corp", "location": "San Francisco, CA", "profile_url": "https://linkedin.com/in/janesmith"}]}},
                "description": "Save profiles array to Connectra database via bulk upsert operations. Creates or updates contacts and companies based on the provided profile data. Returns success status, total profiles count, saved count (contacts created + contacts updated), and any errors."
            }
        ]
    },
    "Admin": {
        "module_description": "Administrative operations for user management (roles, credits, deletion), user statistics, user history, system logs, and log statistics. Requires Admin or SuperAdmin roles. See comprehensive documentation: docs/GraphQL/13_ADMIN_MODULE.md",
        "queries": [
            {
                "name": "List Users (Admin)",
                "query": "query ListUsers($filters: UserFilterInput) { admin { users(filters: $filters) { items { uuid email name profile { role credits } } pageInfo { total } } } }",
                "variables": {"query": {"limit": 50, "offset": 0}},
                "description": "List all users (Admin/SuperAdmin only). See docs/GraphQL/13_ADMIN_MODULE.md#users for validation rules and role-based access."
            },
            {
                "name": "User Stats (Admin)",
                "query": "query { admin { userStats { totalUsers activeUsers usersByRole usersByPlan } } }"
            },
            {
                "name": "Search Logs",
                "query": "query SearchLogs($input: LogSearchInput!) { admin { searchLogs(input: $input) { items { id timestamp level message } pageInfo { total } } } }",
                "variables": {"input": {"query": "error", "limit": 50}}
            }
        ],
        "mutations": [
            {
                "name": "Update User Role",
                "query": "mutation UpdateUserRole($input: UpdateUserRoleInput!) { admin { updateUserRole(input: $input) { uuid profile { role } } } }",
                "variables": {"input": {"userId": "{{userId}}", "role": "Admin"}}
            },
            {
                "name": "Update User Credits",
                "query": "mutation UpdateUserCredits($input: UpdateUserCreditsInput!) { admin { updateUserCredits(input: $input) { uuid profile { credits } } } }",
                "variables": {"input": {"userId": "{{userId}}", "credits": 5000}}
            }
        ]
    },
    "Dashboard Pages": {
        "module_description": "Dashboard page management with role-based access control and content filtering. Admin/SuperAdmin required for CRUD operations. See comprehensive documentation: docs/GraphQL/19_DASHBOARD_PAGES_MODULE.md",
        "queries": [
            {
                "name": "Get Dashboard Page",
                "query": "query GetDashboardPage($pageId: String!) { dashboardPages { dashboardPage(pageId: $pageId) { pageId metadata { title description route } accessControl { allowedRoles restrictionType } } } }",
                "variables": {"pageId": "dashboard-home"},
                "description": "Get dashboard page with role-based filtering. See docs/GraphQL/19_DASHBOARD_PAGES_MODULE.md#dashboardpage for validation rules (pageId max 255) and implementation details."
            },
            {
                "name": "List Dashboard Pages",
                "query": "query { dashboardPages { dashboardPages { pages { pageId metadata { title description } } total } } }"
            }
        ],
        "mutations": [
            {
                "name": "Create Dashboard Page",
                "query": "mutation CreateDashboardPage($input: CreateDashboardPageInput!) { dashboardPages { createDashboardPage(input: $input) { pageId metadata { title } } } }",
                "variables": {"input": {"pageId": "dashboard-home", "metadata": {"title": "Home", "description": "Main dashboard", "route": "/dashboard"}}}
            }
        ]
    },
    "Documentation": {
        "module_description": "Documentation page management with public access to pages and Admin/SuperAdmin CRUD operations. Content stored in S3, metadata in MongoDB. See comprehensive documentation: docs/GraphQL/20_DOCUMENTATION_MODULE.md",
        "queries": [
            {
                "name": "Get Documentation Page",
                "query": "query GetDocumentationPage($pageId: String!) { documentation { documentationPage(pageId: $pageId) { pageId title description contentUrl lastUpdated } } }",
                "variables": {"pageId": "getting-started"},
                "auth": False,
                "description": "Get documentation page metadata. Public access. See docs/GraphQL/20_DOCUMENTATION_MODULE.md#documentationpage for details."
            },
            {
                "name": "List Documentation Pages",
                "query": "query { documentation { documentationPages { pages { pageId title description } total } } }",
                "auth": False
            },
            {
                "name": "Get Documentation Content",
                "query": "query GetContent($pageId: String!) { documentation { documentationPageContent(pageId: $pageId) { pageId content } } }",
                "variables": {"pageId": "getting-started"},
                "auth": False,
                "description": "Get documentation page markdown content from S3. Public access. See docs/GraphQL/20_DOCUMENTATION_MODULE.md#documentationpagecontent for details."
            }
        ],
        "mutations": [
            {
                "name": "Create Documentation Page",
                "query": "mutation CreateDocumentationPage($input: CreateDocumentationPageInput!) { documentation { createDocumentationPage(input: $input) { pageId title description contentUrl } } }",
                "variables": {
                    "input": {
                        "pageId": "getting-started",
                        "title": "Getting Started",
                        "description": "Introduction to the API",
                        "category": "guides",
                        "content": "# Getting Started\n\nWelcome to the API..."
                    }
                },
                "description": "Create a new documentation page. Requires Admin or SuperAdmin role. See docs/GraphQL/20_DOCUMENTATION_MODULE.md#createdocumentationpage for validation rules (pageId max 255, title max 500, content max 100000) and implementation details."
            },
            {
                "name": "Update Documentation Page",
                "query": "mutation UpdateDocumentationPage($pageId: String!, $input: UpdateDocumentationPageInput!) { documentation { updateDocumentationPage(pageId: $pageId, input: $input) { pageId title description contentUrl } } }",
                "variables": {
                    "pageId": "getting-started",
                    "input": {
                        "title": "Updated Getting Started",
                        "description": "Updated introduction"
                    }
                },
                "description": "Update an existing documentation page. Requires Admin or SuperAdmin role. See docs/GraphQL/20_DOCUMENTATION_MODULE.md#updatedocumentationpage for validation rules and implementation details."
            },
            {
                "name": "Delete Documentation Page",
                "query": "mutation DeleteDocumentationPage($pageId: String!) { documentation { deleteDocumentationPage(pageId: $pageId) } }",
                "variables": {"pageId": "getting-started"},
                "description": "Delete a documentation page. Requires Admin or SuperAdmin role. See docs/GraphQL/20_DOCUMENTATION_MODULE.md#deletedocumentationpage for validation rules and implementation details."
            }
        ]
    },
    "Marketing": {
        "module_description": "Marketing page management with publish/unpublish functionality. Public queries return only published pages. Admin/SuperAdmin required for CRUD operations. See comprehensive documentation: docs/GraphQL/22_MARKETING_MODULE.md",
        "queries": [
            {
                "name": "Get Marketing Page",
                "query": "query GetMarketingPage($pageId: String!) { marketing { marketingPage(pageId: $pageId) { pageId metadata { title description status } hero { title subtitle description } } } }",
                "variables": {"pageId": "pricing"},
                "auth": False,
                "description": "Get marketing page. Public access, returns only published pages. See docs/GraphQL/22_MARKETING_MODULE.md#marketingpage for details."
            },
            {
                "name": "List Marketing Pages",
                "query": "query { marketing { marketingPages { pages { pageId metadata { title status } } total } } }",
                "auth": False,
                "description": "List all marketing pages. Public access, returns only published pages. See docs/GraphQL/22_MARKETING_MODULE.md#marketingpages for details."
            }
        ],
        "mutations": [
            {
                "name": "Create Marketing Page",
                "query": "mutation CreateMarketingPage($input: CreateMarketingPageInput!) { marketing { createMarketingPage(input: $input) { pageId metadata { title status } } } }",
                "variables": {
                    "input": {
                        "pageId": "pricing",
                        "metadata": {
                            "title": "Pricing",
                            "description": "Affordable pricing for everyone",
                            "status": "draft"
                        },
                        "hero": {
                            "title": "Simple Pricing",
                            "description": "Choose the plan that's right for you"
                        }
                    }
                },
                "description": "Create a new marketing page. Requires Admin or SuperAdmin role. See docs/GraphQL/22_MARKETING_MODULE.md#createmarketingpage for validation rules (pageId max 255) and implementation details."
            },
            {
                "name": "Update Marketing Page",
                "query": "mutation UpdateMarketingPage($pageId: String!, $input: UpdateMarketingPageInput!) { marketing { updateMarketingPage(pageId: $pageId, input: $input) { pageId metadata { title status } } } }",
                "variables": {
                    "pageId": "pricing",
                    "input": {
                        "metadata": {
                            "title": "Updated Pricing",
                            "status": "published"
                        }
                    }
                },
                "description": "Update an existing marketing page. Requires Admin or SuperAdmin role. See docs/GraphQL/22_MARKETING_MODULE.md#updatemarketingpage for validation rules and implementation details."
            },
            {
                "name": "Delete Marketing Page",
                "query": "mutation DeleteMarketingPage($pageId: String!) { marketing { deleteMarketingPage(pageId: $pageId) } }",
                "variables": {"pageId": "pricing"},
                "description": "Delete a marketing page. Requires Admin or SuperAdmin role. See docs/GraphQL/22_MARKETING_MODULE.md#deletemarketingpage for validation rules and implementation details."
            },
            {
                "name": "Publish Marketing Page",
                "query": "mutation PublishMarketingPage($pageId: String!) { marketing { publishMarketingPage(pageId: $pageId) { pageId metadata { status } } } }",
                "variables": {"pageId": "pricing"},
                "description": "Publish a marketing page (set status to 'published'). Requires Admin or SuperAdmin role. See docs/GraphQL/22_MARKETING_MODULE.md#publishmarketingpage for details."
            },
            {
                "name": "Unpublish Marketing Page",
                "query": "mutation UnpublishMarketingPage($pageId: String!) { marketing { unpublishMarketingPage(pageId: $pageId) { pageId metadata { status } } } }",
                "variables": {"pageId": "pricing"},
                "description": "Unpublish a marketing page (set status to 'draft'). Requires Admin or SuperAdmin role. See docs/GraphQL/22_MARKETING_MODULE.md#unpublishmarketingpage for details."
            }
        ]
    },
    "Saved Searches": {
        "module_description": "Save and manage search queries including search terms, filters, sorting, and pagination settings. Users can save frequently used searches for quick access and track usage statistics. See comprehensive documentation: docs/GraphQL/26_SAVED_SEARCHES_MODULE.md",
        "queries": [
            {
                "name": "List Saved Searches",
                "query": "query ListSavedSearches($type: String, $limit: Int, $offset: Int) { savedSearches { listSavedSearches(type: $type, limit: $limit, offset: $offset) { searches { id name description type search_term filters sort_field sort_direction page_size created_at updated_at last_used_at use_count } total } } }",
                "variables": {"type": "contact", "limit": 50, "offset": 0},
                "description": "List saved searches for the current user with optional type filter and pagination. See docs/GraphQL/26_SAVED_SEARCHES_MODULE.md#listsavedsearches for validation rules (limit 1-1000, type: contact/company/all) and implementation details."
            },
            {
                "name": "Get Saved Search",
                "query": "query GetSavedSearch($id: ID!) { savedSearches { getSavedSearch(id: $id) { id name description type search_term filters sort_field sort_direction page_size created_at updated_at last_used_at use_count } } }",
                "variables": {"id": "1"},
                "description": "Get a specific saved search by ID. Users can only access their own saved searches. See docs/GraphQL/26_SAVED_SEARCHES_MODULE.md#getsavedsearch for validation rules and implementation details."
            }
        ],
        "mutations": [
            {
                "name": "Create Saved Search",
                "query": "mutation CreateSavedSearch($input: CreateSavedSearchInput!) { savedSearches { createSavedSearch(input: $input) { id name description type search_term filters sort_field sort_direction page_size created_at use_count } } }",
                "variables": {
                    "input": {
                        "name": "Tech Companies in SF",
                        "description": "Technology companies in San Francisco",
                        "type": "company",
                        "search_term": "technology",
                        "filters": {"location": "San Francisco", "industry": "Technology"},
                        "sort_field": "name",
                        "sort_direction": "asc",
                        "page_size": 50
                    }
                },
                "description": "Create a new saved search. See docs/GraphQL/26_SAVED_SEARCHES_MODULE.md#createsavedsearch for validation rules (name max 255, description max 1000, type: contact/company/all) and implementation details."
            },
            {
                "name": "Update Saved Search",
                "query": "mutation UpdateSavedSearch($id: ID!, $input: UpdateSavedSearchInput!) { savedSearches { updateSavedSearch(id: $id, input: $input) { id name description type search_term filters sort_field sort_direction page_size updated_at } } }",
                "variables": {
                    "id": "1",
                    "input": {
                        "name": "Updated Search Name",
                        "description": "Updated description",
                        "page_size": 100
                    }
                },
                "description": "Update an existing saved search. Users can only update their own saved searches. See docs/GraphQL/26_SAVED_SEARCHES_MODULE.md#updatesavedsearch for validation rules and implementation details."
            },
            {
                "name": "Delete Saved Search",
                "query": "mutation DeleteSavedSearch($id: ID!) { savedSearches { deleteSavedSearch(id: $id) } }",
                "variables": {"id": "1"},
                "description": "Delete a saved search. Users can only delete their own saved searches. See docs/GraphQL/26_SAVED_SEARCHES_MODULE.md#deletesavedsearch for validation rules and implementation details."
            },
            {
                "name": "Update Saved Search Usage",
                "query": "mutation UpdateSavedSearchUsage($id: ID!) { savedSearches { updateSavedSearchUsage(id: $id) } }",
                "variables": {"id": "1"},
                "description": "Update the last used timestamp and increment use count for a saved search. Users can only update usage for their own saved searches. See docs/GraphQL/26_SAVED_SEARCHES_MODULE.md#updatesavedsearchusage for validation rules and implementation details."
            }
        ]
    },
    "Two-Factor Authentication": {
        "module_description": "Two-factor authentication setup, verification, and management with TOTP (Time-based One-Time Password) and backup codes. See comprehensive documentation: docs/GraphQL/27_TWO_FACTOR_MODULE.md",
        "queries": [
            {
                "name": "Get 2FA Status",
                "query": "query Get2FAStatus { twoFactor { get2FAStatus { enabled verified } } }",
                "description": "Get the current 2FA status for the authenticated user. See docs/GraphQL/27_TWO_FACTOR_MODULE.md#get2fastatus for implementation details."
            }
        ],
        "mutations": [
            {
                "name": "Setup 2FA",
                "query": "mutation Setup2FA { twoFactor { setup2FA { qr_code_url qr_code_data secret backup_codes } } }",
                "description": "Setup 2FA for the current user. Generates a TOTP secret, QR code, and backup codes. Secret and backup codes are shown only once - store them securely. See docs/GraphQL/27_TWO_FACTOR_MODULE.md#setup2fa for implementation details and production notes."
            },
            {
                "name": "Verify 2FA",
                "query": "mutation Verify2FA($code: String!) { twoFactor { verify2FA(code: $code) { verified backup_codes } } }",
                "variables": {"code": "123456"},
                "description": "Verify a 2FA code during setup or login. Enables 2FA if verification succeeds. See docs/GraphQL/27_TWO_FACTOR_MODULE.md#verify2fa for validation rules and implementation details."
            },
            {
                "name": "Disable 2FA",
                "query": "mutation Disable2FA($password: String, $backupCode: String) { twoFactor { disable2FA(password: $password, backupCode: $backupCode) } }",
                "variables": {"password": "userpassword123", "backupCode": "A1B2C3D4"},
                "description": "Disable 2FA for the current user. Requires password or backup code verification. See docs/GraphQL/27_TWO_FACTOR_MODULE.md#disable2fa for validation rules and implementation details."
            },
            {
                "name": "Regenerate Backup Codes",
                "query": "mutation RegenerateBackupCodes { twoFactor { regenerateBackupCodes { backup_codes } } }",
                "description": "Regenerate backup codes for the current user. Invalidates all previous backup codes. New backup codes are shown only once - store them securely. See docs/GraphQL/27_TWO_FACTOR_MODULE.md#regeneratebackupcodes for validation rules and implementation details."
            }
        ]
    },
    "Profile": {
        "module_description": "API key management, active session management, and team member management. Users can create and manage API keys for programmatic access, view and manage active sessions, and invite/manage team members. See comprehensive documentation: docs/GraphQL/28_PROFILE_MODULE.md",
        "queries": [
            {
                "name": "List API Keys",
                "query": "query ListAPIKeys { profile { listAPIKeys { keys { id name prefix created_at last_used_at read_access write_access expires_at } total } } }",
                "description": "List all API keys for the current user. Full keys are never returned (only prefix for display). See docs/GraphQL/28_PROFILE_MODULE.md#listapikeys for implementation details."
            },
            {
                "name": "List Sessions",
                "query": "query ListSessions { profile { listSessions { sessions { id user_agent ip_address created_at last_activity is_current } total } } }",
                "description": "List all active sessions for the current user. Only active sessions are returned. See docs/GraphQL/28_PROFILE_MODULE.md#listsessions for implementation details."
            },
            {
                "name": "List Team Members",
                "query": "query ListTeamMembers { profile { listTeamMembers { members { id email name role invited_at joined_at status } total } } }",
                "description": "List all team members for the current user's team. Only team owners can view their team members. See docs/GraphQL/28_PROFILE_MODULE.md#listteammembers for implementation details."
            }
        ],
        "mutations": [
            {
                "name": "Create API Key",
                "query": "mutation CreateAPIKey($input: CreateAPIKeyInput!) { profile { createAPIKey(input: $input) { id name prefix key read_access write_access expires_at created_at } } }",
                "variables": {
                    "input": {
                        "name": "Production API Key",
                        "read_access": True,
                        "write_access": False,
                        "expires_at": "2025-01-15T10:30:00Z"
                    }
                },
                "description": "Create a new API key for the current user. Full key is returned only once - store it securely. See docs/GraphQL/28_PROFILE_MODULE.md#createapikey for validation rules (name max 255) and security notes."
            },
            {
                "name": "Delete API Key",
                "query": "mutation DeleteAPIKey($id: ID!) { profile { deleteAPIKey(id: $id) } }",
                "variables": {"id": "1"},
                "description": "Delete an API key. Users can only delete their own API keys. See docs/GraphQL/28_PROFILE_MODULE.md#deleteapikey for validation rules and implementation details."
            },
            {
                "name": "Revoke Session",
                "query": "mutation RevokeSession($id: ID!) { profile { revokeSession(id: $id) } }",
                "variables": {"id": "1"},
                "description": "Revoke (logout) a specific session. Users can only revoke their own sessions. See docs/GraphQL/28_PROFILE_MODULE.md#revokesession for validation rules and implementation details."
            },
            {
                "name": "Revoke All Other Sessions",
                "query": "mutation RevokeAllOtherSessions { profile { revokeAllOtherSessions } }",
                "description": "Revoke all sessions except the current one. Useful for security when user suspects account compromise. See docs/GraphQL/28_PROFILE_MODULE.md#revokeallothersessions for implementation details."
            },
            {
                "name": "Invite Team Member",
                "query": "mutation InviteTeamMember($input: InviteTeamMemberInput!) { profile { inviteTeamMember(input: $input) { id email name role invited_at status } } }",
                "variables": {
                    "input": {
                        "email": "member@example.com",
                        "role": "Member"
                    }
                },
                "description": "Invite a new team member. Only team owners can invite members. Email notifications are not yet implemented. See docs/GraphQL/28_PROFILE_MODULE.md#inviteteammember for validation rules (email format, role max 50) and implementation details."
            },
            {
                "name": "Update Team Member Role",
                "query": "mutation UpdateTeamMemberRole($id: ID!, $role: String!) { profile { updateTeamMemberRole(id: $id, role: $role) { id email name role status } } }",
                "variables": {"id": "1", "role": "Admin"},
                "description": "Update a team member's role. Only team owners can update member roles. See docs/GraphQL/28_PROFILE_MODULE.md#updateteammemberrole for validation rules (role max 50) and implementation details."
            },
            {
                "name": "Remove Team Member",
                "query": "mutation RemoveTeamMember($id: ID!) { profile { removeTeamMember(id: $id) } }",
                "variables": {"id": "1"},
                "description": "Remove a team member from the team. Only team owners can remove members. See docs/GraphQL/28_PROFILE_MODULE.md#removeteammember for validation rules and implementation details."
            }
        ]
    },
    "Upload": {
        "module_description": "S3 multipart upload workflow for large files including session management, presigned URLs, resume functionality, and automatic cleanup. See comprehensive documentation: docs/GraphQL/10_UPLOAD_MODULE.md",
        "queries": [
            {
                "name": "Get Upload Status",
                "query": "query GetUploadStatus($uploadId: String!) { upload { uploadStatus(uploadId: $uploadId) { uploadId status partsUploaded totalParts } } }",
                "variables": {"uploadId": "{{uploadId}}"},
                "description": "Get multipart upload session status. See docs/GraphQL/10_UPLOAD_MODULE.md#uploadstatus for validation rules (uploadId max 200) and implementation details."
            },
            {
                "name": "Get Presigned URL",
                "query": "query GetPresignedUrl($uploadId: String!, $partNumber: Int!) { upload { presignedUrl(uploadId: $uploadId, partNumber: $partNumber) { url partNumber expiresAt } } }",
                "variables": {"uploadId": "{{uploadId}}", "partNumber": 1}
            }
        ],
        "mutations": [
            {
                "name": "Initiate Upload",
                "query": "mutation InitiateUpload($input: InitiateUploadInput!) { upload { initiateUpload(input: $input) { uploadId fileKey totalParts partSize } } }",
                "variables": {"input": {"filename": "large-file.zip", "fileSize": 10485760, "contentType": "application/zip"}}
            },
            {
                "name": "Complete Upload",
                "query": "mutation CompleteUpload($input: CompleteUploadInput!) { upload { completeUpload(input: $input) { uploadId fileKey fileUrl } } }",
                "variables": {"input": {"uploadId": "{{uploadId}}", "parts": [{"partNumber": 1, "etag": "etag1"}]}}
            }
        ]
    }
}

def create_request_item(req_config, is_mutation=False):
    """Create a Postman request item from configuration."""
    name = req_config["name"]
    query = req_config["query"]
    variables = req_config.get("variables", {})
    save_tokens = req_config.get("saveTokens", False)
    auth_required = req_config.get("auth", True)
    description = req_config.get("description", f"{name} - {'Mutation' if is_mutation else 'Query'}")
    
    request_item = {
        "name": name,
        "request": {
            "method": "POST",
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json"
                }
            ],
            "body": {
                "mode": "raw",
                "raw": json.dumps({
                    "query": query,
                    "variables": variables
                }, indent=2)
            },
            "url": {
                "raw": "{{baseUrl}}/graphql",
                "host": ["{{baseUrl}}"],
                "path": ["graphql"]
            },
            "description": description
        }
    }
    
    # Add auth header if required
    if auth_required:
        request_item["request"]["header"].append({
            "key": "Authorization",
            "value": "Bearer {{accessToken}}"
        })
    
    # Add test script to save tokens
    if save_tokens:
        request_item["event"] = [{
            "listen": "test",
            "script": {
                "exec": [
                    "if (pm.response.code === 200) {",
                    "    const jsonData = pm.response.json();",
                    "    const authData = jsonData.data?.auth;",
                    "    if (authData) {",
                    "        const result = authData.login || authData.register || authData.refreshToken;",
                    "        if (result) {",
                    "            if (result.accessToken) {",
                    "                pm.environment.set(\"accessToken\", result.accessToken);",
                    "            }",
                    "            if (result.refreshToken) {",
                    "                pm.environment.set(\"refreshToken\", result.refreshToken);",
                    "            }",
                    "            if (result.user && result.user.uuid) {",
                    "                pm.environment.set(\"userId\", result.user.uuid);",
                    "            }",
                    "        }",
                    "    }",
                    "}"
                ],
                "type": "text/javascript"
            }
        }]
    
    return request_item

def build_collection():
    """Build the complete Postman collection."""
    collection = BASE_COLLECTION.copy()
    
    # Add all modules
    for module_name, module_config in MODULE_REQUESTS.items():
        folder = {
            "name": module_name,
            "item": [],
            "description": f"{module_name} module - Queries and Mutations"
        }
        
        # Add queries
        for query_config in module_config.get("queries", []):
            folder["item"].append(create_request_item(query_config, is_mutation=False))
        
        # Add mutations
        for mutation_config in module_config.get("mutations", []):
            folder["item"].append(create_request_item(mutation_config, is_mutation=True))
        
        # Add admin mutations if they exist
        if module_config.get("admin_mutations"):
            admin_folder = {
                "name": f"{module_name} - Admin",
                "item": [],
                "description": f"{module_name} module - Admin Mutations (SuperAdmin only)"
            }
            for mutation_config in module_config.get("admin_mutations", []):
                admin_folder["item"].append(create_request_item(mutation_config, is_mutation=True))
            collection["item"].append(admin_folder)
        
        collection["item"].append(folder)
    
    return collection

def main():
    """Generate the Postman collection file."""
    collection = build_collection()
    output_file = Path(__file__).parent / "Contact360_GraphQL_API.postman_collection.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    total_requests = sum(
        len(m.get("queries", [])) + len(m.get("mutations", [])) + len(m.get("admin_mutations", []))
        for m in MODULE_REQUESTS.values()
    )
    
    print(f"✅ Generated Postman collection: {output_file}")
    print(f"📦 Total modules: {len(MODULE_REQUESTS)}")
    print(f"📝 Total requests: {total_requests}")
    print(f"\n📋 Modules included:")
    for module_name in MODULE_REQUESTS.keys():
        print(f"   - {module_name}")

if __name__ == "__main__":
    main()
