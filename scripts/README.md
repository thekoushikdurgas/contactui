# Lambda Documentation API Scripts

This directory contains utility scripts for development and deployment.

## New Structure (Refactored)

The scripts directory has been refactored to use shared utilities and base classes for better maintainability:

### Shared Utilities (`scripts/utils/`)

- **`context.py`** - Context-aware utilities that work in both Django and Lambda contexts
  - `get_pages_dir()`, `get_endpoints_dir()`, `get_relationships_dir()`
  - `get_logger()`, `get_settings()`, `get_media_root()`, `get_workspace_root()`
  - `find_docs_directory()`, `is_django_context()`, `is_lambda_context()`

- **`validators.py`** - Shared validation logic
  - `load_json_file()`, `validate_json_structure()`, `validate_date_consistency()`
  - `validate_route()`, `validate_with_schema()`, `get_validator()`
  - `validate_relationship_by_page()`, `validate_relationship_by_endpoint()`

- **`config.py`** - Centralized configuration management
  - `ScriptConfig` class with methods for S3, AWS, and script settings
  - `get_config()` function for global config instance

- **`upload_helpers.py`** - Common upload patterns
  - `sanitize_path()`, `normalize_method()`, `normalize_endpoint_path()`
  - `generate_s3_key()`, `normalize_for_lambda()`, `load_and_validate_file()`
  - `collect_upload_errors()`, `format_upload_summary()`, `get_exclude_files()`

### Base Classes (`scripts/base/`)

- **`base_script.py`** - `BaseScript` class with:
  - Common initialization (logging, config, error handling)
  - Dry-run support pattern
  - Progress reporting utilities
  - Statistics tracking
  - Standardized argument parsing

- **`upload_script.py`** - `BaseUploadScript` class extending `BaseScript` with:
  - Batch processing utilities
  - Retry logic framework
  - Error recovery patterns
  - Upload progress tracking

### Custom Exceptions (`scripts/exceptions.py`)

- `ScriptError` - Base exception for all script errors
- `ValidationError` - Validation errors
- `FileError` - File-related errors
- `UploadError` - Upload errors
- `ConfigurationError` - Configuration errors
- `APIError` - API-related errors

### Usage

All refactored scripts now:
- Use context-aware utilities (work in both Django and Lambda contexts)
- Support dry-run mode
- Provide consistent error handling and reporting
- Use shared validation logic
- Follow standardized patterns

## Scripts

### `validate_setup.py`

Validates that all required files and dependencies are in place before deployment.

**Usage:**

```bash
python scripts/validate_setup.py
# or
make validate
```

**What it checks:**

- Core application files (main.py, config.py, etc.)
- Service files (documentation_service.py, etc.)
- Repository files
- API endpoint files
- Infrastructure files (S3 clients, middleware, etc.)
- Utility files
- Python imports
- Environment variables (optional)

### `test_s3_connection.py`

Tests S3 bucket connectivity and access for the documentation API.

**Usage:**

```bash
# Set environment variables (or use .env file)
export S3_BUCKET_NAME="contact360docs"
export S3_DATA_PREFIX="data/"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Run test
python scripts/test_s3_connection.py
```

**What it tests:**

