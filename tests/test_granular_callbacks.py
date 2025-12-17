"""Tests for granular callbacks API."""
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


def test_get_granular_callbacks_only_failure():
    """Test get_granular_callbacks with only failure enabled."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=False
    )
    
    assert callbacks['on_success_callback'] is None
    assert callbacks['on_retry_callback'] is None
    assert callbacks['on_failure_callback'] is not None


def test_get_granular_callbacks_failure_and_retry():
    """Test get_granular_callbacks with failure and retry enabled."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_failure=True,
        on_retry=True,
        email_enabled=True,
        google_chat_enabled=False
    )
    
    assert callbacks['on_success_callback'] is None
    assert callbacks['on_retry_callback'] is not None
    assert callbacks['on_failure_callback'] is not None


def test_get_granular_callbacks_only_success():
    """Test get_granular_callbacks with only success enabled."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_success=True,
        email_enabled=True,
        google_chat_enabled=False
    )
    
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_retry_callback'] is None
    assert callbacks['on_failure_callback'] is None


def test_get_granular_callbacks_all_events():
    """Test get_granular_callbacks with all events enabled."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_success=True,
        on_retry=True,
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=False
    )
    
    assert callbacks['on_success_callback'] is not None
    assert callbacks['on_retry_callback'] is not None
    assert callbacks['on_failure_callback'] is not None


def test_get_granular_callbacks_no_events():
    """Test get_granular_callbacks with no events enabled."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        email_enabled=True,
        google_chat_enabled=False
    )
    
    assert callbacks['on_success_callback'] is None
    assert callbacks['on_retry_callback'] is None
    assert callbacks['on_failure_callback'] is None


def test_get_granular_callbacks_with_both_channels():
    """Test get_granular_callbacks with both email and Google Chat enabled."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=True
    )
    
    assert callbacks['on_success_callback'] is None
    assert callbacks['on_retry_callback'] is None
    assert callbacks['on_failure_callback'] is not None


def test_get_granular_callbacks_with_logo(mock_context):
    """Test get_granular_callbacks with logo_url parameter."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_success=True,
        email_enabled=True,
        google_chat_enabled=False,
        logo_url='https://example.com/logo.png',
        email_recipients=['test@example.com']
    )
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send:
        callbacks['on_success_callback'](mock_context)
        
        # Verify send was called
        assert mock_send.called
        call_args = mock_send.call_args
        # Check that logo_url is in the HTML content
        assert 'https://example.com/logo.png' in call_args[1]['html_content']


def test_get_granular_callbacks_with_smtp_connection(mock_context):
    """Test get_granular_callbacks with smtp_connection_id parameter."""
    from alerts import get_granular_callbacks
    
    callbacks = get_granular_callbacks(
        on_failure=True,
        email_enabled=True,
        google_chat_enabled=False,
        smtp_connection_id='custom_smtp',
        email_recipients=['test@example.com']
    )
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send:
        callbacks['on_failure_callback'](mock_context)
        
        # Verify send was called with custom connection
        assert mock_send.called
        call_args = mock_send.call_args
        assert 'conn_id' in call_args[1]
        assert call_args[1]['conn_id'] == 'custom_smtp'


def test_get_callbacks_with_logo(mock_context):
    """Test get_callbacks with logo_url parameter (backward compatibility)."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=False,
        logo_url='https://example.com/logo.png',
        email_recipients=['test@example.com']
    )
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send:
        callbacks['on_success_callback'](mock_context)
        
        # Verify logo is in HTML
        assert mock_send.called
        call_args = mock_send.call_args
        assert 'https://example.com/logo.png' in call_args[1]['html_content']


def test_get_callbacks_with_smtp_connection(mock_context):
    """Test get_callbacks with smtp_connection_id parameter."""
    from alerts import get_callbacks
    
    callbacks = get_callbacks(
        email_enabled=True,
        google_chat_enabled=False,
        smtp_connection_id='custom_smtp',
        email_recipients=['test@example.com']
    )
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send:
        callbacks['on_success_callback'](mock_context)
        
        # Verify custom connection is used
        assert mock_send.called
        call_args = mock_send.call_args
        assert 'conn_id' in call_args[1]
        assert call_args[1]['conn_id'] == 'custom_smtp'
