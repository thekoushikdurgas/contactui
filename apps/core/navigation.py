"""Sidebar navigation configuration.

Navigation Structure:
- Groups: Top-level sections (DOCUMENTATION, ANALYSIS, etc.)
- Items: Navigation items within groups (can be dynamic or static pages)
- Children: Nested items under parent items (for static pages like forms)

Item Types:
- "dynamic": Data-driven pages (dashboards, lists, details)
- "static": Static structure pages (forms, confirmations)
- "info": Information/documentation pages

Access Patterns:
- "direct": Accessible directly from sidebar
- "via_detail": Accessed via detail page (edit/delete forms)
- "via_list": Accessed via list page (create forms)

Metadata Fields:
- page_type: Type of page (dynamic/static/info)
- parent: Reference to parent item (for nested items)
- redirect_target: Where form redirects after submit
- access_via: How to access this page
- badge: Optional badge text (e.g., "New")
"""

SIDEBAR_MENU = [
    {
        "label": "DOCUMENTATION",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />',
        "items": [
            {
                "label": "Documentation",
                "app_name": "documentation",
                "url_name": "dashboard",
                "page_type": "dynamic",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />'
            },
            {
                "label": "Pages",
                "app_name": "documentation",
                "url_name": "pages_list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />',
                "children": [
                    {
                        "label": "Create Page",
                        "app_name": "documentation",
                        "url_name": "page_create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "page_detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
            {
                "label": "Endpoints",
                "app_name": "documentation",
                "url_name": "endpoints_list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />',
                "children": [
                    {
                        "label": "Create Endpoint",
                        "app_name": "documentation",
                        "url_name": "endpoint_create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "endpoint_detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
            {
                "label": "Relationships",
                "app_name": "documentation",
                "url_name": "relationships_list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />',
                "children": [
                    {
                        "label": "Create Relationship",
                        "app_name": "documentation",
                        "url_name": "relationship_create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "relationship_detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
            {
                "label": "Knowledge Base", 
                "app_name": "knowledge", 
                "url_name": "list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />',
                "children": [
                    {
                        "label": "Create Knowledge Entry",
                        "app_name": "knowledge",
                        "url_name": "create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
            {
                "label": "API Documentation",
                "url": "/api/docs/",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />',
                "external": False
            },
        ]
    },
    {
        "label": "ANALYSIS",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />',
        "items": [
            {
                "label": "Codebase", 
                "app_name": "codebase", 
                "url_name": "dashboard",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />'
            },
            {
                "label": "Analytics", 
                "app_name": "analytics", 
                "url_name": "dashboard",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />'
            },
        ]
    },
    {
        "label": "AI",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />',
        "items": [
            {
                "label": "AI Assistant", 
                "app_name": "ai_agent", 
                "url_name": "chat",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />'
            },
            {
                "label": "Sessions", 
                "app_name": "ai_agent", 
                "url_name": "sessions",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />'
            },
        ]
    },
    {
        "label": "AUTOMATION",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />',
        "items": [
            {
                "label": "Workflows", 
                "app_name": "durgasflow", 
                "url_name": "workflow_list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" />',
                "children": [
                    {
                        "label": "Create Workflow",
                        "app_name": "durgasflow",
                        "url_name": "workflow_create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "workflow_detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    },
                    {
                        "label": "New Editor",
                        "app_name": "durgasflow",
                        "url_name": "editor_new",
                        "page_type": "static",
                        "access_via": "direct",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />'
                    }
                ]
            },
            {
                "label": "Executions", 
                "app_name": "durgasflow", 
                "url_name": "execution_list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />'
            },
            {
                "label": "Credentials", 
                "app_name": "durgasflow", 
                "url_name": "credential_list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />',
                "children": [
                    {
                        "label": "Create Credential",
                        "app_name": "durgasflow",
                        "url_name": "credential_create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "credential_detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
        ]
    },
    {
        "label": "MANAGEMENT",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />',
        "items": [
            {
                "label": "Tasks", 
                "app_name": "tasks", 
                "url_name": "list",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />',
                "children": [
                    {
                        "label": "Create Task",
                        "app_name": "tasks",
                        "url_name": "create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
            {
                "label": "Postman", 
                "app_name": "postman", 
                "url_name": "dashboard",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />',
                "children": [
                    {
                        "label": "Create Postman Config",
                        "app_name": "documentation",
                        "url_name": "postman_create",
                        "page_type": "static",
                        "access_via": "via_list",
                        "redirect_target": "postman_detail",
                        "badge": "New",
                        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />'
                    }
                ]
            },
        ]
    },
    {
        "label": "ADMIN",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />',
        "items": [
            {
                "label": "User Management",
                "app_name": "admin",
                "url_name": "users",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />'
            },
            {
                "label": "User History",
                "app_name": "admin",
                "url_name": "user_history",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />'
            },
            {
                "label": "Statistics",
                "app_name": "admin",
                "url_name": "statistics",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />'
            },
            {
                "label": "System Logs",
                "app_name": "admin",
                "url_name": "logs",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />'
            },
            {
                "label": "System Status",
                "app_name": "admin",
                "url_name": "system_status",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />'
            },
            {
                "label": "Admin Settings",
                "app_name": "admin",
                "url_name": "settings",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />'
            },
        ]
    },
    {
        "label": "TOOLS & INFO",
        "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />',
        "items": [
            {
                "label": "Architecture",
                "app_name": "architecture",
                "url_name": "blueprint",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />'
            },
            {
                "label": "Database Schema",
                "app_name": "database",
                "url_name": "schema",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />'
            },
            {
                "label": "Roadmap",
                "app_name": "roadmap",
                "url_name": "dashboard",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />'
            },
            {
                "label": "Accessibility",
                "app_name": "accessibility",
                "url_name": "dashboard",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />'
            },
            {
                "label": "Test Runner",
                "app_name": "test_runner",
                "url_name": "dashboard",
                "page_type": "dynamic",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
            },
            {
                "label": "Swagger UI",
                "url": "/api/swagger/",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />',
                "external": False
            },
            {
                "label": "ReDoc",
                "url": "/api/redoc/",
                "page_type": "info",
                "access_via": "direct",
                "icon": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />',
                "external": False
            },
        ]
    },
]
