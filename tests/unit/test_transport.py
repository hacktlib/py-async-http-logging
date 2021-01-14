from unittest import mock

import pytest
import requests

import http_logging
from http_logging.transport import AsyncHttpTransport


@pytest.fixture
def get_http_host():
    return lambda: http_logging.HttpHost(
        name='dummy-host.com',
        port=1234,
        path='dummy-path',
    )


def test_custom_path(get_http_host):
    http_host = get_http_host()

    transport = AsyncHttpTransport(http_host=http_host)

    assert transport._path == http_host.path


def test_url_property(get_http_host):
    http_host = get_http_host()
    http_host.port = None

    security = http_logging.HttpSecurity(ssl_enable=False)
    config = http_logging.ConfigLog(security=security)

    transport = AsyncHttpTransport(
        http_host=http_host,
        config=config,
    )

    assert transport.url == \
        f'http://{http_host.name}/{http_host.path}'

    security.ssl_enable = True

    transport = AsyncHttpTransport(
        http_host=http_host,
        config=config,
    )

    assert transport.url == \
        f'https://{http_host.name}/{http_host.path}'

    http_host.port = 1234

    transport = AsyncHttpTransport(
        http_host=http_host,
        config=config,
    )

    assert transport.url == \
        f'https://{http_host.name}:{http_host.port}/{http_host.path}'


def test_headers_property(get_http_host):
    http_host = get_http_host()

    transport = AsyncHttpTransport(
        http_host=http_host,
    )

    transport.get_custom_headers = mock.Mock(return_value={})

    assert transport.headers == {'Content-Type': 'application/json'}

    transport.get_custom_headers = mock.Mock(return_value={'foo': 'bar'})

    assert transport.headers == {
        'Content-Type': 'application/json',
        'foo': 'bar',
    }


def test_get_custom_headers(get_http_host):
    http_host = get_http_host()

    transport = AsyncHttpTransport(
        http_host=http_host,
    )

    assert transport.get_custom_headers() == {}

    dummy_headers = {'foo': 'bar'}
    mock_custom_headers = mock.Mock(return_value=dummy_headers)

    config = http_logging.ConfigLog(custom_headers=mock_custom_headers)

    transport = AsyncHttpTransport(
        http_host=http_host,
        config=config,
    )

    assert transport.get_custom_headers() == dummy_headers


@mock.patch('http_logging.transport.json')
@mock.patch('http_logging.transport.logger')
@mock.patch('http_logging.transport.requests')
def test_send_success_request(
    mock_requests,
    mock_logger,
    mock_json,
    get_http_host,
):
    http_host = get_http_host()
    security = http_logging.HttpSecurity(ssl_enable=True)
    config = http_logging.ConfigLog(
        use_logging=True,
        security=security,
    )

    mock_response = mock.Mock()
    mock_response.ok = False
    mock_post = mock.Mock(return_value=mock_response)
    mock_requests.Session().post = mock_post

    mock_json.dumps().encoding.return_value = '{"foo": "bar"}'

    transport = AsyncHttpTransport(
        http_host=http_host,
        config=config,
    )

    events = mock.Mock()
    batches = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]
    for batch in batches:
        batch.__len__.return_value = 10

    transport._AsyncHttpTransport__batches = mock.Mock(return_value=batches)

    transport.send(events=events)

    transport._AsyncHttpTransport__batches.assert_called_with(events)
    mock_logger.debug.assert_called()
    mock_logger.exception.assert_not_called()
    mock_requests.Session.assert_called()

    post_requests = mock_post.mock_calls

    assert len(post_requests) == 3

    for batch in batches:
        expected_request = mock.call(
            transport.url,
            headers=transport.headers,
            json=batch,
            verify=transport._ssl_verify,
            timeout=transport._timeout,
        )

        assert expected_request in post_requests


@mock.patch('http_logging.transport.json')
@mock.patch('http_logging.transport.logger')
@mock.patch('http_logging.transport.requests')
def test_send_failed_request(
    mock_requests,
    mock_logger,
    mock_json,
    get_http_host,
):
    http_host = get_http_host()
    security = http_logging.HttpSecurity(ssl_enable=True)
    config = http_logging.ConfigLog(
        use_logging=True,
        security=security,
    )

    req_exception = requests.exceptions.RequestException('HTTP Error')
    mock_response = mock.Mock()
    mock_response.ok = False  # Simulate failed request
    mock_response.raise_for_status.side_effect = req_exception
    mock_post = mock.Mock(return_value=mock_response)
    mock_requests.Session().post = mock_post

    mock_json.dumps().encoding.return_value = '{"foo": "bar"}'

    transport = AsyncHttpTransport(
        http_host=http_host,
        config=config,
    )

    events = mock.Mock()
    batches = [mock.MagicMock()]

    batches[0].__len__.return_value = 10

    transport._AsyncHttpTransport__batches = mock.Mock(return_value=batches)

    transport.send(events=events)

    assert len(mock_post.mock_calls) == 1

    mock_requests.Session().close.assert_called()
    mock_response.raise_for_status.assert_called()
    mock_logger.debug.assert_called()
    mock_logger.exception.assert_called_with(req_exception)
