"""
Example DAG demonstrating all new alert features.

This comprehensive example shows:
1. Logo/image support in alerts
2. Granular callback control
3. Custom SMTP and Google Chat connections
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from alerts import get_callbacks, get_granular_callbacks


# Example 1: All features combined - logo + custom connections
callbacks_with_custom_connections = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,  # Set to True if you have Google Chat configured
    email_recipients=['abklb27@gmail.com'],
    corporate_name='Data Engineering Team',
    logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png',
    smtp_connection_id='smtp_default',      # Use specific SMTP connection
    gchat_connection_id='google_chat_alert',       # Use specific GChat connection
    success_message='ETL pipeline completed successfully!'
)


default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    **callbacks_with_custom_connections
}


def extract_data():
    """Extract data from source."""
    print("Extracting data from source...")
    return {"records": 1000, "status": "success"}


def transform_data():
    """Transform extracted data."""
    print("Transforming data...")
    return {"transformed": 1000, "status": "success"}


def load_data():
    """Load data to destination."""
    print("Loading data to destination...")
    return {"loaded": 1000, "status": "success"}


with DAG(
    'example_dag_all_features',
    default_args=default_args,
    description='Comprehensive example showing all new alert features',
    schedule_interval='@daily',
    catchup=False,
    tags=['example', 'comprehensive', 'alerts', 'logo', 'custom-connections'],
) as dag:
    
    # Standard ETL tasks with full alert support
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
    )
    
    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )
    
    load = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
    )
    
    # Example of using granular callbacks on a specific critical task
    # This task only alerts on final failure, not on retries or success
    critical_callbacks = get_granular_callbacks(
        on_success=False,
        on_retry=False,
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=False,
        email_recipients=['critical-alerts@example.com'],
        corporate_name='Data Engineering Team',
        logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png',
        smtp_connection_id='critical_smtp'
    )
    
    def validate_data():
        """Validate loaded data - critical step."""
        print("Validating data integrity...")
        # This is a critical validation step
        return {"validation": "passed"}
    
    validate = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        on_failure_callback=critical_callbacks['on_failure_callback'],
    )
    
    # Example of monitoring task with different alert strategy
    # This task sends alerts on both retry and failure
    monitoring_callbacks = get_granular_callbacks(
        on_success=False,
        on_retry=True,
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=False,
        email_recipients=['ops@example.com'],
        corporate_name='Data Engineering Team'
    )
    
    def monitor_pipeline():
        """Monitor pipeline metrics."""
        print("Monitoring pipeline metrics...")
        return {"status": "healthy"}
    
    monitor = PythonOperator(
        task_id='monitor_pipeline',
        python_callable=monitor_pipeline,
        on_retry_callback=monitoring_callbacks['on_retry_callback'],
        on_failure_callback=monitoring_callbacks['on_failure_callback'],
    )
    
    # Success notification task
    success_notify = BashOperator(
        task_id='success_notification',
        bash_command='echo "Pipeline completed successfully with custom logo and alerts!"',
    )
    
    # Pipeline flow
    extract >> transform >> load >> validate >> monitor >> success_notify


# Example 2: Different DAG with different configuration
with DAG(
    'example_dag_marketing_alerts',
    default_args={
        'owner': 'marketing',
        'start_date': datetime(2024, 1, 1),
        'retries': 1,
        **get_callbacks(
            email_enabled=True,
            google_chat_enabled=False,
            email_recipients=['marketing@example.com'],
            corporate_name='Marketing Team',
            logo_url='https://www.python.org/static/community_logos/python-logo-master-v3-TM.png',
            smtp_connection_id='marketing_smtp',  # Different team uses different SMTP
            success_message='Marketing data pipeline completed!'
        )
    },
    description='Marketing team pipeline with team-specific alerts and logo',
    schedule_interval='@weekly',
    catchup=False,
    tags=['example', 'marketing', 'team-specific'],
) as marketing_dag:
    
    def process_marketing_data():
        """Process marketing campaign data."""
        print("Processing marketing campaign data...")
        return "Success"
    
    process = PythonOperator(
        task_id='process_marketing_data',
        python_callable=process_marketing_data,
    )
