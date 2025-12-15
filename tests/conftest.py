"""Pytest configuration and fixtures."""
import pytest
from datetime import datetime
from unittest.mock import Mock


@pytest.fixture
def mock_context():
    """Create a mock Airflow context for testing."""
    context = {
        'dag': Mock(dag_id='test_dag', description='Test DAG description'),
        'task': Mock(retries=2),
        'task_instance': Mock(
            task_id='test_task',
            try_number=1,
            start_date=datetime(2024, 1, 1, 10, 0, 0),
            end_date=datetime(2024, 1, 1, 10, 5, 0)
        ),
        'execution_date': datetime(2024, 1, 1, 9, 0, 0),
        'ts': '2024-01-01T09:00:00+00:00',
        'exception': 'Test exception message',
        'next_retry_datetime': datetime(2024, 1, 1, 10, 10, 0)
    }
    return context


@pytest.fixture
def mock_jinja_env(mocker):
    """Mock Jinja2 environment."""
    mock_env = mocker.Mock()
    mock_template = mocker.Mock()
    mock_template.render.return_value = "<html>Rendered template</html>"
    mock_env.get_template.return_value = mock_template
    return mock_env
