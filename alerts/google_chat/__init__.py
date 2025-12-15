"""
Google Chat alert module for Airflow notifications.

Provides callback functions to send Google Chat card notifications for DAG/task events:
- success_callback: Sent when a task succeeds
- retry_callback: Sent when a task is being retried
- failure_callback: Sent when a task fails after all retries
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import requests


# Get template directory
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "google_chat"


def _get_jinja_env():
    """Get Jinja2 environment for template rendering."""
    return Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def _get_webhook_url(context: Dict[str, Any], connection_name: Optional[str] = None) -> str:
    """
    Get Google Chat webhook URL from Airflow connection or environment.
    
    Priority: function parameter > environment variable > Airflow Connection
    """
    # Try environment variable
    webhook_url = os.environ.get('AIRFLOW_GCHAT_WEBHOOK_URL')
    
    if not webhook_url:
        # Try Airflow Connection
        try:
            from airflow.hooks.base_hook import BaseHook
            conn_name = connection_name or os.environ.get('AIRFLOW_GCHAT_CONNECTION', 'google_chat_alert')
            conn = BaseHook.get_connection(conn_name)
            webhook_url = conn.host
        except Exception as e:
            logging.error(f"Could not get Google Chat webhook URL: {e}")
            raise ValueError("Google Chat webhook URL not configured")
    
    # Ensure URL has protocol
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"
    
    return webhook_url


def _format_execution_time(start_date, end_date) -> str:
    """Format execution time as human-readable string."""
    if not start_date or not end_date:
        return "Non disponible"
    
    # Handle timezone differences
    if hasattr(start_date, 'tzinfo') and start_date.tzinfo:
        if hasattr(end_date, 'tzinfo') and not end_date.tzinfo:
            end_date = end_date.replace(tzinfo=start_date.tzinfo)
    else:
        if hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            start_date = start_date.replace(tzinfo=None)
        if hasattr(end_date, 'tzinfo') and end_date.tzinfo:
            end_date = end_date.replace(tzinfo=None)
    
    execution_time = (end_date - start_date).total_seconds()
    hours, remainder = divmod(execution_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"


def _send_card(webhook_url: str, card_body: dict, thread_id: str) -> None:
    """Send a card to Google Chat with threading support."""
    # Add thread parameters to URL
    if '?' not in webhook_url:
        thread_ref = f"?threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
    else:
        thread_ref = f"&threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
    
    full_url = f"{webhook_url}{thread_ref}"
    
    # Send request with timeout to prevent indefinite hangs
    response = requests.post(full_url, json=card_body, timeout=30)
    response.raise_for_status()


def success_callback(
    context: Dict[str, Any],
    connection_name: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send success Google Chat notification.
    
    Args:
        context: Airflow task context
        connection_name: Name of Airflow connection (optional)
        **kwargs: Additional template variables
    """
    try:
        webhook_url = _get_webhook_url(context, connection_name)
        
        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date']
        execution_date_str = execution_date.strftime('%Y-%m-%d %H:%M:%S')
        execution_date_short = execution_date.strftime('%Y-%m-%d')
        start_date = context['task_instance'].start_date
        end_date = context['task_instance'].end_date
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        dag_description = getattr(context['dag'], 'description', None) or 'Aucune description disponible'
        
        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date_str,
            'execution_date_short': execution_date_short,
            'start_date': start_date.strftime('%H:%M:%S') if start_date else None,
            'end_date': end_date.strftime('%H:%M:%S') if end_date else None,
            'execution_time_str': _format_execution_time(start_date, end_date),
            'try_number': try_number,
            'max_tries': max_tries,
            'dag_description': dag_description,
            **kwargs
        }
        
        # Render template
        env = _get_jinja_env()
        template = env.get_template('success.json.j2')
        card_json = template.render(**template_vars)
        card_body = json.loads(card_json)
        
        # Create thread ID
        thread_id = f"{dag_id}_{execution_date.strftime('%Y%m%d')}"
        
        # Send card
        _send_card(webhook_url, card_body, thread_id)
        
        logging.info(f"Success Google Chat alert sent for DAG {dag_id}")
        
    except Exception as e:
        logging.error(f"Failed to send Google Chat success alert: {str(e)}")


