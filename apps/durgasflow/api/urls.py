from django.urls import path
from . import views

app_name = 'durgasflow_api'

urlpatterns = [
    # Workflows
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/<uuid:workflow_id>/', views.workflow_detail, name='workflow_detail'),
    path('workflows/<uuid:workflow_id>/graph/', views.workflow_graph, name='workflow_graph'),
    path('workflows/<uuid:workflow_id>/execute/', views.workflow_execute, name='workflow_execute'),
    path('workflows/<uuid:workflow_id>/activate/', views.workflow_activate, name='workflow_activate'),
    path('workflows/<uuid:workflow_id>/deactivate/', views.workflow_deactivate, name='workflow_deactivate'),
    path('workflows/<uuid:workflow_id>/duplicate/', views.workflow_duplicate, name='workflow_duplicate'),
    path('workflows/<uuid:workflow_id>/export/', views.workflow_export, name='workflow_export'),
    path('workflows/import/', views.workflow_import, name='workflow_import'),
    
    # Executions
    path('executions/', views.execution_list, name='execution_list'),
    path('executions/<uuid:execution_id>/', views.execution_detail, name='execution_detail'),
    path('executions/<uuid:execution_id>/cancel/', views.execution_cancel, name='execution_cancel'),
    path('executions/<uuid:execution_id>/retry/', views.execution_retry, name='execution_retry'),
    path('executions/<uuid:execution_id>/logs/', views.execution_logs, name='execution_logs'),
    
    # Node registry
    path('nodes/', views.node_types, name='node_types'),
    path('nodes/<str:node_type>/', views.node_schema, name='node_schema'),
    
    # Credentials
    path('credentials/', views.credential_list, name='credential_list'),
    path('credentials/<uuid:credential_id>/', views.credential_detail, name='credential_detail'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/<uuid:template_id>/', views.template_detail, name='template_detail'),
    
    # Stats
    path('stats/', views.stats, name='stats'),
]
