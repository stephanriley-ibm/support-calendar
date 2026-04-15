# On-Call Provider Integration Architecture

**Version:** 1.0  
**Last Updated:** 2026-04-15  
**Status:** Design Phase

## 🎯 Overview

This document outlines the architecture for integrating external on-call scheduling providers (starting with PagerDuty) in a flexible, provider-agnostic way that allows easy migration to different providers in the future.

## 🏗️ Architecture Principles

### 1. Provider Abstraction
- **Abstract Base Class**: All providers implement a common interface
- **Plugin Architecture**: Providers are self-contained modules
- **Configuration-Driven**: Provider selection via environment variables
- **Graceful Degradation**: System works without external providers

### 2. Data Ownership
- **Local Database is Source of Truth**: External data is synced TO local database
- **Immutable Sync Records**: Track what was synced and when
- **Conflict Resolution**: Local changes take precedence over external
- **Audit Trail**: Full history of sync operations

### 3. Flexibility
- **Easy Provider Switching**: Change provider via configuration
- **Multiple Providers**: Support multiple providers simultaneously (future)
- **Hybrid Mode**: Mix external and manual shifts
- **Migration Path**: Tools to migrate between providers

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Calendar Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           On-Call Management Layer                    │  │
│  │  - OnCallShift Model (local source of truth)         │  │
│  │  - DayInLieu Model (auto-generated)                  │  │
│  │  - Manual shift creation                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ▲                                    │
│                          │                                    │
│  ┌──────────────────────┴───────────────────────────────┐  │
│  │         Provider Integration Layer                    │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │   BaseOnCallProvider (Abstract)              │   │  │
│  │  │   - fetch_schedules()                        │   │  │
│  │  │   - fetch_shifts()                           │   │  │
│  │  │   - fetch_users()                            │   │  │
│  │  │   - validate_connection()                    │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                          ▲                             │  │
│  │                          │                             │  │
│  │         ┌────────────────┼────────────────┐          │  │
│  │         │                │                 │          │  │
│  │  ┌──────┴──────┐  ┌─────┴──────┐  ┌──────┴──────┐  │  │
│  │  │  PagerDuty  │  │   Opsgenie │  │   Custom    │  │  │
│  │  │   Provider  │  │   Provider │  │   Provider  │  │  │
│  │  └─────────────┘  └────────────┘  └─────────────┘  │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────┘  │
│                          ▲                                    │
│                          │                                    │
│  ┌──────────────────────┴───────────────────────────────┐  │
│  │         Sync Service Layer                            │  │
│  │  - ProviderSyncService                                │  │
│  │  - User mapping                                       │  │
│  │  - Conflict detection                                 │  │
│  │  - Sync history tracking                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────┘
```

## 🗄️ Database Schema Changes

### New Models

#### 1. OnCallProvider
Stores configuration for external on-call providers.

```python
class OnCallProvider(models.Model):
    """Configuration for external on-call scheduling providers"""
    
    PROVIDER_TYPES = [
        ('pagerduty', 'PagerDuty'),
        ('opsgenie', 'Opsgenie'),
        ('custom', 'Custom Provider'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "Production PagerDuty"
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)  # Primary provider for sync
    
    # Configuration (encrypted JSON)
    config = models.JSONField(default=dict)  # API keys, URLs, etc.
    
    # Sync settings
    auto_sync_enabled = models.BooleanField(default=True)
    sync_frequency_hours = models.IntegerField(default=24)
    sync_lookback_days = models.IntegerField(default=7)
    sync_lookahead_days = models.IntegerField(default=90)
    
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, default='never')
    last_sync_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 2. ExternalUserMapping
Maps external provider users to local users.

```python
class ExternalUserMapping(models.Model):
    """Maps external provider users to local application users"""
    
    provider = models.ForeignKey(OnCallProvider, on_delete=models.CASCADE)
    external_user_id = models.CharField(max_length=100)
    external_email = models.EmailField()
    external_name = models.CharField(max_length=200)
    
    local_user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['provider', 'external_user_id']
```

#### 3. ProviderSyncLog
Tracks all sync operations for audit and debugging.

