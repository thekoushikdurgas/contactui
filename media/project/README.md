# Documentation Collections Overview

## Introduction

This directory contains comprehensive documentation for the three main collections used by the Documentation API Service:

1. **Pages Collection** - Frontend page metadata
2. **Endpoints Collection** - API endpoint documentation
3. **Relationships Collection** - Bidirectional page-endpoint relationships

## Architecture

The Documentation API Service uses **S3 JSON file storage** (no database tables). All data is stored as JSON files in S3 with index files for fast queries.

### Storage Structure

```
s3://bucket/
├── data/
│   ├── pages/
│   │   ├── {page_id}.json          # Individual page metadata
│   │   └── index.json               # Pages index
│   ├── endpoints/
│   │   ├── {endpoint_id}.json       # Individual endpoint metadata
│   │   └── index.json               # Endpoints index
│   └── relationships/
│       ├── by-page/{page_path}.json
│       ├── by-endpoint/{path}_{method}.json
│       └── index.json
└── content/documentation/{page_id}.md  # Markdown content
```

## Collections

### 1. Pages Collection

**Location**: `pages/`

Stores metadata for all frontend pages (Next.js routes):
- Route information
- File paths
- Authentication/authorization requirements
- Endpoint relationships
- UI components

**See**: [Pages Collection Documentation](./pages/README.md)

### 2. Endpoints Collection

**Location**: `endpoints/`

Stores metadata for all API endpoints:
- Endpoint paths and methods
- Authentication/authorization
- Code traceability (router, service, repository)
- Page relationships
- Rate limits

**See**: [Endpoints Collection Documentation](./endpoints/README.md)

### 3. Relationships Collection

**Location**: `retations/`

Tracks bidirectional relationships between pages and endpoints:
- Which endpoints each page uses
- Which pages use each endpoint
- Usage context and types
- Service and hook information

**See**: [Relationships Collection Documentation](./retations/README.md)

## Quick Start

### Understanding the Structure

1. **Pages** represent frontend routes (e.g., `/companies`, `/contacts`)
2. **Endpoints** represent API routes (e.g., `/api/v4/companies`, `/api/v4/contacts`)
3. **Relationships** connect pages to endpoints they use

### Example Flow

```
Page: /companies
  ↓ uses
Endpoint: GET /api/v4/companies
  ↓ via
Service: companyService
  ↓ via
Hook: useCompanies
```

### Common Operations

#### Query Pages by Type
```bash
GET /docs?page_type=dashboard
```

#### Query Endpoints by Version
```bash
GET /endpoint-docs?api_version=v4
```

#### Get Endpoints for a Page
```bash
GET /docs/relationships/page/companies
```

#### Get Pages for an Endpoint
```bash
GET /docs/relationships/endpoint/api/v4/companies?method=GET
```

## Key Concepts

### No Database Tables

This system uses **S3 JSON file storage**, not traditional database tables:
- Each entity is a JSON file
- Index files enable fast queries
- Optimistic locking via ETag for concurrent writes

### Bidirectional Relationships

Relationships are stored in two files:
- **By-Page**: Lists endpoints used by a page
- **By-Endpoint**: Lists pages that use an endpoint

Both files are automatically kept in sync.

### Index-Based Queries

Index files provide fast lookups:
- **Pages**: By type, by route
- **Endpoints**: By API version, by method, by path+method
- **Relationships**: By API version (statistics)

### Path Sanitization

Paths are sanitized for S3 keys:
- `/companies` → `companies`
- `/api/v4/companies` → `api_v4_companies`
- Special characters are handled safely

## Documentation Structure

Each collection has:
- **README.md** - Overview and usage guide
- **schema.md** - Complete field reference
- **example_*.json** - Full example files
- ***_index_example.json** - Index structure examples

## API Service

The Documentation API Service is located at:
- **Path**: `lambda/documentation.api/`
- **Type**: FastAPI service
- **Deployment**: AWS Lambda
- **Storage**: S3 JSON files

## Related Documentation

- [Documentation API Service README](../../../lambda/documentation.api/README.md)
- [S3 Storage Structure](../../../lambda/documentation.api/docs/s3_storage_structure.md)
- [API Reference](../../../lambda/documentation.api/docs/api.md)

## Support

For questions or issues:
1. Check the collection-specific README files
2. Review schema documentation
3. Examine example JSON files
4. Consult the main API documentation
