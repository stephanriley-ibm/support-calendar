"""
Management command to test PagerDuty connection and fetch available schedules.

Usage:
    python manage.py test_pagerduty_connection [--provider-id ID]
"""

from django.core.management.base import BaseCommand, CommandError
from oncall.models import OnCallProvider
from oncall.services import ProviderSyncService


class Command(BaseCommand):
    help = 'Test PagerDuty connection and list available schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-id',
            type=int,
            help='ID of the OnCallProvider to test (default: first active PagerDuty provider)',
        )

    def handle(self, *args, **options):
        # Get provider
        provider_id = options.get('provider_id')
        
        if provider_id:
            try:
                provider = OnCallProvider.objects.get(id=provider_id)
            except OnCallProvider.DoesNotExist:
                raise CommandError(f'Provider with ID {provider_id} not found')
        else:
            # Get first active PagerDuty provider
            provider = OnCallProvider.objects.filter(
                provider_type='pagerduty',
                is_active=True
            ).first()
            
            if not provider:
                raise CommandError('No active PagerDuty provider found')
        
        self.stdout.write(f'Testing provider: {provider.name} (ID: {provider.id})')
        self.stdout.write('')
        
        # Initialize sync service
        sync_service = ProviderSyncService(provider)
        
        # Test connection
        self.stdout.write('Testing connection...')
        success, message = sync_service.test_connection()
        
        if not success:
            self.stdout.write(self.style.ERROR(f'✗ Connection failed: {message}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✓ Connection successful: {message}'))
        self.stdout.write('')
        
        # Fetch and display schedules
        try:
            self.stdout.write('Fetching available schedules...')
            provider_inst = sync_service._get_provider_instance()
            schedules = provider_inst.fetch_schedules()
            
            if not schedules:
                self.stdout.write(self.style.WARNING('No schedules found'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Found {len(schedules)} schedule(s):'))
            self.stdout.write('')
            
            for schedule in schedules:
                self.stdout.write(f'  Schedule: {schedule["name"]}')
                self.stdout.write(f'    ID: {schedule["external_schedule_id"]}')
                self.stdout.write(f'    Time Zone: {schedule["time_zone"]}')
                self.stdout.write(f'    Description: {schedule.get("description", "N/A")}')
                self.stdout.write('')
            
            # Show configured schedule IDs
            config_schedule_ids = provider.config.get('schedule_ids', [])
            if config_schedule_ids:
                self.stdout.write('Configured schedule IDs in provider:')
                for schedule_id in config_schedule_ids:
                    # Check if it's in the fetched list
                    found = any(s['external_schedule_id'] == schedule_id for s in schedules)
                    status = '✓' if found else '✗ (not found)'
                    self.stdout.write(f'  {status} {schedule_id}')
            else:
                self.stdout.write(self.style.WARNING('No schedule IDs configured in provider'))
                self.stdout.write('Add schedule IDs to provider config to enable syncing')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching schedules: {str(e)}'))


# Made with Bob