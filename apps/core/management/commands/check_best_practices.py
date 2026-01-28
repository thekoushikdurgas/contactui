"""
Django management command to check codebase against 100-point best practices checklist.

Usage:
    python manage.py check_best_practices
    python manage.py check_best_practices --category "Security"
    python manage.py check_best_practices --output reports/check_report.json
"""

from django.core.management.base import BaseCommand
from pathlib import Path
import sys
import os

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"
if scripts_dir.exists():
    sys.path.insert(0, str(scripts_dir))

try:
    from django_checker import DjangoBestPracticesChecker
except ImportError:
    DjangoBestPracticesChecker = None


class Command(BaseCommand):
    help = 'Check Django codebase against 100-point best practices checklist'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Run checks for specific category only (e.g., "Security", "Project Structure")',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path for JSON report',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'text', 'both'],
            default='both',
            help='Output format: json, text, or both',
        )
    
    def handle(self, *args, **options):
        if DjangoBestPracticesChecker is None:
            self.stdout.write(
                self.style.ERROR(
                    'Could not import django_checker. '
                    'Make sure scripts/django_checker.py exists.'
                )
            )
            return
        
        # Get project root (parent of manage.py)
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        # Initialize checker
        checker = DjangoBestPracticesChecker(project_root)
        
        # Run checks
        if options['category']:
            self.stdout.write(
                self.style.WARNING(
                    f'Running checks for category: {options["category"]}'
                )
            )
            # Filter results by category
            checker.run_all_checks()
            checker.results = [
                r for r in checker.results
                if r.category == options['category']
            ]
        else:
            checker.run_all_checks()
        
        # Generate summary
        report = checker._generate_summary()
        
        # Display summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('Django Best Practices Check Summary'))
        self.stdout.write('=' * 70)
        self.stdout.write(f"Total Points: {report['summary']['total_points']}")
        self.stdout.write(
            self.style.SUCCESS(f"Passed: {report['summary']['passed']}")
        )
        self.stdout.write(
            self.style.ERROR(f"Failed: {report['summary']['failed']}")
        )
        self.stdout.write(f"Score: {report['summary']['score']}%")
        self.stdout.write('')
        
        # Display by category
        for category, data in report['categories'].items():
            passed = data['passed']
            total = data['total']
            percentage = (passed / total * 100) if total > 0 else 0
            
            if percentage >= 80:
                style = self.style.SUCCESS
            elif percentage >= 60:
                style = self.style.WARNING
            else:
                style = self.style.ERROR
            
            self.stdout.write(
                style(f"{category}: {passed}/{total} passed ({percentage:.1f}%)")
            )
        
        # Save report if requested
        if options['output']:
            output_file = Path(options['output'])
            output_file.parent.mkdir(parents=True, exist_ok=True)
            checker.save_report(output_file)
            self.stdout.write(
                self.style.SUCCESS(f'\nReport saved to: {output_file}')
            )
        elif options['format'] in ['json', 'both']:
            # Default report location
            reports_dir = project_root / 'reports'
            reports_dir.mkdir(exist_ok=True)
            from datetime import datetime
            output_file = reports_dir / f"check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            checker.save_report(output_file)
            self.stdout.write(
                self.style.SUCCESS(f'\nReport saved to: {output_file}')
            )
        
        # Exit with appropriate code
        if report['summary']['score'] >= 80:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Codebase meets best practices threshold (80%+)')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ Codebase does not meet best practices threshold (80%+)'
                )
            )
            sys.exit(1)
