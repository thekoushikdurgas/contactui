"""
Durgasflow Models - Workflow Automation System

Models for managing workflows, nodes, executions, and credentials.
Inspired by n8n and NodeGraphQt patterns.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TriggerType(models.TextChoices):
    """Types of workflow triggers"""
    MANUAL = 'manual', 'Manual Trigger'
    WEBHOOK = 'webhook', 'Webhook'
    SCHEDULE = 'schedule', 'Scheduled'
    EVENT = 'event', 'Event-based'


class WorkflowStatus(models.TextChoices):
    """Workflow status"""
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ARCHIVED = 'archived', 'Archived'


class ExecutionStatus(models.TextChoices):
    """Execution status"""
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class NodeCategory(models.TextChoices):
    """Node categories"""
    TRIGGER = 'trigger', 'Trigger'
    AI_AGENT = 'ai_agent', 'AI Agent'
    ACTION = 'action', 'Action'
    LOGIC = 'logic', 'Logic & Transform'
    DOCSAI = 'docsai', 'DocsAI Integration'


class Workflow(models.Model):
    """
    Workflow model - represents a complete workflow/automation.
    
    The graph_data field stores the LiteGraph.js serialized graph structure.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    
    # Graph data from LiteGraph.js (serialized JSON)
    graph_data = models.JSONField(default=dict, blank=True)
    
    # Workflow settings
    status = models.CharField(
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT
    )
    is_active = models.BooleanField(default=False)
    trigger_type = models.CharField(
        max_length=20,
        choices=TriggerType.choices,
        default=TriggerType.MANUAL
    )
    
    # Schedule settings (for scheduled triggers)
    schedule_cron = models.CharField(max_length=100, blank=True, default='')
    
    # Webhook settings (for webhook triggers)
    webhook_path = models.CharField(max_length=255, blank=True, default='')
    webhook_secret = models.CharField(max_length=255, blank=True, default='')
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    
    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workflows'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_executed_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    execution_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Workflow'
        verbose_name_plural = 'Workflows'

    def __str__(self):
        return f"{self.name} ({self.status})"

    def activate(self):
        """Activate the workflow"""
        self.is_active = True
        self.status = WorkflowStatus.ACTIVE
        self.save(update_fields=['is_active', 'status', 'updated_at'])

    def deactivate(self):
        """Deactivate the workflow"""
        self.is_active = False
        self.status = WorkflowStatus.INACTIVE
        self.save(update_fields=['is_active', 'status', 'updated_at'])

    def increment_execution(self, success=True):
        """Increment execution counters"""
        self.execution_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_executed_at = timezone.now()
        self.save(update_fields=[
            'execution_count', 'success_count', 'failure_count',
            'last_executed_at', 'updated_at'
        ])


class WorkflowNode(models.Model):
    """
    WorkflowNode model - represents a node within a workflow.
    
    Each node has a type, position, configuration, and input/output ports.
    This model provides a normalized view of the graph data for querying.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='nodes'
    )
    
    # Node identification
    node_id = models.CharField(max_length=100)  # LiteGraph node ID
    node_type = models.CharField(max_length=100)  # e.g., 'trigger/manual', 'ai/chat'
    category = models.CharField(
        max_length=20,
        choices=NodeCategory.choices,
        default=NodeCategory.ACTION
    )
    title = models.CharField(max_length=255, default='')
    
    # Position in the graph canvas
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    
    # Node configuration
    config = models.JSONField(default=dict, blank=True)
    
    # Input/Output port definitions
    inputs = models.JSONField(default=list, blank=True)
    outputs = models.JSONField(default=list, blank=True)
    
    # Node properties from LiteGraph
    properties = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Workflow Node'
        verbose_name_plural = 'Workflow Nodes'
        unique_together = ['workflow', 'node_id']

    def __str__(self):
        return f"{self.title or self.node_type} ({self.node_id})"


class WorkflowConnection(models.Model):
    """
    WorkflowConnection model - represents a connection between nodes.
    
    Connections link output ports of one node to input ports of another.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='connections'
    )
    
    # Source node and output
    source_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.CASCADE,
        related_name='outgoing_connections'
    )
    source_output = models.PositiveIntegerField(default=0)  # Output slot index
    
    # Target node and input
    target_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.CASCADE,
        related_name='incoming_connections'
    )
    target_input = models.PositiveIntegerField(default=0)  # Input slot index
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Workflow Connection'
        verbose_name_plural = 'Workflow Connections'

    def __str__(self):
        return f"{self.source_node} -> {self.target_node}"


