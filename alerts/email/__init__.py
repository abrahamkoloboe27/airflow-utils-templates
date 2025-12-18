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
    corporate_name: Optional[str] = None,
    logo_url: Optional[str] = None
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

    # Get logo URL
    if logo_url:
        config['logo_url'] = logo_url
    else:
        config['logo_url'] = os.environ.get('AIRFLOW_ALERT_LOGO_URL')
        if not config['logo_url']:
            try:
                from airflow.models import Variable
                config['logo_url'] = Variable.get('alert_logo_url', default_var=None)
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
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send success email notification.

    Args:
        context: Airflow task context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        success_message: Custom success message (optional)
        logo_url: URL of logo/image to display at top of email (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional, defaults to 'smtp_default')
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp

        config = _get_config(context, email_recipients, corporate_name, logo_url)

        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date'].strftime('%Y-%m-%d %H:%M:%S')
        start_date = context['task_instance'].start_date
        end_date = context['task_instance'].end_date
        
        # Extract owner and tags
        dag_owner = getattr(context['dag'], 'owner', 'N/A')
        dag_tags = getattr(context['dag'], 'tags', [])

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
            'logo_url': config.get('logo_url'),
            'year': datetime.now().year,
            'owner': dag_owner,
            'tags': dag_tags,
            **kwargs
        }

        # Render template
        env = _get_jinja_env()
        template = env.get_template('success.html')
        html_content = template.render(**template_vars)

        # Send email with optional custom connection
        send_kwargs = {
            'to': config['email_recipients'],
            'subject': f"DAG {dag_id} - Exécution Réussie",
            'html_content': html_content
        }
        if smtp_connection_id:
            send_kwargs['conn_id'] = smtp_connection_id

        send_email_smtp(**send_kwargs)

        logging.info(f"Success email sent for DAG {dag_id}")

    except Exception as e:
        # Log full exception with traceback to aid debugging (e.g., connection refused)
        logging.exception(f"Failed to send success email: {str(e)}")


def retry_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send retry email notification.

    Args:
        context: Airflow task context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        logo_url: URL of logo/image to display at top of email (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional, defaults to 'smtp_default')
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp

        config = _get_config(context, email_recipients, corporate_name, logo_url)

        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date'].strftime('%Y-%m-%d %H:%M:%S')
        exception = context.get('exception', 'Unknown error')
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        next_retry_datetime = context.get('next_retry_datetime')
        
        # Extract owner and tags
        dag_owner = getattr(context['dag'], 'owner', 'N/A')
        dag_tags = getattr(context['dag'], 'tags', [])

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
            'logo_url': config.get('logo_url'),
            'year': datetime.now().year,
            'owner': dag_owner,
            'tags': dag_tags,
            **kwargs
        }

        # Render template
        env = _get_jinja_env()
        template = env.get_template('retry.html')
        html_content = template.render(**template_vars)

        # Send email with optional custom connection
        send_kwargs = {
            'to': config['email_recipients'],
            'subject': f"DAG {dag_id} - Retentative {try_number}/{max_tries}",
            'html_content': html_content
        }
        if smtp_connection_id:
            send_kwargs['conn_id'] = smtp_connection_id

        send_email_smtp(**send_kwargs)

        logging.info(f"Retry email sent for DAG {dag_id}")

    except Exception as e:
        # Log full exception with traceback to aid debugging (e.g., connection refused)
        logging.exception(f"Failed to send retry email: {str(e)}")


