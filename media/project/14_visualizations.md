# Visualizations: Contact360 Documentation System

**Generated:** 2026-01-20  
**Total Visualizations:** 15+

## Overview

This document contains visual representations of the Contact360 documentation system including relationship graphs, distribution charts, and architecture diagrams using Mermaid diagrams and structured visualizations.

---

## 1. Relationship Graphs

### 1.1 Page-to-Endpoint Relationship Graph (Top Pages)

```mermaid
graph TB
    subgraph "Dashboard Pages"
        P1["/companies<br/>4 endpoints"]
        P2["/contacts<br/>7 endpoints"]
        P3["/profile<br/>13 endpoints"]
        P4["/billing<br/>9 endpoints"]
        P5["/dashboard<br/>5 endpoints"]
    end
    
    subgraph "Endpoints"
        E1["QueryCompanies<br/>QUERY"]
        E2["QueryContacts<br/>QUERY"]
        E3["GetMe<br/>QUERY"]
        E4["GetBilling<br/>QUERY"]
        E5["GetActivities<br/>QUERY"]
    end
    
    P1 --> E1
    P2 --> E2
    P3 --> E3
    P4 --> E4
    P5 --> E5
    P5 --> E5
```

### 1.2 Service Dependency Graph

```mermaid
graph LR
    subgraph "Pages"
        P1["/companies"]
        P2["/contacts"]
        P3["/profile"]
        P4["/billing"]
        P5["/dashboard"]
    end
    
    subgraph "Services"
        S1["companiesService<br/>6 relationships"]
        S2["contactsService<br/>4 relationships"]
        S3["profileService<br/>8 relationships"]
        S4["billingService<br/>9 relationships"]
        S5["activitiesService<br/>3 relationships"]
        S6["marketingService<br/>15 relationships"]
    end
    
    subgraph "Endpoints"
        E1["GraphQL<br/>Endpoints"]
    end
    
    P1 --> S1
    P2 --> S2
    P3 --> S3
    P4 --> S4
    P5 --> S5
    S1 --> E1
    S2 --> E1
    S3 --> E1
    S4 --> E1
    S5 --> E1
    S6 --> E1
```

### 1.3 Most Used Endpoints Graph

```mermaid
graph TD
    E1["GetMarketingPage<br/>14 pages"]
    E2["GetActivities<br/>3 pages"]
    E3["GetDashboardPage<br/>2 pages"]
    E4["QueryCompanies<br/>2 pages"]
    E5["QueryContacts<br/>2 pages"]
    
    E1 --> P1["14 Marketing Pages"]
    E2 --> P2["/activities"]
    E2 --> P3["/dashboard"]
    E2 --> P4["/verifier"]
    E3 --> P3
    E3 --> P5["/dashboard/[uuid]"]
    E4 --> P6["/companies"]
    E4 --> P7["/app/data-search"]
    E5 --> P8["/contacts"]
    E5 --> P7
```

---

## 2. Distribution Charts

### 2.1 Page Type Distribution

```mermaid
pie title Page Type Distribution (48 pages)
    "Dashboard" : 33
    "Marketing" : 15
    "Auth" : 2
```

### 2.2 Endpoint Method Distribution

```mermaid
pie title Endpoint Method Distribution (145 endpoints)
    "QUERY" : 80
    "MUTATION" : 65
```

### 2.3 Authentication Distribution (Pages)

```mermaid
pie title Page Authentication Distribution
    "Required" : 35
    "Not Required" : 13
```

### 2.4 Authorization Distribution (Endpoints)

```mermaid
pie title Endpoint Authorization Distribution
    "User role required" : 120
    "Admin role required" : 15
    "Super Admin role required" : 5
    "Pro user role required" : 2
    "No authorization" : 3
```

### 2.5 Usage Type Distribution (Relationships)

```mermaid
pie title Relationship Usage Type Distribution (95 relationships)
    "Primary" : 60
    "Secondary" : 30
    "Conditional" : 5
```

### 2.6 Usage Context Distribution (Relationships)

```mermaid
pie title Relationship Usage Context Distribution
    "data_fetching" : 50
    "data_mutation" : 35
    "authentication" : 3
    "analytics" : 5
    "reporting" : 2
```

### 2.7 Service Usage Distribution

```mermaid
graph TB
    S1["marketingService<br/>15"]
    S2["billingService<br/>9"]
    S3["adminService<br/>8"]
    S4["profileService<br/>8"]
    S5["companiesService<br/>6"]
    S6["savedSearchesService<br/>6"]
    S7["aiChatsService<br/>6"]
    S8["contactsService<br/>4"]
    S9["emailService<br/>5"]
    S10["activitiesService<br/>3"]
```

---

## 3. Architecture Diagrams

### 3.1 System Overview Architecture

