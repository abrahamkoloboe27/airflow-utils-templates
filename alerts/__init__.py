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
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    gchat_connection_id: Optional[str] = None,
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
        logo_url: URL of logo/image to display in alerts (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional)
        gchat_connection_id: Airflow connection ID for Google Chat (optional)
        **overrides: Additional override parameters for callbacks
        
    Returns:
        Dict with keys: on_success_callback, on_retry_callback, on_failure_callback
        
    Example:
        from alerts import get_callbacks
        
        default_args = {
            'owner': 'airflow',
            'retries': 2,
            **get_callbacks(
                email_recipients=['team@example.com'],
                logo_url='https://example.com/logo.png'
            )
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
            logo_url=logo_url,
            smtp_connection_id=smtp_connection_id,
            **overrides
        )
        callbacks['on_retry_callback'] = lambda context: email_retry(
            context,
            email_recipients=email_recipients,
            corporate_name=corporate_name,
            logo_url=logo_url,
            smtp_connection_id=smtp_connection_id,
            **overrides
        )
        callbacks['on_failure_callback'] = lambda context: email_failure(
            context,
            email_recipients=email_recipients,
            corporate_name=corporate_name,
            logo_url=logo_url,
            smtp_connection_id=smtp_connection_id,
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
            
            # Use default arguments to capture current values
            callbacks['on_success_callback'] = lambda context, os=original_success, gs=gchat_success, gc=gchat_connection_id, lu=logo_url, ov=overrides: (
                os(context), gs(context, connection_name=gc, logo_url=lu, **ov)
            )
            callbacks['on_retry_callback'] = lambda context, ort=original_retry, gr=gchat_retry, gc=gchat_connection_id, lu=logo_url, ov=overrides: (
                ort(context), gr(context, connection_name=gc, logo_url=lu, **ov)
            )
            callbacks['on_failure_callback'] = lambda context, of=original_failure, gf=gchat_failure, gc=gchat_connection_id, lu=logo_url, ov=overrides: (
                of(context), gf(context, connection_name=gc, logo_url=lu, **ov)
            )
        else:
            callbacks['on_success_callback'] = lambda context, gs=gchat_success, gc=gchat_connection_id, lu=logo_url, ov=overrides: gs(context, connection_name=gc, logo_url=lu, **ov)
            callbacks['on_retry_callback'] = lambda context, gr=gchat_retry, gc=gchat_connection_id, lu=logo_url, ov=overrides: gr(context, connection_name=gc, logo_url=lu, **ov)
            callbacks['on_failure_callback'] = lambda context, gf=gchat_failure, gc=gchat_connection_id, lu=logo_url, ov=overrides: gf(context, connection_name=gc, logo_url=lu, **ov)
    
    return callbacks


def get_granular_callbacks(
    on_success: bool = False,
    on_retry: bool = False,
    on_failure: bool = False,
    email_enabled: bool = True,
    google_chat_enabled: bool = True,
    email_recipients: Optional[list] = None,
    corporate_name: Optional[str] = None,
    success_message: Optional[str] = None,
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    gchat_connection_id: Optional[str] = None,
    **overrides
) -> Dict[str, Optional[Callable]]:
    """
    Get a dictionary of callback functions with granular control over which events trigger alerts.
    
    This function allows you to specify exactly which events (success, retry, failure) should 
    trigger email and/or Google Chat notifications. By default, no callbacks are enabled unless
    explicitly specified.
    
    Args:
        on_success: Enable callbacks for successful task completion (default: False)
        on_retry: Enable callbacks for task retries (default: False)
        on_failure: Enable callbacks for task failures (default: False)
        email_enabled: Enable email notifications for selected events (default: True)
        google_chat_enabled: Enable Google Chat notifications for selected events (default: True)
        email_recipients: List of email addresses (overrides Airflow Variable)
        corporate_name: Corporate name for email footer (overrides Airflow Variable)
        success_message: Custom success message for email
        logo_url: URL of logo/image to display in alerts (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional)
        gchat_connection_id: Airflow connection ID for Google Chat (optional)
        **overrides: Additional override parameters for callbacks
        
    Returns:
        Dict with keys: on_success_callback, on_retry_callback, on_failure_callback
        
    Example:
        from alerts import get_granular_callbacks
        
        # Only send alerts on failure and retry
        default_args = {
            'owner': 'airflow',
            'retries': 2,
            **get_granular_callbacks(
                on_failure=True,
                on_retry=True,
                email_recipients=['team@example.com'],
                logo_url='https://example.com/logo.png'
            )
        }
        
        # Only send alerts on success, email only
        default_args = {
            'owner': 'airflow',
            **get_granular_callbacks(
                on_success=True,
                email_enabled=True,
                google_chat_enabled=False,
                email_recipients=['team@example.com']
            )
        }
    """
    callbacks = {
        'on_success_callback': None,
        'on_retry_callback': None,
        'on_failure_callback': None,
    }
    
    # Build callback functions based on granular selections
    def _build_callback(event_type: str):
        """Helper to build chained callback for a specific event type."""
        event_callback = None
        
        if email_enabled:
            if event_type == 'success':
                from alerts.email import success_callback as email_success
                # Use default arguments to capture current values
                event_callback = lambda context, cb=email_success, er=email_recipients, cn=corporate_name, sm=success_message, lu=logo_url, sc=smtp_connection_id, ov=overrides: cb(
                    context,
                    email_recipients=er,
                    corporate_name=cn,
                    success_message=sm,
                    logo_url=lu,
                    smtp_connection_id=sc,
                    **ov
                )
            elif event_type == 'retry':
                from alerts.email import retry_callback as email_retry
                event_callback = lambda context, cb=email_retry, er=email_recipients, cn=corporate_name, lu=logo_url, sc=smtp_connection_id, ov=overrides: cb(
                    context,
                    email_recipients=er,
                    corporate_name=cn,
                    logo_url=lu,
                    smtp_connection_id=sc,
                    **ov
                )
            elif event_type == 'failure':
                from alerts.email import failure_callback as email_failure
                event_callback = lambda context, cb=email_failure, er=email_recipients, cn=corporate_name, lu=logo_url, sc=smtp_connection_id, ov=overrides: cb(
                    context,
                    email_recipients=er,
                    corporate_name=cn,
                    logo_url=lu,
                    smtp_connection_id=sc,
                    **ov
                )
        
        if google_chat_enabled:
            gchat_cb = None
            if event_type == 'success':
                from alerts.google_chat import success_callback as gchat_success
                gchat_cb = lambda context, cb=gchat_success, gc=gchat_connection_id, lu=logo_url, ov=overrides: cb(context, connection_name=gc, logo_url=lu, **ov)
            elif event_type == 'retry':
                from alerts.google_chat import retry_callback as gchat_retry
                gchat_cb = lambda context, cb=gchat_retry, gc=gchat_connection_id, lu=logo_url, ov=overrides: cb(context, connection_name=gc, logo_url=lu, **ov)
            elif event_type == 'failure':
                from alerts.google_chat import failure_callback as gchat_failure
                gchat_cb = lambda context, cb=gchat_failure, gc=gchat_connection_id, lu=logo_url, ov=overrides: cb(context, connection_name=gc, logo_url=lu, **ov)
            
            # Chain with email if both are enabled
            if gchat_cb:
                if event_callback:
                    original_callback = event_callback
                    event_callback = lambda context, oc=original_callback, gc=gchat_cb: (oc(context), gc(context))
                else:
                    event_callback = gchat_cb
        
        return event_callback
    
    # Only create callbacks for selected events
    if on_success:
        callbacks['on_success_callback'] = _build_callback('success')
    
    if on_retry:
        callbacks['on_retry_callback'] = _build_callback('retry')
    
    if on_failure:
        callbacks['on_failure_callback'] = _build_callback('failure')
    
    return callbacks


__all__ = ['get_callbacks', 'get_granular_callbacks']
