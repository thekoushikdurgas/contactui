"""Create demo data for Durgasman testing."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.durgasman.models import Collection, ApiRequest, Environment, EnvVariable


class Command(BaseCommand):
    help = 'Create demo data for Durgasman testing'

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return

        self.stdout.write(f'Creating demo data for user: {user.username}')

        # Create a demo collection
        collection, created = Collection.objects.get_or_create(
            name='Demo API Collection',
            user=user,
            defaults={
                'description': 'A demo collection with sample API requests'
            }
        )

        if created:
            self.stdout.write(f'Created collection: {collection.name}')
        else:
            self.stdout.write(f'Using existing collection: {collection.name}')

        # Create demo requests
        demo_requests = [
            {
                'name': 'Get User Profile',
                'method': 'GET',
                'url': '{{baseUrl}}/api/v1/users/me',
                'headers': [
                    {'key': 'Authorization', 'value': 'Bearer {{accessToken}}', 'enabled': True},
                    {'key': 'Accept', 'value': 'application/json', 'enabled': True}
                ]
            },
            {
                'name': 'Update User Profile',
                'method': 'PUT',
                'url': '{{baseUrl}}/api/v1/users/me',
                'headers': [
                    {'key': 'Authorization', 'value': 'Bearer {{accessToken}}', 'enabled': True},
                    {'key': 'Content-Type', 'value': 'application/json', 'enabled': True}
                ],
                'body': '{"firstName": "John", "lastName": "Doe", "email": "{{userEmail}}"}'
            },
            {
                'name': 'Create New Contact',
                'method': 'POST',
                'url': '{{baseUrl}}/api/v1/contacts',
                'headers': [
                    {'key': 'Authorization', 'value': 'Bearer {{accessToken}}', 'enabled': True},
                    {'key': 'Content-Type', 'value': 'application/json', 'enabled': True}
                ],
                'body': '{"firstName": "Jane", "lastName": "Smith", "email": "jane@example.com"}'
            }
        ]

        for req_data in demo_requests:
            request, created = ApiRequest.objects.get_or_create(
                collection=collection,
                name=req_data['name'],
                defaults={
                    'method': req_data['method'],
                    'url': req_data['url'],
                    'headers': req_data['headers'],
                    'body': req_data.get('body', '')
                }
            )

            if created:
                self.stdout.write(f'  Created request: {request.name}')
            else:
                self.stdout.write(f'  Using existing request: {request.name}')

        # Create demo environment
        environment, created = Environment.objects.get_or_create(
            name='Demo Environment',
            user=user,
            defaults={
                'variables_list': []
            }
        )

        if created:
            self.stdout.write(f'Created environment: {environment.name}')
        else:
            self.stdout.write(f'Using existing environment: {environment.name}')

        # Create demo variables
        demo_vars = [
            {'key': 'baseUrl', 'value': 'https://api.example.com'},
            {'key': 'accessToken', 'value': 'demo_token_12345'},
            {'key': 'userEmail', 'value': 'user@example.com'},
            {'key': 'userId', 'value': '123'}
        ]

        for var_data in demo_vars:
            var, created = EnvVariable.objects.get_or_create(
                environment=environment,
                key=var_data['key'],
                defaults={
                    'value': var_data['value'],
                    'enabled': True
                }
            )

            if created:
                self.stdout.write(f'  Created variable: {var.key} = {var.value}')
            else:
                self.stdout.write(f'  Using existing variable: {var.key}')

        self.stdout.write(self.style.SUCCESS('\nDemo data creation completed!'))
        self.stdout.write('You can now test Durgasman at: /durgasman/')