- AWS credentials configuration
- Bucket existence check
- Bucket creation capability (if bucket doesn't exist)
- Read access (listing objects)
- Write access (uploading test file)
- Presigned URL generation
- Proper cleanup of test files

**Required Environment Variables:**

- `S3_BUCKET_NAME` - S3 bucket name for documentation storage
- `S3_DATA_PREFIX` - S3 prefix for JSON data files (default: "data/")
- `AWS_ACCESS_KEY_ID` - AWS access key (or use IAM role/default credentials)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (or use IAM role/default credentials)
- `AWS_REGION` - AWS region where bucket is/will be located (default: "us-east-1")

**Output:**

- Configuration display (masked credentials)
- Bucket existence status
- Read/write permission verification
- Object listing (if any exist)
- Troubleshooting tips on failure
- Exit code: 0 for success, 1 for failure

**Example Output:**

```
============================================================
S3 Bucket Connection Test
============================================================

📋 Configuration:
  Bucket Name: contact360docs
  AWS Region: us-east-1
  Access Key ID: AKIAIOSFO...
  Secret Key: ✅ Configured
  S3 Prefix: documentation/

🔍 Test 1: Checking if bucket exists...
  ✅ Bucket 'contact360docs' exists and is accessible

📋 Test 2: Testing read access (listing objects)...
  ✅ Read access confirmed
  📊 Found 5 object(s) with prefix 'documentation/'

✍️  Test 3: Testing write access...
  ✅ Write access confirmed
  📝 Test file uploaded: documentation/_test_connection.txt
  🧹 Test file deleted (cleanup successful)

🔗 Test 4: Testing presigned URL generation...
  ✅ Presigned URL generation confirmed

============================================================
✅ All S3 connection tests passed!
============================================================
```

### `generate_s3_json_files.py`

Generates JSON files for S3 bucket seeding. Creates JSON files in the correct S3 structure format that can be saved locally or uploaded directly to S3.

**Usage:**

```bash
# Generate JSON files locally (saved to ./generated_json)
python scripts/generate_s3_json_files.py

# Generate and upload directly to S3
python scripts/generate_s3_json_files.py --upload-to-s3

# Generate with custom output directory
python scripts/generate_s3_json_files.py --output-dir ./my_json_files

# Generate with endpoints and relationships (when implemented)
python scripts/generate_s3_json_files.py --include-endpoints --include-relationships
```

**What it does:**

- Reads markdown files from `contact360/docs/pages/` (auto-detected, or use `--docs-dir`)
- Parses metadata (Route, File, Authentication, Authorization, Purpose)
- Generates page JSON files in S3 format: `data/pages/{page_id}.json`
- Generates pages index file: `data/pages/index.json`
- Optionally generates endpoint JSON files from page metadata or external file
- Optionally generates relationship JSON files (by-page and by-endpoint)
- Optionally uploads directly to S3 or saves locally

**Documentation Directory:**

The script automatically tries to find the docs directory in these locations:

- `{workspace_root}/contact360/docs/pages` (primary)
- `{workspace_root}/frontent/docs/pages` (legacy)

You can also specify a custom path:
```bash
python scripts/generate_s3_json_files.py --docs-dir "D:\code\ayan\contact360\contact360\docs\pages"
```

**Endpoint Generation:**

Endpoints can be generated from:

1. Page metadata: Extracts endpoints from `metadata.uses_endpoints` array in page JSON
2. External file: Reads `endpoints_data.json` from script directory (if exists)

**Relationship Generation:**

Relationships are automatically generated from:

- Page metadata: Extracts endpoint references from `metadata.uses_endpoints`
- Creates bidirectional relationships (by-page and by-endpoint)

**Output Structure:**

```
generated_json/
├── data/
│   └── pages/
│       ├── {page_id}.json    # Individual page metadata
│       └── index.json        # Pages index
```

**Required Environment Variables:**

- `S3_BUCKET_NAME` - S3 bucket name (required for --upload-to-s3)
- `S3_DATA_PREFIX` - S3 prefix for JSON data files (default: "data/")
- `S3_DOCUMENTATION_PREFIX` - S3 prefix for markdown content (default: "documentation/")
- `AWS_ACCESS_KEY_ID` - AWS access key (optional, uses IAM role in Lambda)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (optional, uses IAM role in Lambda)
- `AWS_REGION` - AWS region (default: "us-east-1")

**Example Output:**

```
============================================================
S3 JSON Files Generator
============================================================

📁 Output directory: ./generated_json

📁 Found 53 documentation files to process
📂 Directory: /path/to/frontent/docs/pages

[  1/ 53] ✅ Generated: about_page
[  2/ 53] ✅ Generated: contacts_page
...

📋 Generating pages index...
✅ Generated: pages/index.json

📡 Generating endpoint JSON files...
  📄 Loaded 12 endpoints from endpoints_data.json
  [  1/ 12] ✅ Generated: get_users_v1
  [  2/ 12] ✅ Generated: post_contacts_v1
...

📋 Generating endpoints index...
✅ Generated: endpoints/index.json

🔗 Generating relationship JSON files...
  ✅ Generated: by-page/_about.json
  ✅ Generated: by-page/_contacts.json
  ✅ Generated: by-endpoint/_api_v1_users_GET.json
...

📋 Generating relationships index...
✅ Generated: relationships/index.json

============================================================
Generation Summary
============================================================
  ✅ Pages generated:  53
  ❌ Pages errors:    0
  ✅ Endpoints generated: 12
  ❌ Endpoints errors:    0
  ✅ Relationships generated: 25
  ❌ Relationships errors:   0

📁 Generated files saved to: ./generated_json
============================================================
```

### `upload_json_to_s3.py`

Uploads locally generated JSON files to S3 bucket. Reads JSON files from a local directory (generated by `generate_s3_json_files.py`) and uploads them to S3.

**Usage:**

```bash
# Upload from default directory (./generated_json)
python scripts/upload_json_to_s3.py

# Upload from custom directory
python scripts/upload_json_to_s3.py ./my_json_files

# Dry run (show what would be uploaded)
python scripts/upload_json_to_s3.py --dry-run
```

**What it does:**

- Reads JSON files from local directory structure
- Uploads to S3 in correct structure
- Handles pages, endpoints, and relationships
- Preserves S3 key structure

**Required Environment Variables:**

- `S3_BUCKET_NAME` - S3 bucket name (required)
- `S3_DATA_PREFIX` - S3 prefix for JSON data files (default: "data/")
- AWS credentials (or use IAM role)

**Example Output:**

```
============================================================
Upload JSON Files to S3
============================================================

📄 Uploading pages...
  ✅ Uploaded: about_page.json -> data/pages/about_page.json
  ✅ Uploaded: contacts_page.json -> data/pages/contacts_page.json
  ✅ Uploaded: index.json -> data/pages/index.json

============================================================
Upload Summary
============================================================
  ✅ Uploaded:  53
  ❌ Errors:   0
  ⏭️  Skipped:  0

  📦 S3 Bucket: contact360docs
  📂 S3 Prefix: data/
============================================================
```

### `seed_documentation_pages.py`

Seeds documentation pages from markdown files into S3 storage using the service layer.

**Usage:**

```bash
# Set environment variables (or use .env file)
export S3_BUCKET_NAME="contact360docs"
export S3_DATA_PREFIX="data/"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Run seeding
python scripts/seed_documentation_pages.py
```

**What it does:**

- Checks S3 bucket exists and creates it if missing
- Verifies S3 connection
- Reads markdown files from `contact360/docs/pages/` (auto-detected)
- Parses metadata (Route, File, Authentication, Authorization, Purpose)
- Uploads content to S3
- Stores metadata in S3 as JSON files
- Creates new pages or updates existing ones
- Shows progress and summary

**Required Environment Variables:**

- `S3_BUCKET_NAME` - S3 bucket name (required)
- `S3_DATA_PREFIX` - S3 prefix for JSON data files (default: "data/")
- `AWS_ACCESS_KEY_ID` - AWS access key (or use IAM role in Lambda)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (or use IAM role in Lambda)
- `AWS_REGION` - AWS region (default: "us-east-1")

**Excluded Files:**
The script automatically excludes template and tracking files:

- `_page_docs_template.md`
- Files containing: `CSS_`, `DOCUMENTATION_`, `FINAL_`, `IMPLEMENTATION_`, `PROGRESS_`, `page_docs_coverage`, `sidebar_`

**Output:**

- Progress indicator showing which pages are being created/updated
- Summary with counts of created, updated, and error pages
- S3 bucket and prefix information
- Error details if any failures occur

**Example Output:**

```
============================================================
Documentation Pages Seeding Script
============================================================

📁 Found 53 documentation files to seed
📂 Directory: /path/to/frontent/docs/pages

✅ Using S3 storage backend

[  1/ 53] ➕ Creating: about_page
[  2/ 53] ➕ Creating: contacts_page
[  3/ 53] 🔄 Updating: dashboard_page
...

============================================================
Seeding Summary
============================================================
  ✅ Created:  45
  🔄 Updated:  8
  ❌ Errors:  0
  📄 Total:   53

  📦 S3 Bucket:  contact360docs
  📂 S3 Prefix:  documentation/
  🗄️  Database:   documentation
  📋 Collection: documentation_pages
============================================================
```

### `test_local.py`

Tests the API locally when running with `uvicorn`.

**Usage:**

```bash
# Terminal 1: Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: Run tests
python scripts/test_local.py
# or
make test-local
```

**What it tests:**

- Health check endpoint (`/health`)
- Root endpoint (`/`)
- List pages endpoint (`/docs`) - public
- API key authentication

### `deploy.sh` (Linux/macOS)

Interactive deployment script for Linux/macOS.

**Usage:**

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**What it does:**

- Checks prerequisites (SAM CLI, AWS CLI, Docker)
- Validates AWS credentials
- Builds the application
- Validates the template
- Deploys to AWS
- Shows stack outputs

### `deploy.ps1` (Windows)

Interactive deployment script for Windows PowerShell.

**Usage:**

```powershell
.\scripts\deploy.ps1
```

**What it does:**

- Same as `deploy.sh` but for Windows

### `verify_deployment.py`

Verifies Lambda deployment after AWS deployment.

**Usage:**

```bash
# Set environment variables
export LAMBDA_DOCUMENTATION_API_URL="https://your-api-url.execute-api.us-east-1.amazonaws.com"
export LAMBDA_DOCUMENTATION_API_KEY="your-api-key"

# Run verification
python scripts/verify_deployment.py
# or
make verify-deployment
```

**What it tests:**

- Health check endpoint
- Root endpoint
- List pages endpoint (public)
- API key authentication
- CORS headers
- Response time

### `integration_test.sh`

Bash script for integration testing (alternative to Python script).

**Usage:**

```bash
chmod +x scripts/integration_test.sh
./scripts/integration_test.sh
```

**What it tests:**

- Health check
- Root endpoint
- List pages
- API key authentication
- Protected endpoint without key

## JSON File Generation Workflow

### Option 1: Generate and Upload in One Step

```bash
# Generate JSON files and upload directly to S3
python scripts/generate_s3_json_files.py --upload-to-s3
```

### Option 2: Generate Locally, Review, Then Upload

```bash
# Step 1: Generate JSON files locally
python scripts/generate_s3_json_files.py --output-dir ./generated_json

# Step 2: Review generated files
ls -R generated_json/

# Step 3: Upload to S3
python scripts/upload_json_to_s3.py ./generated_json
```

### Option 3: Use Service Layer (Existing Method)

```bash
# Use the service layer to seed directly (uploads content + metadata)
python scripts/seed_documentation_pages.py
```

**Comparison:**

- `generate_s3_json_files.py` + `upload_json_to_s3.py`: Generate JSON files first, review, then upload (better for bulk operations, review, backup)
- `seed_documentation_pages.py`: Uses service layer, uploads content + metadata in one step (better for incremental updates)

## Running Scripts

All scripts should be run from the `lambda/documentation.api` directory:

```bash
cd lambda/documentation.api
python scripts/validate_setup.py
python scripts/test_s3_connection.py
python scripts/seed_documentation_pages.py
```

Or use the Makefile commands:

```bash
make validate      # Run validation
make test-local    # Run local tests
```

## Environment Variables

For seeding scripts, create a `.env` file in the `lambda/documentation.api` directory:

```bash
# S3 Configuration
S3_BUCKET_NAME=contact360docs
S3_DATA_PREFIX=data/

# AWS Credentials (or use IAM role in Lambda)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# API (for testing)
API_KEY=your-api-key
```

## Troubleshooting

### S3 Storage Issues

1. **Bucket not found**: Ensure S3 bucket exists or can be created
2. **Access denied**: Verify IAM permissions for S3 read/write
3. **Index file errors**: Run index rebuild if needed
4. **Data not found**: Verify data files exist in S3 at expected paths

**Solution:**

```bash
# Test S3 connection first
python scripts/test_s3_connection.py
```

### S3 Upload Issues

1. **Access denied**: Verify AWS credentials and IAM permissions
2. **Bucket not found**: Ensure S3 bucket exists in the specified region
3. **Region mismatch**: Check AWS_REGION matches bucket region

**Solution:**

- Verify AWS credentials: `aws s3 ls`
- Check bucket exists: `aws s3 ls s3://contact360docs`
- Verify IAM permissions for S3 upload

### Seeding Issues

1. **Markdown files not found**: Ensure `contact360/docs/pages/` directory exists relative to workspace root
   - Script automatically tries: `{workspace_root}/contact360/docs/pages/` (primary)
   - Falls back to: `{workspace_root}/frontent/docs/pages/` (legacy)
   - Check the path is correct or use custom path

2. **Metadata parsing errors**: Check markdown file format matches expected structure
   - Required fields: `**Route:**`, `**File:**`, `**Authentication:**`, `**Purpose:**`
   - Optional field: `**Authorization:**`

3. **Page already exists**: Script will update existing pages automatically

**Solution:**

- Verify files exist: `ls frontent/docs/pages/*.md`
- Check markdown format matches template
- Review error messages in output for specific issues

### Common Errors

**Error: "Documentation directory not found"**

- Solution: Ensure `contact360/docs/pages/` exists relative to workspace root
- Or use `--docs-dir` to specify custom path: `--docs-dir "D:\code\ayan\contact360\contact360\docs\pages"`

**Error: "Storage backend connection failed"**

- Solution: Run `test_s3_connection.py` to diagnose S3 issues
- Verify S3 bucket exists and is accessible
- Check AWS credentials and IAM permissions

**Error: "S3 upload failed" or "S3 bucket check failed"**

- Solution: Run `python scripts/test_s3_connection.py` to diagnose S3 issues
- Verify AWS credentials and bucket permissions
- Check S3_BUCKET_NAME is correct
- The seed script will attempt to create the bucket if it doesn't exist

**Error: "Page with page_id 'X' already exists"**

- Solution: This shouldn't happen - script checks and updates existing pages
- If it occurs, check S3 for existing page files

## Bulk Upload Scripts

### `analyze_docs_files.py`

Analyzes and validates all documentation JSON files in `docs/pages/`, `docs/endpoints/`, and `docs/retations/`.

**Usage:**

```bash
# Analyze all files
python scripts/analyze_docs_files.py

# Analyze only pages
python scripts/analyze_docs_files.py --pages-only

# Analyze only endpoints
python scripts/analyze_docs_files.py --endpoints-only

# Analyze only relationships
python scripts/analyze_docs_files.py --relationships-only

# Save report to file
python scripts/analyze_docs_files.py --output report.json
```

**What it does:**

- Scans all JSON files in docs directories
- Validates JSON structure against schemas
- Checks required fields
- Identifies duplicate IDs
- Generates validation report

**Output:**

- Console output with validation results
- Optional JSON report file
- Exit code: 0 if all valid, 1 if errors found

### `upload_docs_pages_to_s3.py`

Uploads all page JSON files from `docs/pages/` to S3 with validation and index updates.

**Usage:**

```bash
# Upload all pages
python scripts/upload_docs_pages_to_s3.py

# Dry run (see what would be uploaded)
python scripts/upload_docs_pages_to_s3.py --dry-run

# Skip existing files
python scripts/upload_docs_pages_to_s3.py --skip-existing

# Custom batch size
python scripts/upload_docs_pages_to_s3.py --batch-size 100
```

**What it does:**

- Reads all JSON files from `docs/pages/`
- Validates each file using schema validator
- Uploads to S3 at `data/pages/{page_id}.json`
- Updates pages index automatically
- Handles errors gracefully (continues on individual failures)
- Provides progress feedback

**Required Environment Variables:**

- `S3_BUCKET_NAME` - S3 bucket name (required)
- `S3_DATA_PREFIX` - S3 prefix (default: "data/")
- AWS credentials (or use IAM role)

### `upload_docs_endpoints_to_s3.py`

Uploads all endpoint JSON files from `docs/endpoints/` to S3 with validation and index updates.

**Usage:**

```bash
# Upload all endpoints
python scripts/upload_docs_endpoints_to_s3.py

# Dry run
python scripts/upload_docs_endpoints_to_s3.py --dry-run

# Skip existing files
python scripts/upload_docs_endpoints_to_s3.py --skip-existing
```

**What it does:**

- Reads all JSON files from `docs/endpoints/`
- Validates each file using schema validator
- Uploads to S3 at `data/endpoints/{endpoint_id}.json`
- Updates endpoints index automatically
- Handles errors gracefully

### `upload_docs_relationships_to_s3.py`

Uploads all relationship JSON files from `docs/retations/` to S3 ensuring bidirectional consistency.

**Usage:**

```bash
# Upload all relationships
python scripts/upload_docs_relationships_to_s3.py

# Dry run
python scripts/upload_docs_relationships_to_s3.py --dry-run

# Skip existing files
python scripts/upload_docs_relationships_to_s3.py --skip-existing
```

**What it does:**

- Reads by-page relationship files from `docs/retations/by-page/`
- Reads by-endpoint relationship files from `docs/retations/` (filtered by `by-endpoint_` prefix)
- Validates each file using schema validator
- Uploads to S3:
  - By-page: `data/relationships/by-page/{sanitized_path}.json`
  - By-endpoint: `data/relationships/by-endpoint/{sanitized_path}_{method}.json`
- Ensures bidirectional consistency (updates both files for each relationship)
- Updates relationships index

### `upload_all_docs_to_s3.py`

Unified script to upload all documentation files (pages, endpoints, relationships, and indexes) to S3.

**Usage:**

```bash
# Upload everything
python scripts/upload_all_docs_to_s3.py

# Dry run
python scripts/upload_all_docs_to_s3.py --dry-run

# Upload only pages
python scripts/upload_all_docs_to_s3.py --pages-only

# Upload only endpoints
python scripts/upload_all_docs_to_s3.py --endpoints-only

# Upload only relationships
python scripts/upload_all_docs_to_s3.py --relationships-only

# Skip index files
python scripts/upload_all_docs_to_s3.py --skip-indexes

# Skip existing files
python scripts/upload_all_docs_to_s3.py --skip-existing
```

**What it does:**

- Orchestrates uploads for all three types (Pages → Endpoints → Relationships)
- Validates index files before upload
- Uploads index files to S3
- Generates comprehensive upload report
- Supports selective upload options

### `upload_index_files_to_s3.py`

Uploads index files from `docs/` to S3 after validation.

**Usage:**

```bash
# Upload index files
python scripts/upload_index_files_to_s3.py

# Dry run
python scripts/upload_index_files_to_s3.py --dry-run
```

**What it does:**

- Reads `pages_index.json`, `endpoints_index.json`, `relationships_index.json`
- Validates index structure
- Uploads to S3 at correct paths
- Verifies index consistency (total matches structure)

## Bulk Upload Workflow

### Recommended Workflow

1. **Analyze files first:**
   ```bash
   python scripts/analyze_docs_files.py --output validation_report.json
   ```

2. **Review validation report** and fix any errors

3. **Upload all files:**
   ```bash
   # Dry run first
   python scripts/upload_all_docs_to_s3.py --dry-run
   
   # Actual upload
   python scripts/upload_all_docs_to_s3.py
   ```

4. **Verify upload:**
   ```bash
   python scripts/test_bulk_upload.py
   ```

### Individual Upload Workflow

If you need to upload types separately:

```bash
# Step 1: Upload pages
python scripts/upload_docs_pages_to_s3.py

# Step 2: Upload endpoints
python scripts/upload_docs_endpoints_to_s3.py

# Step 3: Upload relationships
python scripts/upload_docs_relationships_to_s3.py

# Step 4: Upload index files
python scripts/upload_index_files_to_s3.py
```

## Validation Process

All upload scripts use schema validators to ensure data integrity:

- **Pages**: Validated against page schema (required fields, valid types, etc.)
- **Endpoints**: Validated against endpoint schema (method, api_version, etc.)
- **Relationships**: Validated against relationship schema (bidirectional consistency)

Invalid files are skipped with detailed error messages. Check the error details in the summary output.

## API Endpoints for Bulk Operations

After uploading files, you can use the API endpoints for bulk operations:

### Bulk Sync Endpoints

- `POST /docs/sync/bulk` - Bulk sync pages
- `POST /endpoint-docs/sync/bulk` - Bulk sync endpoints
- `POST /docs/relationships/sync/bulk` - Bulk sync relationships

### Index Rebuild Endpoints

- `POST /docs/index/rebuild` - Rebuild pages index
- `POST /endpoint-docs/index/rebuild` - Rebuild endpoints index
- `POST /docs/relationships/index/rebuild` - Rebuild relationships index

### Validation Endpoints

- `POST /docs/validate` - Validate page data
- `POST /endpoint-docs/validate` - Validate endpoint data
- `POST /docs/relationships/validate/data` - Validate relationship data

All endpoints require API key authentication.

See `docs/BULK_UPLOAD_GUIDE.md` for detailed usage instructions.
