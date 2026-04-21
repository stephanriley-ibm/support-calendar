# Generated manually to ensure correct migration order

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oncall', '0004_alter_oncallshift_day_of_week'),
    ]

    operations = [
        # Step 1: Create the new models first
        migrations.CreateModel(
            name='OnCallProvider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Provider name (e.g., 'Production PagerDuty')", max_length=100)),
                ('provider_type', models.CharField(choices=[('pagerduty', 'PagerDuty'), ('opsgenie', 'Opsgenie'), ('custom', 'Custom Provider')], help_text='Type of provider', max_length=50)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this provider is active')),
                ('is_primary', models.BooleanField(default=False, help_text='Primary provider for sync')),
                ('config', models.JSONField(default=dict, help_text='Provider configuration (API keys, schedule IDs, etc.)')),
                ('auto_sync_enabled', models.BooleanField(default=True, help_text='Enable automatic sync')),
                ('sync_frequency_hours', models.IntegerField(default=24, help_text='Sync frequency in hours')),
                ('sync_lookback_days', models.IntegerField(default=7, help_text='Days to look back when syncing')),
                ('sync_lookahead_days', models.IntegerField(default=90, help_text='Days to look ahead when syncing')),
                ('last_sync_at', models.DateTimeField(blank=True, help_text='Last successful sync time', null=True)),
                ('last_sync_status', models.CharField(default='never', help_text='Status of last sync', max_length=20)),
                ('last_sync_error', models.TextField(blank=True, help_text='Error message from last sync')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'oncall_providers',
                'ordering': ['-is_primary', 'name'],
            },
        ),
        
        # Step 2: Add provider field to OnCallShift (nullable first)
        migrations.AddField(
            model_name='oncallshift',
            name='provider',
            field=models.ForeignKey(blank=True, help_text='External provider this shift was synced from', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='synced_shifts', to='oncall.oncallprovider'),
        ),
        
        # Step 3: Add other fields to OnCallShift
        migrations.AddField(
            model_name='oncallshift',
            name='external_shift_id',
            field=models.CharField(blank=True, help_text='ID in external provider system', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='oncallshift',
            name='external_schedule_id',
            field=models.CharField(blank=True, help_text='Schedule ID in external provider system', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='oncallshift',
            name='synced_at',
            field=models.DateTimeField(blank=True, help_text='When this shift was last synced from provider', null=True),
        ),
        migrations.AddField(
            model_name='oncallshift',
            name='is_synced',
            field=models.BooleanField(default=False, help_text='Whether this shift came from an external provider'),
        ),
        migrations.AddField(
            model_name='oncallshift',
            name='sync_metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Additional metadata from provider'),
        ),
        
        # Step 4: Create ExternalUserMapping model
        migrations.CreateModel(
            name='ExternalUserMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_user_id', models.CharField(help_text='User ID in external provider', max_length=100)),
                ('external_email', models.EmailField(help_text='User email in external provider', max_length=254)),
                ('external_name', models.CharField(help_text='User name in external provider', max_length=200)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this mapping is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('local_user', models.ForeignKey(help_text='Local user this maps to', on_delete=django.db.models.deletion.CASCADE, related_name='external_mappings', to=settings.AUTH_USER_MODEL)),
                ('provider', models.ForeignKey(help_text='Provider this mapping belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='user_mappings', to='oncall.oncallprovider')),
            ],
            options={
                'db_table': 'external_user_mappings',
                'unique_together': {('provider', 'external_user_id')},
            },
        ),
        
        # Step 5: Create ProviderSyncLog model
        migrations.CreateModel(
            name='ProviderSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_type', models.CharField(help_text="Type of sync (scheduled, manual, initial)", max_length=50)),
                ('status', models.CharField(choices=[('started', 'Started'), ('success', 'Success'), ('partial', 'Partial Success'), ('failed', 'Failed')], help_text='Sync status', max_length=20)),
                ('start_time', models.DateTimeField(auto_now_add=True, help_text='Sync start time')),
                ('end_time', models.DateTimeField(blank=True, help_text='Sync end time', null=True)),
                ('shifts_fetched', models.IntegerField(default=0, help_text='Number of shifts fetched from provider')),
                ('shifts_created', models.IntegerField(default=0, help_text='Number of new shifts created')),
                ('shifts_updated', models.IntegerField(default=0, help_text='Number of existing shifts updated')),
                ('shifts_skipped', models.IntegerField(default=0, help_text='Number of shifts skipped')),
                ('error_message', models.TextField(blank=True, help_text='Error message if sync failed')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Additional sync details')),
                ('provider', models.ForeignKey(help_text='Provider that was synced', on_delete=django.db.models.deletion.CASCADE, related_name='sync_logs', to='oncall.oncallprovider')),
            ],
            options={
                'db_table': 'provider_sync_logs',
                'ordering': ['-start_time'],
            },
        ),
        
        # Step 6: Add indexes (after all fields exist)
        migrations.AddIndex(
            model_name='oncallshift',
            index=models.Index(fields=['provider', 'external_shift_id'], name='oncall_shif_provide_711de0_idx'),
        ),
        migrations.AddIndex(
            model_name='oncallshift',
            index=models.Index(fields=['is_synced', 'shift_date'], name='oncall_shif_is_sync_dc0768_idx'),
        ),
        migrations.AddIndex(
            model_name='externalusermapping',
            index=models.Index(fields=['provider', 'external_user_id'], name='external_us_provide_a6b4bb_idx'),
        ),
        migrations.AddIndex(
            model_name='externalusermapping',
            index=models.Index(fields=['local_user'], name='external_us_local_u_19272a_idx'),
        ),
        migrations.AddIndex(
            model_name='providersynclog',
            index=models.Index(fields=['provider', '-start_time'], name='provider_sy_provide_b25fdb_idx'),
        ),
        migrations.AddIndex(
            model_name='providersynclog',
            index=models.Index(fields=['status'], name='provider_sy_status_961b1c_idx'),
        ),
        
        # Step 7: Add constraint (after all fields and indexes exist)
        migrations.AddConstraint(
            model_name='oncallshift',
            constraint=models.UniqueConstraint(condition=models.Q(('provider__isnull', False), ('external_shift_id__isnull', False)), fields=('provider', 'external_shift_id'), name='unique_provider_shift'),
        ),
    ]

# Made with Bob
