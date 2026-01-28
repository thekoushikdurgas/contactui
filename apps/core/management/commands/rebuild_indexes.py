"""Django management command to rebuild S3 indexes."""

from django.core.management.base import BaseCommand
from apps.documentation.utils.s3_index_manager import S3IndexManager


class Command(BaseCommand):
    """Rebuild S3 indexes for pages, endpoints, and relationships."""
    
    help = 'Rebuild S3 indexes by scanning all files'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--resource-type',
            type=str,
            choices=['pages', 'endpoints', 'relationships', 'all'],
            default='all',
            help='Type of resource to rebuild index for'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        resource_type = options['resource_type']
        index_manager = S3IndexManager()
        
        if resource_type == 'all':
            resource_types = ['pages', 'endpoints', 'relationships']
        else:
            resource_types = [resource_type]
        
        for rt in resource_types:
            self.stdout.write(f'Rebuilding index for {rt}...')
            success = index_manager.rebuild_index(rt)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully rebuilt index for {rt}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to rebuild index for {rt}')
                )
        
        self.stdout.write(self.style.SUCCESS('Index rebuild completed'))