```mermaid
graph TB
    subgraph "Frontend (React)"
        P[Pages<br/>48 pages]
        H[Hooks<br/>35 hooks]
        C[Components<br/>182 components]
    end
    
    subgraph "API Layer (GraphQL)"
        G[GraphQL API<br/>145 endpoints]
    end
    
    subgraph "Service Layer"
        S1[companiesService]
        S2[contactsService]
        S3[billingService]
        S4[marketingService]
        S5[adminService]
        S6[Other Services<br/>18 services]
    end
    
    subgraph "Data Layer"
        R[Repositories]
        DB[(S3 Storage<br/>JSON Files)]
    end
    
    P --> H
    H --> S1
    H --> S2
    H --> S3
    H --> S4
    H --> S5
    H --> S6
    S1 --> G
    S2 --> G
    S3 --> G
    S4 --> G
    S5 --> G
    S6 --> G
    G --> R
    R --> DB
```

### 3.2 Data Flow Architecture

```mermaid
sequenceDiagram
    participant Page
    participant Hook
    participant Service
    participant GraphQL
    participant Repository
    participant S3
    
    Page->>Hook: User Action
    Hook->>Service: Call Service Method
    Service->>GraphQL: GraphQL Query/Mutation
    GraphQL->>Repository: Execute Query
    Repository->>S3: Read/Write JSON
    S3-->>Repository: Return Data
    Repository-->>GraphQL: Processed Data
    GraphQL-->>Service: Response
    Service-->>Hook: Formatted Data
    Hook-->>Page: Update UI
```

### 3.3 Service Layer Architecture

```mermaid
graph LR
    subgraph "Service Layer (24 services)"
        direction TB
        S1[marketingService<br/>15 uses]
        S2[billingService<br/>9 uses]
        S3[adminService<br/>8 uses]
        S4[profileService<br/>8 uses]
        S5[companiesService<br/>6 uses]
        S6[contactsService<br/>4 uses]
        S7[Other Services<br/>18 services]
    end
    
    subgraph "GraphQL Endpoints"
        E[145 Endpoints]
    end
    
    S1 --> E
    S2 --> E
    S3 --> E
    S4 --> E
    S5 --> E
    S6 --> E
    S7 --> E
```

### 3.4 Documentation System Architecture

```mermaid
graph TB
    subgraph "Documentation API Service"
        API[FastAPI Endpoints]
        SRV[Documentation Services]
        REPO[Repositories]
    end
    
    subgraph "S3 Storage"
        PAGES[pages/<br/>48 JSON files]
        ENDPOINTS[endpoints/<br/>145 JSON files]
        RELS[relationships/<br/>95 JSON files]
        INDEXES[index.json<br/>3 files]
    end
    
    API --> SRV
    SRV --> REPO
    REPO --> PAGES
    REPO --> ENDPOINTS
    REPO --> RELS
    REPO --> INDEXES
```

### 3.5 Relationship Storage Architecture

```mermaid
graph LR
    subgraph "Bidirectional Storage"
        BP[By-Page Files<br/>40 files]
        BE[By-Endpoint Files<br/>55 files]
    end
    
    subgraph "Example"
        P1["companies.json<br/>Lists endpoints<br/>for /companies"]
        E1["QueryCompanies_QUERY.json<br/>Lists pages<br/>using endpoint"]
    end
    
    BP --> P1
    BE --> E1
    P1 <--> E1
```

---

## 4. Statistical Visualizations

### 4.1 Page Complexity Chart

```
Pages by Endpoint Count:

profile_page        ████████████████████████ 13
billing_page        ████████████████ 9
contacts_page       ███████████ 7
ai_chat_page        ████████ 6
admin_users_page    ██████ 5
companies_page      ████ 4
export_page         ████ 4
analytics_page      ████ 4
```

### 4.2 Endpoint Usage Chart

```
Endpoints by Page Count:

GetMarketingPage    ████████████████████████████████████████ 14
GetActivities       ████████ 3
GetDashboardPage    █████ 2
QueryCompanies      █████ 2
QueryContacts       █████ 2
ListExports         █████ 2
Others (90)         █ 1 each
```

### 4.3 Service Relationship Chart

```
Services by Relationship Count:

marketingService    ████████████████ 15
billingService      █████████ 9
adminService        ████████ 8
profileService      ████████ 8
companiesService    ██████ 6
savedSearchesService ██████ 6
aiChatsService      ██████ 6
```

---

## 5. Dependency Graphs

### 5.1 Page Dependency Graph (Sample)

```mermaid
graph TD
    subgraph "Core Pages"
        P1[/companies]
        P2[/contacts]
        P3[/profile]
        P4[/billing]
    end
    
    subgraph "Feature Pages"
        P5[/dashboard]
        P6[/app]
        P7[/verifier]
        P8[/ai-chat]
    end
    
    subgraph "Admin Pages"
        P9[/admin/users]
        P10[/admin/marketing]
        P11[/admin/logs]
    end
    
    P5 --> P1
    P5 --> P2
    P5 --> P3
    P3 --> P4
    P9 --> P1
    P9 --> P2
    P10 --> P5
```

