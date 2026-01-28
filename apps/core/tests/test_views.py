"""Tests for core views."""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class CoreViewsTest(TestCase):
    """Test core views."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_view_get(self):
        """Test login page GET request."""
        response = self.client.get(reverse('core:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login', status_code=200)
    
    def test_login_view_post_success(self):
        """Test successful login."""
        response = self.client.post(reverse('core:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('core:dashboard'))
    
    def test_login_view_post_invalid(self):
        """Test login with invalid credentials."""
        response = self.client.post(reverse('core:login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid', status_code=200)
    
    def test_register_view_get(self):
        """Test register page GET request."""
        response = self.client.get(reverse('core:register'))
        self.assertEqual(response.status_code, 200)
    
    def test_register_view_post_success(self):
        """Test successful registration."""
        response = self.client.post(reverse('core:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertRedirects(response, reverse('core:dashboard'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_dashboard_view_requires_login(self):
        """Test dashboard requires authentication."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertRedirects(response, f"{reverse('core:login')}?next={reverse('core:dashboard')}")
    
    def test_dashboard_view_authenticated(self):
        """Test dashboard for authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_logout_view(self):
        """Test logout."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:logout'))
        self.assertRedirects(response, reverse('core:login'))
