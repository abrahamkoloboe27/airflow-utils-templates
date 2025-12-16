"""
Email alert module for Airflow notifications.

Provides callback functions to send HTML email notifications for DAG/task events:
- success_callback: Sent when a task succeeds
- retry_callback: Sent when a task is being retried
- failure_callback: Sent when a task fails after all retries
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


# Get template directory
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "email"


def _get_jinja_env():
    """Get Jinja2 environment for template rendering."""
    return Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def _get_config(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get configuration from Airflow Variables, environment, or parameters.
    
    Priority: function parameters > environment variables > Airflow Variables
    """
    config = {}
    
    # Get email recipients
    if email_recipients:
        config['email_recipients'] = email_recipients
    else:
        # Try environment variable
        env_emails = os.environ.get('AIRFLOW_ALERT_EMAIL_RECIPIENTS')
        if env_emails:
            config['email_recipients'] = [e.strip() for e in env_emails.split(',')]
        else:
            # Try Airflow Variable
            try:
                from airflow.models import Variable
                var_emails = Variable.get('alert_email_recipients', default_var=None)
                if var_emails:
                    config['email_recipients'] = [e.strip() for e in var_emails.split(',')]
                else:
                    config['email_recipients'] = ['airflow@example.com']
            except Exception as e:
                logging.warning(f"Could not get email recipients from Variable: {e}")
                config['email_recipients'] = ['airflow@example.com']
    
    # Get corporate name
    if corporate_name:
        config['corporate_name'] = corporate_name
    else:
        config['corporate_name'] = os.environ.get(
            'AIRFLOW_ALERT_CORPORATE_NAME',
            'Your Company'
        )
        try:
            from airflow.models import Variable
            config['corporate_name'] = Variable.get(
                'alert_corporate_name',
                default_var=config['corporate_name']
            )
        except Exception:
            pass
    
    return config


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


def success_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    success_message: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send success email notification.
    
    Args:
        context: Airflow task context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        success_message: Custom success message (optional)
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp
        
        config = _get_config(context, email_recipients, corporate_name)
        
        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date'].strftime('%Y-%m-%d %H:%M:%S')
        start_date = context['task_instance'].start_date
        end_date = context['task_instance'].end_date
        
        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date,
            'start_date': start_date.strftime('%H:%M:%S') if start_date else None,
            'end_date': end_date.strftime('%H:%M:%S') if end_date else None,
            'execution_time': _format_execution_time(start_date, end_date),
            'message': success_message or '',
            'corporate': config['corporate_name'],
            'year': datetime.now().year,
            **kwargs
        }
        
        # Render template
        env = _get_jinja_env()
        template = env.get_template('success.html')
        html_content = template.render(**template_vars)
        
        # Send email
        send_email_smtp(
            to=config['email_recipients'],
            subject=f"{config['corporate_name']} DAG {dag_id} - Exécution Réussie",
            html_content=html_content
        )
        
        logging.info(f"Success email sent for DAG {dag_id}")
        
    except Exception as e:
        # Log full exception with traceback to aid debugging (e.g., connection refused)
        logging.exception(f"Failed to send success email: {str(e)}")


def retry_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send retry email notification.
    
    Args:
        context: Airflow task context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp
        
        config = _get_config(context, email_recipients, corporate_name)
        
        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date'].strftime('%Y-%m-%d %H:%M:%S')
        exception = context.get('exception', 'Unknown error')
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        next_retry_datetime = context.get('next_retry_datetime')
        
        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date,
            'exception': str(exception),
            'try_number': try_number,
            'max_tries': max_tries,
            'next_retry_datetime': next_retry_datetime.strftime('%Y-%m-%d %H:%M:%S') if next_retry_datetime else None,
            'corporate': config['corporate_name'],
            'year': datetime.now().year,
            **kwargs
        }
        
        # Render template
        env = _get_jinja_env()
        template = env.get_template('retry.html')
        html_content = template.render(**template_vars)
        
        # Send email
        send_email_smtp(
            to=config['email_recipients'],
            subject=f"{config['corporate_name']} DAG {dag_id} - Retentative {try_number}/{max_tries}",
            html_content=html_content
        )
        
        logging.info(f"Retry email sent for DAG {dag_id}")
        
    except Exception as e:
        # Log full exception with traceback to aid debugging (e.g., connection refused)
        logging.exception(f"Failed to send retry email: {str(e)}")


def failure_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send failure email notification.
    
    Args:
        context: Airflow task context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp
        
        config = _get_config(context, email_recipients, corporate_name)
        
        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date'].strftime('%Y-%m-%d %H:%M:%S')
        exception = context.get('exception', 'Unknown error')
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        
        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date,
            'exception': str(exception),
            'try_number': try_number,
            'max_tries': max_tries,
            'corporate': config['corporate_name'],
            'year': datetime.now().year,
            **kwargs
        }
        
        # Render template
        env = _get_jinja_env()
        template = env.get_template('failure.html')
        html_content = template.render(**template_vars)
        
        # Send email
        send_email_smtp(
            to=config['email_recipients'],
            subject=f"{config['corporate_name']} DAG {dag_id} - Échec Critique ⚠️",
            html_content=html_content
        )
        
        logging.info(f"Failure email sent for DAG {dag_id}")
        
    except Exception as e:
        # Log full exception with traceback to aid debugging (e.g., connection refused)
        logging.exception(f"Failed to send failure email: {str(e)}")


__all__ = ['success_callback', 'retry_callback', 'failure_callback']