### 5.2 Endpoint Category Dependency

```mermaid
graph LR
    subgraph "Core Categories"
        C1[Authentication<br/>6 endpoints]
        C2[Companies<br/>5 endpoints]
        C3[Contacts<br/>3 endpoints]
        C4[Email Ops<br/>7 endpoints]
    end
    
    subgraph "Feature Categories"
        C5[Dashboard<br/>5 endpoints]
        C6[Marketing<br/>8 endpoints]
        C7[Billing<br/>17 endpoints]
        C8[Profile<br/>9 endpoints]
    end
    
    C1 --> C8
    C2 --> C4
    C3 --> C4
    C5 --> C2
    C5 --> C3
    C6 --> C5
```

---

## 6. Data Flow Diagrams

### 6.1 Page Load Flow

```mermaid
flowchart TD
    Start[User Visits Page] --> CheckAuth{Authentication<br/>Required?}
    CheckAuth -->|Yes| VerifyAuth[Verify JWT Token]
    CheckAuth -->|No| LoadPage[Load Page Component]
    VerifyAuth -->|Valid| LoadPage
    VerifyAuth -->|Invalid| RedirectLogin[Redirect to /login]
    LoadPage --> CallHook[Call React Hook]
    CallHook --> CallService[Call Service Method]
    CallService --> GraphQL[GraphQL Query/Mutation]
    GraphQL --> Process[Process Response]
    Process --> UpdateUI[Update UI State]
    UpdateUI --> End[Page Rendered]
```

### 6.2 Relationship Sync Flow

```mermaid
flowchart LR
    Start[Create Relationship] --> UpdateByPage[Update By-Page File]
    UpdateByPage --> UpdateByEndpoint[Update By-Endpoint File]
    UpdateByEndpoint --> UpdateIndex[Update Index File]
    UpdateIndex --> Validate[Validate Consistency]
    Validate -->|Valid| Complete[Complete]
    Validate -->|Invalid| Error[Error Handling]
```

---

## 7. Component Hierarchy

### 7.1 Page Component Structure

```
Page Structure:
├── Layout Component
│   ├── Header
│   ├── Navigation
│   └── Footer
├── Main Content
│   ├── Data Table/List
│   ├── Filters
│   ├── Actions
│   └── Pagination
└── Modals/Dialogs
    ├── Create Modal
    ├── Edit Modal
    └── Delete Confirmation
```

### 7.2 Service Layer Structure

```
Service Layer:
├── Domain Services (24 services)
│   ├── companiesService
│   ├── contactsService
│   ├── billingService
│   └── ...
├── GraphQL Client
│   ├── Query Builder
│   ├── Mutation Builder
│   └── Response Handler
└── Error Handling
    ├── Network Errors
    ├── Validation Errors
    └── Business Logic Errors
```

---

## 8. Quick Reference Visualizations

### 8.1 System Statistics Summary

```
┌─────────────────────────────────────────┐
│   Contact360 Documentation System       │
├─────────────────────────────────────────┤
│ Pages:           48                      │
│ Endpoints:       145                     │
│ Relationships:   95                      │
│ Services:        24                      │
│ Hooks:           35                      │
│ Components:      182                     │
└─────────────────────────────────────────┘
```

### 8.2 Coverage Metrics

```
Documentation Coverage:
████████████████████████████████████████ 100%

Data Quality:
████████████████████████████████████████ 100%

Relationship Coverage:
████████████████████████████████████████ 100%
```

---

## 9. Mermaid Diagram Index

1. **Relationship Graphs:**
   - Page-to-Endpoint Graph
   - Service Dependency Graph
   - Most Used Endpoints Graph

2. **Distribution Charts:**
   - Page Type Distribution
   - Endpoint Method Distribution
   - Authentication Distribution
   - Authorization Distribution
   - Usage Type Distribution
   - Usage Context Distribution

3. **Architecture Diagrams:**
   - System Overview
   - Data Flow
   - Service Layer
   - Documentation System
   - Relationship Storage

4. **Dependency Graphs:**
   - Page Dependencies
   - Endpoint Category Dependencies

5. **Flow Diagrams:**
   - Page Load Flow
   - Relationship Sync Flow

---

## 10. Visualization Usage

### How to View Mermaid Diagrams

1. **GitHub/GitLab:** Mermaid diagrams render automatically
2. **VS Code:** Install "Markdown Preview Mermaid Support" extension
3. **Online:** Use [Mermaid Live Editor](https://mermaid.live)
4. **Documentation Sites:** Most support Mermaid natively

### Export Options

- **PNG/SVG:** Use Mermaid CLI or online editor
- **PDF:** Include in Markdown to PDF converters
- **Interactive:** Embed in web documentation

---

**Last Updated:** 2026-01-20  
**Total Visualizations:** 15+  
**Diagram Types:** Mermaid, ASCII, Text Charts
