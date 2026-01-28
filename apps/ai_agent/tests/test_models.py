"""Tests for AI agent models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.ai_agent.models import AILearningSession, ChatMessage
from django.utils import timezone

User = get_user_model()


class AILearningSessionModelTest(TestCase):
    """Test AILearningSession model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_session(self):
        """Test session creation."""
        session = AILearningSession.objects.create(
            session_name='Test Session',
            status='pending',
            created_by=self.user
        )
        self.assertEqual(session.session_name, 'Test Session')
        self.assertEqual(session.status, 'pending')
        self.assertEqual(session.created_by, self.user)
        self.assertIsNotNone(session.session_id)
    
    def test_session_str(self):
        """Test session string representation."""
        session = AILearningSession.objects.create(
            session_name='Test Session',
            status='running',
            created_by=self.user
        )
        self.assertIn('Test Session', str(session))
        self.assertIn('running', str(session))
    
    def test_session_status_choices(self):
        """Test session status choices."""
        session = AILearningSession.objects.create(
            session_name='Test Session',
            status='completed',
            created_by=self.user
        )
        self.assertEqual(session.status, 'completed')
    
    def test_session_timestamps(self):
        """Test session timestamps."""
        session = AILearningSession.objects.create(
            session_name='Test Session',
            created_by=self.user
        )
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.updated_at)


class ChatMessageModelTest(TestCase):
    """Test ChatMessage model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = AILearningSession.objects.create(
            session_name='Test Session',
            created_by=self.user
        )
    
    def test_create_message(self):
        """Test message creation."""
        message = ChatMessage.objects.create(
            session=self.session,
            role='user',
            content='Test message',
            created_by=self.user
        )
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.session, self.session)
        self.assertIsNotNone(message.message_id)
    
    def test_message_str(self):
        """Test message string representation."""
        message = ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content='This is a test message',
            created_by=self.user
        )
        self.assertIn('assistant', str(message))
        self.assertIn('This is a test message', str(message))
    
    def test_message_without_session(self):
        """Test message creation without session."""
        message = ChatMessage.objects.create(
            role='user',
            content='Standalone message',
            created_by=self.user
        )
        self.assertIsNone(message.session)
        self.assertEqual(message.content, 'Standalone message')
    
    def test_message_metadata(self):
        """Test message with metadata."""
        message = ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content='Test',
            metadata={'sources': ['source1', 'source2']},
            created_by=self.user
        )
        self.assertEqual(message.metadata['sources'], ['source1', 'source2'])