```python
class ProviderSyncLog(models.Model):
    """Log of provider sync operations"""
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]
    
    provider = models.ForeignKey(OnCallProvider, on_delete=models.CASCADE)
    sync_type = models.CharField(max_length=50)  # 'scheduled', 'manual', 'initial'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    shifts_fetched = models.IntegerField(default=0)
    shifts_created = models.IntegerField(default=0)
    shifts_updated = models.IntegerField(default=0)
    shifts_skipped = models.IntegerField(default=0)
    
    error_message = models.TextField(blank=True)
    details = models.JSONField(default=dict)  # Additional sync details
```

#### 4. Update OnCallShift Model
Add fields to track external provider information.

```python
class OnCallShift(models.Model):
    # ... existing fields ...
    
    # New provider tracking fields
    provider = models.ForeignKey(
        'OnCallProvider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='synced_shifts',
        help_text="External provider this shift was synced from"
    )
    external_shift_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID in external provider system"
    )
    external_schedule_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Schedule ID in external provider system"
    )
    synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this shift was last synced from provider"
    )
    is_synced = models.BooleanField(
        default=False,
        help_text="Whether this shift came from an external provider"
    )
    sync_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata from provider"
    )
    
    class Meta:
        # ... existing meta ...
        unique_together = [
            ['provider', 'external_shift_id'],  # Prevent duplicate syncs
        ]
```

## 🔌 Provider Interface

### Base Provider Class

```python
# backend/oncall/providers/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date

class BaseOnCallProvider(ABC):
    """
    Abstract base class for on-call scheduling providers.
    All provider implementations must inherit from this class.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration dict
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> Tuple[bool, str]:
        """
        Validate provider configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to provider API.
        
        Returns:
            Tuple of (is_connected, error_message)
        """
        pass
    
    @abstractmethod
    def fetch_schedules(self) -> List[Dict]:
        """
        Fetch all available schedules from provider.
        
        Returns:
            List of schedule dicts with keys:
            - id: External schedule ID
            - name: Schedule name
            - description: Schedule description
            - timezone: Schedule timezone
        """
        pass
    
    @abstractmethod
    def fetch_shifts(
        self,
        schedule_ids: List[str],
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Fetch on-call shifts for specified schedules and date range.
        
        Args:
            schedule_ids: List of external schedule IDs
            start_date: Start date for shift fetch
            end_date: End date for shift fetch
        
        Returns:
            List of shift dicts with keys:
            - external_shift_id: Unique shift ID in provider
            - external_schedule_id: Schedule ID
            - external_user_id: User ID in provider
            - start_datetime: Shift start (datetime)
            - end_datetime: Shift end (datetime)
            - shift_type: Type of shift (if applicable)
            - metadata: Additional provider-specific data
        """
        pass
    
    @abstractmethod
    def fetch_users(self) -> List[Dict]:
        """
        Fetch all users from provider for mapping.
        
        Returns:
            List of user dicts with keys:
            - external_user_id: User ID in provider
            - email: User email
            - name: User full name
            - metadata: Additional user data
        """
        pass
    
    @abstractmethod
    def get_user_by_id(self, external_user_id: str) -> Optional[Dict]:
        """
        Fetch specific user by external ID.
        
        Args:
            external_user_id: User ID in provider system
        
        Returns:
            User dict or None if not found
        """
        pass
    
    def normalize_shift_type(self, provider_shift_data: Dict) -> str:
        """
        Normalize provider-specific shift type to local shift type.
        Override this method if provider has custom shift types.
        
        Args:
            provider_shift_data: Raw shift data from provider
        
        Returns:
            Local shift type string
        """
        # Default implementation - override in subclass
        return 'secondary'  # Default to secondary shift
    
    def calculate_shift_dates(
        self,
        start_datetime: datetime,
        end_datetime: datetime
    ) -> List[date]:
        """
        Calculate all dates covered by a shift.
        Useful for multi-day shifts.
        
        Args:
            start_datetime: Shift start
            end_datetime: Shift end
        
        Returns:
            List of dates covered by shift
        """
        dates = []
        current = start_datetime.date()
        end = end_datetime.date()
        
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
```

## 🔧 PagerDuty Provider Implementation

### PagerDuty Provider Class

