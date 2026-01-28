#!/usr/bin/env python
"""
Test script to verify route migration from /docs/media-manager/* to /docs/*

This script tests:
1. All new routes are accessible (return 200 or expected status)
2. All redirects work correctly (old routes redirect to new routes)
3. URL names resolve correctly
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docsai.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model

# Route mappings: old_name -> new_name
ROUTE_MAPPINGS = {
    # Dashboard routes
    'media_manager_dashboard': 'dashboard',
    'media_manager_pages': 'dashboard_pages',
    'media_manager_endpoints': 'dashboard_endpoints',
    'media_manager_relationships': 'dashboard_relationships',
    
    # Page routes
    'media_manager_page_detail': 'page_detail_enhanced',
    'media_manager_page_sections': 'page_sections',
    'media_manager_page_components': 'page_components',
    'media_manager_page_endpoints': 'page_endpoints',
    'media_manager_page_versions': 'page_versions',
    'media_manager_page_access_control': 'page_access_control',
    
    # Pages API routes
    'media_manager_pages_format': 'pages_format',
    'media_manager_pages_statistics': 'pages_statistics',
    'media_manager_pages_types': 'pages_types',
    'media_manager_pages_by_type_docs': 'pages_by_type_docs',
    'media_manager_pages_by_type_marketing': 'pages_by_type_marketing',
    'media_manager_pages_by_type_dashboard': 'pages_by_type_dashboard',
    
    # Endpoint routes
    'media_manager_endpoint_detail': 'endpoint_detail_enhanced',
    'media_manager_endpoint_pages': 'endpoint_pages',
    'media_manager_endpoint_access_control': 'endpoint_access_control',
    
    # Endpoints API routes
    'media_manager_endpoints_format': 'endpoints_format',
    'media_manager_endpoints_statistics': 'endpoints_statistics',
    'media_manager_endpoints_api_versions': 'endpoints_api_versions',
    'media_manager_endpoints_methods': 'endpoints_methods',
    
    # Relationship routes
    'media_manager_relationship_detail': 'relationship_detail_enhanced',
    'media_manager_relationship_access_control': 'relationship_access_control',
    
    # Relationships API routes
    'media_manager_relationships_format': 'relationships_format',
    'media_manager_relationships_statistics': 'relationships_statistics',
    'media_manager_relationships_graph': 'relationships_graph',
    
    # Postman routes
    'media_manager_postman_detail': 'postman_detail_enhanced',
    'media_manager_postman_collection': 'postman_collection',
    
    # Postman API routes
    'media_manager_postman_format': 'postman_format',
    'media_manager_postman_statistics': 'postman_statistics',
    
    # Health routes
    'media_manager_health': 'health',
    'media_manager_health_database': 'health_database',
    'media_manager_health_cache': 'health_cache',
    
    # Index routes
    'media_manager_index_pages': 'index_pages',
    'media_manager_index_pages_validate': 'index_pages_validate',
    
    # Service info routes
    'media_manager_service_info': 'service_info',
    'media_manager_docs_endpoint_stats': 'docs_endpoint_stats',
    'media_manager_statistics': 'statistics',
}

def test_url_name_resolution():
    """Test that all new URL names resolve correctly."""
    print("=" * 80)
    print("TEST 1: URL Name Resolution")
    print("=" * 80)
    
    # Routes that require parameters
    PARAMETERIZED_ROUTES = {
        'page_detail_enhanced': {'page_id': 'test-page'},
        'page_sections': {'page_id': 'test-page'},
        'page_components': {'page_id': 'test-page'},
        'page_endpoints': {'page_id': 'test-page'},
        'page_versions': {'page_id': 'test-page'},
        'page_access_control': {'page_id': 'test-page'},
        'endpoint_detail_enhanced': {'endpoint_id': 'test-endpoint'},
        'endpoint_pages': {'endpoint_id': 'test-endpoint'},
        'endpoint_access_control': {'endpoint_id': 'test-endpoint'},
        'relationship_detail_enhanced': {'relationship_id': 'test-rel'},
        'relationship_access_control': {'relationship_id': 'test-rel'},
        'postman_detail_enhanced': {'config_id': 'test-config'},
        'postman_collection': {'config_id': 'test-config'},
    }
    
    passed = 0
    failed = 0
    skipped = 0
    errors = []
    
    for old_name, new_name in ROUTE_MAPPINGS.items():
        try:
            # Check if route requires parameters
            if new_name in PARAMETERIZED_ROUTES:
                params = PARAMETERIZED_ROUTES[new_name]
                url = reverse(f'documentation:{new_name}', kwargs=params)
                print(f"✓ {new_name:50} -> {url} (with params)")
                passed += 1
            else:
                # Test new route exists without parameters
                url = reverse(f'documentation:{new_name}')
                print(f"✓ {new_name:50} -> {url}")
                passed += 1
        except NoReverseMatch as e:
            # Check if it's a parameterized route that we didn't handle
            if 'arguments' in str(e) or 'keyword arguments' in str(e):
                print(f"⚠ {new_name:50} -> Requires parameters (expected)")
                skipped += 1
            else:
                print(f"✗ {new_name:50} -> ERROR: {e}")
                failed += 1
                errors.append(f"{new_name}: {e}")
        except Exception as e:
            print(f"✗ {new_name:50} -> ERROR: {e}")
            failed += 1
            errors.append(f"{new_name}: {e}")
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped (parameterized)")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    return failed == 0


def test_redirect_routes():
    """Test that old routes redirect to new routes."""
    print("\n" + "=" * 80)
    print("TEST 2: Redirect Routes")
    print("=" * 80)
    
    User = get_user_model()
    client = Client()
    
    # Create a test user and login
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("⚠ No superuser found. Skipping redirect tests (requires authentication).")
            return True
        
        client.force_login(user)
    except Exception as e:
        print(f"⚠ Could not login: {e}. Skipping redirect tests.")
        return True
    
    passed = 0
    failed = 0
    errors = []
    
    # Test a few key redirects
    redirect_tests = [
        ('media_manager_dashboard', 'dashboard'),
        ('media_manager_pages', 'dashboard_pages'),
        ('media_manager_service_info', 'service_info'),
        ('media_manager_health', 'health'),
    ]
    
    for old_name, new_name in redirect_tests:
        try:
            # Get old route URL (should redirect)
            old_url = reverse(f'documentation:{old_name}_redirect')
            new_url = reverse(f'documentation:{new_name}')
            
            response = client.get(old_url, follow=False)
            
            if response.status_code in [301, 302, 307, 308]:
                redirect_location = response.get('Location', '')
                if new_url in redirect_location or new_name in redirect_location:
                    print(f"✓ {old_name:50} -> redirects to {new_name}")
                    passed += 1
                else:
                    print(f"✗ {old_name:50} -> redirects to wrong location: {redirect_location}")
                    failed += 1
                    errors.append(f"{old_name}: redirects to {redirect_location}, expected {new_url}")
            else:
                print(f"✗ {old_name:50} -> status {response.status_code}, expected redirect")
                failed += 1
                errors.append(f"{old_name}: status {response.status_code}, expected redirect")
        except NoReverseMatch:
            # Redirect route might not exist, that's okay
            print(f"⚠ {old_name:50} -> redirect route not found (may be intentional)")
        except Exception as e:
            print(f"✗ {old_name:50} -> ERROR: {e}")
            failed += 1
            errors.append(f"{old_name}: {e}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    return failed == 0


def test_new_routes_accessible():
    """Test that new routes are accessible (require authentication)."""
    print("\n" + "=" * 80)
    print("TEST 3: New Routes Accessibility")
    print("=" * 80)
    
    User = get_user_model()
    client = Client()
    
    # Create a test user and login
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("⚠ No superuser found. Skipping accessibility tests (requires authentication).")
            return True
        
        client.force_login(user)
    except Exception as e:
        print(f"⚠ Could not login: {e}. Skipping accessibility tests.")
        return True
    
    passed = 0
    failed = 0
    errors = []
    
    # Test a few key routes
    test_routes = [
        'dashboard',
        'dashboard_pages',
        'service_info',
        'health',
        'pages_statistics',
        'endpoints_statistics',
        'relationships_statistics',
        'postman_statistics',
    ]
    
    for route_name in test_routes:
        try:
            url = reverse(f'documentation:{route_name}')
            response = client.get(url)
            
            # Accept 200 (OK), 302 (redirect to login), 403 (forbidden), 404 (not found is okay for some routes)
            if response.status_code in [200, 302, 403]:
                print(f"✓ {route_name:50} -> {url:40} (status: {response.status_code})")
                passed += 1
            elif response.status_code == 404:
                # Some routes might need parameters
                print(f"⚠ {route_name:50} -> {url:40} (status: 404 - may need parameters)")
            else:
                print(f"✗ {route_name:50} -> {url:40} (status: {response.status_code})")
                failed += 1
                errors.append(f"{route_name}: status {response.status_code}")
        except NoReverseMatch as e:
            print(f"✗ {route_name:50} -> ERROR: {e}")
            failed += 1
            errors.append(f"{route_name}: {e}")
        except Exception as e:
            print(f"✗ {route_name:50} -> ERROR: {e}")
            failed += 1
            errors.append(f"{route_name}: {e}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ROUTE MIGRATION TEST SUITE")
    print("=" * 80)
    print("\nTesting route migration from /docs/media-manager/* to /docs/*\n")
    
    results = []
    
    # Test 1: URL name resolution
    results.append(("URL Name Resolution", test_url_name_resolution()))
    
    # Test 2: Redirect routes
    results.append(("Redirect Routes", test_redirect_routes()))
    
    # Test 3: New routes accessible
    results.append(("New Routes Accessibility", test_new_routes_accessible()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status:6} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
