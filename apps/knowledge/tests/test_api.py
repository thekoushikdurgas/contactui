"""Tests for knowledge base API."""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json
from apps.knowledge.models import KnowledgeBase

User = get_user_model()


class KnowledgeAPITest(TestCase):
    """Test knowledge base API."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_knowledge_list_api(self):
        """Test knowledge list view."""
        KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            created_by=self.user
        )
        
        response = self.client.get(reverse('knowledge:list'))
        self.assertEqual(response.status_code, 200)
        # These are HTML views, not API endpoints
        self.assertContains(response, 'Test Pattern')
    
    def test_knowledge_detail_api(self):
        """Test knowledge detail view."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            content='Test content',
            created_by=self.user
        )
        
        response = self.client.get(reverse('knowledge:detail', args=[item.knowledge_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pattern')
    
    def test_knowledge_create_api(self):
        """Test knowledge create view."""
        response = self.client.post(reverse('knowledge:create'), {
            'pattern_type': 'pattern',
            'title': 'API Pattern',
            'content': 'API content',
        })
        
        # Should redirect on success
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(KnowledgeBase.objects.filter(title='API Pattern').exists())
    
    def test_knowledge_update_api(self):
        """Test knowledge update view."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Original Title',
            created_by=self.user
        )
        
        response = self.client.post(
            reverse('knowledge:edit', args=[item.knowledge_id]),
            {'title': 'Updated Title'}
        )
        
        # Should redirect on success
        self.assertIn(response.status_code, [200, 302])
        item.refresh_from_db()
        self.assertEqual(item.title, 'Updated Title')
    
    def test_knowledge_delete_api(self):
        """Test knowledge delete view."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='To Delete',
            created_by=self.user
        )
        
        response = self.client.post(reverse('knowledge:delete', args=[item.knowledge_id]))
        # Should redirect on success
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(KnowledgeBase.objects.filter(knowledge_id=item.knowledge_id).exists())
