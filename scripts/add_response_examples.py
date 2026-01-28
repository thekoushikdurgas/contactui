#!/usr/bin/env python3
"""
Add example responses to Postman collection for Contact360 GraphQL API.

This script reads the existing Postman collection and adds example response bodies
for each endpoint based on the GraphQL query/mutation structure.

> **📚 For comprehensive module documentation**, see docs/GraphQL/README.md which includes
> detailed queries, mutations, validation rules, error handling, and implementation details
> for all 22 modules.

Usage:
    python add_response_examples.py

The script will:
1. Load the existing Postman collection
2. Generate example responses for all endpoints across 22 modules
3. Add response arrays to each request (success + error examples)
4. Save the updated collection
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseExampleGenerator:
    """Generate example responses for Postman collection."""
    
    def __init__(self):
        """Initialize with example response templates."""
        self.base_uuid = "550e8400-e29b-41d4-a716-446655440000"
        self.base_timestamp = "2024-01-15T10:30:00Z"
        self.base_timestamp_iso = datetime.now().isoformat() + "Z"
        self.response_patterns = self._initialize_response_patterns()
    
    def _initialize_response_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize example responses based on endpoint patterns."""
        base_uuid = self.base_uuid
        base_timestamp = self.base_timestamp
        base_timestamp_iso = self.base_timestamp_iso
        
        return {
            # ========== AUTH MODULE ==========
            r"auth\s*\{\s*me\s*\{": {
                "data": {
                    "auth": {
                        "me": {
                            "uuid": base_uuid,
                            "email": "user@example.com",
                            "name": "John Doe",
                            "profile": {
                                "jobTitle": "Software Engineer",
                                "bio": "Full-stack developer with 5+ years of experience",
                                "role": "User",
                                "credits": 1000
                            }
                        }
                    }
                }
            },
            r"auth\s*\{\s*session\s*\{": {
                "data": {
                    "auth": {
                        "session": {
                            "userUuid": base_uuid,
                            "email": "user@example.com",
                            "isAuthenticated": True,
                            "lastSignInAt": base_timestamp
                        }
                    }
                }
            },
            r"auth\s*\{\s*login\s*\(": {
                "data": {
                    "auth": {
                        "login": {
                            "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDY5NzU4MDB9.signature",
                            "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDcwMDE4MDB9.signature",
                            "user": {
                                "uuid": base_uuid,
                                "email": "user@example.com",
                                "name": "John Doe"
                            }
                        }
                    }
                }
            },
            r"auth\s*\{\s*register\s*\(": {
                "data": {
                    "auth": {
                        "register": {
                            "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDY5NzU4MDB9.signature",
                            "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDcwMDE4MDB9.signature",
                            "user": {
                                "uuid": base_uuid,
                                "email": "user@example.com",
                                "name": "John Doe"
                            }
                        }
                    }
                }
            },
            r"auth\s*\{\s*logout": {
                "data": {
                    "auth": {
                        "logout": True
                    }
                }
            },
            r"auth\s*\{\s*refreshToken\s*\(": {
                "data": {
                    "auth": {
                        "refreshToken": {
                            "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDY5NzU4MDB9.signature",
                            "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDcwMDE4MDB9.signature"
                        }
                    }
                }
            },
            
            # ========== USERS MODULE ==========
            r"users\s*\{\s*user\s*\(uuid": {
                "data": {
                    "users": {
                        "user": {
                            "uuid": base_uuid,
                            "email": "user@example.com",
                            "name": "John Doe",
                            "isActive": True,
                            "profile": {
                                "jobTitle": "Software Engineer",
                                "bio": "Full-stack developer",
                                "role": "User",
                                "credits": 1000,
                                "subscriptionPlan": "pro"
                            }
                        }
                    }
                }
            },
            r"users\s*\{\s*users\s*\(": {
                "data": {
                    "users": {
                        "users": [
                            {
                                "uuid": base_uuid,
                                "email": "user1@example.com",
                                "name": "John Doe",
                                "isActive": True,
                                "createdAt": base_timestamp
                            },
                            {
                                "uuid": "660e8400-e29b-41d4-a716-446655440001",
                                "email": "user2@example.com",
                                "name": "Jane Smith",
                                "isActive": True,
                                "createdAt": base_timestamp
                            }
                        ]
                    }
                }
            },
            r"users\s*\{\s*userStats": {
                "data": {
                    "users": {
                        "userStats": {
                            "totalUsers": 150,
                            "activeUsers": 120,
                            "inactiveUsers": 30,
                            "usersByRole": [
                                {"role": "User", "count": 140},
                                {"role": "Admin", "count": 8},
                                {"role": "SuperAdmin", "count": 2}
                            ],
                            "usersBySubscription": [
                                {"subscriptionPlan": "free", "count": 50},
                                {"subscriptionPlan": "pro", "count": 80},
                                {"subscriptionPlan": "enterprise", "count": 20}
                            ]
                        }
                    }
                }
            },
            r"users\s*\{\s*updateProfile": {
                "data": {
                    "users": {
                        "updateProfile": {
                            "userId": base_uuid,
                            "jobTitle": "Software Engineer",
                            "bio": "Developer",
                            "timezone": "America/New_York"
                        }
                    }
                }
            },
            r"users\s*\{\s*uploadAvatar": {
                "data": {
                    "users": {
                        "uploadAvatar": {
                            "userId": "123e4567-e89b-12d3-a456-426614174000",
                            "avatarUrl": "https://s3.amazonaws.com/bucket/avatars/123e4567-e89b-12d3-a456-426614174000/123e4567-e89b-12d3-a456-426614174000.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
                            "jobTitle": None,
                            "bio": None,
                            "timezone": None,
                            "role": "Member",
                            "credits": 100,
                            "subscriptionPlan": "free",
                            "subscriptionStatus": "active",
                            "createdAt": "2024-01-15T10:30:00Z",
                            "updatedAt": "2024-01-15T10:35:00Z"
                        }
                    }
                }
            },
            
            # ========== HEALTH MODULE ==========
            r"health\s*\{\s*apiMetadata": {
                "data": {
                    "health": {
                        "apiMetadata": {
                            "name": "Contact360 GraphQL API",
                            "version": "1.0.0",
                            "docs": "https://api.contact360.io/docs"
                        }
                    }
                }
            },
            r"health\s*\{\s*apiHealth": {
                "data": {
                    "health": {
                        "apiHealth": {
                            "status": "healthy",
                            "environment": "production"
                        }
                    }
                }
            },
            r"health\s*\{\s*vqlHealth": {
                "data": {
                    "health": {
                        "vqlHealth": {
                            "connectraEnabled": True,
                            "connectraStatus": "connected",
                            "connectraBaseUrl": "https://api.connectra.io"
                        }
                    }
                }
            },
            r"health\s*\{\s*performanceStats": {
                "data": {
                    "health": {
                        "performanceStats": {
                            "cache": {
                                "enabled": True,
                                "hits": 1250,
                                "misses": 350,
                                "hitRate": 0.78125
                            },
                            "database": {
                                "status": "healthy",
                                "poolSize": 10,
                                "activeConnections": 3
                            }
                        }
                    }
                }
            },
            
            # ========== CONTACTS MODULE ==========
            r"contacts\s*\{\s*contact\s*\(uuid": {
                "data": {
                    "contacts": {
                        "contact": {
                            "uuid": "770e8400-e29b-41d4-a716-446655440000",
                            "firstName": "John",
                            "lastName": "Doe",
                            "email": "john.doe@example.com",
                            "title": "VP of Engineering",
                            "companyUuid": "880e8400-e29b-41d4-a716-446655440000",
                            "linkedinUrl": "https://linkedin.com/in/johndoe",
                            "city": "San Francisco",
                            "country": "United States",
                            "company": {
                                "uuid": "880e8400-e29b-41d4-a716-446655440000",
                                "name": "Acme Corporation",
                                "employeesCount": 500,
                                "industries": ["Technology", "Software"],
                                "address": "123 Main St, San Francisco, CA",
                                "annualRevenue": 10000000,
                                "website": "https://acme.com",
                                "linkedinUrl": "https://linkedin.com/company/acme",
                                "phoneNumber": "+1-555-123-4567",
                                "city": "San Francisco",
                                "state": "California",
                                "country": "United States"
                            }
                        }
                    }
                }
            },
            r"contacts\s*\{\s*contacts\s*\(": {
                "data": {
                    "contacts": {
                        "contacts": {
                            "items": [
                                {
                                    "uuid": "770e8400-e29b-41d4-a716-446655440000",
                                    "firstName": "John",
                                    "lastName": "Doe",
                                    "email": "john.doe@example.com",
                                    "title": "VP of Engineering"
                                },
                                {
                                    "uuid": "770e8400-e29b-41d4-a716-446655440001",
                                    "firstName": "Jane",
                                    "lastName": "Smith",
                                    "email": "jane.smith@example.com",
                                    "title": "Director of Sales"
                                }
                            ],
                            "total": 150,
                            "limit": 50,
                            "offset": 0
                        }
                    }
                }
            },
            r"contacts\s*\{\s*contactCount": {
                "data": {
                    "contacts": {
                        "contactCount": 1250
                    }
                }
            },
            r"contacts\s*\{\s*contactQuery": {
                "data": {
                    "contacts": {
                        "contactQuery": {
                            "items": [
                                {
                                    "uuid": "770e8400-e29b-41d4-a716-446655440000",
                                    "firstName": "John",
                                    "lastName": "Doe",
                                    "email": "john.doe@example.com"
                                }
                            ],
                            "total": 45
                        }
                    }
                }
            },
            
            # ========== COMPANIES MODULE ==========
            r"companies\s*\{\s*company\s*\(uuid": {
                "data": {
                    "companies": {
                        "company": {
                            "uuid": "880e8400-e29b-41d4-a716-446655440000",
                            "name": "Acme Corporation",
                            "employeesCount": 500,
                            "industries": ["Technology", "Software"],
                            "keywords": ["AI", "ML", "Enterprise"],
                            "address": "123 Tech Street, San Francisco, CA 94105",
                            "linkedinUrl": "https://linkedin.com/company/acme",
                            "website": "https://acme.com",
                            "city": "San Francisco",
                            "country": "United States"
                        }
                    }
                }
            },
            r"companies\s*\{\s*companies\s*\(": {
                "data": {
                    "companies": {
                        "companies": {
                            "items": [
                                {
                                    "uuid": "880e8400-e29b-41d4-a716-446655440000",
                                    "name": "Acme Corporation",
                                    "employeesCount": 500,
                                    "industries": ["Technology"]
                                },
                                {
                                    "uuid": "880e8400-e29b-41d4-a716-446655440001",
                                    "name": "Tech Innovations Inc",
                                    "employeesCount": 250,
                                    "industries": ["Software"]
                                }
                            ],
                            "total": 75,
                            "limit": 50,
                            "offset": 0
                        }
                    }
                }
            },
            r"companies\s*\{\s*companyQuery": {
                "data": {
                    "companies": {
                        "companyQuery": {
                            "items": [
                                {
                                    "uuid": "880e8400-e29b-41d4-a716-446655440000",
                                    "name": "Acme Corporation",
                                    "employeesCount": 500
                                }
                            ],
                            "total": 25
                        }
                    }
                }
            },
            r"companies\s*\{\s*companyContacts": {
                "data": {
                    "companies": {
                        "companyContacts": {
                            "items": [
                                {
                                    "uuid": "770e8400-e29b-41d4-a716-446655440000",
                                    "firstName": "John",
                                    "lastName": "Doe",
                                    "email": "john.doe@example.com",
                                    "title": "VP of Engineering"
                                }
                            ],
                            "total": 15
                        }
                    }
                }
            },
            
            # ========== NOTIFICATIONS MODULE ==========
            r"notifications\s*\{\s*notifications\s*\(": {
                "data": {
                    "notifications": {
                        "notifications": {
                            "items": [
                                {
                                    "id": "990e8400-e29b-41d4-a716-446655440000",
                                    "title": "New Contact Added",
                                    "message": "John Doe has been added to your contacts",
                                    "type": "info",
                                    "priority": "normal",
                                    "read": False,
                                    "createdAt": base_timestamp
                                },
                                {
                                    "id": "990e8400-e29b-41d4-a716-446655440001",
                                    "title": "Export Complete",
                                    "message": "Your export is ready for download",
                                    "type": "success",
                                    "priority": "high",
                                    "read": False,
                                    "createdAt": base_timestamp
                                }
                            ],
                            "total": 10
                        }
                    }
                }
            },
            r"notifications\s*\{\s*notification\s*\(notificationId": {
                "data": {
                    "notifications": {
                        "notification": {
                            "id": "990e8400-e29b-41d4-a716-446655440000",
                            "title": "New Contact Added",
                            "message": "John Doe has been added to your contacts",
                            "type": "info",
                            "priority": "normal",
                            "read": False,
                            "createdAt": base_timestamp
                        }
                    }
                }
            },
            r"notifications\s*\{\s*unreadCount": {
                "data": {
                    "notifications": {
                        "unreadCount": {
                            "count": 5
                        }
                    }
                }
            },
            r"notifications\s*\{\s*notificationPreferences": {
                "data": {
                    "notifications": {
                        "notificationPreferences": {
                            "emailEnabled": True,
                            "pushEnabled": True
                        }
                    }
                }
            },
            r"notifications\s*\{\s*markNotificationAsRead": {
                "data": {
                    "notifications": {
                        "markNotificationAsRead": {
                            "id": "990e8400-e29b-41d4-a716-446655440000",
                            "read": True
                        }
                    }
                }
            },
            r"notifications\s*\{\s*markAllNotificationsAsRead": {
                "data": {
                    "notifications": {
                        "markAllNotificationsAsRead": {
                            "count": 5
                        }
                    }
                }
            },
            r"notifications\s*\{\s*deleteNotification": {
                "data": {
                    "notifications": {
                        "deleteNotification": True
                    }
                }
            },
            
            # ========== EXPORTS MODULE ==========
            r"exports\s*\{\s*export\s*\(exportId": {
                "data": {
                    "exports": {
                        "export": {
                            "exportId": "aa0e8400-e29b-41d4-a716-446655440000",
                            "downloadUrl": "https://s3.amazonaws.com/bucket/exports/export.csv",
                            "expiresAt": base_timestamp,
                            "status": "completed",
                            "contactCount": 100,
                            "companyCount": 25
                        }
                    }
                }
            },
            r"exports\s*\{\s*exports\s*\(": {
                "data": {
                    "exports": {
                        "exports": {
                            "items": [
                                {
                                    "exportId": "aa0e8400-e29b-41d4-a716-446655440000",
                                    "status": "completed",
                                    "createdAt": base_timestamp,
                                    "contactCount": 100
                                },
                                {
                                    "exportId": "aa0e8400-e29b-41d4-a716-446655440001",
                                    "status": "processing",
                                    "createdAt": base_timestamp,
                                    "contactCount": 50
                                }
                            ],
                            "total": 15
                        }
                    }
                }
            },
            r"exports\s*\{\s*exportStatus": {
                "data": {
                    "exports": {
                        "exportStatus": {
                            "status": "processing",
                            "progressPercentage": 65,
                            "downloadUrl": None
                        }
                    }
                }
            },
            r"exports\s*\{\s*createContactExport": {
                "data": {
                    "exports": {
                        "createContactExport": {
                            "exportId": "aa0e8400-e29b-41d4-a716-446655440000",
                            "downloadUrl": None,
                            "status": "processing"
                        }
                    }
                }
            },
            r"exports\s*\{\s*createCompanyExport": {
                "data": {
                    "exports": {
                        "createCompanyExport": {
                            "exportId": "aa0e8400-e29b-41d4-a716-446655440001",
                            "downloadUrl": None,
                            "status": "processing"
                        }
                    }
                }
            },
            
            # ========== S3 MODULE ==========
            r"s3\s*\{\s*s3Files\s*\(": {
                "data": {
                    "s3": {
                        "s3Files": {
                            "files": [
                                {
                                    "key": "exports/export-2024-01-15.csv",
                                    "filename": "export-2024-01-15.csv",
                                    "size": 1024000,
                                    "lastModified": base_timestamp
                                },
                                {
                                    "key": "exports/export-2024-01-14.csv",
                                    "filename": "export-2024-01-14.csv",
                                    "size": 2048000,
                                    "lastModified": base_timestamp
                                }
                            ],
                            "total": 25
                        }
                    }
                }
            },
            r"s3\s*\{\s*s3FileData": {
                "data": {
                    "s3": {
                        "s3FileData": {
                            "rows": [
                                {"data": {"column1": "value1", "column2": "value2"}},
                                {"data": {"column1": "value3", "column2": "value4"}}
                            ],
                            "total": 100,
                            "limit": 100,
                            "offset": 0
                        }
                    }
                }
            },
            r"s3\s*\{\s*s3FileInfo": {
                "data": {
                    "s3": {
                        "s3FileInfo": {
                            "key": "exports/export-2024-01-15.csv",
                            "filename": "export-2024-01-15.csv",
                            "size": 1024000,
                            "lastModified": base_timestamp,
                            "contentType": "text/csv"
                        }
                    }
                }
            },
            
            # ========== EMAIL MODULE ==========
            r"email\s*\{\s*findEmails": {
                "data": {
                    "email": {
                        "findEmails": {
                            "emails": [
                                {"uuid": base_uuid, "email": "john.doe@example.com"},
                                {"uuid": "bb0e8400-e29b-41d4-a716-446655440000", "email": "j.doe@example.com"}
                            ],
                            "total": 2
                        }
                    }
                }
            },
            r"email\s*\{\s*findSingleEmail": {
                "data": {
                    "email": {
                        "findSingleEmail": {
                            "email": "john.doe@example.com",
                            "source": "api"
                        }
                    }
                }
            },
            r"email\s*\{\s*verifySingle": {
                "data": {
                    "email": {
                        "verifySingle": {
                            "email": "john.doe@example.com",
                            "status": "valid",
                            "score": 95,
                            "reason": "Email exists and is deliverable"
                        }
                    }
                }
            },
            r"email\s*\{\s*verifyBulk": {
                "data": {
                    "email": {
                        "verifyBulk": {
                            "results": [
                                {"email": "john.doe@example.com", "status": "valid", "score": 95},
                                {"email": "invalid@example.com", "status": "invalid", "score": 10}
                            ],
                            "total": 2,
                            "validCount": 1,
                            "invalidCount": 1
                        }
                    }
                }
            },
            
            # ========== BILLING MODULE ==========
            r"billing\s*\{\s*billing": {
                "data": {
                    "billing": {
                        "billing": {
                            "credits": 1000,
                            "creditsUsed": 250,
                            "creditsLimit": 5000,
                            "subscriptionPlan": "pro",
                            "subscriptionStatus": "active",
                            "usagePercentage": 5.0
                        }
                    }
                }
            },
            r"billing\s*\{\s*plans": {
                "data": {
                    "billing": {
                        "plans": [
                            {
                                "tier": "free",
                                "name": "Free Plan",
                                "category": "basic",
                                "periods": {
                                    "monthly": {"price": 0, "credits": 100},
                                    "yearly": {"price": 0, "credits": 1200, "savings": {"percentage": 0}}
                                }
                            },
                            {
                                "tier": "pro",
                                "name": "Pro Plan",
                                "category": "professional",
                                "periods": {
                                    "monthly": {"price": 99, "credits": 5000},
                                    "yearly": {"price": 990, "credits": 60000, "savings": {"percentage": 17}}
                                }
                            }
                        ]
                    }
                }
            },
            r"billing\s*\{\s*addons": {
                "data": {
                    "billing": {
                        "addons": [
                            {"id": "addon_1000_credits", "name": "1000 Credits", "credits": 1000, "price": 29},
                            {"id": "addon_5000_credits", "name": "5000 Credits", "credits": 5000, "price": 99}
                        ]
                    }
                }
            },
            r"billing\s*\{\s*invoices\s*\(": {
                "data": {
                    "billing": {
                        "invoices": {
                            "items": [
                                {
                                    "id": "inv_001",
                                    "amount": 99.00,
                                    "status": "paid",
                                    "createdAt": base_timestamp
                                },
                                {
                                    "id": "inv_002",
                                    "amount": 99.00,
                                    "status": "pending",
                                    "createdAt": base_timestamp
                                }
                            ],
                            "total": 10
                        }
                    }
                }
            },
            r"billing\s*\{\s*subscribe": {
                "data": {
                    "billing": {
                        "subscribe": {
                            "message": "Subscription activated successfully",
                            "subscriptionPlan": "pro",
                            "credits": 5000
                        }
                    }
                }
            },
            r"billing\s*\{\s*purchaseAddon": {
                "data": {
                    "billing": {
                        "purchaseAddon": {
                            "message": "Addon purchased successfully",
                            "creditsAdded": 1000,
                            "totalCredits": 6000
                        }
                    }
                }
            },
            r"billing\s*\{\s*cancelSubscription": {
                "data": {
                    "billing": {
                        "cancelSubscription": {
                            "message": "Subscription cancelled successfully",
                            "subscriptionStatus": "cancelled"
                        }
                    }
                }
            },
            
            # ========== USAGE MODULE ==========
            r"usage\s*\{\s*usage\s*\(": {
                "data": {
                    "usage": {
                        "usage": {
                            "features": [
                                {
                                    "feature": "EMAIL_FINDER",
                                    "used": 250,
                                    "limit": 5000,
                                    "remaining": 4750,
                                    "resetAt": base_timestamp
                                }
                            ]
                        }
                    }
                }
            },
            r"usage\s*\{\s*trackUsage": {
                "data": {
                    "usage": {
                        "trackUsage": {
                            "feature": "EMAIL_FINDER",
                            "used": 251,
                            "limit": 5000,
                            "success": True
                        }
                    }
                }
            },
            r"usage\s*\{\s*resetUsage": {
                "data": {
                    "usage": {
                        "resetUsage": {
                            "feature": "EMAIL_FINDER",
                            "used": 0,
                            "limit": 5000,
                            "success": True
                        }
                    }
                }
            },
            
            # ========== ACTIVITIES MODULE ==========
            r"activities\s*\{\s*activities\s*\(": {
                "data": {
                    "activities": {
                        "activities": {
                            "items": [
                                {
                                    "id": 1,
                                    "userId": "aa0e8400-e29b-41d4-a716-446655440000",
                                    "serviceType": "ai_chats",
                                    "actionType": "create",
                                    "status": "success",
                                    "resultCount": 1,
                                    "createdAt": base_timestamp
                                },
                                {
                                    "id": 2,
                                    "userId": "aa0e8400-e29b-41d4-a716-446655440000",
                                    "serviceType": "contacts",
                                    "actionType": "query",
                                    "status": "success",
                                    "resultCount": 25,
                                    "createdAt": base_timestamp
                                }
                            ],
                            "total": 150,
                            "limit": 50,
                            "offset": 0,
                            "hasNext": True,
                            "hasPrevious": False
                        }
                    }
                }
            },
            r"activities\s*\{\s*activityStats": {
                "data": {
                    "activities": {
                        "activityStats": {
                            "totalActivities": 150,
                            "byServiceType": {
                                "jobs": 20,
                                "imports": 15,
                                "contacts": 45,
                                "companies": 30,
                                "email": 25,
                                "ai_chats": 35,
                                "linkedin": 40,
                                "sales_navigator": 10
                            },
                            "byActionType": {
                                "create": 50,
                                "update": 30,
                                "delete": 5,
                                "query": 80,
                                "search": 45,
                                "export": 25,
                                "import": 15,
                                "send": 20,
                                "verify": 15,
                                "analyze": 10,
                                "generate": 8,
                                "parse": 12,
                                "scrape": 5
                            },
                            "byStatus": {
                                "success": 140,
                                "failed": 10
                            },
                            "recentActivities": 5
                        }
                    }
                }
            },
            
            # ========== AI CHATS MODULE ==========
            r"aiChats\s*\{\s*aiChats\s*\(": {
                "data": {
                    "aiChats": {
                        "aiChats": {
                            "items": [
                                {
                                    "uuid": "cc0e8400-e29b-41d4-a716-446655440000",
                                    "title": "Find VPs in Tech",
                                    "createdAt": base_timestamp
                                },
                                {
                                    "uuid": "cc0e8400-e29b-41d4-a716-446655440001",
                                    "title": "Sales Leads",
                                    "createdAt": base_timestamp
                                }
                            ],
                            "pageInfo": {
                                "total": 10
                            }
                        }
                    }
                }
            },
            r"aiChats\s*\{\s*aiChat\s*\(chatId": {
                "data": {
                    "aiChats": {
                        "aiChat": {
                            "uuid": "cc0e8400-e29b-41d4-a716-446655440000",
                            "title": "Find VPs in Tech",
                            "messages": [
                                {
                                    "sender": "user",
                                    "text": "Find VPs at tech companies",
                                    "contacts": [
                                        {
                                            "firstName": "John",
                                            "lastName": "Doe",
                                            "email": "john.doe@example.com"
                                        }
                                    ]
                                },
                                {
                                    "sender": "assistant",
                                    "text": "I found 5 VPs at tech companies",
                                    "contacts": []
                                }
                            ]
                        }
                    }
                }
            },
            r"aiChats\s*\{\s*createAIChat": {
                "data": {
                    "aiChats": {
                        "createAIChat": {
                            "uuid": "cc0e8400-e29b-41d4-a716-446655440000",
                            "title": "New Chat",
                            "messages": [
                                {"sender": "assistant", "text": "Hello! How can I help you find contacts today?"}
                            ]
                        }
                    }
                }
            },
            r"aiChats\s*\{\s*sendMessage": {
                "data": {
                    "aiChats": {
                        "sendMessage": {
                            "uuid": "cc0e8400-e29b-41d4-a716-446655440000",
                            "messages": [
                                {
                                    "sender": "user",
                                    "text": "Find VPs at tech companies",
                                    "contacts": []
                                },
                                {
                                    "sender": "assistant",
                                    "text": "I found 5 VPs. Here are the results:",
                                    "contacts": [
                                        {
                                            "firstName": "John",
                                            "lastName": "Doe"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            },
            
            # ========== AI CHATS MODULE - GEMINI OPERATIONS ==========
            r"aiChats\s*\{\s*analyzeEmailRisk": {
                "data": {
                    "aiChats": {
                        "analyzeEmailRisk": {
                            "riskScore": 25,
                            "analysis": "Low risk email. Appears to be a personal email address.",
                            "isRoleBased": False,
                            "isDisposable": False
                        }
                    }
                }
            },
            r"aiChats\s*\{\s*generateCompanySummary": {
                "data": {
                    "aiChats": {
                        "generateCompanySummary": {
                            "summary": "Acme Corporation is a leading technology company specializing in AI and machine learning solutions for enterprises. Founded in 2015, the company has grown to 500 employees and serves Fortune 500 companies worldwide."
                        }
                    }
                }
            },
            r"aiChats\s*\{\s*parseContactFilters": {
                "data": {
                    "aiChats": {
                        "parseContactFilters": {
                            "jobTitles": ["VP", "Vice President"],
                            "companyNames": ["tech companies", "technology companies"],
                            "industry": "Technology",
                            "location": "San Francisco",
                            "employees": None,
                            "seniority": "executive"
                        }
                    }
                }
            },
            
            # ========== ANALYTICS MODULE ==========
            r"analytics\s*\{\s*performanceMetrics": {
                "data": {
                    "analytics": {
                        "performanceMetrics": [
                            {
                                "id": "dd0e8400-e29b-41d4-a716-446655440000",
                                "metricName": "LCP",
                                "metricValue": 2.5,
                                "timestamp": base_timestamp,
                                "metadata": {"page": "/dashboard"}
                            },
                            {
                                "id": "dd0e8400-e29b-41d4-a716-446655440001",
                                "metricName": "FID",
                                "metricValue": 0.1,
                                "timestamp": base_timestamp,
                                "metadata": {"page": "/contacts"}
                            }
                        ]
                    }
                }
            },
            r"analytics\s*\{\s*aggregateMetrics": {
                "data": {
                    "analytics": {
                        "aggregateMetrics": {
                            "avg": 2.3,
                            "min": 1.5,
                            "max": 5.2,
                            "p50": 2.1,
                            "p75": 3.0,
                            "p95": 4.5,
                            "count": 1000
                        }
                    }
                }
            },
            r"analytics\s*\{\s*submitPerformanceMetric": {
                "data": {
                    "analytics": {
                        "submitPerformanceMetric": {
                            "success": True,
                            "message": "Metric recorded successfully"
                        }
                    }
                }
            },
            
            # ========== LINKEDIN MODULE ==========
            r"linkedin\s*\{\s*search": {
                "data": {
                    "linkedin": {
                        "search": {
                            "contacts": [
                                {
                                    "contact": {
                                        "uuid": base_uuid,
                                        "firstName": "John",
                                        "lastName": "Doe",
                                        "email": "john.doe@example.com"
                                    }
                                }
                            ],
                            "totalContacts": 1
                        }
                    }
                }
            },
            r"linkedin\s*\{\s*exportLinkedInResults": {
                "data": {
                    "linkedin": {
                        "exportLinkedInResults": {
                            "exportId": "aa0e8400-e29b-41d4-a716-446655440000",
                            "downloadUrl": "https://s3.amazonaws.com/bucket/exports/linkedin-export.csv",
                            "contactCount": 50,
                            "companyCount": 10
                        }
                    }
                }
            },
            
            # ========== SALES NAVIGATOR MODULE ==========
            r"salesNavigator\s*\{\s*salesNavigatorRecords": {
                "data": {
                    "salesNavigator": {
                        "salesNavigatorRecords": {
                            "items": [
                                {
                                    "id": "ee0e8400-e29b-41d4-a716-446655440000",
                                    "timestamp": base_timestamp,
                                    "version": "1.0",
                                    "source": "linkedin_sales_navigator"
                                }
                            ],
                            "pageInfo": {
                                "total": 5
                            }
                        }
                    }
                }
            },
            r"salesNavigator\s*\{\s*saveSalesNavigatorProfiles": {
                "data": {
                    "salesNavigator": {
                        "saveSalesNavigatorProfiles": {
                            "success": True,
                            "totalProfiles": 1,
                            "savedCount": 1,
                            "errors": []
                        }
                    }
                }
            },
            
            # ========== ADMIN MODULE ==========
            r"admin\s*\{\s*users\s*\(filters": {
                "data": {
                    "admin": {
                        "users": {
                            "items": [
                                {
                                    "uuid": base_uuid,
                                    "email": "user@example.com",
                                    "name": "John Doe",
                                    "profile": {
                                        "role": "User",
                                        "credits": 1000
                                    }
                                }
                            ],
                            "pageInfo": {
                                "total": 150
                            }
                        }
                    }
                }
            },
            r"admin\s*\{\s*userStats": {
                "data": {
                    "admin": {
                        "userStats": {
                            "totalUsers": 150,
                            "activeUsers": 120,
                            "usersByRole": [
                                {"role": "User", "count": 140},
                                {"role": "Admin", "count": 8}
                            ],
                            "usersByPlan": [
                                {"plan": "free", "count": 50},
                                {"plan": "pro", "count": 80}
                            ]
                        }
                    }
                }
            },
            r"admin\s*\{\s*searchLogs": {
                "data": {
                    "admin": {
                        "searchLogs": {
                            "items": [
                                {
                                    "id": "ff0e8400-e29b-41d4-a716-446655440000",
                                    "timestamp": base_timestamp,
                                    "level": "ERROR",
                                    "message": "Database connection timeout"
                                }
                            ],
                            "pageInfo": {
                                "total": 50
                            }
                        }
                    }
                }
            },
            r"admin\s*\{\s*updateUserRole": {
                "data": {
                    "admin": {
                        "updateUserRole": {
                            "uuid": base_uuid,
                            "profile": {
                                "role": "Admin"
                            }
                        }
                    }
                }
            },
            r"admin\s*\{\s*updateUserCredits": {
                "data": {
                    "admin": {
                        "updateUserCredits": {
                            "uuid": base_uuid,
                            "profile": {
                                "credits": 5000
                            }
                        }
                    }
                }
            },
            
            # ========== DASHBOARD PAGES MODULE ==========
            r"dashboardPages\s*\{\s*dashboardPage\s*\(pageId": {
                "data": {
                    "dashboardPages": {
                        "dashboardPage": {
                            "pageId": "dashboard-home",
                            "metadata": {
                                "title": "Home Dashboard",
                                "description": "Main dashboard page",
                                "route": "/dashboard"
                            },
                            "accessControl": {
                                "allowedRoles": ["User", "Admin"],
                                "restrictionType": "role_based"
                            }
                        }
                    }
                }
            },
            r"dashboardPages\s*\{\s*dashboardPages": {
                "data": {
                    "dashboardPages": {
                        "dashboardPages": {
                            "pages": [
                                {
                                    "pageId": "dashboard-home",
                                    "metadata": {
                                        "title": "Home",
                                        "description": "Main dashboard"
                                    }
                                },
                                {
                                    "pageId": "dashboard-contacts",
                                    "metadata": {
                                        "title": "Contacts",
                                        "description": "Contacts dashboard"
                                    }
                                }
                            ],
                            "total": 5
                        }
                    }
                }
            },
            r"dashboardPages\s*\{\s*createDashboardPage": {
                "data": {
                    "dashboardPages": {
                        "createDashboardPage": {
                            "pageId": "dashboard-home",
                            "metadata": {
                                "title": "Home"
                            }
                        }
                    }
                }
            },
            
            # ========== DOCUMENTATION MODULE ==========
            r"documentation\s*\{\s*documentationPage\s*\(pageId": {
                "data": {
                    "documentation": {
                        "documentationPage": {
                            "pageId": "getting-started",
                            "title": "Getting Started",
                            "description": "Introduction to Contact360 API",
                            "contentUrl": "https://docs.contact360.io/getting-started",
                            "lastUpdated": base_timestamp
                        }
                    }
                }
            },
            r"documentation\s*\{\s*documentationPages": {
                "data": {
                    "documentation": {
                        "documentationPages": {
                            "pages": [
                                {
                                    "pageId": "getting-started",
                                    "title": "Getting Started",
                                    "description": "Introduction guide"
                                },
                                {
                                    "pageId": "api-reference",
                                    "title": "API Reference",
                                    "description": "Complete API documentation"
                                }
                            ],
                            "total": 20
                        }
                    }
                }
            },
            r"documentation\s*\{\s*documentationPageContent": {
                "data": {
                    "documentation": {
                        "documentationPageContent": {
                            "pageId": "getting-started",
                            "content": "# Getting Started\n\nWelcome to Contact360 API..."
                        }
                    }
                }
            },
            
            # ========== MARKETING MODULE ==========
            r"marketing\s*\{\s*marketingPage\s*\(pageId": {
                "data": {
                    "marketing": {
                        "marketingPage": {
                            "pageId": "pricing",
                            "metadata": {
                                "title": "Pricing",
                                "description": "Our pricing plans",
                                "status": "published"
                            },
                            "hero": {
                                "title": "Simple, Transparent Pricing",
                                "subtitle": "Choose the plan that's right for you",
                                "description": "All plans include access to our core features"
                            }
                        }
                    }
                }
            },
            r"marketing\s*\{\s*marketingPages": {
                "data": {
                    "marketing": {
                        "marketingPages": {
                            "pages": [
                                {
                                    "pageId": "pricing",
                                    "metadata": {
                                        "title": "Pricing",
                                        "status": "published"
                                    }
                                },
                                {
                                    "pageId": "features",
                                    "metadata": {
                                        "title": "Features",
                                        "status": "published"
                                    }
                                }
                            ],
                            "total": 10
                        }
                    }
                }
            },
            
            # ========== UPLOAD MODULE ==========
            r"upload\s*\{\s*uploadStatus": {
                "data": {
                    "upload": {
                        "uploadStatus": {
                            "uploadId": "gg0e8400-e29b-41d4-a716-446655440000",
                            "status": "in_progress",
                            "partsUploaded": 3,
                            "totalParts": 5
                        }
                    }
                }
            },
            r"upload\s*\{\s*presignedUrl": {
                "data": {
                    "upload": {
                        "presignedUrl": {
                            "url": "https://s3.amazonaws.com/bucket/uploads/file.zip?signature=...",
                            "partNumber": 1,
                            "expiresAt": base_timestamp
                        }
                    }
                }
            },
            r"upload\s*\{\s*initiateUpload": {
                "data": {
                    "upload": {
                        "initiateUpload": {
                            "uploadId": "gg0e8400-e29b-41d4-a716-446655440000",
                            "fileKey": "uploads/large-file.zip",
                            "totalParts": 5,
                            "partSize": 5242880
                        }
                    }
                }
            },
            r"upload\s*\{\s*completeUpload": {
                "data": {
                    "upload": {
                        "completeUpload": {
                            "uploadId": "gg0e8400-e29b-41d4-a716-446655440000",
                            "fileKey": "uploads/large-file.zip",
                            "fileUrl": "https://s3.amazonaws.com/bucket/uploads/large-file.zip"
                        }
                    }
                }
            },
        }
    
    def generate_for_request(self, request_item: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Generate example responses for a request, including success and error examples."""
        request_body = request_item.get("request", {}).get("body", {}).get("raw", "")
        
        if not request_body:
            return None
        
        try:
            body_data = json.loads(request_body)
            query = body_data.get("query", "").strip()
            
            responses = []
            
            # Generate success response
            success_data = None
            for pattern, example_data in self.response_patterns.items():
                if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
                    success_data = example_data
                    break
            
            if success_data:
                responses.append(self._create_postman_response(200, "Success", success_data))
            else:
                # Generate generic GraphQL response if no pattern matches
                responses.append(self._create_postman_response(200, "Success", {
                    "data": {},
                    "errors": []
                }))
            
            # Generate error response examples
            error_responses = self._generate_error_responses(query)
            responses.extend(error_responses)
            
            return responses
            
        except json.JSONDecodeError:
            return None
    
    def _generate_error_responses(self, query: str) -> List[Dict[str, Any]]:
        """Generate error response examples based on query type."""
        error_responses = []
        
        # Determine query type and generate appropriate errors
        is_mutation = "mutation" in query.lower()
        is_auth = "auth" in query.lower() or "login" in query.lower() or "register" in query.lower()
        has_uuid = "uuid" in query.lower()
        
        # 401 Unauthorized - for auth-related queries
        if not is_auth:
            error_responses.append(self._create_postman_response(401, "Unauthorized", {
                "errors": [{
                    "message": "Authentication required",
                    "extensions": {
                        "code": "UNAUTHORIZED",
                        "statusCode": 401
                    }
                }]
            }))
        
        # 422 Validation Error - common for all queries/mutations
        error_responses.append(self._create_postman_response(422, "Validation Error", {
            "errors": [{
                "message": "Invalid input",
                "extensions": {
                    "code": "VALIDATION_ERROR",
                    "statusCode": 422,
                    "fieldErrors": {
                        "email": ["Email must be a valid email address format"],
                        "password": ["Password must be at least 8 characters"]
                    }
                }
            }]
        }))
        
        # 404 Not Found - for queries with UUIDs
        if has_uuid:
            error_responses.append(self._create_postman_response(404, "Not Found", {
                "errors": [{
                    "message": "Resource with identifier '123e4567-e89b-12d3-a456-426614174000' not found",
                    "extensions": {
                        "code": "NOT_FOUND",
                        "statusCode": 404,
                        "resourceType": "Resource",
                        "identifier": "123e4567-e89b-12d3-a456-426614174000"
                    }
                }]
            }))
        
        # 403 Forbidden - for mutations and admin operations
        if is_mutation or "admin" in query.lower() or "delete" in query.lower() or "update" in query.lower():
            error_responses.append(self._create_postman_response(403, "Forbidden", {
                "errors": [{
                    "message": "You do not have permission to perform this action",
                    "extensions": {
                        "code": "FORBIDDEN",
                        "statusCode": 403,
                        "requiredRole": "Admin"
                    }
                }]
            }))
        
        # 400 Bad Request - for mutations
        if is_mutation:
            error_responses.append(self._create_postman_response(400, "Bad Request", {
                "errors": [{
                    "message": "Invalid request data",
                    "extensions": {
                        "code": "BAD_REQUEST",
                        "statusCode": 400
                    }
                }]
            }))
        
        # 503 Service Unavailable - for external service operations
        service_keywords = {
            "export": "export_service",
            "import": "connectra",
            "email": "lambda_email",
            "ai": "lambda_ai",
            "connectra": "connectra",
            "s3": "s3",
            "linkedin": "linkedin",
            "sales": "lambda_sales_navigator",
            "documentation": "lambda_documentation"
        }
        
        detected_service = None
        query_lower = query.lower()
        for keyword, service_name in service_keywords.items():
            if keyword in query_lower:
                detected_service = service_name
                break
        
        if detected_service:
            error_responses.append(self._create_postman_response(503, "Service Unavailable", {
                "errors": [{
                    "message": "Service temporarily unavailable. Please try again later.",
                    "extensions": {
                        "code": "SERVICE_UNAVAILABLE",
                        "statusCode": 503,
                        "serviceName": detected_service
                    }
                }]
            }))
        
        return error_responses
    
    def _create_postman_response(
        self,
        status_code: int,
        name: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Postman response format."""
        # Get original request for response reference
        original_request = {
            "method": "POST",
            "header": [
                {"key": "Content-Type", "value": "application/json"}
            ],
            "body": {
                "mode": "raw",
                "raw": "{\n  \"query\": \"...\",\n  \"variables\": {}\n}"
            },
            "url": {
                "raw": "{{baseUrl}}/graphql",
                "host": ["{{baseUrl}}"],
                "path": ["graphql"]
            }
        }
        
        return {
            "name": name,
            "originalRequest": original_request,
            "status": "OK" if status_code == 200 else "Error",
            "code": status_code,
            "_postman_previewlanguage": "json",
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json; charset=utf-8"
                },
                {
                    "key": "Content-Length",
                    "value": str(len(json.dumps(body, ensure_ascii=False)))
                }
            ],
            "cookie": [],
            "body": json.dumps(body, indent=2, ensure_ascii=False)
        }


def add_responses_to_collection(
    collection_path: Path,
    output_path: Optional[Path] = None,
    dry_run: bool = False
):
    """Add example responses to Postman collection."""
    if output_path is None:
        output_path = collection_path
    
    # Load collection
    print(f"📖 Loading collection: {collection_path}")
    with open(collection_path, "r", encoding="utf-8") as f:
        collection = json.load(f)
    
    generator = ResponseExampleGenerator()
    requests_processed = 0
    responses_added = 0
    
    # Process all requests recursively
    def process_item(item: Dict[str, Any], module_name: str = "") -> None:
        """Recursively process collection items."""
        nonlocal requests_processed, responses_added
        
        if "item" in item:
            # Folder - process children
            current_module = item.get("name", module_name)
            for child in item["item"]:
                process_item(child, current_module)
        elif "request" in item:
            # Request - add response
            requests_processed += 1
            request_name = item.get("name", "Unknown")
            
            # Skip if response already exists
            if "response" in item and item["response"]:
                print(f"  ⊘ Skipped (has response): {request_name}")
                return
            
            responses = generator.generate_for_request(item)
            if responses:
                item["response"] = responses
                responses_added += 1
                print(f"  ✓ Added response to: {request_name}")
            else:
                print(f"  ✗ No response generated for: {request_name}")
    
    # Process all modules
    print("\n🔄 Processing requests...\n")
    for module in collection.get("item", []):
        module_name = module.get("name", "Unknown")
        print(f"📁 Processing module: {module_name}")
        process_item(module, module_name)
        print()
    
    # Save updated collection
    if not dry_run:
        print(f"💾 Saving updated collection: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        print("✅ Collection updated successfully!")
    else:
        print("\n🔍 Dry run - collection not modified")
    
    print(f"\n📊 Summary:")
    print(f"   Requests processed: {requests_processed}")
    print(f"   Responses added: {responses_added}")
    print(f"   Collection saved to: {output_path}")


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    collection_path = script_dir / "Contact360_GraphQL_API.postman_collection.json"
    
    if not collection_path.exists():
        print(f"❌ Collection not found: {collection_path}")
        exit(1)
    
    # Run with dry_run=False to actually update the file
    print("🚀 Starting response example generation...\n")
    add_responses_to_collection(collection_path, dry_run=False)
    print("\n✨ Done!")
