# Airflow Alerts Templates

[![CI/CD Pipeline](https://github.com/abrahamkoloboe27/airflow-utils-templates/actions/workflows/ci.yml/badge.svg)](https://github.com/abrahamkoloboe27/airflow-utils-templates/actions/workflows/ci.yml)

Modular and reusable Airflow alert system for email and Google Chat notifications. This package provides clean, production-ready templates and callbacks for DAG/task monitoring.

## Features

- 🎯 **Modular Design**: Separate packages for email and Google Chat alerts
- 📧 **Email Notifications**: Beautiful HTML templates for success, retry, and failure alerts
- 💬 **Google Chat Integration**: Rich card notifications with threading support
- 🖼️ **Custom Logos**: Optional logo/image support in email and Google Chat alerts
- 🎛️ **Granular Control**: Choose exactly which events (success/retry/failure) trigger alerts
- 🔧 **Easy Configuration**: Via Airflow Variables, environment variables, or function parameters
- 🔌 **Multi-Connection Support**: Use different SMTP/GChat connections per DAG
- 🎨 **Customizable Templates**: Jinja2 templates easily overridable
- ✅ **Production Ready**: Tested, documented, and following best practices
- 🚀 **Simple API**: One-line integration with `get_callbacks()`

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/abrahamkoloboe27/airflow-utils-templates.git

# Install dependencies
pip install -r requirements.txt

# For development/testing
pip install -r requirements-dev.txt
```

Or install as a package:

```bash
pip install -e .
```

### Using Docker

Pull the pre-built Docker image from GitHub Container Registry:

```bash
# Latest version
docker pull ghcr.io/abrahamkoloboe27/airflow-utils-templates:latest

# Specific version
docker pull ghcr.io/abrahamkoloboe27/airflow-utils-templates:v1.0.0
```

Or use docker-compose:

```bash
# Build and start services
make build-up

# Or manually
docker compose up -d
```

## Quick Start

### Basic Usage

```python
from datetime import datetime
from airflow import DAG
from alerts import get_callbacks

# Get pre-configured callbacks
callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['team@example.com'],
    corporate_name='My Company'
)

# Use in DAG default_args
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    **callbacks  # Injects on_success_callback, on_retry_callback, on_failure_callback
}

with DAG('my_dag', default_args=default_args, ...) as dag:
    # Your tasks here
    pass
```

### Individual Callbacks

```python
from alerts.email import success_callback, failure_callback
from alerts.google_chat import retry_callback

# Attach to specific tasks
my_task = PythonOperator(
    task_id='important_task',
    python_callable=my_function,
    on_failure_callback=failure_callback,
)
```

### Custom Logo/Image Support

Add a custom logo or corporate image to your alert templates (optional):

```python
from alerts import get_callbacks

callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    email_recipients=['team@example.com'],
    corporate_name='My Company',
    logo_url='https://example.com/logo.png'  # Optional logo URL
)
```

The logo will appear at the top of email alerts and in the header of Google Chat cards. If not provided, alerts will display without a logo.

You can also configure the logo via environment variable or Airflow Variable:

```bash
# Via Environment Variable
export AIRFLOW_ALERT_LOGO_URL="https://example.com/logo.png"

# Via Airflow Variable
airflow variables set alert_logo_url "https://example.com/logo.png"
```

### Granular Callback Control

Use `get_granular_callbacks()` to specify exactly which events trigger alerts:

```python
from alerts import get_granular_callbacks

# Example 1: Only send alerts on failures and retries (not on success)
callbacks = get_granular_callbacks(
    on_success=False,
    on_retry=True,
    on_failure=True,
    email_enabled=True,
    google_chat_enabled=False,
    email_recipients=['ops@example.com']
)

# Example 2: Only send alerts on final failure (no retry or success alerts)
callbacks = get_granular_callbacks(
    on_success=False,
    on_retry=False,
    on_failure=True,
    email_enabled=True,
    email_recipients=['critical@example.com']
)

# Example 3: All events enabled (same as get_callbacks with all defaults)
callbacks = get_granular_callbacks(
    on_success=True,
    on_retry=True,
    on_failure=True,
    email_enabled=True
)
```

This is useful for:
- **Critical pipelines**: Only alert on final failures, not retries
- **High-volume DAGs**: Reduce alert noise by skipping success notifications
- **Different alert recipients**: Send retry alerts to ops team, failures to management

### Custom SMTP and Google Chat Connections

Specify custom Airflow connections for sending alerts:

```python
from alerts import get_callbacks

