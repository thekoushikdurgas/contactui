"""
Action Nodes - Workflow action nodes

These nodes perform various actions like sending emails, notifications, etc.
"""

import json
import logging
from typing import Dict, Any
from ..services.node_registry import NodeRegistry, BaseNodeHandler

logger = logging.getLogger(__name__)


@NodeRegistry.register
class EmailNode(BaseNodeHandler):
    """Send email node"""
    node_type = "action/email"
    title = "Send Email"
    category = "action"
    description = "Send an email notification"
    color = "#44aa88"
    
    inputs = [{"name": "data", "type": "object"}]
    outputs = [{"name": "result", "type": "object"}]
    properties = [
        {"name": "to", "type": "string", "default": ""},
        {"name": "subject", "type": "string", "default": ""},
        {"name": "body", "type": "textarea", "default": ""},
        {"name": "html", "type": "boolean", "default": False},
        {"name": "credential_id", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from django.core.mail import send_mail
        from django.conf import settings
        
        to_email = config.get('to', '')
        subject = config.get('subject', 'Notification')
        body = config.get('body', '')
        is_html = config.get('html', False)
        
        # Template substitution for body
        if input_data and isinstance(input_data, dict):
            for key, value in input_data.items():
                body = body.replace(f'{{{{{key}}}}}', str(value))
                subject = subject.replace(f'{{{{{key}}}}}', str(value))
        
        try:
            if is_html:
                send_mail(
                    subject=subject,
                    message='',
                    html_message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to_email],
                    fail_silently=False
                )
            else:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to_email],
                    fail_silently=False
                )
            
            return {
                'sent': True,
                'to': to_email,
                'subject': subject
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                'sent': False,
                'error': str(e)
            }


@NodeRegistry.register
class SlackNode(BaseNodeHandler):
    """Send Slack message node"""
    node_type = "action/slack"
    title = "Send to Slack"
    category = "action"
    description = "Send a message to Slack"
    color = "#44aa88"
    
    inputs = [{"name": "data", "type": "object"}]
    outputs = [{"name": "result", "type": "object"}]
    properties = [
        {"name": "webhook_url", "type": "string", "default": ""},
        {"name": "channel", "type": "string", "default": ""},
        {"name": "message", "type": "textarea", "default": ""},
        {"name": "username", "type": "string", "default": "Durgasflow Bot"},
        {"name": "icon_emoji", "type": "string", "default": ":robot_face:"},
        {"name": "credential_id", "type": "string", "default": ""}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        import requests
        
        webhook_url = config.get('webhook_url', '')
        message = config.get('message', '')
        
        # Template substitution
        if input_data and isinstance(input_data, dict):
            for key, value in input_data.items():
                message = message.replace(f'{{{{{key}}}}}', str(value))
        
        payload = {
            'text': message,
            'username': config.get('username', 'Durgasflow Bot'),
            'icon_emoji': config.get('icon_emoji', ':robot_face:')
        }
        
        if config.get('channel'):
            payload['channel'] = config['channel']
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {
                'sent': True,
                'message': message
            }
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return {
                'sent': False,
                'error': str(e)
            }


@NodeRegistry.register
class DatabaseQueryNode(BaseNodeHandler):
    """Execute database query node"""
    node_type = "action/database_query"
    title = "Database Query"
    category = "action"
    description = "Execute a database query"
    color = "#44aa88"
    
    inputs = [{"name": "params", "type": "object"}]
    outputs = [{"name": "results", "type": "object"}]
    properties = [
        {"name": "query", "type": "code", "default": "SELECT * FROM table_name WHERE id = %s"},
        {"name": "params", "type": "json", "default": "[]"},
        {"name": "database", "type": "select", "options": ["default"], "default": "default"},
        {"name": "fetch_mode", "type": "select", "options": ["all", "one", "count"], "default": "all"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        from django.db import connections
        
        query = config.get('query', '')
        params = config.get('params', [])
        database = config.get('database', 'default')
        fetch_mode = config.get('fetch_mode', 'all')
        
        if isinstance(params, str):
            params = json.loads(params)
        
        # Allow input data to override params
        if input_data and isinstance(input_data, list):
            params = input_data
        
        try:
            with connections[database].cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch_mode == 'one':
                    result = cursor.fetchone()
                    if result and cursor.description:
                        columns = [col[0] for col in cursor.description]
                        result = dict(zip(columns, result))
                elif fetch_mode == 'count':
                    result = cursor.rowcount
                else:
                    results = cursor.fetchall()
                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        result = [dict(zip(columns, row)) for row in results]
                    else:
                        result = results
            
            return {
                'results': result,
                'row_count': cursor.rowcount if hasattr(cursor, 'rowcount') else len(result) if isinstance(result, list) else 1
            }
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise


@NodeRegistry.register
class WaitNode(BaseNodeHandler):
    """Wait/delay node"""
    node_type = "action/wait"
    title = "Wait"
    category = "action"
    description = "Wait for a specified duration"
    color = "#888888"
    
    inputs = [{"name": "input", "type": "object"}]
    outputs = [{"name": "output", "type": "object"}]
    properties = [
        {"name": "duration", "type": "number", "default": 1},
        {"name": "unit", "type": "select", "options": ["seconds", "minutes"], "default": "seconds"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        import time
        
        duration = config.get('duration', 1)
        unit = config.get('unit', 'seconds')
        
        if unit == 'minutes':
            duration *= 60
        
        time.sleep(duration)
        
        return input_data


@NodeRegistry.register
class WriteFileNode(BaseNodeHandler):
    """Write to file node"""
    node_type = "action/write_file"
    title = "Write File"
    category = "action"
    description = "Write data to a file"
    color = "#44aa88"
    
    inputs = [{"name": "data", "type": "object"}]
    outputs = [{"name": "result", "type": "object"}]
    properties = [
        {"name": "filename", "type": "string", "default": "output.json"},
        {"name": "format", "type": "select", "options": ["json", "text", "csv"], "default": "json"},
        {"name": "storage", "type": "select", "options": ["local", "s3"], "default": "local"}
    ]
    
    def execute(self, config: Dict, input_data: Any, context: Any) -> Any:
        import os
        from django.conf import settings
        
        filename = config.get('filename', 'output.json')
        format_type = config.get('format', 'json')
        storage = config.get('storage', 'local')
        
        # Prepare content based on format
        if format_type == 'json':
            content = json.dumps(input_data, indent=2, default=str)
        elif format_type == 'csv':
            if isinstance(input_data, list) and input_data:
                import csv
                import io
                output = io.StringIO()
                if isinstance(input_data[0], dict):
                    writer = csv.DictWriter(output, fieldnames=input_data[0].keys())
                    writer.writeheader()
                    writer.writerows(input_data)
                else:
                    writer = csv.writer(output)
                    writer.writerows(input_data)
                content = output.getvalue()
            else:
                content = str(input_data)
        else:
            content = str(input_data)
        
        if storage == 'local':
            # Write to media directory
            output_dir = os.path.join(settings.MEDIA_ROOT, 'durgasflow_outputs')
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'filepath': filepath,
                'size': len(content)
            }
        else:
            # S3 storage would go here
            return {
                'success': False,
                'error': 'S3 storage not implemented'
            }
