"""
Example DAG demonstrating DAG-level alerts.

This example shows how to use alert_level='dag' to send a single alert
per DAG execution with a complete summary of all tasks, instead of 
sending individual alerts for each task.
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


def extract_data(**context):
    """Simulate data extraction."""
    print("Extracting data from source...")
    import time
    time.sleep(2)
    print("Data extracted successfully!")
    return {"records": 1000, "source": "database"}


def transform_data(**context):
    """Simulate data transformation."""
    print("Transforming data...")
    import time
    time.sleep(3)
    print("Data transformed successfully!")
    return {"records_transformed": 950, "records_filtered": 50}


def load_data(**context):
    """Simulate data loading."""
    print("Loading data to destination...")
    import time
    time.sleep(2)
    print("Data loaded successfully!")
    return {"records_loaded": 950}


def validate_data(**context):
    """Simulate data validation."""
    print("Validating data quality...")
    checks = {
        "row_count": True,
        "null_check": True,
        "schema_validation": True,
    }
    for check, result in checks.items():
        status = "PASSED" if result else "FAILED"
        print(f"{check}: {status}")
    print("All validations passed!")
    return checks


# Configure DAG-level callbacks
# This will send ONE alert at the end of the DAG execution with a summary
# of all tasks (success count, failure count, duration, etc.)
# IMPORTANT: DAG-level callbacks must be passed to DAG constructor, not default_args!
dag_callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['abklb27@gmail.com'],
    corporate_name='TEST',
    alert_level='dag',  # KEY: This enables DAG-level alerts instead of task-level
    logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png'
)

# DAG configuration - DO NOT include callbacks here for DAG-level alerts
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'example_dag_level_alerts',
    default_args=default_args,
    description='ETL pipeline with DAG-level summary alerts',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['example', 'dag-level', 'alerts', 'etl'],
    # Attach DAG-level callbacks directly to DAG, not in default_args
    on_success_callback=dag_callbacks['on_success_callback'],
    on_failure_callback=dag_callbacks['on_failure_callback'],
) as dag:
    
    # Start task
    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting ETL pipeline..."',
    )
    
    # Extract task
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        provide_context=True,
    )
    
    # Transform task
    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
        provide_context=True,
    )
    
    # Load task
    load = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
        provide_context=True,
    )
    
    # Validate task
    validate = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
    )
    
    # End task
    end = BashOperator(
        task_id='end',
        bash_command='echo "ETL pipeline completed successfully!"',
    )
    
    # Define task dependencies
    start >> extract >> transform >> load >> validate >> end
