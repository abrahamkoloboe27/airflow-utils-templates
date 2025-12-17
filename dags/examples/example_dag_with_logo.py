"""
Example DAG demonstrating logo support in alert templates.

This example shows how to use custom logos in email and Google Chat alerts.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from alerts import get_callbacks


# Get callbacks with custom logo
callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=False,  # Set to True if you have Google Chat configured
    email_recipients=['your-email@example.com'],
    corporate_name='My Company',
    logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png',
    success_message='Pipeline completed successfully with custom logo!'
)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    **callbacks
}


def sample_success_task():
    """Sample task that succeeds."""
    print("Task executed successfully!")
    return "Success with logo!"


with DAG(
    'example_dag_with_logo',
    default_args=default_args,
    description='Example DAG with custom logo in alerts',
    schedule_interval=None,
    catchup=False,
    tags=['example', 'logo', 'alerts'],
) as dag:
    
    # Task that will succeed and trigger success callback with logo
    success_task = PythonOperator(
        task_id='task_with_logo',
        python_callable=sample_success_task,
    )
    
    # Simple bash task
    bash_task = BashOperator(
        task_id='echo_task',
        bash_command='echo "Alert templates now support custom logos!"',
    )
    
    success_task >> bash_task
