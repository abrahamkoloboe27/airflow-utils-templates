"""
Example DAG demonstrating successful execution with alert callbacks.

This DAG simulates a simple ETL pipeline that completes successfully.
It demonstrates how to use the alert module to send notifications.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Add alerts package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from alerts import get_callbacks


def extract_data(**context):
    """Simulate data extraction."""
    print("Extracting data from source...")
    data = [
        {"id": 1, "name": "Product A", "price": 100},
        {"id": 2, "name": "Product B", "price": 200},
        {"id": 3, "name": "Product C", "price": 300},
    ]
    print(f"Extracted {len(data)} records")
    return data


def transform_data(**context):
    """Simulate data transformation."""
    print("Transforming data...")
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')
    
    # Apply transformations
    transformed = [
        {
            **item,
            "price_with_tax": item["price"] * 1.2,
            "discount_price": item["price"] * 0.9
        }
        for item in data
    ]
    
    print(f"Transformed {len(transformed)} records")
    return transformed


def load_data(**context):
    """Simulate data loading."""
    print("Loading data to destination...")
    ti = context['ti']
    data = ti.xcom_pull(task_ids='transform')
    
    # Simulate loading
    for item in data:
        print(f"Loading: {item}")
    
    print(f"Successfully loaded {len(data)} records")


# Configure callbacks with custom settings
# You can also set email_recipients=['your-email@example.com'] to receive real notifications
callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['abklb27@gmail.com'],  # Uncomment to override
    corporate_name='My Company',
    success_message='ETL pipeline completed successfully with all data processed.'
)

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    **callbacks  # Attach alert callbacks
}

with DAG(
    'example_etl_success',
    default_args=default_args,
    description='Example ETL pipeline with successful execution',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['example', 'etl', 'alerts'],
) as dag:
    
    # Start task
    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting ETL pipeline..."',
    )
    
    # Extract task
    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        provide_context=True,
    )
    
    # Transform task
    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        provide_context=True,
    )
    
    # Load task
    load = PythonOperator(
        task_id='load',
        python_callable=load_data,
        provide_context=True,
    )
    
    # End task
    end = BashOperator(
        task_id='end',
        bash_command='echo "ETL pipeline completed successfully!"',
    )
    
    # Define task dependencies
    start >> extract >> transform >> load >> end
