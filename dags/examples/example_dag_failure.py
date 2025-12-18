"""
Example DAG demonstrating failure and retry with alert callbacks.

This DAG simulates a pipeline that fails on the first attempts but can succeed
after retries. It demonstrates how to use the alert module for retry and failure notifications.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os
import random

# Add alerts package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from alerts import get_callbacks


def flaky_task(**context):
    """
    A task that fails randomly to demonstrate retry and failure alerts.
    
    On the first attempt, it always fails.
    On subsequent attempts, it has a 50% chance of success.
    """
    ti = context['task_instance']
    try_number = ti.try_number
    
    print(f"Attempt {try_number} of flaky task")
    
    # Always fail on first attempt
    if try_number == 1:
        print("First attempt - simulating failure...")
        raise Exception("Simulated failure: Database connection timeout")
    
    # 50% chance on subsequent attempts
    if random.random() < 0.5:
        print("Random failure - simulating transient error...")
        raise Exception("Simulated failure: Network timeout during data fetch")
    
    print("Task succeeded!")
    return "success"


def guaranteed_failure_task(**context):
    """
    A task that always fails to demonstrate failure alerts.
    Uncomment this task in the DAG to test failure notifications.
    """
    print("This task will always fail...")
    raise Exception("Guaranteed failure: Critical error in data validation")


def data_quality_check(**context):
    """Simulate a data quality check that passes."""
    print("Running data quality checks...")
    
    # Simulate some checks
    checks = {
        "row_count": True,
        "null_check": True,
        "duplicate_check": True,
        "schema_validation": True,
    }
    
    for check, result in checks.items():
        status = "PASSED" if result else "FAILED"
        print(f"{check}: {status}")
    
    print("All quality checks passed!")
    return True


# Configure callbacks
# Set email_enabled and google_chat_enabled based on your setup
callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    gchat_connection_id='google_chat_alert', 
    email_recipients=['abklb27@gmail.com'],  # Uncomment to override
    corporate_name='My Company'
)

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,  # More retries to demonstrate retry alerts
    'retry_delay': timedelta(minutes=1),
    **callbacks  # Attach alert callbacks
}

with DAG(
    'example_etl_with_retries',
    default_args=default_args,
    description='Example pipeline with simulated failures and retries',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['example', 'failure', 'retry', 'alerts'],
) as dag:
    
    # Start task
    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting pipeline with potential failures..."',
    )
    
    # Flaky task that might fail
    flaky = PythonOperator(
        task_id='flaky_extraction',
        python_callable=flaky_task,
        provide_context=True,
    )
    
    # Quality check task
    quality_check = PythonOperator(
        task_id='quality_check',
        python_callable=data_quality_check,
        provide_context=True,
    )
    
    # Uncomment to add a guaranteed failure task
    # guaranteed_failure = PythonOperator(
    #     task_id='guaranteed_failure',
    #     python_callable=guaranteed_failure_task,
    #     provide_context=True,
    # )
    
    # End task
    end = BashOperator(
        task_id='end',
        bash_command='echo "Pipeline completed!"',
    )
    
    # Define task dependencies
    start >> flaky >> quality_check >> end
    # Uncomment to test guaranteed failure:
    # start >> flaky >> quality_check >> guaranteed_failure >> end
