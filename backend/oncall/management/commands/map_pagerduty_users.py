"""
Management command to map PagerDuty users to local users.

Usage:
    python manage.py map_pagerduty_users [--provider-id ID] [--auto-map]
"""

from django.core.management.base import BaseCommand, CommandError
from oncall.models import OnCallProvider, ExternalUserMapping
from oncall.services import ProviderSyncService
from users.models import User


class Command(BaseCommand):
    help = 'Map PagerDuty users to local users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-id',
            type=int,
            help='ID of the OnCallProvider (default: first active PagerDuty provider)',
        )
        parser.add_argument(
            '--auto-map',
            action='store_true',
            help='Automatically map users by email address',
        )
        parser.add_argument(
            '--list-unmapped',
            action='store_true',
            help='List unmapped PagerDuty users',
        )
        parser.add_argument(
            '--show-mappings',
            action='store_true',
            help='Show all current user mappings',
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
        
        self.stdout.write(f'Using provider: {provider.name} (ID: {provider.id})')
        self.stdout.write('')
        
        # Show current mappings
        if options.get('show_mappings'):
            self._show_mappings(provider)
            return
        
        # Initialize sync service
        sync_service = ProviderSyncService(provider)
        
        # Auto-map users
        if options.get('auto_map'):
            self.stdout.write('Fetching PagerDuty users and attempting auto-mapping...')
            stats = sync_service.fetch_and_map_users()
            
            self.stdout.write('')
            self.stdout.write('Mapping Results:')
            self.stdout.write(f'  Total PagerDuty users: {stats["total_fetched"]}')
            self.stdout.write(f'  Already mapped: {stats["already_mapped"]}')
            self.stdout.write(f'  Auto-mapped: {stats["auto_mapped"]}')
            self.stdout.write(f'  Unmapped: {stats["unmapped"]}')
            
            if stats['auto_mapped'] > 0:
                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully auto-mapped {stats["auto_mapped"]} user(s)'))
            
            if stats['unmapped'] > 0:
                self.stdout.write(self.style.WARNING(f'\n⚠ {stats["unmapped"]} user(s) could not be auto-mapped'))
                self.stdout.write('\nUnmapped users:')
                for user in stats['unmapped_users']:
                    self.stdout.write(f'  - {user["name"]} ({user["email"]})')
                    self.stdout.write(f'    ID: {user["id"]}')
                self.stdout.write('\nTo manually map these users, use Django admin or create ExternalUserMapping records.')
            
            if 'error' in stats:
                self.stdout.write(self.style.ERROR(f'\n✗ Error: {stats["error"]}'))
            
            return
        
        # List unmapped users
        if options.get('list_unmapped'):
            self._list_unmapped(provider, sync_service)
            return
        
        # Default: show help
        self.stdout.write('Use one of the following options:')
        self.stdout.write('  --auto-map         Automatically map users by email')
        self.stdout.write('  --list-unmapped    List unmapped PagerDuty users')
        self.stdout.write('  --show-mappings    Show current user mappings')
    
    def _show_mappings(self, provider):
        """Display all current user mappings."""
        mappings = ExternalUserMapping.objects.filter(
            provider=provider
        ).select_related('local_user').order_by('external_name')
        
        if not mappings:
            self.stdout.write(self.style.WARNING('No user mappings found'))
            return
        
        self.stdout.write(f'Current User Mappings ({mappings.count()}):')
        self.stdout.write('')
        
        for mapping in mappings:
            status = '✓ Active' if mapping.is_active else '✗ Inactive'
            self.stdout.write(f'  {status} {mapping.external_name}')
            self.stdout.write(f'    PagerDuty: {mapping.external_email} (ID: {mapping.external_user_id})')
            self.stdout.write(f'    Local User: {mapping.local_user.get_full_name()} ({mapping.local_user.email})')
            self.stdout.write('')
    
    def _list_unmapped(self, provider, sync_service):
        """List PagerDuty users that are not mapped."""
        self.stdout.write('Fetching PagerDuty users...')
        
        try:
            provider_inst = sync_service._get_provider_instance()
            external_users = provider_inst.fetch_users()
            
            # Get existing mappings
            mapped_ids = set(
                ExternalUserMapping.objects.filter(
                    provider=provider
                ).values_list('external_user_id', flat=True)
            )
            
            # Find unmapped users
            unmapped = [u for u in external_users if u['external_user_id'] not in mapped_ids]
            
            if not unmapped:
                self.stdout.write(self.style.SUCCESS('\n✓ All PagerDuty users are mapped'))
                return
            
            self.stdout.write(self.style.WARNING(f'\nFound {len(unmapped)} unmapped user(s):'))
            self.stdout.write('')
            
            for user in unmapped:
                self.stdout.write(f'  {user["name"]}')
                self.stdout.write(f'    Email: {user["email"]}')
                self.stdout.write(f'    PagerDuty ID: {user["external_user_id"]}')
                
                # Check if local user exists with same email
                if user['email']:
                    local_user = User.objects.filter(email=user['email']).first()
                    if local_user:
                        self.stdout.write(f'    → Can auto-map to: {local_user.get_full_name()}')
                    else:
                        self.stdout.write('    → No local user with matching email')
                
                self.stdout.write('')
            
            self.stdout.write('Run with --auto-map to automatically map users by email')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching users: {str(e)}'))


# Made with Bob