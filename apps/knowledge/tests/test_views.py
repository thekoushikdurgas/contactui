"""Tests for knowledge base views."""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.knowledge.models import KnowledgeBase

User = get_user_model()


class KnowledgeViewsTest(TestCase):
    """Test knowledge base views."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_knowledge_list_view(self):
        """Test knowledge list view."""
        KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            created_by=self.user
        )
        
        response = self.client.get(reverse('knowledge:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pattern', status_code=200)
    
    def test_knowledge_detail_view(self):
        """Test knowledge detail view."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            content='Test content',
            created_by=self.user
        )
        
        response = self.client.get(reverse('knowledge:detail', args=[item.knowledge_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pattern', status_code=200)
    
    def test_knowledge_create_view_get(self):
        """Test knowledge create view GET."""
        response = self.client.get(reverse('knowledge:create'))
        self.assertEqual(response.status_code, 200)
    
    def test_knowledge_create_view_post(self):
        """Test knowledge create view POST."""
        response = self.client.post(reverse('knowledge:create'), {
            'pattern_type': 'pattern',
            'title': 'New Pattern',
            'content': 'New content',
            'tags': 'tag1,tag2'
        })
        # View redirects to detail page, not list
        created_item = KnowledgeBase.objects.get(title='New Pattern')
        self.assertRedirects(response, reverse('knowledge:detail', args=[created_item.knowledge_id]))
        self.assertTrue(KnowledgeBase.objects.filter(title='New Pattern').exists())