```python
# backend/oncall/providers/pagerduty.py

import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from .base import BaseOnCallProvider

class PagerDutyProvider(BaseOnCallProvider):
    """PagerDuty on-call scheduling provider implementation"""
    
    BASE_URL = "https://api.pagerduty.com"
    
    def validate_config(self) -> Tuple[bool, str]:
        """Validate PagerDuty configuration"""
        required_keys = ['api_token']
        
        for key in required_keys:
            if key not in self.config:
                return False, f"Missing required config key: {key}"
        
        if not self.config['api_token']:
            return False, "API token cannot be empty"
        
        return True, ""
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to PagerDuty API"""
        try:
            response = self._make_request('GET', '/users', params={'limit': 1})
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
    
    def fetch_schedules(self) -> List[Dict]:
        """Fetch all schedules from PagerDuty"""
        schedules = []
        offset = 0
        limit = 100
        
        while True:
            response = self._make_request(
                'GET',
                '/schedules',
                params={'offset': offset, 'limit': limit}
            )
            
            for schedule in response.get('schedules', []):
                schedules.append({
                    'id': schedule['id'],
                    'name': schedule['name'],
                    'description': schedule.get('description', ''),
                    'timezone': schedule.get('time_zone', 'UTC'),
                })
            
            if not response.get('more', False):
                break
            
            offset += limit
        
        return schedules
    
    def fetch_shifts(
        self,
        schedule_ids: List[str],
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """Fetch on-call shifts from PagerDuty"""
        shifts = []
        
        for schedule_id in schedule_ids:
            # Format dates for PagerDuty API
            since = start_date.isoformat() + 'T00:00:00Z'
            until = end_date.isoformat() + 'T23:59:59Z'
            
            response = self._make_request(
                'GET',
                f'/schedules/{schedule_id}',
                params={
                    'since': since,
                    'until': until,
                    'time_zone': 'UTC',
                }
            )
            
            schedule = response.get('schedule', {})
            final_schedule = schedule.get('final_schedule', {})
            rendered_schedule_entries = final_schedule.get('rendered_schedule_entries', [])
            
            for entry in rendered_schedule_entries:
                shifts.append({
                    'external_shift_id': entry['id'],
                    'external_schedule_id': schedule_id,
                    'external_user_id': entry['user']['id'],
                    'start_datetime': datetime.fromisoformat(entry['start'].replace('Z', '+00:00')),
                    'end_datetime': datetime.fromisoformat(entry['end'].replace('Z', '+00:00')),
                    'shift_type': self._determine_shift_type(entry),
                    'metadata': {
                        'user_name': entry['user']['summary'],
                        'user_email': entry['user'].get('email', ''),
                        'schedule_name': schedule.get('name', ''),
                    }
                })
        
        return shifts
    
    def fetch_users(self) -> List[Dict]:
        """Fetch all users from PagerDuty"""
        users = []
        offset = 0
        limit = 100
        
        while True:
            response = self._make_request(
                'GET',
                '/users',
                params={'offset': offset, 'limit': limit}
            )
            
            for user in response.get('users', []):
                users.append({
                    'external_user_id': user['id'],
                    'email': user.get('email', ''),
                    'name': user.get('name', ''),
                    'metadata': {
                        'role': user.get('role', ''),
                        'time_zone': user.get('time_zone', ''),
                    }
                })
            
            if not response.get('more', False):
                break
            
            offset += limit
        
        return users
    
    def get_user_by_id(self, external_user_id: str) -> Optional[Dict]:
        """Fetch specific user from PagerDuty"""
        try:
            response = self._make_request('GET', f'/users/{external_user_id}')
            user = response.get('user', {})
            
            return {
                'external_user_id': user['id'],
                'email': user.get('email', ''),
                'name': user.get('name', ''),
                'metadata': {
                    'role': user.get('role', ''),
                    'time_zone': user.get('time_zone', ''),
                }
            }
        except Exception:
            return None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to PagerDuty API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            'Authorization': f"Token token={self.config['api_token']}",
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Content-Type': 'application/json',
        }
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        return response.json()
    
    def _determine_shift_type(self, entry: Dict) -> str:
        """
        Determine local shift type from PagerDuty entry.
        This is a simple implementation - customize based on your needs.
        """
        start = datetime.fromisoformat(entry['start'].replace('Z', '+00:00'))
        
        # Check if weekend
        if start.weekday() in [5, 6]:  # Saturday or Sunday
            # You could add more logic here to determine primary vs secondary
            return 'secondary'
        
        return 'secondary'  # Default
```

## 🔄 Sync Service

