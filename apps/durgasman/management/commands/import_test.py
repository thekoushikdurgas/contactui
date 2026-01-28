"""Test command for Durgasman import functionality."""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.durgasman.services.postman_importer import import_postman_collection, import_postman_environment
from apps.durgasman.services.endpoint_importer import import_endpoint_json
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Durgasman import functionality with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['postman', 'endpoints', 'all'],
            default='all',
            help='Type of import to test'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to associate imports with (defaults to first user)'
        )

    def handle(self, *args, **options):
        # Get user
        User = get_user_model()
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                raise CommandError(f'User with ID {options["user_id"]} does not exist')
        else:
            user = User.objects.first()
            if not user:
                raise CommandError('No users found. Please create a user first.')

        self.stdout.write(self.style.SUCCESS(f'Using user: {user.username} (ID: {user.id})'))

        import_type = options['type']

        if import_type in ['postman', 'all']:
            self.test_postman_import(user)

        if import_type in ['endpoints', 'all']:
            self.test_endpoints_import(user)

        self.stdout.write(self.style.SUCCESS('Import testing completed!'))

    def test_postman_import(self, user):
        """Test Postman collection and environment import."""
        self.stdout.write('Testing Postman imports...')

        # Test collection import
        collection_path = os.path.join(settings.MEDIA_ROOT, 'postman', 'collection', 'Contact360 API.postman_collection.json')
        if os.path.exists(collection_path):
            try:
                collection = import_postman_collection(collection_path, user)
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Imported Postman collection: {collection.name} '
                    f'({collection.requests.count()} requests)'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to import collection: {e}'))
        else:
            self.stdout.write(self.style.WARNING(f'Postman collection not found: {collection_path}'))

        # Test environment import
        env_path = os.path.join(settings.MEDIA_ROOT, 'postman', 'environment', 'Contact360_Local.postman_environment.json')
        if os.path.exists(env_path):
            try:
                environment = import_postman_environment(env_path, user)
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Imported environment: {environment.name} '
                    f'({environment.env_variables.count()} variables)'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to import environment: {e}'))
        else:
            self.stdout.write(self.style.WARNING(f'Environment file not found: {env_path}'))

    def test_endpoints_import(self, user):
        """Test endpoint JSON import."""
        self.stdout.write('Testing endpoint imports...')

        endpoints_dir = os.path.join(settings.MEDIA_ROOT, 'endpoints')
        if not os.path.exists(endpoints_dir):
            self.stdout.write(self.style.WARNING(f'Endpoints directory not found: {endpoints_dir}'))
            return

        # Test importing a few endpoint files
        endpoint_files = [
            'get_contact_graphql.json',
            'get_activities_graphql.json',
            'mutation_create_api_key_graphql.json'
        ]

        imported_count = 0
        for filename in endpoint_files:
            file_path = os.path.join(endpoints_dir, filename)
            if os.path.exists(file_path):
                try:
                    collection = import_endpoint_json(file_path, user)
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Imported endpoint: {collection.name}'
                    ))
                    imported_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Failed to import {filename}: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'Endpoint file not found: {filename}'))

        if imported_count == 0:
            self.stdout.write(self.style.WARNING('No endpoint files were imported'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} endpoint collections'))
