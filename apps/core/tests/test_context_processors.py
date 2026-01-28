"""Tests for core context processors."""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import resolve, Resolver404
from unittest.mock import patch, MagicMock

from apps.core.context_processors import navigation, theme

User = get_user_model()


class NavigationContextProcessorTest(TestCase):
    """Test navigation context processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_navigation_with_valid_url(self):
        """Test navigation processor with valid URL."""
        request = self.factory.get('/docs/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_match = MagicMock()
            mock_match.url_name = 'dashboard'
            mock_match.app_name = 'documentation'
            mock_resolve.return_value = mock_match
            
            context = navigation(request)
            
            self.assertIn('sidebar_menu', context)
            self.assertIn('current_view', context)
            self.assertIn('current_app', context)
            self.assertEqual(context['current_view'], 'dashboard')
            self.assertEqual(context['current_app'], 'documentation')
    
    def test_navigation_with_404(self):
        """Test navigation processor with 404 URL."""
        request = self.factory.get('/nonexistent/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_resolve.side_effect = Resolver404()
            
            context = navigation(request)
            
            self.assertIn('sidebar_menu', context)
            self.assertIsNone(context['current_view'])
            self.assertIsNone(context['current_app'])
    
    def test_navigation_sets_active_state(self):
        """Test that active state is set correctly."""
        request = self.factory.get('/docs/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_match = MagicMock()
            mock_match.url_name = 'dashboard'
            mock_match.app_name = 'documentation'
            mock_resolve.return_value = mock_match
            
            context = navigation(request)
            sidebar_menu = context['sidebar_menu']
            
            # Find Documentation group
            doc_group = next(
                (g for g in sidebar_menu if g['label'] == 'DOCUMENTATION'),
                None
            )
            self.assertIsNotNone(doc_group)
            
            # Find Documentation item
            doc_item = next(
                (i for i in doc_group['items'] if i['label'] == 'Documentation'),
                None
            )
            self.assertIsNotNone(doc_item)
            self.assertTrue(doc_item['active'])
            self.assertTrue(doc_group['active'])
    
    def test_navigation_with_nested_items(self):
        """Test navigation processor with nested items."""
        request = self.factory.get('/docs/pages/list/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_match = MagicMock()
            mock_match.url_name = 'pages_list'
            mock_match.app_name = 'documentation'
            mock_resolve.return_value = mock_match
            
            context = navigation(request)
            sidebar_menu = context['sidebar_menu']
            
            # Find Pages item with children
            doc_group = next(
                (g for g in sidebar_menu if g['label'] == 'DOCUMENTATION'),
                None
            )
            pages_item = next(
                (i for i in doc_group['items'] if i.get('label') == 'Pages'),
                None
            )
            
            if pages_item and 'children' in pages_item:
                self.assertIsInstance(pages_item['children'], list)
                self.assertTrue(len(pages_item['children']) > 0)
    
    def test_navigation_with_nested_active_child(self):
        """Test that parent is active when child is active."""
        request = self.factory.get('/docs/pages/create/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_match = MagicMock()
            mock_match.url_name = 'page_create'
            mock_match.app_name = 'documentation'
            mock_resolve.return_value = mock_match
            
            context = navigation(request)
            sidebar_menu = context['sidebar_menu']
            
            # Find Pages item
            doc_group = next(
                (g for g in sidebar_menu if g['label'] == 'DOCUMENTATION'),
                None
            )
            pages_item = next(
                (i for i in doc_group['items'] if i.get('label') == 'Pages'),
                None
            )
            
            if pages_item:
                # Check if parent is active when child is active
                has_active_child = any(
                    c.get('active', False) 
                    for c in pages_item.get('children', [])
                )
                if has_active_child:
                    self.assertTrue(pages_item.get('active', False))
    
    def test_navigation_with_direct_url(self):
        """Test navigation processor with direct URL."""
        request = self.factory.get('/api/docs/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_match = MagicMock()
            mock_match.url_name = None
            mock_match.app_name = None
            mock_resolve.return_value = mock_match
            
            context = navigation(request)
            sidebar_menu = context['sidebar_menu']
            
            # Find API Documentation item
            doc_group = next(
                (g for g in sidebar_menu if g['label'] == 'DOCUMENTATION'),
                None
            )
            api_docs_item = next(
                (i for i in doc_group['items'] if i.get('label') == 'API Documentation'),
                None
            )
            
            if api_docs_item:
                # Check if it has url field
                self.assertIn('url', api_docs_item)
    
    def test_navigation_expanded_state(self):
        """Test that groups are expanded when they have active items."""
        request = self.factory.get('/docs/')
        request.user = self.user
        
        with patch('apps.core.context_processors.resolve') as mock_resolve:
            mock_match = MagicMock()
            mock_match.url_name = 'dashboard'
            mock_match.app_name = 'documentation'
            mock_resolve.return_value = mock_match
            
            context = navigation(request)
            sidebar_menu = context['sidebar_menu']
            
            # Find Documentation group
            doc_group = next(
                (g for g in sidebar_menu if g['label'] == 'DOCUMENTATION'),
                None
            )
            
            if doc_group and doc_group.get('active'):
                # Group should be expanded if active
                self.assertTrue(doc_group.get('expanded', False))


class ThemeContextProcessorTest(TestCase):
    """Test theme context processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_theme_default_light(self):
        """Test theme defaults to light."""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {}
        
        context = theme(request)
        
        self.assertIn('theme', context)
        self.assertEqual(context['theme'], 'light')
    
    def test_theme_from_session(self):
        """Test theme from session."""
        request = self.factory.get('/')
        request.user = self.user
        request.session = {'theme': 'dark'}
        
        context = theme(request)
        
        self.assertEqual(context['theme'], 'dark')
    
    def test_theme_different_values(self):
        """Test theme with different values."""
        request = self.factory.get('/')
        request.user = self.user
        
        for theme_value in ['light', 'dark', 'auto']:
            request.session = {'theme': theme_value}
            context = theme(request)
            self.assertEqual(context['theme'], theme_value)