callbacks = get_callbacks(
    email_enabled=True,
    google_chat_enabled=True,
    smtp_connection_id='custom_smtp',      # Use specific SMTP connection
    gchat_connection_id='custom_gchat',    # Use specific GChat connection
    email_recipients=['team@example.com']
)
```

This allows you to:
- Use different SMTP servers for different DAGs
- Route alerts to different Google Chat spaces
- Support multi-tenant deployments with separate notification channels

## Configuration

### Priority Order

Configuration is resolved in this order (highest to lowest priority):
1. Function parameters
2. Environment variables
3. Airflow Variables
4. Default values

### Email Configuration

**Via Airflow Variables:**
```bash
airflow variables set alert_email_recipients "team@example.com,ops@example.com"
airflow variables set alert_corporate_name "My Company"
```

**Via Environment Variables:**
```bash
export AIRFLOW_ALERT_EMAIL_RECIPIENTS="team@example.com,ops@example.com"
export AIRFLOW_ALERT_CORPORATE_NAME="My Company"
```

**Via Function Parameters:**
```python
callbacks = get_callbacks(
    email_recipients=['team@example.com'],
    corporate_name='My Company',
    success_message='Custom success message'
)
```

### Google Chat Configuration

**Via Airflow Connection:**
```bash
airflow connections add google_chat_alert \
    --conn-type http \
    --conn-host "chat.googleapis.com/v1/spaces/SPACE_ID/messages?key=KEY&token=TOKEN"
```

**Via Environment Variable:**
```bash
export AIRFLOW_GCHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/SPACE_ID/messages?key=KEY&token=TOKEN"
```

**Via Connection Name Override:**
```python
from alerts.google_chat import success_callback

success_callback(context, connection_name='my_custom_connection')
```

## Project Structure

```
airflow-utils-templates/
├── alerts/                      # Main alerts package
│   ├── __init__.py             # Public API with get_callbacks()
│   ├── email/                  # Email alert module
│   │   └── __init__.py
│   └── google_chat/            # Google Chat alert module
│       └── __init__.py
├── templates/                   # Jinja2 templates
│   ├── email/
│   │   ├── success.html
│   │   ├── retry.html
│   │   └── failure.html
│   └── google_chat/
│       ├── success.json.j2
│       ├── retry.json.j2
│       └── failure.json.j2
├── dags/
│   ├── examples/               # Example DAGs
│   │   ├── example_dag_success.py
│   │   └── example_dag_failure.py
│   └── utils/                  # Legacy code (deprecated)
├── tests/                      # Unit tests
│   ├── test_email_alerts.py
│   ├── test_google_chat_alerts.py
│   └── test_alerts_api.py
├── docs/
│   └── usage.md               # Detailed usage guide
└── requirements.txt
```

## Examples

See the `dags/examples/` directory for complete working examples:

- **example_dag_success.py**: ETL pipeline with successful execution
- **example_dag_failure.py**: Pipeline with simulated failures and retries

Run examples:
```bash
# Copy examples to your Airflow DAGs folder
cp dags/examples/*.py $AIRFLOW_HOME/dags/

# Trigger manually
airflow dags trigger example_etl_success
airflow dags trigger example_etl_with_retries
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=alerts --cov-report=html

# Run specific test file
pytest tests/test_email_alerts.py -v
```

## Template Customization

### Override Email Templates

Copy templates to your project and modify:

```bash
cp -r templates/email /path/to/your/templates/
```

Update template path in code:
```python
from pathlib import Path
from alerts.email import TEMPLATE_DIR

# Override template directory
import alerts.email as email_module
email_module.TEMPLATE_DIR = Path('/path/to/your/templates/email')
```

### Custom Template Variables

Pass additional variables to templates:

```python
callbacks = get_callbacks(
    email_enabled=True,
    custom_var='custom_value',
    additional_info='Some extra info'
)
```

Access in templates:
```html
<p>{{ custom_var }}</p>
<p>{{ additional_info }}</p>
```

## API Reference

### `get_callbacks(**kwargs)`

Main API function that returns a dictionary of callbacks.

**Parameters:**
- `email_enabled` (bool): Enable email notifications (default: True)
- `google_chat_enabled` (bool): Enable Google Chat notifications (default: True)
- `email_recipients` (list): List of email addresses
- `corporate_name` (str): Corporate name for email footer
- `success_message` (str): Custom success message for email
- `**overrides`: Additional parameters passed to callbacks

**Returns:**
- Dict with keys: `on_success_callback`, `on_retry_callback`, `on_failure_callback`

### Email Module Functions

- `success_callback(context, **kwargs)`: Send success email
- `retry_callback(context, **kwargs)`: Send retry email
- `failure_callback(context, **kwargs)`: Send failure email

### Google Chat Module Functions

- `success_callback(context, **kwargs)`: Send success card
- `retry_callback(context, **kwargs)`: Send retry card
- `failure_callback(context, **kwargs)`: Send failure card

## Requirements

- Python >= 3.7
- Apache Airflow >= 2.0.0
- Jinja2 >= 3.0.0
- requests >= 2.28.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests: `pytest`
6. Submit a pull request

## License

MIT License - feel free to use in your projects.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes and releases.

## Support

For detailed documentation, see [docs/usage.md](docs/usage.md).

For issues or questions, please open an issue on GitHub.
