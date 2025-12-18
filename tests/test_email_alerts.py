"""Tests for email alert module."""
import pytest
import sys
from unittest.mock import patch, Mock, MagicMock, MagicMock as MockModule
from datetime import datetime

# Mock Airflow modules
sys.modules['airflow'] = MockModule()
sys.modules['airflow.utils'] = MockModule()
sys.modules['airflow.utils.email'] = MockModule()
sys.modules['airflow.models'] = MockModule()
sys.modules['airflow.hooks'] = MockModule()
sys.modules['airflow.hooks.base_hook'] = MockModule()


def test_email_success_callback(mock_context):
    """Test email success callback sends email correctly."""
    from alerts.email import success_callback
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email:
        success_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp',
            success_message='Test success message'
        )
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        
        assert 'test@example.com' in call_args[1]['to']
        assert 'test_dag' in call_args[1]['subject']
        assert 'Réussie' in call_args[1]['subject']
        assert 'Test success message' in call_args[1]['html_content']


def test_email_retry_callback(mock_context):
    """Test email retry callback sends email correctly."""
    from alerts.email import retry_callback
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email:
        retry_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp'
        )
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        
        assert 'test@example.com' in call_args[1]['to']
        assert 'test_dag' in call_args[1]['subject']
        assert 'Retentative' in call_args[1]['subject']
        assert 'Test exception message' in call_args[1]['html_content']


def test_email_failure_callback(mock_context):
    """Test email failure callback sends email correctly."""
    from alerts.email import failure_callback
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email:
        failure_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp'
        )
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        
        assert 'test@example.com' in call_args[1]['to']
        assert 'test_dag' in call_args[1]['subject']
        assert 'Échec' in call_args[1]['subject']
        assert 'Test exception message' in call_args[1]['html_content']


def test_email_callback_with_env_variable(mock_context, monkeypatch):
    """Test email callback uses environment variables for configuration."""
    from alerts.email import success_callback
    
    monkeypatch.setenv('AIRFLOW_ALERT_EMAIL_RECIPIENTS', 'env@example.com,env2@example.com')
    monkeypatch.setenv('AIRFLOW_ALERT_CORPORATE_NAME', 'EnvCorp')
    
    # Mock Variable.get to return the default_var (which comes from environment)
    def mock_variable_get(key, default_var=None):
        return default_var
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email, \
         patch('airflow.models.Variable.get', side_effect=mock_variable_get):
        success_callback(mock_context)
        
        # Verify email was sent with env values
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        
        assert 'env@example.com' in call_args[1]['to']
        assert 'EnvCorp' in call_args[1]['subject']


def test_email_callback_handles_error_gracefully(mock_context):
    """Test email callback handles errors without raising exceptions."""
    from alerts.email import success_callback
    
    with patch('airflow.utils.email.send_email_smtp', side_effect=Exception("SMTP Error")):
        # Should not raise exception
        success_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp'
        )


def test_format_execution_time():
    """Test execution time formatting."""
    from alerts.email import _format_execution_time
    
    start = datetime(2024, 1, 1, 10, 0, 0)
    end = datetime(2024, 1, 1, 10, 5, 30)
    
    result = _format_execution_time(start, end)
    assert result == "0h 5m 30s"
    
    # Test with None values
    result = _format_execution_time(None, None)
    assert result == "Non disponible"


def test_template_rendering_success(mock_context):
    """Test that success template renders correctly."""
    from alerts.email import success_callback
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email:
        success_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp'
        )
        
        html_content = mock_send_email.call_args[1]['html_content']
        
        # Verify template content
        assert 'test_dag' in html_content
        assert 'test_task' in html_content
        assert '✅' in html_content or 'Réussie' in html_content


def test_template_rendering_failure(mock_context):
    """Test that failure template renders correctly."""
    from alerts.email import failure_callback
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email:
        failure_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp'
        )
        
        html_content = mock_send_email.call_args[1]['html_content']
        
        # Verify template content
        assert 'test_dag' in html_content
        assert 'Test exception message' in html_content
        assert '⚠️' in html_content or 'Échec' in html_content


def test_email_callback_includes_owner_and_tags(mock_context):
    """Test that email callbacks include owner and tags in template."""
    from alerts.email import success_callback
    
    with patch('airflow.utils.email.send_email_smtp') as mock_send_email:
        success_callback(
            mock_context,
            email_recipients=['test@example.com'],
            corporate_name='Test Corp'
        )
        
        html_content = mock_send_email.call_args[1]['html_content']
        
        # Verify owner and tags are in the email content
        assert 'test_owner' in html_content
        assert 'test' in html_content
        assert 'example' in html_content
        assert 'alerts' in html_content
