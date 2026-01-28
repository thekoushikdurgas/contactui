"""Django management command to create superuser with better defaults."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    """Create a superuser with interactive prompts."""
    
    help = 'Create a superuser account'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the superuser'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the superuser'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser'
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Use provided arguments without prompting'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        noinput = options.get('noinput', False)
        
        if not noinput:
            if not username:
                username = input('Username: ')
            if not email:
                email = input('Email: ')
            if not password:
                password = input('Password: ')
        
        if not username or not email or not password:
            self.stdout.write(
                self.style.ERROR('Username, email, and password are required')
            )
            return
        
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {username}')
            )
        except IntegrityError:
            self.stdout.write(
                self.style.ERROR(f'User with username {username} already exists')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