def failure_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send failure email notification.

    Args:
        context: Airflow task context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        logo_url: URL of logo/image to display at top of email (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional, defaults to 'smtp_default')
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp

        config = _get_config(context, email_recipients, corporate_name, logo_url)

        # Extract context data
        dag_id = context['dag'].dag_id
        task_id = context['task_instance'].task_id
        execution_date = context['execution_date'].strftime('%Y-%m-%d %H:%M:%S')
        exception = context.get('exception', 'Unknown error')
        try_number = context['task_instance'].try_number
        max_tries = context['task'].retries + 1
        
        # Extract owner and tags
        dag_owner = getattr(context['dag'], 'owner', 'N/A')
        dag_tags = getattr(context['dag'], 'tags', [])

        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'task_id': task_id,
            'execution_date': execution_date,
            'exception': str(exception),
            'try_number': try_number,
            'max_tries': max_tries,
            'corporate': config['corporate_name'],
            'logo_url': config.get('logo_url'),
            'year': datetime.now().year,
            'owner': dag_owner,
            'tags': dag_tags,
            **kwargs
        }

        # Render template
        env = _get_jinja_env()
        template = env.get_template('failure.html')
        html_content = template.render(**template_vars)

        # Send email with optional custom connection
        send_kwargs = {
            'to': config['email_recipients'],
            'subject': f"DAG {dag_id} - Échec Critique ⚠️",
            'html_content': html_content
        }
        if smtp_connection_id:
            send_kwargs['conn_id'] = smtp_connection_id

        send_email_smtp(**send_kwargs)

        logging.info(f"Failure email sent for DAG {dag_id}")

    except Exception as e:
        # Log full exception with traceback to aid debugging (e.g., connection refused)
        logging.exception(f"Failed to send failure email: {str(e)}")


