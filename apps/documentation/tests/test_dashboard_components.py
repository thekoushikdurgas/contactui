"""
Tests for Dashboard JavaScript Components.

Tests pagination, controller, and modal components.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.template.loader import render_to_string

User = get_user_model()


class DashboardComponentsTestCase(TestCase):
    """Base test case for dashboard component tests."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')


class PaginationComponentTest(DashboardComponentsTestCase):
    """Tests for pagination component template."""
    
    def test_pagination_template_renders(self):
        """Test that pagination template renders without errors."""
        context = {
            'container_id': 'test-pagination',
            'total': 100,
            'current_page': 1,
            'page_size': 20
        }
        
        try:
            html = render_to_string('components/dashboard_pagination.html', context)
            self.assertIn('test-pagination', html)
            self.assertIn('100', html)
        except Exception as e:
            self.fail(f"Pagination template failed to render: {e}")
    
    def test_pagination_template_with_options(self):
        """Test pagination template with custom options."""
        context = {
            'container_id': 'test-pagination',
            'total': 50,
            'current_page': 2,
            'page_size': 10,
            'page_size_options': [5, 10, 25, 50],
            'show_page_size': True,
            'show_total': True
        }
        
        html = render_to_string('components/dashboard_pagination.html', context)
        self.assertIn('test-pagination', html)
        self.assertIn('50', html)


class ButtonComponentTest(DashboardComponentsTestCase):
    """Tests for button component template."""
    
    def test_button_template_renders(self):
        """Test that button template renders."""
        context = {
            'type': 'primary',
            'size': 'md',
            'text': 'Click Me'
        }
        
        try:
            html = render_to_string('components/button.html', context)
            self.assertIn('Click Me', html)
            self.assertIn('btn-primary', html)
            self.assertIn('btn-md', html)
        except Exception as e:
            self.fail(f"Button template failed to render: {e}")
    
    def test_button_template_as_link(self):
        """Test button template as link."""
        context = {
            'type': 'primary',
            'text': 'Go',
            'href': '/path'
        }
        
        html = render_to_string('components/button.html', context)
        self.assertIn('<a href="/path"', html)
        self.assertIn('Go', html)
    
    def test_button_template_with_icon(self):
        """Test button template with icon."""
        context = {
            'type': 'primary',
            'text': 'Save',
            'icon': '<svg>...</svg>',
            'icon_position': 'left'
        }
        
        html = render_to_string('components/button.html', context)
        self.assertIn('btn-icon', html)
        self.assertIn('Save', html)


class FormInputComponentTest(DashboardComponentsTestCase):
    """Tests for form input component templates."""
    
    def test_input_template_renders(self):
        """Test input component template."""
        context = {
            'type': 'text',
            'name': 'username',
            'label': 'Username',
            'placeholder': 'Enter username'
        }
        
        try:
            html = render_to_string('components/input.html', context)
            self.assertIn('username', html)
            self.assertIn('Username', html)
            self.assertIn('Enter username', html)
        except Exception as e:
            self.fail(f"Input template failed to render: {e}")
    
    def test_input_template_with_error(self):
        """Test input component with error."""
        context = {
            'type': 'text',
            'name': 'email',
            'label': 'Email',
            'error': 'Invalid email address'
        }
        
        html = render_to_string('components/input.html', context)
        self.assertIn('form-error', html)
        self.assertIn('Invalid email address', html)
        self.assertIn('aria-invalid="true"', html)
    
    def test_select_template_renders(self):
        """Test select component template."""
        context = {
            'name': 'status',
            'label': 'Status',
            'options': [('active', 'Active'), ('inactive', 'Inactive')]
        }
        
        try:
            html = render_to_string('components/select.html', context)
            self.assertIn('status', html)
            self.assertIn('Status', html)
            self.assertIn('Active', html)
            self.assertIn('Inactive', html)
        except Exception as e:
            self.fail(f"Select template failed to render: {e}")
    
    def test_textarea_template_renders(self):
        """Test textarea component template."""
        context = {
            'name': 'description',
            'label': 'Description',
            'rows': 5,
            'placeholder': 'Enter description'
        }
        
        try:
            html = render_to_string('components/textarea.html', context)
            self.assertIn('description', html)
            self.assertIn('Description', html)
            self.assertIn('rows="5"', html)
        except Exception as e:
            self.fail(f"Textarea template failed to render: {e}")


class ModalComponentTest(DashboardComponentsTestCase):
    """Tests for modal component template."""
    
    def test_modal_template_exists(self):
        """Test that modal template exists."""
        try:
            html = render_to_string('components/modal.html', {})
            # Modal is created dynamically, template is just a placeholder
            self.assertIsNotNone(html)
        except Exception as e:
            self.fail(f"Modal template failed to render: {e}")
