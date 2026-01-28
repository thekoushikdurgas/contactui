"""Tests for knowledge base services."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.knowledge.models import KnowledgeBase
from apps.knowledge.services import KnowledgeBaseService

User = get_user_model()


class KnowledgeBaseServiceTest(TestCase):
    """Test KnowledgeBaseService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = KnowledgeBaseService()
    
    def test_create_knowledge_item(self):
        """Test creating a knowledge item."""
        item = self.service.create(
            pattern_type='pattern',
            title='Test Pattern',
            content='Test content',
            tags=['test', 'pattern'],
            created_by=self.user
        )
        self.assertIsNotNone(item)
        self.assertEqual(item.title, 'Test Pattern')
        self.assertEqual(item.pattern_type, 'pattern')
    
    def test_get_knowledge_item(self):
        """Test getting a knowledge item."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            content='Test content',
            created_by=self.user
        )
        
        retrieved = self.service.get_by_id(str(item.knowledge_id))
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, 'Test Pattern')
    
    def test_update_knowledge_item(self):
        """Test updating a knowledge item."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Original Title',
            content='Original content',
            created_by=self.user
        )
        
        updated = self.service.update(
            str(item.knowledge_id),
            title='Updated Title',
            content='Updated content'
        )
        self.assertTrue(updated)
        
        item.refresh_from_db()
        self.assertEqual(item.title, 'Updated Title')
        self.assertEqual(item.content, 'Updated content')
    
    def test_delete_knowledge_item(self):
        """Test deleting a knowledge item."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            created_by=self.user
        )
        
        success = self.service.delete(str(item.knowledge_id))
        self.assertTrue(success)
        self.assertFalse(KnowledgeBase.objects.filter(knowledge_id=item.knowledge_id).exists())
    
    def test_search_knowledge_items(self):
        """Test searching knowledge items."""
        KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Django Pattern',
            content='Django best practices',
            created_by=self.user
        )
        KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='React Pattern',
            content='React hooks',
            created_by=self.user
        )
        
        results = self.service.search('Django')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Django Pattern')
