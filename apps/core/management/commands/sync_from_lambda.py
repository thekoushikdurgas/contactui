"""Django management command to sync data from Lambda API."""

from django.core.management.base import BaseCommand
from apps.documentation.services.pages_service import PagesService
from apps.documentation.services.endpoints_service import EndpointsService
from apps.documentation.services.relationships_service import RelationshipsService


class Command(BaseCommand):
    """Sync documentation data from Lambda API to S3."""
    
    help = 'Sync pages, endpoints, and relationships from Lambda API to S3'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--resource-type',
            type=str,
            choices=['pages', 'endpoints', 'relationships', 'all'],
            default='all',
            help='Type of resource to sync'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of items to sync'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        resource_type = options['resource_type']
        limit = options['limit']
        
        if resource_type in ['pages', 'all']:
            self.stdout.write('Syncing pages from Lambda API...')
            pages_service = PagesService()
            try:
                result = pages_service.list_pages(limit=limit)
                count = result.get('total', 0)
                self.stdout.write(
                    self.style.SUCCESS(f'Found {count} pages')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing pages: {e}')
                )
        
        if resource_type in ['endpoints', 'all']:
            self.stdout.write('Syncing endpoints from Lambda API...')
            endpoints_service = EndpointsService()
            try:
                result = endpoints_service.list_endpoints(limit=limit)
                count = result.get('total', 0)
                self.stdout.write(
                    self.style.SUCCESS(f'Found {count} endpoints')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing endpoints: {e}')
                )
        
        if resource_type in ['relationships', 'all']:
            self.stdout.write('Syncing relationships from Lambda API...')
            relationships_service = RelationshipsService()
            try:
                result = relationships_service.list_relationships(limit=limit)
                count = result.get('total', 0)
                self.stdout.write(
                    self.style.SUCCESS(f'Found {count} relationships')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error syncing relationships: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('Sync completed'))
