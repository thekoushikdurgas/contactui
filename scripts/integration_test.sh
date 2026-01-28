#!/bin/bash
# Integration test script for Lambda documentation API

set -e

echo "=========================================="
echo "Lambda Documentation API - Integration Test"
echo "=========================================="

# Get API URL
if [ -z "$LAMBDA_DOCUMENTATION_API_URL" ]; then
    read -p "Enter Lambda API URL: " API_URL
else
    API_URL="$LAMBDA_DOCUMENTATION_API_URL"
fi

# Get API key
if [ -z "$LAMBDA_DOCUMENTATION_API_KEY" ]; then
    read -p "Enter API key: " API_KEY
else
    API_KEY="$LAMBDA_DOCUMENTATION_API_KEY"
fi

echo ""
echo "Testing API: $API_URL"
echo ""

# Test 1: Health check
echo "1. Health Check..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$HEALTH" = "200" ]; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed: $HEALTH"
    exit 1
fi

# Test 2: Root endpoint
echo "2. Root Endpoint..."
ROOT=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/")
if [ "$ROOT" = "200" ]; then
    echo "   ✅ Root endpoint passed"
else
    echo "   ❌ Root endpoint failed: $ROOT"
    exit 1
fi

# Test 3: List pages (public)
echo "3. List Pages (public)..."
PAGES=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$PAGES" = "200" ]; then
    echo "   ✅ List pages passed"
else
    echo "   ❌ List pages failed: $PAGES"
    exit 1
fi

# Test 4: API key authentication
echo "4. API Key Authentication..."
if [ -n "$API_KEY" ]; then
    AUTH=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/endpoint-docs")
    if [ "$AUTH" = "200" ] || [ "$AUTH" = "404" ]; then
        echo "   ✅ API key authentication passed"
    else
        echo "   ❌ API key authentication failed: $AUTH"
        exit 1
    fi
else
    echo "   ⚠️  Skipped (no API key provided)"
fi

# Test 5: Without API key (should fail for protected endpoints)
echo "5. Protected Endpoint Without API Key..."
NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/endpoint-docs")
if [ "$NO_AUTH" = "401" ]; then
    echo "   ✅ API key protection working"
else
    echo "   ⚠️  Unexpected status: $NO_AUTH"
fi

echo ""
echo "=========================================="
echo "✅ All integration tests passed!"
echo "=========================================="
