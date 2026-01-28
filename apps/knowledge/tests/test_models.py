"""Tests for knowledge base models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.knowledge.models import KnowledgeBase

User = get_user_model()


class KnowledgeBaseModelTest(TestCase):
    """Test KnowledgeBase model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_knowledge_item(self):
        """Test knowledge item creation."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            content='This is a test pattern',
            created_by=self.user
        )
        self.assertEqual(item.title, 'Test Pattern')
        self.assertEqual(item.pattern_type, 'pattern')
        self.assertEqual(item.content, 'This is a test pattern')
        self.assertIsNotNone(item.knowledge_id)
    
    def test_knowledge_item_str(self):
        """Test knowledge item string representation."""
        item = KnowledgeBase.objects.create(
            pattern_type='documentation',
            title='Test Documentation',
            created_by=self.user
        )
        self.assertEqual(str(item), 'Test Documentation')
    
    def test_knowledge_item_with_tags(self):
        """Test knowledge item with tags."""
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            tags=['tag1', 'tag2', 'tag3'],
            created_by=self.user
        )
        self.assertEqual(len(item.tags), 3)
        self.assertIn('tag1', item.tags)
    
    def test_knowledge_item_with_metadata(self):
        """Test knowledge item with metadata."""
        metadata = {'source': 'test', 'version': '1.0'}
        item = KnowledgeBase.objects.create(
            pattern_type='pattern',
            title='Test Pattern',
            metadata=metadata,
            created_by=self.user
        )
        self.assertEqual(item.metadata['source'], 'test')
        self.assertEqual(item.metadata['version'], '1.0')
    
    def test_knowledge_item_pattern_types(self):
        """Test all pattern type choices."""
        types = ['pattern', 'documentation', 'code_snippet', 'best_practice', 'api_pattern', 'architecture']
        for pattern_type in types:
            item = KnowledgeBase.objects.create(
                pattern_type=pattern_type,
                title=f'Test {pattern_type}',
                created_by=self.user
            )
            self.assertEqual(item.pattern_type, pattern_type)
