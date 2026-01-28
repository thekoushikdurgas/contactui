#!/usr/bin/env python3
"""
Generate Postman collection from GraphQL module documentation.

> **📚 For comprehensive module documentation**, see docs/GraphQL/README.md which includes
> detailed queries, mutations, validation rules, error handling, and implementation details
> for all 22 modules.

Note: This is a basic generator. For comprehensive collection with detailed queries,
mutations, and validation rule references, use build_complete_collection.py instead.
"""

import json
import os
from pathlib import Path

# Module definitions with their queries and mutations
MODULES = {
    "Auth": {
        "queries": ["me", "session"],
        "mutations": ["login", "register", "logout", "refreshToken"]
    },
    "Users": {
        "queries": ["user", "users", "userStats"],
        "mutations": ["updateProfile", "uploadAvatar", "updateUser"]
    },
    "Contacts": {
        "queries": ["contact", "contacts", "contactCount", "contactQuery"],
        "mutations": ["createContact", "updateContact", "deleteContact", "batchCreateContacts"]
    },
    "Companies": {
        "queries": ["company", "companies", "companyQuery", "companyContacts"],
        "mutations": ["createCompany", "updateCompany", "deleteCompany"]
    },
    "Health": {
        "queries": ["apiMetadata", "apiHealth", "vqlHealth", "vqlStats", "performanceStats"],
        "mutations": []
    },
    "Notifications": {
        "queries": ["notifications", "notification", "unreadCount", "notificationPreferences"],
        "mutations": ["markNotificationAsRead", "markNotificationsAsRead", "deleteNotifications", "updateNotificationPreferences"]
    },
    "Exports": {
        "queries": ["export", "exports", "exportStatus"],
        "mutations": ["createContactExport", "createCompanyExport"]
    },
    "S3": {
        "queries": ["s3Files", "s3FileData", "s3FileInfo"],
        "mutations": []
    },
    "Upload": {
        "queries": ["uploadStatus", "presignedUrl"],
        "mutations": ["initiateUpload", "registerPart", "completeUpload", "abortUpload"]
    },
    "Jobs": {
        "queries": ["jobs", "job", "uploadUrl", "exportDownloadUrl"],
        "mutations": ["createJob", "createExportJob"]
    },
    "Imports": {
        "queries": ["importJobs", "importJob"],
        "mutations": ["createImportJob"]
    },
    "Usage": {
        "queries": ["usage"],
        "mutations": ["trackUsage", "resetUsage"]
    },
    "Activities": {
        "queries": ["activities", "activityStats"],
        "mutations": []
    },
    "Admin": {
        "queries": ["users", "userStats", "userHistory", "logs", "logStats", "searchLogs"],
        "mutations": ["updateUserRole", "updateUserCredits", "deleteUser", "promoteToAdmin", "promoteToSuperAdmin"]
    },
    "Billing": {
        "queries": ["billing", "plans", "addons", "invoices"],
        "mutations": ["subscribe", "purchaseAddon", "cancelSubscription"]
    },
    "Email": {
        "queries": ["findEmails"],
        "mutations": ["findSingleEmail", "verifySingle", "verifyBulk", "generateAndVerify", "verifyAndFind", "exportEmails"]
    },
    "AI Chats": {
        "queries": ["aiChats", "aiChat"],
        "mutations": ["createAIChat", "updateAIChat", "deleteAIChat", "sendMessage", "analyzeEmailRisk", "generateCompanySummary", "parseContactFilters"]
    },
    "Analytics": {
        "queries": ["performanceMetrics", "aggregateMetrics"],
        "mutations": ["submitPerformanceMetric"]
    },
    "Dashboard Pages": {
        "queries": ["dashboardPage", "dashboardPages"],
        "mutations": ["createDashboardPage", "updateDashboardPage", "deleteDashboardPage"]
    },
    "Documentation": {
        "queries": ["documentationPage", "documentationPages", "documentationPageContent"],
        "mutations": ["createDocumentationPage", "updateDocumentationPage", "deleteDocumentationPage"]
    },
    "LinkedIn": {
        "queries": [],
        "mutations": ["search", "exportLinkedInResults"]
    },
    "Marketing": {
        "queries": ["marketingPage", "marketingPages"],
        "mutations": ["createMarketingPage", "updateMarketingPage", "deleteMarketingPage", "publishMarketingPage", "unpublishMarketingPage"]
    },
    "Sales Navigator": {
        "queries": ["salesNavigatorRecords"],
        "mutations": ["saveSalesNavigatorProfiles"]
    },
    "Saved Searches": {
        "queries": ["listSavedSearches", "getSavedSearch"],
        "mutations": ["createSavedSearch", "updateSavedSearch", "deleteSavedSearch", "updateSavedSearchUsage"]
    },
    "Two-Factor Authentication": {
        "queries": ["get2FAStatus"],
        "mutations": ["setup2FA", "verify2FA", "disable2FA", "regenerateBackupCodes"]
    },
    "Profile": {
        "queries": ["listAPIKeys", "listSessions", "listTeamMembers"],
        "mutations": ["createAPIKey", "deleteAPIKey", "revokeSession", "revokeAllOtherSessions", "inviteTeamMember", "updateTeamMemberRole", "removeTeamMember"]
    }
}

