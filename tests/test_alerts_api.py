"""Tests for alerts API (get_callbacks)."""
import pytest
import sys
from unittest.mock import patch, Mock, MagicMock as MockModule

# Mock Airflow modules
sys.modules['airflow'] = MockModule()
sys.modules['airflow.utils'] = MockModule()
sys.modules['airflow.utils.email'] = MockModule()
sys.modules['airflow.models'] = MockModule()
sys.modules['airflow.hooks'] = MockModule()
sys.modules['airflow.hooks.base_hook'] = MockModule()


def test_get_callbacks_default():
    """Test get_callbacks returns all three callbacks by default."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(email_enabled=True, google_chat_enabled=False)
    
    assert 'on_success_callback' in callbacks
    assert 'on_retry_callback' in callbacks
    assert 'on_failure_callback' in callbacks
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_retry_callback'] is not None
    assert callbacks['on_failure_callback'] is not None


def test_get_callbacks_email_only():
    """Test get_callbacks with only email enabled."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(email_enabled=True, google_chat_enabled=False)
    
    assert all(cb is not None for cb in callbacks.values())


def test_get_callbacks_google_chat_only():
    """Test get_callbacks with only Google Chat enabled."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(email_enabled=False, google_chat_enabled=True)
    
    assert all(cb is not None for cb in callbacks.values())


def test_get_callbacks_both_enabled(mock_context):
    """Test get_callbacks with both email and Google Chat enabled."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=True,
        email_recipients=['test@example.com'],
        corporate_name='Test Corp'
    )
    
    # All callbacks should be present
    assert all(cb is not None for cb in callbacks.values())
    
    # Test that callbacks can be called without error
    with patch('airflow.utils.email.send_email_smtp'), \
         patch('alerts.google_chat.requests.post'), \
         patch('alerts.google_chat._get_webhook_url', return_value='https://test.com'):
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        # Should not raise any exceptions
        callbacks['on_success_callback'](mock_context)


def test_get_callbacks_none_enabled():
    """Test get_callbacks with both disabled returns None callbacks."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(email_enabled=False, google_chat_enabled=False)
    
    assert callbacks['on_success_callback'] is None
    assert callbacks['on_retry_callback'] is None
    assert callbacks['on_failure_callback'] is None


def test_get_callbacks_with_overrides(mock_context):
    """Test get_callbacks accepts and passes override parameters."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=False,
        email_recipients=['override@example.com'],
        corporate_name='Override Corp',
        success_message='Custom success message'
    )
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send:
        callbacks['on_success_callback'](mock_context)
        
        # Verify overrides were used
        call_args = mock_send.call_args
        assert 'override@example.com' in call_args[1]['to']
        assert 'Override Corp' in call_args[1]['subject']
        assert 'Custom success message' in call_args[1]['html_content']


def test_callbacks_integration_in_dag_default_args():
    """Test that callbacks can be integrated into DAG default_args."""
    from alerts import get_callbacks
    
    # Simulate DAG default_args usage
    default_args = {
        'owner': 'airflow',
        'retries': 2,
        **get_callbacks(email_enabled=True, google_chat_enabled=False)
    }
    
    assert 'on_success_callback' in default_args
    assert 'on_retry_callback' in default_args
    assert 'on_failure_callback' in default_args
    assert 'owner' in default_args
    assert 'retries' in default_args


def test_get_callbacks_dag_level():
    """Test get_callbacks with alert_level='dag'."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=False,
        alert_level='dag'
    )
    
    assert 'on_success_callback' in callbacks
    assert 'on_retry_callback' in callbacks
    assert 'on_failure_callback' in callbacks
    # DAG-level alerts should have success and failure callbacks
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_failure_callback'] is not None
    # But no retry callback for DAG-level
    assert callbacks['on_retry_callback'] is None


def test_get_callbacks_dag_level_both_channels():
    """Test get_callbacks with alert_level='dag' and both channels."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=True,
        alert_level='dag',
        email_recipients=['team@example.com']
    )
    
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_failure_callback'] is not None
    assert callbacks['on_retry_callback'] is None


def test_get_callbacks_task_level_default():
    """Test get_callbacks defaults to task-level alerts."""
    from alerts import get_callbacks
    
    # Without alert_level, should default to task-level
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=False
    )
    
    # Task-level should have all three callbacks
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_retry_callback'] is not None
    assert callbacks['on_failure_callback'] is not None


def test_get_granular_callbacks_dag_level():
    """Test get_granular_callbacks with alert_level='dag'."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_success=True,
        on_failure=True,
        on_retry=False,  # Should be ignored for DAG-level
        email_enabled=True,
        google_chat_enabled=False,
        alert_level='dag'
    )
    
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_failure_callback'] is not None
    # Retry should be None for DAG-level even if on_retry=True
    assert callbacks['on_retry_callback'] is None


def test_get_granular_callbacks_dag_level_failure_only():
    """Test get_granular_callbacks with DAG-level failure-only alerts."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_success=False,
        on_failure=True,
        email_enabled=True,
        alert_level='dag',
        email_recipients=['critical@example.com']
    )
    
    assert callbacks['on_success_callback'] is None
    assert callbacks['on_failure_callback'] is not None
    assert callbacks['on_retry_callback'] is None
