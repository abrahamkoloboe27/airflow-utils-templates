"""
Example DAG demonstrating granular callback control.

This example shows how to use get_granular_callbacks to specify exactly
which events (success, retry, failure) trigger alerts.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from alerts import get_granular_callbacks


# Example 1: Only send alerts on failure and retry (not on success)
callbacks_errors_only = get_granular_callbacks(
    on_success=False,
    on_retry=True,
    on_failure=True,
    email_enabled=True,
    google_chat_enabled=False,
    email_recipients=['ops-team@example.com'],
    corporate_name='My Company',
    logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    **callbacks_errors_only  # Only failure and retry alerts will be sent
}


def task_that_may_fail():
    """Sample task that might fail."""
    import random
    if random.random() > 0.7:
        raise Exception("Random failure for testing retry/failure alerts")
    print("Task succeeded!")
    return "Success - but no alert will be sent!"


with DAG(
    'example_dag_granular_callbacks',
    default_args=default_args,
    description='Example DAG with granular callback control - only errors trigger alerts',
    schedule_interval=None,
    catchup=False,
    tags=['example', 'granular', 'alerts'],
) as dag:
    
    # This task will send alerts only on retry or failure, NOT on success
    error_sensitive_task = PythonOperator(
        task_id='error_sensitive_task',
        python_callable=task_that_may_fail,
    )
    
    # Example of a critical task that should only alert on failure (no retry alerts)
    critical_callbacks = get_granular_callbacks(
        on_success=False,
        on_retry=False,
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=False,
        email_recipients=['critical-team@example.com'],
        corporate_name='My Company'
    )
    
    def critical_task():
        """Critical task - only alerts on final failure."""
        print("Critical task executed")
        return "Done"
    
    critical_task_op = PythonOperator(
        task_id='critical_task',
        python_callable=critical_task,
        on_failure_callback=critical_callbacks['on_failure_callback'],
    )
    
    error_sensitive_task >> critical_task_op
