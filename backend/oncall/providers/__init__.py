"""
On-call provider integrations.

This package contains provider implementations for syncing on-call schedules
from external systems like PagerDuty, Opsgenie, etc.
"""

from .base import BaseOnCallProvider
from .pagerduty import PagerDutyProvider


def get_provider_instance(provider_model):
    """
    Factory function to get provider instance based on provider type.
    
    Args:
        provider_model: OnCallProvider model instance
    
    Returns:
        Provider instance (subclass of BaseOnCallProvider)
    
    Raises:
        ValueError: If provider type is not supported
    """
    provider_classes = {
        'pagerduty': PagerDutyProvider,
        # Add more providers here as they're implemented
        # 'opsgenie': OpsgenieProvider,
        # 'custom': CustomProvider,
    }
    
    provider_class = provider_classes.get(provider_model.provider_type)
    if not provider_class:
        raise ValueError(f"Unsupported provider type: {provider_model.provider_type}")
    
    return provider_class(provider_model.config)


__all__ = [
    'BaseOnCallProvider',
    'PagerDutyProvider',
    'get_provider_instance',
]

# Made with Bob