def create_request(name, operation_type, query_template, description=""):
    """Create a Postman request item."""
    is_mutation = operation_type == "mutation"
    operation_name = name[0].lower() + name[1:] if name else ""
    
    # Build GraphQL query - use string replacement instead of format to avoid brace conflicts
    query = query_template.replace("{operation}", name).replace("{operationName}", operation_name)
    
    request = {
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
                    "variables": {}
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
    
    # Add Authorization header for mutations and most queries
    if is_mutation or name not in ["apiMetadata", "apiHealth", "plans", "addons"]:
        request["request"]["header"].append({
            "key": "Authorization",
            "value": "Bearer {{accessToken}}"
        })
    
    # Add test script for login/register to save tokens
    if name in ["Login", "Register"]:
        request["event"] = [{
            "listen": "test",
            "script": {
                "exec": [
                    "if (pm.response.code === 200) {",
                    "    const jsonData = pm.response.json();",
                    f"    const path = jsonData.data?.auth?.{operation_name};",
                    "    if (path) {",
                    "        pm.environment.set(\"accessToken\", path.accessToken);",
                    "        pm.environment.set(\"refreshToken\", path.refreshToken);",
                    "        if (path.user) {",
                    "            pm.environment.set(\"userId\", path.user.uuid);",
                    "        }",
                    "    }",
                    "}"
                ],
                "type": "text/javascript"
            }
        }]
    
    return request

def create_module_folder(module_name, module_data):
    """Create a folder for a module with all its requests."""
    folder = {
        "name": module_name,
        "item": [],
        "description": f"{module_name} module requests"
    }
    
    # Add queries
    for query in module_data["queries"]:
        query_name = query[0].upper() + query[1:] if query else ""
        # Use {operation} and {operationName} as placeholders - escape GraphQL braces properly
        module_lower = module_name.lower()
        query_template = f"query {{operation}} {{ {module_lower} {{ {{operationName}} }} }}"
        request = create_request(
            query_name,
            "query",
            query_template,
            f"{module_name} {query} query"
        )
        folder["item"].append(request)
    
    # Add mutations
    for mutation in module_data["mutations"]:
        mutation_name = mutation[0].upper() + mutation[1:] if mutation else ""
        # Use {operation} and {operationName} as placeholders - escape GraphQL braces properly
        module_lower = module_name.lower()
        mutation_template = f"mutation {{operation}}($input: Input!) {{ {module_lower} {{ {{operationName}}(input: $input) }} }}"
        request = create_request(
            mutation_name,
            "mutation",
            mutation_template,
            f"{module_name} {mutation} mutation"
        )
        folder["item"].append(request)
    
    return folder

def generate_collection():
    """Generate the complete Postman collection."""
    collection = {
        "info": {
            "_postman_id": "contact360-graphql-api-v1",
            "name": "Contact360 GraphQL API",
            "description": "Complete GraphQL API collection for Contact360 Appointment service. Includes all 25 modules with queries and mutations.\n\n**📚 For comprehensive module documentation**, see docs/GraphQL/README.md which includes detailed queries, mutations, validation rules, error handling, and implementation details for each module.\n\n**Setup Instructions:**\n1. Import this collection into Postman\n2. Create/import environment with baseUrl variable\n3. Use Auth > Login or Register to get access token\n4. Token will be automatically saved to environment\n5. All other requests will use the saved token",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "_exporter_id": "contact360"
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "accessToken",
                "value": "",
                "type": "string"
            },
            {
                "key": "refreshToken",
                "value": "",
                "type": "string"
            },
            {
                "key": "userId",
                "value": "",
                "type": "string"
            }
        ],
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{accessToken}}",
                    "type": "string"
                }
            ]
        }
    }
    
    # Add all modules
    for module_name, module_data in MODULES.items():
        folder = create_module_folder(module_name, module_data)
        collection["item"].append(folder)
    
    return collection

if __name__ == "__main__":
    collection = generate_collection()
    output_file = Path(__file__).parent / "Contact360_GraphQL_API.postman_collection.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"Generated Postman collection: {output_file}")
    print(f"Total modules: {len(MODULES)}")
    print(f"Total requests: {sum(len(m['queries']) + len(m['mutations']) for m in MODULES.values())}")
