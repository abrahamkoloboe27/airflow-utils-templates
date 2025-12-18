"""
Example DAG demonstrating automatic display of DAG owner and tags in alert templates.

This DAG shows how the alert system automatically extracts and displays:
- DAG owner(s) from default_args
- DAG tags from the DAG definition

No additional configuration is needed - owner and tags are automatically
included in all email and Google Chat alert templates.
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
    """Simulate data extraction with owner and tags visible in alerts."""
    print("Extracting data from source...")
    print(f"DAG Owner: {context['dag'].owner}")
    print(f"DAG Tags: {context['dag'].tags}")
    data = [
        {"id": 1, "name": "Item A", "value": 100},
        {"id": 2, "name": "Item B", "value": 200},
        {"id": 3, "name": "Item C", "value": 300},
    ]
    print(f"Extracted {len(data)} records")
    return data


def process_data(**context):
    """Process the extracted data."""
    print("Processing data...")
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')
    
    # Apply processing
    processed = [
        {
            **item,
            "processed": True,
            "value_doubled": item["value"] * 2
        }
        for item in data
    ]
    
    print(f"Processed {len(processed)} records")
    return processed


def validate_data(**context):
    """Validate the processed data."""
    print("Validating data...")
    ti = context['ti']
    data = ti.xcom_pull(task_ids='process')
    
    # Validate all items
    for item in data:
        if not item.get('processed'):
            raise ValueError(f"Item {item['id']} was not processed correctly!")
    
    print(f"Validated {len(data)} records successfully")


# Configure callbacks - owner and tags will be automatically included in alerts
callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['abklb27@gmail.com'],  # Replace with your email
    corporate_name='Data Engineering Team',
    gchat_connection_id='google_chat_alert', 
    success_message='Pipeline completed successfully with all validations passed.'
)

# DAG configuration with specific owner and tags
default_args = {
    'owner': 'data_engineer_team',  # This will appear in alerts
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    **callbacks  # Attach alert callbacks
}

with DAG(
    'example_dag_owner_tags',
    default_args=default_args,
    description='Example showing automatic owner and tags display in alerts',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['example', 'owner-tags', 'alerts', 'data-engineering', 'production'],  # These will appear in alerts
) as dag:
    
    # Start task
    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting pipeline with owner and tags tracking..."',
    )
    
    # Extract task
    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        provide_context=True,
    )
    
    # Process task
    process = PythonOperator(
        task_id='process',
        python_callable=process_data,
        provide_context=True,
    )
    
    # Validate task
    validate = PythonOperator(
        task_id='validate',
        python_callable=validate_data,
        provide_context=True,
    )
    
    # End task
    end = BashOperator(
        task_id='end',
        bash_command='echo "Pipeline completed! Check alerts for owner and tags."',
    )
    
    # Define task dependencies
    start >> extract >> process >> validate >> end


"""
When you run this DAG, the alert emails and Google Chat messages will automatically show:

Email Alert Example:
-------------------
DAG: example_dag_owner_tags
Task: validate
Owner | Propriétaire: data_engineer_team
Tags | Étiquettes: example, owner-tags, alerts, data-engineering, production
Date d'exécution: 2024-01-15 10:30:00
...

Google Chat Alert Example:
--------------------------
📅 Date d'exécution: 2024-01-15 10:30:00
✅ Statut: Succès
🔍 Tâche: validate
👤 Owner: data_engineer_team
🏷️ Tags: example, owner-tags, alerts, data-engineering, production
...

Key Points:
-----------
1. Owner is automatically extracted from default_args['owner']
2. Tags are automatically extracted from the DAG tags list
3. No additional configuration needed in get_callbacks()
4. Works with all alert types: success, retry, failure
5. Works with both task-level and DAG-level alerts
6. Backward compatible - existing DAGs work without changes
"""
