from django.urls import path
from . import views

app_name = 'durgasflow'

urlpatterns = [
    # Dashboard views
    path('', views.dashboard, name='dashboard'),
    path('workflows/', views.workflow_list, name='workflow_list'),
    
    # Workflow CRUD
    path('workflow/create/', views.workflow_create, name='workflow_create'),
    path('workflow/<uuid:workflow_id>/', views.workflow_detail, name='workflow_detail'),
    path('workflow/<uuid:workflow_id>/edit/', views.workflow_edit, name='workflow_edit'),
    path('workflow/<uuid:workflow_id>/delete/', views.workflow_delete, name='workflow_delete'),
    
    # Visual Editor
    path('editor/<uuid:workflow_id>/', views.editor, name='editor'),
    path('editor/new/', views.editor_new, name='editor_new'),
    
    # Executions
    path('executions/', views.execution_list, name='execution_list'),
    path('execution/<uuid:execution_id>/', views.execution_detail, name='execution_detail'),
    
    # Workflow actions
    path('workflow/<uuid:workflow_id>/execute/', views.workflow_execute, name='workflow_execute'),
    path('workflow/<uuid:workflow_id>/activate/', views.workflow_activate, name='workflow_activate'),
    path('workflow/<uuid:workflow_id>/deactivate/', views.workflow_deactivate, name='workflow_deactivate'),
    
    # Credentials
    path('credentials/', views.credential_list, name='credential_list'),
    path('credential/create/', views.credential_create, name='credential_create'),
    path('credential/<uuid:credential_id>/', views.credential_detail, name='credential_detail'),
    path('credential/<uuid:credential_id>/delete/', views.credential_delete, name='credential_delete'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('template/<uuid:template_id>/use/', views.template_use, name='template_use'),

    # N8n Import
    path('import/n8n/<path:workflow_path>/', views.import_n8n_workflow, name='import_n8n'),

    # Webhook endpoint
    path('webhook/<uuid:workflow_id>/<str:webhook_path>/', views.webhook_handler, name='webhook_handler'),
]
