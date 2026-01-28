"""Tests for AI agent views."""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.ai_agent.models import AILearningSession, ChatMessage

User = get_user_model()


class AIAgentViewsTest(TestCase):
    """Test AI agent views."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_chat_view(self):
        """Test chat view."""
        response = self.client.get(reverse('ai_agent:chat'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'chat', status_code=200)
    
    def test_list_sessions_view(self):
        """Test sessions list view."""
        # Create test session
        session = AILearningSession.objects.create(
            session_name='Test Session',
            created_by=self.user
        )
        
        response = self.client.get(reverse('ai_agent:sessions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Session', status_code=200)
    
    def test_session_detail_view(self):
        """Test session detail view."""
        session = AILearningSession.objects.create(
            session_name='Test Session',
            created_by=self.user
        )
        
        response = self.client.get(reverse('ai_agent:session_detail', args=[session.session_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Session', status_code=200)
    
    def test_session_detail_not_found(self):
        """Test session detail with invalid ID."""
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.get(reverse('ai_agent:session_detail', args=[fake_id]))
        # View redirects to sessions list when session not found
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ai_agent:sessions'))