class Execution(models.Model):
    """
    Execution model - represents a single run of a workflow.
    
    Tracks the status, timing, and results of workflow executions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution status
    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING
    )
    
    # Trigger information
    trigger_type = models.CharField(
        max_length=20,
        choices=TriggerType.choices,
        default=TriggerType.MANUAL
    )
    trigger_data = models.JSONField(default=dict, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    result_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')
    error_stack = models.TextField(blank=True, default='')
    
    # Node-level execution data
    node_results = models.JSONField(default=dict, blank=True)
    
    # Metadata
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Who triggered it
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_executions'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Execution'
        verbose_name_plural = 'Executions'

    def __str__(self):
        return f"Execution {self.id} - {self.status}"

    @property
    def duration(self):
        """Calculate execution duration in seconds"""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def start(self):
        """Mark execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def complete(self, result_data=None):
        """Mark execution as completed"""
        self.status = ExecutionStatus.COMPLETED
        self.finished_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save(update_fields=['status', 'finished_at', 'result_data', 'updated_at'])
        self.workflow.increment_execution(success=True)

    def fail(self, error_message, error_stack=''):
        """Mark execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.finished_at = timezone.now()
        self.error_message = error_message
        self.error_stack = error_stack
        self.save(update_fields=[
            'status', 'finished_at', 'error_message', 'error_stack', 'updated_at'
        ])
        self.workflow.increment_execution(success=False)


class ExecutionLog(models.Model):
    """
    ExecutionLog model - detailed logs for each node execution.
    
    Provides a timeline of events during workflow execution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(
        Execution,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    # Which node
    node_id = models.CharField(max_length=100)
    node_type = models.CharField(max_length=100)
    node_title = models.CharField(max_length=255, default='')
    
    # Log level
    LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    
    # Log content
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Execution Log'
        verbose_name_plural = 'Execution Logs'

    def __str__(self):
        return f"[{self.level}] {self.node_title}: {self.message[:50]}"


class Credential(models.Model):
    """
    Credential model - secure storage for API keys, tokens, etc.
    
    Used by workflow nodes to authenticate with external services.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    
    # Credential type
    CREDENTIAL_TYPES = [
        ('api_key', 'API Key'),
        ('oauth2', 'OAuth 2.0'),
        ('basic_auth', 'Basic Auth'),
        ('bearer_token', 'Bearer Token'),
        ('custom', 'Custom'),
    ]
    credential_type = models.CharField(
        max_length=20,
        choices=CREDENTIAL_TYPES,
        default='api_key'
    )
    
    # Service this credential is for
    service_name = models.CharField(max_length=100, blank=True, default='')
    
    # Encrypted credential data
    # In production, use django-encrypted-model-fields or similar
    data = models.JSONField(default=dict)
    
    # Ownership
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credentials'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Credential'
        verbose_name_plural = 'Credentials'

    def __str__(self):
        return f"{self.name} ({self.credential_type})"

    def mark_used(self):
        """Update last used timestamp"""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class WorkflowTemplate(models.Model):
    """
    WorkflowTemplate model - pre-built workflow templates.
    
    Users can start from templates to quickly create common workflows.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    
    # Template category
    TEMPLATE_CATEGORIES = [
        ('automation', 'Automation'),
        ('ai', 'AI & Machine Learning'),
        ('data', 'Data Processing'),
        ('integration', 'Integration'),
        ('notification', 'Notifications'),
    ]
    category = models.CharField(
        max_length=20,
        choices=TEMPLATE_CATEGORIES,
        default='automation'
    )
    
    # Graph data template
    graph_data = models.JSONField(default=dict)
    
    # Preview image
    thumbnail_url = models.URLField(blank=True, default='')
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=False)
    use_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-use_count']
        verbose_name = 'Workflow Template'
        verbose_name_plural = 'Workflow Templates'

    def __str__(self):
        return self.name
