"""
Base provider interface for on-call scheduling systems.

All provider implementations must inherit from BaseOnCallProvider
and implement the required abstract methods.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta


class BaseOnCallProvider(ABC):
    """
    Abstract base class for on-call scheduling providers.
    
    This defines the interface that all provider implementations must follow,
    ensuring consistency and making it easy to swap providers.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration dict containing
                   API keys, URLs, and other settings
        """
        self.config = config
        is_valid, error = self.validate_config()
        if not is_valid:
            raise ValueError(f"Invalid provider configuration: {error}")
    
    @abstractmethod
    def validate_config(self) -> Tuple[bool, str]:
        """
        Validate provider configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message should be empty string
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test connection to provider API.
        
        Returns:
            Tuple of (is_connected, error_message)
            If connected, error_message should be empty string
        """
        pass
    
    @abstractmethod
    def fetch_schedules(self) -> List[Dict]:
        """
        Fetch all available schedules from provider.
        
        Returns:
            List of schedule dicts with keys:
            - id: External schedule ID (string)
            - name: Schedule name (string)
            - description: Schedule description (string)
            - timezone: Schedule timezone (string)
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
            schedule_ids: List of external schedule IDs to fetch
            start_date: Start date for shift fetch (inclusive)
            end_date: End date for shift fetch (inclusive)
        
        Returns:
            List of shift dicts with keys:
            - external_shift_id: Unique shift ID in provider (string)
            - external_schedule_id: Schedule ID (string)
            - external_user_id: User ID in provider (string)
            - start_datetime: Shift start (datetime with timezone)
            - end_datetime: Shift end (datetime with timezone)
            - shift_type: Type of shift if determinable (string, optional)
            - metadata: Additional provider-specific data (dict)
        """
        pass
    
    @abstractmethod
    def fetch_users(self) -> List[Dict]:
        """
        Fetch all users from provider for mapping.
        
        Returns:
            List of user dicts with keys:
            - external_user_id: User ID in provider (string)
            - email: User email (string)
            - name: User full name (string)
            - metadata: Additional user data (dict)
        """
        pass
    
    @abstractmethod
    def get_user_by_id(self, external_user_id: str) -> Optional[Dict]:
        """
        Fetch specific user by external ID.
        
        Args:
            external_user_id: User ID in provider system
        
        Returns:
            User dict with same structure as fetch_users(),
            or None if user not found
        """
        pass
    
    def normalize_shift_type(self, provider_shift_data: Dict) -> str:
        """
        Normalize provider-specific shift type to local shift type.
        
        Override this method in subclass if provider has custom shift types
        or if you need custom logic to determine shift type.
        
        Args:
            provider_shift_data: Raw shift data from provider
        
        Returns:
            Local shift type string (one of: 'early_primary', 'late_primary',
            'secondary', 'early_secondary', 'late_secondary', 'holiday')
        """
        # Default implementation - override in subclass for custom logic
        start_datetime = provider_shift_data.get('start_datetime')
        
        if not start_datetime:
            return 'secondary'  # Default fallback
        
        # Simple logic: determine by day of week
        if start_datetime.weekday() == 5:  # Saturday
            return 'early_primary'
        elif start_datetime.weekday() == 6:  # Sunday
            return 'late_primary'
        else:
            return 'secondary'
    
    def calculate_shift_dates(
        self,
        start_datetime: datetime,
        end_datetime: datetime
    ) -> List[date]:
        """
        Calculate all dates covered by a shift.
        
        Useful for multi-day shifts that span multiple calendar days.
        
        Args:
            start_datetime: Shift start (datetime with timezone)
            end_datetime: Shift end (datetime with timezone)
        
        Returns:
            List of dates covered by shift (sorted)
        """
        dates = []
        current = start_datetime.date()
        end = end_datetime.date()
        
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    def is_weekend_shift(self, shift_date: date) -> bool:
        """
        Check if a date is a weekend (Saturday or Sunday).
        
        Args:
            shift_date: Date to check
        
        Returns:
            True if weekend, False otherwise
        """
        return shift_date.weekday() in [5, 6]  # Saturday=5, Sunday=6
    
    def get_config_value(self, key: str, default=None):
        """
        Safely get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)


# Made with Bob