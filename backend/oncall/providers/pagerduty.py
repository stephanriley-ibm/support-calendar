"""
PagerDuty provider implementation for on-call schedule syncing.

This module provides integration with PagerDuty's REST API v2 using
the official pagerduty Python library.
"""

from pagerduty import APISession
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from .base import BaseOnCallProvider


class PagerDutyProvider(BaseOnCallProvider):
    """
    PagerDuty on-call scheduling provider implementation.
    
    Uses the official pagerduty Python library to fetch on-call shifts
    and user data from PagerDuty API v2.
    """
    
    def __init__(self, config: Dict):
        """Initialize PagerDuty provider with API session."""
        super().__init__(config)
        self.session = APISession(self.config['api_token'])
    
    def validate_config(self) -> Tuple[bool, str]:
        """
        Validate PagerDuty configuration.
        
        Required config keys:
        - api_token: PagerDuty API token
        
        Optional config keys:
        - schedule_ids: List of schedule IDs to sync
        """
        required_keys = ['api_token']
        
        for key in required_keys:
            if key not in self.config:
                return False, f"Missing required config key: {key}"
        
        if not self.config['api_token']:
            return False, "API token cannot be empty"
        
        return True, ""
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to PagerDuty API.
        
        Makes a simple API call to verify credentials work.
        """
        try:
            # Try to fetch one user to test connection
            list(self.session.iter_all('users', params={'limit': 1}))
            return True, "Connection successful"
        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or 'Unauthorized' in error_msg:
                return False, "Authentication failed - invalid API token"
            elif '403' in error_msg or 'Forbidden' in error_msg:
                return False, "Access forbidden - check API token permissions"
            else:
                return False, f"Connection error: {error_msg}"
    
    def fetch_schedules(self) -> List[Dict]:
        """
        Fetch all schedules from PagerDuty.
        
        Returns list of schedules with id, name, description, and timezone.
        """
        schedules = []
        
        try:
            for schedule in self.session.iter_all('schedules'):
                schedules.append({
                    'id': schedule['id'],
                    'name': schedule['name'],
                    'description': schedule.get('description', ''),
                    'timezone': schedule.get('time_zone', 'UTC'),
                })
        except Exception as e:
            print(f"Error fetching schedules: {e}")
        
        return schedules
    
    def fetch_shifts(
        self,
        schedule_ids: List[str],
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Fetch on-call shifts from PagerDuty schedules.
        
        Args:
            schedule_ids: List of PagerDuty schedule IDs
            start_date: Start date for fetching shifts
            end_date: End date for fetching shifts
        
        Returns:
            List of shift dicts with user assignments and times
        """
        shifts = []
        
        for schedule_id in schedule_ids:
            try:
                schedule_shifts = self._fetch_schedule_shifts(
                    schedule_id,
                    start_date,
                    end_date
                )
                shifts.extend(schedule_shifts)
            except Exception as e:
                # Log error but continue with other schedules
                print(f"Error fetching shifts for schedule {schedule_id}: {e}")
                continue
        
        return shifts
    
    def _fetch_schedule_shifts(
        self,
        schedule_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Fetch shifts for a single schedule.
        
        Internal method that handles date formatting and parsing.
        """
        shifts = []
        
        # Format dates for PagerDuty API (ISO 8601 with timezone)
        since = start_date.isoformat() + 'T00:00:00Z'
        until = end_date.isoformat() + 'T23:59:59Z'
        
        try:
            # Fetch schedule with rendered entries
            schedule = self.session.rget(
                f'/schedules/{schedule_id}',
                params={
                    'since': since,
                    'until': until,
                    'time_zone': 'UTC',
                }
            )
            
            schedule_name = schedule.get('name', '')
            final_schedule = schedule.get('final_schedule', {})
            rendered_schedule_entries = final_schedule.get('rendered_schedule_entries', [])
            
            for entry in rendered_schedule_entries:
                # Parse datetimes
                start_dt = self._parse_datetime(entry['start'])
                end_dt = self._parse_datetime(entry['end'])
                
                # Determine shift type based on schedule name and date
                shift_type = self._determine_shift_type(schedule_name, start_dt)
                
                shifts.append({
                    'external_shift_id': entry['id'],
                    'external_schedule_id': schedule_id,
                    'external_user_id': entry['user']['id'],
                    'start_datetime': start_dt,
                    'end_datetime': end_dt,
                    'shift_type': shift_type,
                    'metadata': {
                        'user_name': entry['user']['summary'],
                        'user_email': entry['user'].get('email', ''),
                        'schedule_name': schedule_name,
                        'pagerduty_entry': entry,
                    }
                })
        
        except Exception as e:
            print(f"Error in _fetch_schedule_shifts for {schedule_id}: {e}")
            raise
        
        return shifts
    
    def fetch_users(self) -> List[Dict]:
        """
        Fetch all users from PagerDuty.
        
        Returns list of users with id, email, name, and metadata.
        """
        users = []
        
        try:
            for user in self.session.iter_all('users'):
                users.append({
                    'external_user_id': user['id'],
                    'email': user.get('email', ''),
                    'name': user.get('name', ''),
                    'metadata': {
                        'role': user.get('role', ''),
                        'time_zone': user.get('time_zone', ''),
                        'job_title': user.get('job_title', ''),
                    }
                })
        except Exception as e:
            print(f"Error fetching users: {e}")
        
        return users
    
    def get_user_by_id(self, external_user_id: str) -> Optional[Dict]:
        """
        Fetch specific user from PagerDuty by ID.
        
        Args:
            external_user_id: PagerDuty user ID
        
        Returns:
            User dict or None if not found
        """
        try:
            user = self.session.rget(f'/users/{external_user_id}')
            
            return {
                'external_user_id': user['id'],
                'email': user.get('email', ''),
                'name': user.get('name', ''),
                'metadata': {
                    'role': user.get('role', ''),
                    'time_zone': user.get('time_zone', ''),
                    'job_title': user.get('job_title', ''),
                }
            }
        except Exception as e:
            if '404' in str(e) or 'Not Found' in str(e):
                return None
            print(f"Error fetching user {external_user_id}: {e}")
            return None
    
    def _parse_datetime(self, dt_string: str) -> datetime:
        """
        Parse PagerDuty datetime string to Python datetime.
        
        PagerDuty returns ISO 8601 format with 'Z' suffix for UTC.
        
        Args:
            dt_string: ISO 8601 datetime string
        
        Returns:
            datetime object with UTC timezone
        """
        # Replace 'Z' with '+00:00' for Python's fromisoformat
        if dt_string.endswith('Z'):
            dt_string = dt_string[:-1] + '+00:00'
        
        return datetime.fromisoformat(dt_string)
    
    def _determine_shift_type(self, schedule_name: str, start_datetime: datetime) -> str:
        """
        Determine local shift type from PagerDuty schedule name and start time.
        
        Maps PagerDuty schedules to local shift types based on:
        - Schedule name (Primary vs Secondary)
        - Day of week (Saturday vs Sunday)
        
        Args:
            schedule_name: Name of PagerDuty schedule
            start_datetime: Shift start datetime
        
        Returns:
            Local shift type string
        """
        # Check if it's a Primary or Secondary schedule
        is_primary = 'primary' in schedule_name.lower()
        
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = start_datetime.weekday()
        
        # Weekend shifts
        if day_of_week == 5:  # Saturday
            return 'early_primary' if is_primary else 'early_secondary'
        elif day_of_week == 6:  # Sunday
            return 'late_primary' if is_primary else 'late_secondary'
        else:
            # Weekday shift - default to secondary
            return 'secondary'


# Made with Bob