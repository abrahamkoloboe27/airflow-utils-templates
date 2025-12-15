# Migration Guide: Old Utils to New Alerts Package

This guide helps you migrate from the old `dags/utils/` alert functions to the new modular `alerts` package.

## Overview

The old alert utilities in `dags/utils/` have been refactored into a cleaner, more maintainable package structure. The old files are still present but should be considered deprecated.

## What Changed

### Old Structure (Deprecated)
```
dags/utils/
├── mail_alert.py          # Email functions with hardcoded templates
└── google_chat_alert.py   # Google Chat functions with hardcoded templates
```

### New Structure (Recommended)
```
alerts/
├── __init__.py           # Public API
├── email/               # Email module with template separation
└── google_chat/         # Google Chat module with template separation

templates/
├── email/               # HTML templates
└── google_chat/         # JSON templates
```

## Migration Steps

### Step 1: Update Imports

**Old Code:**
```python
from dags.utils.mail_alert import success_callback, failure_callback
from dags.utils.google_chat_alert import send_success_alert, send_failure_alert
```

**New Code:**
```python
from alerts import get_callbacks
# or
from alerts.email import success_callback, retry_callback, failure_callback
from alerts.google_chat import success_callback, retry_callback, failure_callback
```

### Step 2: Update Callback Usage

#### Option A: Use Simple API (Recommended)

**Old Code:**
```python
from dags.utils.mail_alert import success_callback, failure_callback

default_args = {
    'owner': 'airflow',
    'on_success_callback': lambda context: success_callback(
        context,
        mails_list=['team@example.com'],
        corporate='Acme Corp',
        message='Success!'
    ),
    'on_failure_callback': lambda context: failure_callback(
        context,
        mails_list=['team@example.com'],
        corporate='Acme Corp'
    ),
}
```

**New Code:**
```python
from alerts import get_callbacks

default_args = {
    'owner': 'airflow',
    **get_callbacks(
        email_enabled=True,
        google_chat_enabled=True,
        email_recipients=['team@example.com'],
        corporate_name='Acme Corp',
        success_message='Success!'
    )
}
```

#### Option B: Use Individual Functions

**Old Code:**
```python
from dags.utils.mail_alert import success_callback
from dags.utils.google_chat_alert import send_success_alert

default_args = {
    'owner': 'airflow',
    'on_success_callback': lambda context: (
        success_callback(context, ['team@example.com'], 'Acme Corp', 'Success!'),
        send_success_alert(context)
    ),
}
```

**New Code:**
```python
from alerts.email import success_callback as email_success
from alerts.google_chat import success_callback as gchat_success

default_args = {
    'owner': 'airflow',
    'on_success_callback': lambda context: (
        email_success(
            context,
            email_recipients=['team@example.com'],
            corporate_name='Acme Corp',
            success_message='Success!'
        ),
        gchat_success(context)
    ),
}
```

### Step 3: Update Configuration

#### Email Configuration

**Old Code:**
```python
# Hardcoded in function call
success_callback(context, ['email1@example.com', 'email2@example.com'], 'Corp', 'msg')
```

**New Code - Option 1: Environment Variables**
```bash
export AIRFLOW_ALERT_EMAIL_RECIPIENTS="email1@example.com,email2@example.com"
export AIRFLOW_ALERT_CORPORATE_NAME="Corp"
```

```python
from alerts import get_callbacks
callbacks = get_callbacks()  # Uses environment variables
```

**New Code - Option 2: Airflow Variables**
```bash
airflow variables set alert_email_recipients "email1@example.com,email2@example.com"
airflow variables set alert_corporate_name "Corp"
```

**New Code - Option 3: Function Parameters**
```python
callbacks = get_callbacks(
    email_recipients=['email1@example.com', 'email2@example.com'],
    corporate_name='Corp'
)
```

#### Google Chat Configuration

