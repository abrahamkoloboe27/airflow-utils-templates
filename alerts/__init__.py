"""
Airflow alerts package providing modular email and Google Chat notifications.
"""
import os
from typing import Dict, Callable, Optional, Any


def get_callbacks(
    email_enabled: bool = True,
    google_chat_enabled: bool = True,
    email_recipients: Optional[list] = None,
    corporate_name: Optional[str] = None,
    success_message: Optional[str] = None,
    **overrides
) -> Dict[str, Optional[Callable]]:
    """
    Get a dictionary of callback functions for Airflow DAG/task notifications.
    
    This function provides a simple API to get all three callback functions
    (success, retry, failure) configured and ready to use in DAG default_args.
    
    Args:
        email_enabled: Enable email notifications (default: True)
        google_chat_enabled: Enable Google Chat notifications (default: True)
        email_recipients: List of email addresses (overrides Airflow Variable)
        corporate_name: Corporate name for email footer (overrides Airflow Variable)
        success_message: Custom success message for email
        **overrides: Additional override parameters for callbacks
        
    Returns:
        Dict with keys: on_success_callback, on_retry_callback, on_failure_callback
        
    Example:
        from alerts import get_callbacks
        
        default_args = {
            'owner': 'airflow',
            'retries': 2,
            **get_callbacks(email_recipients=['team@example.com'])
        }
    """
    callbacks = {
        'on_success_callback': None,
        'on_retry_callback': None,
        'on_failure_callback': None,
    }
    
    # Import modules only if needed
    if email_enabled:
        from alerts.email import success_callback as email_success
        from alerts.email import retry_callback as email_retry
        from alerts.email import failure_callback as email_failure
        
        # Create wrapper functions with configuration
        callbacks['on_success_callback'] = lambda context: email_success(
            context,
            email_recipients=email_recipients,
            corporate_name=corporate_name,
            success_message=success_message,
            **overrides
        )
        callbacks['on_retry_callback'] = lambda context: email_retry(
            context,
            email_recipients=email_recipients,
            corporate_name=corporate_name,
            **overrides
        )
        callbacks['on_failure_callback'] = lambda context: email_failure(
            context,
            email_recipients=email_recipients,
            corporate_name=corporate_name,
            **overrides
        )
    
    if google_chat_enabled:
        from alerts.google_chat import success_callback as gchat_success
        from alerts.google_chat import retry_callback as gchat_retry
        from alerts.google_chat import failure_callback as gchat_failure
        
        # Chain callbacks if email is also enabled
        if email_enabled:
            original_success = callbacks['on_success_callback']
            original_retry = callbacks['on_retry_callback']
            original_failure = callbacks['on_failure_callback']
            
            callbacks['on_success_callback'] = lambda context: (
                original_success(context), gchat_success(context, **overrides)
            )
            callbacks['on_retry_callback'] = lambda context: (
                original_retry(context), gchat_retry(context, **overrides)
            )
            callbacks['on_failure_callback'] = lambda context: (
                original_failure(context), gchat_failure(context, **overrides)
            )
        else:
            callbacks['on_success_callback'] = lambda context: gchat_success(context, **overrides)
            callbacks['on_retry_callback'] = lambda context: gchat_retry(context, **overrides)
            callbacks['on_failure_callback'] = lambda context: gchat_failure(context, **overrides)
    
    return callbacks


__all__ = ['get_callbacks']