def retry_callback(
    context: Dict[str, Any],
    connection_name: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send retry Google Chat notification.
    
    Args:
        context: Airflow task context
        connection_name: Name of Airflow connection (optional)
        **kwargs: Additional template variables
    """
    try:
        webhook_url = _get_webhook_url(context, connection_name)
        
        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date']
        execution_date_str = execution_date.strftime('%Y-%m-%d %H:%M:%S')
        execution_date_short = execution_date.strftime('%Y-%m-%d')
        start_date = context['task_instance'].start_date
        exception = context.get('exception', 'Unknown error')
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        next_retry_datetime = context.get('next_retry_datetime')
        dag_description = getattr(context['dag'], 'description', None) or 'Aucune description disponible'
        
        # Handle timezone for current time
        if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            current_time = datetime.now(start_date.tzinfo)
        else:
            current_time = datetime.now()
            if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
        
        # Format exception message
        exception_msg = str(exception)
        if len(exception_msg) > 500:
            exception_msg = exception_msg[:497] + "..."
        
        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date_str,
            'execution_date_short': execution_date_short,
            'start_date': start_date.strftime('%H:%M:%S') if start_date else None,
            'failure_time': current_time.strftime('%H:%M:%S'),
            'execution_time_str': _format_execution_time(start_date, current_time),
            'try_number': try_number,
            'max_tries': max_tries,
            'next_retry_datetime': next_retry_datetime.strftime('%H:%M:%S') if next_retry_datetime else None,
            'exception_msg': exception_msg,
            'dag_description': dag_description,
            **kwargs
        }
        
        # Render template
        env = _get_jinja_env()
        template = env.get_template('retry.json.j2')
        card_json = template.render(**template_vars)
        card_body = json.loads(card_json)
        
        # Create thread ID
        thread_id = f"{dag_id}_{execution_date.strftime('%Y%m%d')}"
        
        # Send card
        _send_card(webhook_url, card_body, thread_id)
        
        logging.info(f"Retry Google Chat alert sent for DAG {dag_id}")
        
    except Exception as e:
        logging.error(f"Failed to send Google Chat retry alert: {str(e)}")


def failure_callback(
    context: Dict[str, Any],
    connection_name: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send failure Google Chat notification.
    
    Args:
        context: Airflow task context
        connection_name: Name of Airflow connection (optional)
        **kwargs: Additional template variables
    """
    try:
        webhook_url = _get_webhook_url(context, connection_name)
        
        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date']
        execution_date_str = execution_date.strftime('%Y-%m-%d %H:%M:%S')
        execution_date_short = execution_date.strftime('%Y-%m-%d')
        start_date = context['task_instance'].start_date
        exception = context.get('exception', 'Unknown error')
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        dag_description = getattr(context['dag'], 'description', None) or 'Aucune description disponible'
        
        # Handle timezone for current time
        if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            current_time = datetime.now(start_date.tzinfo)
        else:
            current_time = datetime.now()
            if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
        
        # Format exception message
        exception_msg = str(exception)
        if len(exception_msg) > 500:
            exception_msg = exception_msg[:497] + "..."
        
        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date_str,
            'execution_date_short': execution_date_short,
            'start_date': start_date.strftime('%H:%M:%S') if start_date else None,
            'failure_time': current_time.strftime('%H:%M:%S'),
            'execution_time_str': _format_execution_time(start_date, current_time),
            'try_number': try_number,
            'max_tries': max_tries,
            'exception_msg': exception_msg,
            'dag_description': dag_description,
            **kwargs
        }
        
        # Render template
        env = _get_jinja_env()
        template = env.get_template('failure.json.j2')
        card_json = template.render(**template_vars)
        card_body = json.loads(card_json)
        
        # Create thread ID
        thread_id = f"{dag_id}_{execution_date.strftime('%Y%m%d')}"
        
        # Send card
        _send_card(webhook_url, card_body, thread_id)
        
        logging.info(f"Failure Google Chat alert sent for DAG {dag_id}")
        
    except Exception as e:
        logging.error(f"Failed to send Google Chat failure alert: {str(e)}")


__all__ = ['success_callback', 'retry_callback', 'failure_callback']