**Old Code:**
```python
# Hardcoded connection name in function
GCHAT_CONNECTION = "google_chat_alert"
```

**New Code - Option 1: Environment Variable**
```bash
export AIRFLOW_GCHAT_WEBHOOK_URL="https://chat.googleapis.com/..."
```

**New Code - Option 2: Airflow Connection (same as before)**
```bash
airflow connections add google_chat_alert \
    --conn-type http \
    --conn-host "chat.googleapis.com/v1/spaces/..."
```

## Parameter Mapping

### Email Parameters

| Old Parameter | New Parameter | Notes |
|---------------|---------------|-------|
| `mails_list` | `email_recipients` | Same functionality |
| `corporate` | `corporate_name` | Same functionality |
| `message` | `success_message` | Only for success callback |
| N/A | `**kwargs` | Additional template variables |

### Google Chat Parameters

| Old Parameter | New Parameter | Notes |
|---------------|---------------|-------|
| `context` | `context` | Same |
| N/A | `connection_name` | Optional override |
| N/A | `**kwargs` | Additional template variables |

## Key Benefits of Migration

### 1. Cleaner Code
**Before:**
```python
# 5 lines to configure callbacks
from dags.utils.mail_alert import success_callback, failure_callback
default_args = {
    'on_success_callback': lambda c: success_callback(c, emails, corp, msg),
    'on_failure_callback': lambda c: failure_callback(c, emails, corp),
}
```

**After:**
```python
# 1 line to configure callbacks
from alerts import get_callbacks
default_args = {**get_callbacks()}
```

### 2. Template Customization
**Before:** Templates hardcoded in Python code (difficult to customize)

**After:** Templates in separate files (easy to customize)
```bash
cp templates/email/success.html my_templates/
# Edit my_templates/success.html
```

### 3. Flexible Configuration
**Before:** Must pass parameters in every function call

**After:** Configure once via environment/variables, reuse everywhere

### 4. Better Testing
**Before:** No tests

**After:** 24 comprehensive tests ensuring reliability

## Compatibility Notes

- The old `dags/utils/` files are still present and functional
- You can migrate gradually, DAG by DAG
- Both old and new can coexist during migration
- Old files will be marked as deprecated in a future release

## Common Patterns

### Pattern 1: Email-only alerts
```python
from alerts import get_callbacks

default_args = {
    **get_callbacks(
        email_enabled=True,
        google_chat_enabled=False,
        email_recipients=['team@example.com']
    )
}
```

### Pattern 2: Different recipients for different DAGs
```python
# Critical DAG
critical_callbacks = get_callbacks(
    email_recipients=['oncall@example.com', 'manager@example.com']
)

# Regular DAG
regular_callbacks = get_callbacks(
    email_recipients=['team@example.com']
)
```

### Pattern 3: Custom success message
```python
callbacks = get_callbacks(
    success_message='Data pipeline completed with 1M records processed'
)
```

## Troubleshooting

### "Module not found" error
**Solution:** Ensure the alerts package is in your Python path:
```python
import sys
sys.path.insert(0, '/path/to/airflow-utils-templates')
```

Or install as a package:
```bash
pip install -e /path/to/airflow-utils-templates
```

### Templates not found
**Solution:** Templates are automatically discovered relative to the package. Ensure the `templates/` directory is at the repository root.

### Configuration not being applied
**Solution:** Check configuration priority:
1. Function parameters (highest)
2. Environment variables
3. Airflow Variables
4. Defaults (lowest)

## Need Help?

- Check [README.md](README.md) for quick start
- Read [docs/usage.md](docs/usage.md) for detailed guide
- Look at examples in [dags/examples/](dags/examples/)
- Run tests: `pytest tests/`

## Timeline

- **Current:** Both old and new code available
- **Future (6 months):** Old code marked as deprecated
- **Future (12 months):** Old code may be removed

Migrate at your convenience, but new projects should use the new `alerts` package.
