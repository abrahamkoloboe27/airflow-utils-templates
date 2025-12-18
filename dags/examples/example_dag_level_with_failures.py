"""
Example DAG demonstrating DAG-level alerts with task failures.

This example shows how DAG-level failure alerts include detailed information
about which tasks failed and a complete summary of all task states.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from alerts import get_callbacks


def successful_task_1(**context):
    """A task that always succeeds."""
    print("Task 1 executing...")
    import time
    time.sleep(1)
    print("Task 1 completed successfully!")
    return "success"


def successful_task_2(**context):
    """Another task that always succeeds."""
    print("Task 2 executing...")
    import time
    time.sleep(2)
    print("Task 2 completed successfully!")
    return "success"


def flaky_task(**context):
    """A task that might fail on first attempt."""
    ti = context['task_instance']
    try_number = ti.try_number
    
    print(f"Flaky task - Attempt {try_number}")
    
    # Fail on first attempt, succeed on retry
    if try_number == 1:
        print("First attempt - simulating failure...")
        raise Exception("Simulated transient error: Connection timeout")
    
    print("Task succeeded on retry!")
    return "success"


def successful_task_3(**context):
    """Another successful task."""
    print("Task 3 executing...")
    import time
    time.sleep(1)
    print("Task 3 completed successfully!")
    return "success"


def critical_task(**context):
    """A task that sometimes fails even after retries."""
    ti = context['task_instance']
    try_number = ti.try_number
    
    print(f"Critical task - Attempt {try_number}")
    
    # This task has a 70% chance of ultimate failure
    # Uncomment the next lines to test failure scenario
    # if random.random() < 0.7:
    #     raise Exception("Critical error: Data validation failed")
    
    print("Critical task completed!")
    return "success"


# Configure DAG-level callbacks with granular control
# Only send alerts on failure (not on success) to reduce noise
from alerts import get_granular_callbacks

# IMPORTANT: DAG-level callbacks must be passed to DAG constructor, not default_args!
dag_callbacks = get_granular_callbacks(
    on_success=True,  # Send success alert with full summary
    on_failure=True,  # Send failure alert with detailed error info
    on_retry=False,   # Don't send retry alerts (DAG-level doesn't support retry callbacks)
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['abklb27@gmail.com'],
    corporate_name='My Company',
    alert_level='dag',  # DAG-level alerts with task summary
    logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
)

# DAG configuration - DO NOT include DAG-level callbacks in default_args
# default_args apply to tasks, not the DAG itself
default_args = {
    'owner': 'ops_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'example_dag_level_with_failures',
    default_args=default_args,
    description='Pipeline with potential failures - demonstrates DAG-level failure alerts',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['example', 'dag-level', 'alerts', 'failures'],
    # Attach DAG-level callbacks directly to DAG, not in default_args
    on_success_callback=dag_callbacks['on_success_callback'],
    on_failure_callback=dag_callbacks['on_failure_callback'],
) as dag:
    
    # Start task
    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting pipeline with potential failures..."',
    )
    
    # Successful tasks in parallel
    task1 = PythonOperator(
        task_id='successful_task_1',
        python_callable=successful_task_1,
        provide_context=True,
    )
    
    task2 = PythonOperator(
        task_id='successful_task_2',
        python_callable=successful_task_2,
        provide_context=True,
    )
    
    # Flaky task that needs retry
    flaky = PythonOperator(
        task_id='flaky_task_with_retry',
        python_callable=flaky_task,
        provide_context=True,
    )
    
    # Another successful task
    task3 = PythonOperator(
        task_id='successful_task_3',
        python_callable=successful_task_3,
        provide_context=True,
    )
    
    # Critical task (uncomment failure in function to test)
    critical = PythonOperator(
        task_id='critical_validation',
        python_callable=critical_task,
        provide_context=True,
    )
    
    # End task
    end = BashOperator(
        task_id='end',
        bash_command='echo "Pipeline execution completed!"',
    )
    
    # Define task dependencies - parallel execution where possible
    start >> [task1, task2]
    [task1, task2] >> flaky
    flaky >> task3 >> critical >> end


# Additional example: DAG-level alerts with only failure notifications
# This configuration only sends an alert if the DAG fails, not on success
dag_callbacks_failure_only = get_granular_callbacks(
    on_success=False,  # No alert on success
    on_failure=True,   # Only alert on failure with full details
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['critical-alerts@example.com'],
    corporate_name='My Company',
    alert_level='dag'
)

with DAG(
    'example_dag_level_critical_only',
    default_args={
        'owner': 'ops_team',
        'depends_on_past': False,
        'start_date': datetime(2024, 1, 1),
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    },
    description='Only alerts on DAG failure - silent on success',
    schedule_interval=None,
    catchup=False,
    tags=['example', 'dag-level', 'alerts', 'critical-only'],
    # Attach DAG-level callbacks directly to DAG, not in default_args
    on_failure_callback=dag_callbacks_failure_only['on_failure_callback'],
) as dag_critical:
    
    t1 = BashOperator(
        task_id='task1',
        bash_command='echo "Task 1"',
    )
    
    t2 = BashOperator(
        task_id='task2',
        bash_command='echo "Task 2"',
    )
    
    t1 >> t2
