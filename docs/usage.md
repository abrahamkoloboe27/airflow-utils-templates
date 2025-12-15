# Usage Guide - Airflow Alerts

This guide provides detailed information on how to use the Airflow alerts package effectively.

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Configuration Methods](#configuration-methods)
3. [Email Alerts](#email-alerts)
4. [Google Chat Alerts](#google-chat-alerts)
5. [Using get_callbacks() API](#using-get_callbacks-api)
6. [Advanced Usage](#advanced-usage)
7. [Template Customization](#template-customization)
8. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Step 1: Install the Package

```bash
# Clone repository
git clone https://github.com/abrahamkoloboe27/airflow-utils-templates.git
cd airflow-utils-templates

# Install dependencies
pip install -r requirements.txt

# Install as package (optional)
pip install -e .
```

### Step 2: Configure Airflow

Ensure your Airflow environment has SMTP configured for email alerts:

```ini
# airflow.cfg
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your-email@gmail.com
smtp_password = your-app-password
smtp_port = 587
smtp_mail_from = your-email@gmail.com
```

### Step 3: Add to Python Path (if not using pip install)

```python
import sys
sys.path.insert(0, '/path/to/airflow-utils-templates')
```

---

## Configuration Methods

The package supports three configuration methods with the following priority:

**Priority (highest to lowest):**
1. Function parameters (passed directly to callback functions)
2. Environment variables
3. Airflow Variables
4. Default values

### Method 1: Function Parameters (Recommended)

```python
from alerts import get_callbacks

callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['team@example.com', 'ops@example.com'],
    corporate_name='Acme Corp',
    success_message='Pipeline completed successfully!'
)
```

**Pros:**
- Explicit and visible in code
- Easy to override per DAG
- No external configuration needed

**Cons:**
- Hardcoded values
- Changes require code updates

### Method 2: Environment Variables

```bash
# Email configuration
export AIRFLOW_ALERT_EMAIL_RECIPIENTS="team@example.com,ops@example.com"
export AIRFLOW_ALERT_CORPORATE_NAME="Acme Corp"

# Google Chat configuration
export AIRFLOW_GCHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/..."
export AIRFLOW_GCHAT_CONNECTION="my_gchat_connection"
```

```python
from alerts import get_callbacks

# Will use environment variables
callbacks = get_callbacks()
```

**Pros:**
- Easy to change without code modifications
- Good for container deployments
- Suitable for CI/CD pipelines

**Cons:**
- Less visible in code
- Requires environment setup

### Method 3: Airflow Variables

```bash
# Set via CLI
airflow variables set alert_email_recipients "team@example.com,ops@example.com"
airflow variables set alert_corporate_name "Acme Corp"

# Or via UI: Admin -> Variables
```

```python
from alerts import get_callbacks

# Will use Airflow Variables
callbacks = get_callbacks()
```

**Pros:**
- Centralized configuration in Airflow
- Easy to change via UI
- Can be environment-specific

**Cons:**
- Requires Airflow access
- May require additional permissions

### Method 4: Airflow Connections (for Google Chat)

```bash
# Add connection via CLI
airflow connections add google_chat_alert \
    --conn-type http \
    --conn-host "chat.googleapis.com/v1/spaces/AAAAA/messages?key=KEY&token=TOKEN"

# Or via UI: Admin -> Connections
```

---

## Email Alerts

### Basic Email Setup

```python
from alerts.email import success_callback, retry_callback, failure_callback
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data-team',
    'on_success_callback': lambda context: success_callback(
        context,
        email_recipients=['team@example.com'],
        corporate_name='Acme Corp'
    ),
    'on_retry_callback': lambda context: retry_callback(
        context,
        email_recipients=['team@example.com'],
        corporate_name='Acme Corp'
    ),
    'on_failure_callback': lambda context: failure_callback(
        context,
        email_recipients=['team@example.com'],
        corporate_name='Acme Corp'
    ),
}

with DAG('my_dag', default_args=default_args, ...) as dag:
    task = PythonOperator(...)
```

### Email Templates

Three templates are available:

1. **success.html**: Green header, shows execution time
2. **retry.html**: Orange header, shows retry attempt and error
3. **failure.html**: Red header, shows final failure and error

Templates are located in `templates/email/` and use Jinja2.

### Customize Email Subject

```python
# Override subject by modifying the callback
def custom_success_callback(context):
    from alerts.email import success_callback as base_callback
    # Custom logic here
    base_callback(context, email_recipients=['team@example.com'])
```

---

## Google Chat Alerts

### Setup Google Chat Webhook

1. **Open Google Chat space**
2. **Click space name → Manage webhooks**
3. **Create new webhook**
4. **Copy webhook URL**

### Configure in Airflow

**Option A: Via Connection**

```bash
airflow connections add google_chat_alert \
    --conn-type http \
    --conn-host "chat.googleapis.com/v1/spaces/SPACE_ID/messages?key=KEY&token=TOKEN"
```

**Option B: Via Environment Variable**

```bash
export AIRFLOW_GCHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/..."
```

### Basic Google Chat Setup

```python
from alerts.google_chat import success_callback, retry_callback, failure_callback

default_args = {
    'owner': 'data-team',
    'on_success_callback': success_callback,
    'on_retry_callback': retry_callback,
    'on_failure_callback': failure_callback,
}

with DAG('my_dag', default_args=default_args, ...) as dag:
    task = PythonOperator(...)
```

### Message Threading

Messages from the same DAG run are automatically grouped into threads using:
- Thread ID format: `{dag_id}_{execution_date_YYYYMMDD}`
- All alerts (success, retry, failure) for the same run appear in one thread

### Google Chat Card Templates

Three templates are available:

1. **success.json.j2**: Green checkmark icon
2. **retry.json.j2**: Orange sync icon
3. **failure.json.j2**: Red X icon

Templates are located in `templates/google_chat/` and use Jinja2 to render JSON.

---

## Using get_callbacks() API

The `get_callbacks()` function is the recommended way to use this package.

### Basic Usage

```python
from alerts import get_callbacks

callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
)

default_args = {
    'owner': 'airflow',
    'retries': 2,
    **callbacks  # Unpacks: on_success_callback, on_retry_callback, on_failure_callback
}
```

### Selective Notifications

**Email only:**
```python
callbacks = get_callbacks(email_enabled=True, google_chat_enabled=False)
```

**Google Chat only:**
```python
callbacks = get_callbacks(email_enabled=False, google_chat_enabled=True)
```

**Disable all (for testing):**
```python
callbacks = get_callbacks(email_enabled=False, google_chat_enabled=False)
```

### With Custom Configuration

```python
callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['team@example.com', 'manager@example.com'],
    corporate_name='Acme Corp',
    success_message='All data processing completed successfully!',
)
```

---

## Advanced Usage

### Per-Task Callbacks

Apply callbacks to specific tasks instead of entire DAG:

```python
from alerts.email import failure_callback

critical_task = PythonOperator(
    task_id='critical_task',
    python_callable=critical_function,
    on_failure_callback=lambda context: failure_callback(
        context,
        email_recipients=['oncall@example.com'],  # Different recipients
        corporate_name='Acme Corp'
    ),
)
```

### Mixed Callbacks

Combine different alert types for different events:

```python
from alerts.email import failure_callback
from alerts.google_chat import success_callback

default_args = {
    'on_success_callback': success_callback,  # Google Chat for success
    'on_failure_callback': lambda context: failure_callback(  # Email for failures
        context,
        email_recipients=['oncall@example.com']
    ),
}
```

### Custom Context Variables

Pass additional data to templates:

```python
callbacks = get_callbacks(
    email_enabled=True,
    environment='production',
    team='data-engineering',
    priority='high',
)
```

Access in custom templates:
```html
<p>Environment: {{ environment }}</p>
<p>Team: {{ team }}</p>
<p>Priority: {{ priority }}</p>
```

### Conditional Alerts

Send alerts based on conditions:

```python
def conditional_failure_callback(context):
    from alerts.email import failure_callback
    
    # Only alert on production
    if os.environ.get('ENV') == 'production':
        failure_callback(context, email_recipients=['team@example.com'])
```

---

## Template Customization

### Override Email Templates

1. **Copy templates to your location:**
```bash
cp -r templates/email /path/to/custom/templates/email
```

2. **Modify templates as needed**

3. **Update template path in your DAG:**
```python
import alerts.email as email_module
from pathlib import Path

# Override template directory
email_module.TEMPLATE_DIR = Path('/path/to/custom/templates/email')

# Use callbacks normally
from alerts import get_callbacks
callbacks = get_callbacks()
```

### Template Variables Available

**Email templates receive:**
- `dag_id`: DAG identifier
- `task_id`: Task identifier
- `execution_date`: Execution timestamp
- `start_date`: Task start time
- `end_date`: Task end time (success only)
- `execution_time`: Formatted execution duration
- `try_number`: Current attempt number
- `max_tries`: Maximum attempts
- `exception`: Error message (retry/failure only)
- `message`: Custom message (success only)
- `corporate`: Corporate name
- `year`: Current year

**Google Chat templates receive:**
- All above variables plus:
- `execution_date_short`: Short date format (YYYY-MM-DD)
- `dag_description`: DAG description
- `exception_msg`: Truncated exception (max 500 chars)
- `failure_time`: Time of failure
- `next_retry_datetime`: Next retry time (retry only)

### Example Custom Template

```html
<!-- custom_success.html -->
<div style="padding: 20px;">
    <h1>✅ Success: {{ dag_id }}</h1>
    <p>Task: {{ task_id }}</p>
    <p>Time: {{ execution_time }}</p>
    {% if custom_var %}
    <p>Custom: {{ custom_var }}</p>
    {% endif %}
</div>
```

---

## Troubleshooting

### Emails Not Sending

**Check SMTP configuration:**
```bash
# Test email from Airflow
airflow tasks test your_dag your_task 2024-01-01
```

**Check logs:**
```bash
tail -f $AIRFLOW_HOME/logs/scheduler/latest/*.log | grep -i email
```

**Common issues:**
- SMTP not configured in `airflow.cfg`
- Firewall blocking port 587/465
- Invalid credentials
- Missing `send_email_smtp` import

### Google Chat Alerts Not Working

**Check webhook URL:**
```bash
# Test webhook manually
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'
```

**Common issues:**
- Invalid webhook URL
- Connection not configured
- Network/firewall issues
- Webhook expired (regenerate in Google Chat)

**Check logs:**
```bash
tail -f $AIRFLOW_HOME/logs/scheduler/latest/*.log | grep -i "google chat"
```

### Templates Not Rendering

**Check template path:**
```python
from alerts.email import TEMPLATE_DIR
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Templates exist: {TEMPLATE_DIR.exists()}")
```

**Common issues:**
- Templates not in correct directory
- Jinja2 not installed
- File permissions
- Template syntax errors

### Import Errors

**Add package to Python path:**
```python
import sys
sys.path.insert(0, '/path/to/airflow-utils-templates')
```

**Or install as package:**
```bash
pip install -e /path/to/airflow-utils-templates
```

### Callback Not Triggered

**Verify callback attachment:**
```python
# Print to see if callbacks are set
print(default_args)
print(dag.default_args)
```

**Common issues:**
- Callback not in `default_args`
- Task-level callback overriding DAG-level
- Exception in callback (check logs)
- Callback returning None

---

## Best Practices

1. **Use `get_callbacks()` for consistency**
   ```python
   callbacks = get_callbacks()
   default_args = {**other_args, **callbacks}
   ```

2. **Configure via environment for flexibility**
   ```bash
   export AIRFLOW_ALERT_EMAIL_RECIPIENTS="..."
   ```

3. **Different recipients for critical tasks**
   ```python
   critical_task = PythonOperator(
       on_failure_callback=lambda ctx: failure_callback(
           ctx, email_recipients=['oncall@example.com']
       )
   )
   ```

4. **Test in development first**
   ```python
   callbacks = get_callbacks(
       email_enabled=is_production(),
       google_chat_enabled=is_production()
   )
   ```

5. **Monitor callback execution**
   ```python
   import logging
   logging.info("Callback executed successfully")
   ```

---

## Support

For additional help:
- Check [README.md](../README.md) for quick start
- Review example DAGs in `dags/examples/`
- Run tests: `pytest tests/ -v`
- Open an issue on GitHub

## Changelog

### Version 1.0.0
- Initial release
- Email and Google Chat support
- Jinja2 templates
- Comprehensive tests
- Full documentation