### Provider Sync Service

```python
# backend/oncall/services/provider_sync.py

from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from django.db import transaction
from django.utils import timezone
from ..models import (
    OnCallProvider,
    OnCallShift,
    ExternalUserMapping,
    ProviderSyncLog,
)
from ..providers import get_provider_instance
from .days_in_lieu import DaysInLieuGenerator

class ProviderSyncService:
    """Service for syncing on-call shifts from external providers"""
    
    def __init__(self, provider: OnCallProvider):
        self.provider = provider
        self.provider_instance = get_provider_instance(provider)
        self.stats = {
            'fetched': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
        }
    
    def sync_shifts(
        self,
        schedule_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sync_type: str = 'manual'
    ) -> ProviderSyncLog:
        """
        Sync shifts from external provider.
        
        Args:
            schedule_ids: List of external schedule IDs (None = use config)
            start_date: Start date for sync (None = use lookback setting)
            end_date: End date for sync (None = use lookahead setting)
            sync_type: Type of sync ('manual', 'scheduled', 'initial')
        
        Returns:
            ProviderSyncLog instance with sync results
        """
        # Create sync log
        sync_log = ProviderSyncLog.objects.create(
            provider=self.provider,
            sync_type=sync_type,
            status='started',
        )
        
        try:
            # Determine date range
            if not start_date:
                start_date = date.today() - timedelta(days=self.provider.sync_lookback_days)
            if not end_date:
                end_date = date.today() + timedelta(days=self.provider.sync_lookahead_days)
            
            # Get schedule IDs from config if not provided
            if not schedule_ids:
                schedule_ids = self.provider.config.get('schedule_ids', [])
            
            if not schedule_ids:
                raise ValueError("No schedule IDs configured or provided")
            
            # Fetch shifts from provider
            external_shifts = self.provider_instance.fetch_shifts(
                schedule_ids=schedule_ids,
                start_date=start_date,
                end_date=end_date
            )
            
            self.stats['fetched'] = len(external_shifts)
            
            # Process each shift
            for external_shift in external_shifts:
                try:
                    self._process_shift(external_shift)
                except Exception as e:
                    self.stats['errors'].append({
                        'shift_id': external_shift.get('external_shift_id'),
                        'error': str(e)
                    })
            
            # Update sync log
            sync_log.status = 'success' if not self.stats['errors'] else 'partial'
            sync_log.shifts_fetched = self.stats['fetched']
            sync_log.shifts_created = self.stats['created']
            sync_log.shifts_updated = self.stats['updated']
            sync_log.shifts_skipped = self.stats['skipped']
            sync_log.details = self.stats
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            self.stats['errors'].append({'general': str(e)})
        
        finally:
            sync_log.end_time = timezone.now()
            sync_log.save()
            
            # Update provider last sync
            self.provider.last_sync_at = timezone.now()
            self.provider.last_sync_status = sync_log.status
            if sync_log.status == 'failed':
                self.provider.last_sync_error = sync_log.error_message
            else:
                self.provider.last_sync_error = ''
            self.provider.save()
        
        return sync_log
    
    @transaction.atomic
    def _process_shift(self, external_shift: Dict):
        """Process a single external shift"""
        # Map external user to local user
        user_mapping = self._get_or_create_user_mapping(
            external_shift['external_user_id'],
            external_shift.get('metadata', {})
        )
        
        if not user_mapping:
            self.stats['skipped'] += 1
            return
        
        # Check if shift already exists
        existing_shift = OnCallShift.objects.filter(
            provider=self.provider,
            external_shift_id=external_shift['external_shift_id']
        ).first()
        
        # Determine shift dates (handle multi-day shifts)
        shift_dates = self.provider_instance.calculate_shift_dates(
            external_shift['start_datetime'],
            external_shift['end_datetime']
        )
        
        # Create or update shift for each date
        for shift_date in shift_dates:
            shift_data = {
                'shift_date': shift_date,
                'shift_type': external_shift['shift_type'],
                'engineer': user_mapping.local_user,
                'provider': self.provider,
                'external_shift_id': external_shift['external_shift_id'],
                'external_schedule_id': external_shift['external_schedule_id'],
                'synced_at': timezone.now(),
                'is_synced': True,
                'sync_metadata': external_shift.get('metadata', {}),
            }
            
            if existing_shift:
                # Update existing shift
                for key, value in shift_data.items():
                    setattr(existing_shift, key, value)
                existing_shift.save()
                self.stats['updated'] += 1
            else:
                # Create new shift
                shift = OnCallShift.objects.create(**shift_data)
                self.stats['created'] += 1
                
                # Generate days in lieu
                generator = DaysInLieuGenerator()
                generator.generate_for_shift(shift)
    
    def _get_or_create_user_mapping(
        self,
        external_user_id: str,
        metadata: Dict
    ) -> Optional[ExternalUserMapping]:
        """Get or create user mapping for external user"""
        # Try to find existing mapping
        mapping = ExternalUserMapping.objects.filter(
            provider=self.provider,
            external_user_id=external_user_id,
            is_active=True
        ).first()
        
        if mapping:
            return mapping
        
        # Try to auto-map by email
        email = metadata.get('user_email', '')
        if email:
            from users.models import User
            local_user = User.objects.filter(email=email).first()
            
            if local_user:
                mapping = ExternalUserMapping.objects.create(
                    provider=self.provider,
                    external_user_id=external_user_id,
                    external_email=email,
                    external_name=metadata.get('user_name', ''),
                    local_user=local_user,
                    is_active=True
                )
                return mapping
        
        # No mapping found and couldn't auto-create
        return None
```

