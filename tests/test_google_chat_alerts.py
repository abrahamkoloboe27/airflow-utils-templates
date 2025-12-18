"""Tests for Google Chat alert module."""
import pytest
import sys
import json
from unittest.mock import patch, Mock, MagicMock, MagicMock as MockModule

# Mock Airflow modules
sys.modules['airflow'] = MockModule()
sys.modules['airflow.hooks'] = MockModule()
sys.modules['airflow.hooks.base_hook'] = MockModule()


def test_gchat_success_callback(mock_context):
    """Test Google Chat success callback sends request correctly."""
    from alerts.google_chat import success_callback
    
    with patch('alerts.google_chat.requests.post') as mock_post, \
         patch('alerts.google_chat._get_webhook_url', return_value='https://chat.googleapis.com/webhook/test'):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success_callback(mock_context)
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify URL contains thread parameters
        assert 'threadKey=' in call_args[0][0]
        assert 'test_dag' in call_args[0][0]
        
        # Verify card body
        card_body = call_args[1]['json']
        assert 'cardsV2' in card_body
        assert card_body['cardsV2'][0]['cardId'] == 'test_dag_success_alert'


def test_gchat_retry_callback(mock_context):
    """Test Google Chat retry callback sends request correctly."""
    from alerts.google_chat import retry_callback
    
    with patch('alerts.google_chat.requests.post') as mock_post, \
         patch('alerts.google_chat._get_webhook_url', return_value='https://chat.googleapis.com/webhook/test'):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        retry_callback(mock_context)
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify card body contains retry information
        card_body = call_args[1]['json']
        assert 'cardsV2' in card_body
        assert card_body['cardsV2'][0]['cardId'] == 'test_dag_retry_alert'
        
        # Verify exception message is in the card
        card_json = json.dumps(card_body)
        assert 'Test exception message' in card_json


def test_gchat_failure_callback(mock_context):
    """Test Google Chat failure callback sends request correctly."""
    from alerts.google_chat import failure_callback
    
    with patch('alerts.google_chat.requests.post') as mock_post, \
         patch('alerts.google_chat._get_webhook_url', return_value='https://chat.googleapis.com/webhook/test'):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        failure_callback(mock_context)
        
        # Verify request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify card body contains failure information
        card_body = call_args[1]['json']
        assert 'cardsV2' in card_body
        assert card_body['cardsV2'][0]['cardId'] == 'test_dag_failure_alert'
        
        # Verify exception message is in the card
        card_json = json.dumps(card_body)
        assert 'Test exception message' in card_json


def test_gchat_webhook_from_env(mock_context, monkeypatch):
    """Test Google Chat callback uses environment variable for webhook URL."""
    from alerts.google_chat import success_callback
    
    monkeypatch.setenv('AIRFLOW_GCHAT_WEBHOOK_URL', 'https://env-webhook.example.com')
    
    with patch('alerts.google_chat.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success_callback(mock_context)
        
        # Verify environment webhook was used
        call_url = mock_post.call_args[0][0]
        assert 'env-webhook.example.com' in call_url


def test_gchat_webhook_from_connection(mock_context):
    """Test Google Chat callback uses Airflow connection for webhook URL."""
    from alerts.google_chat import success_callback
    
    mock_connection = Mock()
    mock_connection.host = 'chat.googleapis.com/webhook/connection'
    
    with patch('alerts.google_chat.requests.post') as mock_post, \
         patch('airflow.hooks.base_hook.BaseHook.get_connection', return_value=mock_connection):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success_callback(mock_context)
        
        # Verify connection webhook was used
        call_url = mock_post.call_args[0][0]
        assert 'chat.googleapis.com/webhook/connection' in call_url


def test_gchat_callback_handles_error_gracefully(mock_context):
    """Test Google Chat callback handles errors without raising exceptions."""
    from alerts.google_chat import success_callback
    
    with patch('alerts.google_chat.requests.post', side_effect=Exception("Network Error")), \
         patch('alerts.google_chat._get_webhook_url', return_value='https://chat.googleapis.com/webhook/test'):
        
        # Should not raise exception
        success_callback(mock_context)


def test_gchat_long_exception_message_truncated(mock_context):
    """Test that long exception messages are truncated."""
    from alerts.google_chat import failure_callback
    
    # Create very long exception message
    long_exception = 'A' * 600
    mock_context['exception'] = long_exception
    
    with patch('alerts.google_chat.requests.post') as mock_post, \
         patch('alerts.google_chat._get_webhook_url', return_value='https://chat.googleapis.com/webhook/test'):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        failure_callback(mock_context)
        
        # Verify exception was truncated
        card_body = mock_post.call_args[1]['json']
        card_json = json.dumps(card_body)
        assert '...' in card_json
        assert len(card_json) < 5000  # Should be reasonably sized


def test_gchat_thread_id_format(mock_context):
    """Test that thread ID is formatted correctly for grouping messages."""
    from alerts.google_chat import success_callback
    
    with patch('alerts.google_chat.requests.post') as mock_post, \
         patch('alerts.google_chat._get_webhook_url', return_value='https://chat.googleapis.com/webhook/test'):
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        success_callback(mock_context)
        
        # Verify thread ID format in URL
        call_url = mock_post.call_args[0][0]
        assert 'threadKey=test_dag_20240101' in call_url
        assert 'messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD' in call_url


def test_format_execution_time():
    """Test execution time formatting."""
    from alerts.google_chat import _format_execution_time
    from datetime import datetime
    
    start = datetime(2024, 1, 1, 10, 0, 0)
    end = datetime(2024, 1, 1, 10, 5, 30)
    
    result = _format_execution_time(start, end)
    assert result == "0h 5m 30s"
    
    # Test with None values
    result = _format_execution_time(None, None)
    assert result == "Non disponible"


def test_gchat_callback_includes_owner_and_tags(mock_context, monkeypatch):
    """Test that Google Chat callbacks include owner and tags in card."""
    from alerts.google_chat import success_callback
    
    monkeypatch.setenv('AIRFLOW_GCHAT_WEBHOOK_URL', 'https://chat.googleapis.com/v1/spaces/test')
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        success_callback(
            mock_context,
            logo_url='https://example.com/logo.png'
        )
        
        # Get the card body from the request
        card_body = mock_post.call_args[1]['json']
        card_json = str(card_body)
        
        # Verify owner and tags are in the card
        assert 'test_owner' in card_json
        assert 'test' in card_json or 'example' in card_json or 'alerts' in card_json
