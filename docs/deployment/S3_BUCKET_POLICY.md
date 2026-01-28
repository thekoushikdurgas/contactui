# S3 Bucket Configuration Guide

## Bucket Name
`contact360docs`

## Region
`us-east-1` (or as configured in `AWS_REGION`)

## CORS Configuration

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
        "AllowedOrigins": [
            "https://your-domain.com",
            "https://www.your-domain.com"
        ],
        "ExposeHeaders": ["ETag", "Content-Length"],
        "MaxAgeSeconds": 3000
    }
]
```

## Bucket Policy (IAM)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::contact360docs/*"
        },
        {
            "Sid": "AllowPutObject",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USER"
            },
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::contact360docs/*"
        }
    ]
}
```

## Lifecycle Policies

### Transition to Glacier
- **Rule Name**: Transition to Glacier after 90 days
- **Prefix**: `data/`
- **Transition**: After 90 days → Glacier
- **Expiration**: None

### Delete Incomplete Multipart Uploads
- **Rule Name**: Delete incomplete multipart uploads
- **Prefix**: `media/`
- **Action**: Delete incomplete multipart uploads after 7 days

## Versioning

Enable versioning for important data:
- **Status**: Enabled (optional)
- **MFA Delete**: Disabled (for easier management)

## Encryption

- **Server-Side Encryption**: AES256 (default)
- **Bucket Key**: Enabled (reduces encryption costs)

## Public Access Settings

- **Block Public Access**: Configured per bucket policy
- **Public Read**: Allowed for static/media files via bucket policy
- **Public Write**: Blocked (only IAM user can write)

## Setup Instructions

1. **Create Bucket**:
   ```bash
   aws s3 mb s3://contact360docs --region us-east-1
   ```

2. **Configure CORS**:
   ```bash
   aws s3api put-bucket-cors \
     --bucket contact360docs \
     --cors-configuration file://cors-config.json
   ```

3. **Set Bucket Policy**:
   ```bash
   aws s3api put-bucket-policy \
     --bucket contact360docs \
     --policy file://bucket-policy.json
   ```

4. **Enable Versioning** (optional):
   ```bash
   aws s3api put-bucket-versioning \
     --bucket contact360docs \
     --versioning-configuration Status=Enabled
   ```

5. **Configure Lifecycle**:
   ```bash
   aws s3api put-bucket-lifecycle-configuration \
     --bucket contact360docs \
     --lifecycle-configuration file://lifecycle-config.json
   ```

## Directory Structure

```
contact360docs/
├── static/          # Static files (CSS, JS, images)
├── media/           # User-uploaded media files
├── data/            # Application data (JSON files)
│   ├── pages/
│   ├── endpoints/
│   ├── relationships/
│   └── postman/
└── documentation/   # Documentation files
```

## Access Patterns

- **Static Files**: Public read, served via CloudFront (optional)
- **Media Files**: Public read via presigned URLs or public bucket policy
- **Data Files**: Private, accessed via IAM credentials
- **Documentation**: Public read

## Cost Optimization

1. **Use S3 Intelligent-Tiering** for infrequently accessed files
2. **Enable S3 Lifecycle** to transition old files to Glacier
3. **Use CloudFront** for static file delivery (reduces S3 requests)
4. **Enable S3 Transfer Acceleration** for faster uploads (optional)

## Security Best Practices

1. **IAM User**: Create dedicated IAM user with minimal required permissions
2. **Access Keys**: Rotate access keys regularly
3. **Bucket Policy**: Restrict write access to specific IAM users/roles
4. **CORS**: Limit CORS origins to your domain(s) only
5. **Encryption**: Enable server-side encryption for all objects
6. **Versioning**: Enable versioning for critical data
7. **Logging**: Enable S3 access logging to CloudTrail

## Monitoring

- **CloudWatch Metrics**: Monitor bucket size, requests, errors
- **S3 Access Logs**: Enable access logging for audit trail
- **Cost Alerts**: Set up billing alerts for unexpected costs