def _get_dag_run_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract summary information from a DAG run.

    Returns:
        Dict with task statistics and details
    """
    try:
        dag_run = context.get('dag_run')
        if not dag_run:
            return {}

        # Get all task instances for this DAG run
        task_instances = dag_run.get_task_instances()

        summary = {
            'total_tasks': len(task_instances),
            'success_count': 0,
            'failed_count': 0,
            'retry_count': 0,
            'running_count': 0,
            'skipped_count': 0,
            'tasks': []
        }

        for ti in task_instances:
            task_info = {
                'task_id': ti.task_id,
                'state': str(ti.state),
                'start_date': ti.start_date,
                'end_date': ti.end_date,
                'duration': None,
                'try_number': ti.try_number,
            }

            # Calculate duration
            if ti.start_date and ti.end_date:
                task_info['duration'] = _format_execution_time(ti.start_date, ti.end_date)

            # Count by state
            state_lower = str(ti.state).lower()
            if state_lower == 'success':
                summary['success_count'] += 1
            elif state_lower == 'failed':
                summary['failed_count'] += 1
                # Get exception info if available
                task_info['error'] = str(ti.log_url) if hasattr(ti, 'log_url') else 'Error details in logs'
            elif state_lower == 'running':
                summary['running_count'] += 1
            elif state_lower == 'skipped':
                summary['skipped_count'] += 1
            elif state_lower in ['up_for_retry', 'up_for_reschedule']:
                summary['retry_count'] += 1

            summary['tasks'].append(task_info)

        return summary

    except Exception as e:
        logging.error(f"Error getting DAG run summary: {e}")
        return {}


def dag_success_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    success_message: Optional[str] = None,
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send DAG-level success email notification with task summary.

    Args:
        context: Airflow DAG context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        success_message: Custom success message (optional)
        logo_url: URL of logo/image to display at top of email (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional, defaults to 'smtp_default')
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp

        config = _get_config(context, email_recipients, corporate_name, logo_url)

        # Extract context data
        dag_id = context['dag'].dag_id
        dag_run = context.get('dag_run')
        execution_date = dag_run.execution_date.strftime('%Y-%m-%d %H:%M:%S') if dag_run else 'N/A'
        start_date = dag_run.start_date if dag_run else None
        end_date = dag_run.end_date if dag_run else datetime.now()
        
        # Extract owner and tags
        dag_owner = getattr(context['dag'], 'owner', 'N/A')
        dag_tags = getattr(context['dag'], 'tags', [])

        # Get task summary
        summary = _get_dag_run_summary(context)

        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'execution_date': execution_date,
            'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else 'N/A',
            'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else 'N/A',
            'execution_time': _format_execution_time(start_date, end_date) if start_date else 'N/A',
            'message': success_message or '',
            'corporate': config['corporate_name'],
            'logo_url': config.get('logo_url'),
            'year': datetime.now().year,
            'owner': dag_owner,
            'tags': dag_tags,
            'summary': summary,
            **kwargs
        }

        # Render template
        env = _get_jinja_env()
        template = env.get_template('dag_success.html')
        html_content = template.render(**template_vars)

        # Send email with optional custom connection
        send_kwargs = {
            'to': config['email_recipients'],
            'subject': f"DAG {dag_id} - Exécution Complète Réussie",
            'html_content': html_content
        }
        if smtp_connection_id:
            send_kwargs['conn_id'] = smtp_connection_id

        send_email_smtp(**send_kwargs)

        logging.info(f"DAG-level success email sent for DAG {dag_id}")

    except Exception as e:
        logging.exception(f"Failed to send DAG-level success email: {str(e)}")


def dag_failure_callback(
    context: Dict[str, Any],
    email_recipients: Optional[List[str]] = None,
    corporate_name: Optional[str] = None,
    logo_url: Optional[str] = None,
    smtp_connection_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Send DAG-level failure email notification with failed task details.

    Args:
        context: Airflow DAG context
        email_recipients: List of email addresses (optional)
        corporate_name: Corporate name for footer (optional)
        logo_url: URL of logo/image to display at top of email (optional)
        smtp_connection_id: Airflow connection ID for SMTP (optional, defaults to 'smtp_default')
        **kwargs: Additional template variables
    """
    try:
        from airflow.utils.email import send_email_smtp

        config = _get_config(context, email_recipients, corporate_name, logo_url)

        # Extract context data
        dag_id = context['dag'].dag_id
        dag_run = context.get('dag_run')
        execution_date = dag_run.execution_date.strftime('%Y-%m-%d %H:%M:%S') if dag_run else 'N/A'
        start_date = dag_run.start_date if dag_run else None
        end_date = dag_run.end_date if dag_run else datetime.now()
        
        # Extract owner and tags
        dag_owner = getattr(context['dag'], 'owner', 'N/A')
        dag_tags = getattr(context['dag'], 'tags', [])

        # Get task summary
        summary = _get_dag_run_summary(context)

        # Extract failed tasks with details
        failed_tasks = [t for t in summary.get('tasks', []) if t['state'].lower() == 'failed']

        # Prepare template variables
        template_vars = {
            'dag_id': dag_id,
            'execution_date': execution_date,
            'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else 'N/A',
            'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else 'N/A',
            'execution_time': _format_execution_time(start_date, end_date) if start_date else 'N/A',
            'corporate': config['corporate_name'],
            'logo_url': config.get('logo_url'),
            'year': datetime.now().year,
            'owner': dag_owner,
            'tags': dag_tags,
            'summary': summary,
            'failed_tasks': failed_tasks,
            **kwargs
        }

        # Render template
        env = _get_jinja_env()
        template = env.get_template('dag_failure.html')
        html_content = template.render(**template_vars)

        # Send email with optional custom connection
        send_kwargs = {
            'to': config['email_recipients'],
            'subject': f"DAG {dag_id} - Échec du DAG ⚠️",
            'html_content': html_content
        }
        if smtp_connection_id:
            send_kwargs['conn_id'] = smtp_connection_id

        send_email_smtp(**send_kwargs)

        logging.info(f"DAG-level failure email sent for DAG {dag_id}")

    except Exception as e:
        logging.exception(f"Failed to send DAG-level failure email: {str(e)}")


__all__ = ['success_callback', 'retry_callback', 'failure_callback',
           'dag_success_callback', 'dag_failure_callback']