## 📝 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create database models (OnCallProvider, ExternalUserMapping, ProviderSyncLog)
- [ ] Add migration to update OnCallShift model
- [ ] Create base provider interface
- [ ] Set up provider factory/registry
- [ ] Add provider configuration to environment variables

### Phase 2: PagerDuty Integration (Week 2)
- [ ] Implement PagerDutyProvider class
- [ ] Create provider sync service
- [ ] Add management command for manual sync
- [ ] Test PagerDuty connection and data fetch
- [ ] Implement user mapping logic

### Phase 3: Admin Interface (Week 3)
- [ ] Create provider configuration UI
- [ ] Build user mapping interface
- [ ] Add sync history view
- [ ] Create manual sync trigger
- [ ] Add provider health monitoring

### Phase 4: Automation (Week 4)
- [ ] Set up scheduled sync (Celery task)
- [ ] Add sync error notifications
- [ ] Implement conflict resolution
- [ ] Create sync monitoring dashboard
- [ ] Add provider switching tools

### Phase 5: Testing & Documentation (Week 5)
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Write user documentation
- [ ] Create migration guide
- [ ] UAT deployment

## 🔄 Migration Strategy

### Switching Providers

When switching from PagerDuty to another provider:

1. **Configure New Provider**
   - Add new provider configuration
   - Set as primary provider
   - Keep PagerDuty as secondary (read-only)

2. **Map Users**
   - Create user mappings for new provider
   - Verify all users are mapped

3. **Initial Sync**
   - Run initial sync from new provider
   - Compare with existing data
   - Resolve any conflicts

4. **Transition Period**
   - Run both providers in parallel
   - Monitor for discrepancies
   - Gradually shift trust to new provider

5. **Decommission Old Provider**
   - Disable auto-sync for old provider
   - Mark as inactive
   - Keep historical data for audit

## 🔐 Security Considerations

1. **API Token Storage**
   - Encrypt sensitive config data in database
   - Use Django's encryption utilities
   - Never log API tokens

2. **Rate Limiting**
   - Implement exponential backoff
   - Respect provider rate limits
   - Cache responses when appropriate

3. **Access Control**
   - Only admins can configure providers
   - Audit all provider operations
   - Log all sync activities

## 📊 Monitoring & Alerts

### Key Metrics
- Sync success rate
- Sync duration
- Shifts synced per day
- User mapping coverage
- API error rate

### Alerts
- Sync failures (3 consecutive)
- Unmapped users detected
- API rate limit warnings
- Configuration errors

## 🎯 Success Criteria

- ✅ PagerDuty shifts sync automatically
- ✅ Days-in-lieu generated from synced shifts
- ✅ User mapping works seamlessly
- ✅ Easy to switch providers via configuration
- ✅ No data loss during provider migration
- ✅ System works without external provider
- ✅ Full audit trail of all sync operations

---

**Next Steps:**
1. Review and approve this architecture
2. Begin Phase 1 implementation
3. Set up PagerDuty test account
4. Create initial database migrations