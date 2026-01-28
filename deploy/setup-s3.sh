#!/bin/bash
set -e

# S3 Bucket Setup Script
# This script helps set up the S3 bucket with proper configuration

BUCKET_NAME=${S3_BUCKET_NAME:-contact360docs}
REGION=${AWS_REGION:-us-east-1}

echo "Setting up S3 bucket: $BUCKET_NAME"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first:"
    echo "  pip install awscli"
    echo "  aws configure"
    exit 1
fi

# Check if bucket exists
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Bucket does not exist. Creating bucket..."
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION
    echo "Bucket created successfully"
else
    echo "Bucket already exists"
fi

# Create CORS configuration file
cat > /tmp/cors-config.json <<EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag", "Content-Length"],
            "MaxAgeSeconds": 3000
        }
    ]
}
EOF

# Configure CORS
echo "Configuring CORS..."
aws s3api put-bucket-cors \
    --bucket $BUCKET_NAME \
    --cors-configuration file:///tmp/cors-config.json

echo "CORS configured successfully"

# Create directory structure
echo "Creating directory structure..."
aws s3api put-object --bucket $BUCKET_NAME --key static/
aws s3api put-object --bucket $BUCKET_NAME --key media/
aws s3api put-object --bucket $BUCKET_NAME --key data/
aws s3api put-object --bucket $BUCKET_NAME --key documentation/

echo "Directory structure created"

# Enable versioning (optional)
read -p "Enable versioning? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    aws s3api put-bucket-versioning \
        --bucket $BUCKET_NAME \
        --versioning-configuration Status=Enabled
    echo "Versioning enabled"
fi

# Enable encryption
echo "Enabling server-side encryption..."
aws s3api put-bucket-encryption \
    --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

echo "Encryption enabled"

echo ""
echo "S3 bucket setup completed!"
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo ""
echo "Next steps:"
echo "1. Configure bucket policy (see docs/deployment/S3_BUCKET_POLICY.md)"
echo "2. Set up CloudFront distribution (optional)"
echo "3. Update CORS AllowedOrigins with your domain"
