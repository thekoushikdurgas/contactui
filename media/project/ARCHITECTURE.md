# Documentation Collections Architecture

## System Overview

The Documentation API Service uses a **file-based storage architecture** with S3 JSON files instead of traditional database tables. This design provides:

- **Scalability**: S3 handles large-scale storage
- **Simplicity**: No database management overhead
- **Performance**: Index files enable fast queries
- **Flexibility**: Easy to backup, restore, and migrate

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Documentation API Service                 │
│                    (FastAPI on AWS Lambda)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Pages      │   │  Endpoints   │   │Relationships │
│  Repository  │   │  Repository  │   │  Repository  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                    S3 Storage Layer                      │
│                                                          │
│  data/pages/          data/endpoints/   data/relationships/│
│  ├── {id}.json       ├── {id}.json     ├── by-page/      │
│  └── index.json      └── index.json    ├── by-endpoint/  │
│                                         └── index.json   │
│                                                          │
│  content/documentation/                                  │
│  └── {id}.md (markdown content)                         │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Create Operation

```
API Request
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
S3 Storage
    ├── Write entity file ({id}.json)
    └── Update index file (index.json)
```

### Read Operation

```
API Request
    ↓
Service Layer
    ↓
Repository Layer
    ├── Read index file (fast lookup)
    ├── Filter in-memory
    └── Load entity files (as needed)
```

### Update Operation (Optimistic Locking)

```
API Request
    ↓
Service Layer
    ↓
Repository Layer
    ├── Read entity file + ETag
    ├── Apply updates
    ├── Write with ETag check (atomic)
    └── Update index file
```

## Collection Relationships

```
┌─────────────┐         ┌──────────────┐
│    Pages    │────────▶│  Endpoints  │
│ Collection  │         │ Collection   │
└─────────────┘         └──────────────┘
       │                       │
       │                       │
       └───────────┬───────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Relationships   │
         │   Collection     │
         │  (Bidirectional) │
         └─────────────────┘
```

## Storage Patterns

### 1. Entity Files

Each entity (page, endpoint) is stored as a separate JSON file:
- **Path**: `data/{collection}/{id}.json`
- **Size**: Typically < 10KB per file
- **Format**: JSON with UTF-8 encoding

### 2. Index Files

Index files enable fast queries without loading all entities:
- **Path**: `data/{collection}/index.json`
- **Size**: Typically < 1MB
- **Structure**: Contains summaries and lookup maps

### 3. Relationship Files

Relationships use bidirectional storage:
- **By-Page**: `data/relationships/by-page/{sanitized_path}.json`
- **By-Endpoint**: `data/relationships/by-endpoint/{sanitized_path}_{method}.json`
- **Sync**: Both files updated simultaneously

## Query Patterns

### Fast Queries (Index-Based)

1. **List by Type**: Read index → Filter by type → Return summaries
2. **Get by Route**: Read index → Lookup route → Load single file
3. **List by API Version**: Read index → Filter by version → Return summaries

### Slower Queries (File-Based)

1. **Full Entity Details**: Read index → Load entity files
2. **Complex Filtering**: Read index → Load files → Filter in-memory
3. **Relationship Traversal**: Read relationship files → Load related entities

## Performance Optimizations

### 1. Index Files

- Small size (< 1MB) for fast reads
- In-memory caching for warm Lambda starts
- Automatic updates on every operation

### 2. Optimistic Locking

- ETag-based concurrent write handling
- Retry mechanism with exponential backoff
- Prevents lost updates

### 3. Query Caching

- In-memory TTL cache for frequently accessed queries
- Configurable cache size and TTL
- Stale-while-revalidate pattern

### 4. Batch Operations

- Bulk reads for list operations
- Parallel S3 reads where possible
- Pagination to limit data transfer

## Consistency Guarantees

### Eventual Consistency

- Index files updated after entity operations
- Relationship files updated simultaneously
- S3 eventual consistency handled by retries

### Atomic Operations

- Single-file updates use ETag checks
- Index updates are separate (can be rebuilt)
- Relationship updates update both files

### Validation

- Index validation checks consistency
- Relationship validation finds broken links
- Periodic rebuilds ensure accuracy

## Scalability Considerations

### Current Limits

- **Pages**: ~52 pages (can scale to thousands)
- **Endpoints**: ~45 endpoints (can scale to thousands)
- **Relationships**: ~150 relationships (can scale to tens of thousands)

### Scaling Strategies

1. **Index Size**: If index > 1MB, consider pagination or sharding
2. **Query Performance**: Use filters to limit data transfer
3. **Caching**: Increase cache size for high-traffic queries
4. **Parallel Reads**: Load multiple files in parallel

## Backup and Recovery

### Backup Strategy

- S3 versioning enabled
- Regular snapshots of index files
- Content files stored separately

### Recovery Procedures

1. **Index Corruption**: Rebuild from entity files
2. **Entity Loss**: Restore from S3 versioning
3. **Relationship Sync**: Rebuild from page/endpoint metadata

## Security

### Access Control

- API key authentication for protected endpoints
- Public endpoints for documentation pages
- S3 bucket policies restrict access

### Data Protection

- No sensitive data in documentation
- Presigned URLs for content access
- ETag-based optimistic locking prevents conflicts

## Monitoring

### Key Metrics

- Index file size
- Query response times
- Cache hit rates
- Relationship consistency

### Health Checks

- S3 connectivity
- Index file validity
- Relationship consistency
- Service availability

## Future Enhancements

### Potential Improvements

1. **Search**: Full-text search across pages/endpoints
2. **Analytics**: Usage tracking and analytics
3. **Versioning**: Track changes over time
4. **GraphQL**: GraphQL API for flexible queries
5. **Real-time Updates**: WebSocket support for live updates
