from unittest import mock

import pytest
import requests

import http_logging


def test_custom_path():
    host = 'dummy-host.com'
    path = 'dummy-path'

    transport = http_logging.AsyncHttpTransport(
        host=host,
        path=path,
    )

    assert transport._path == path


def test_url_property():
    host = 'dummy-host.com'
    port = 1234
    path = 'dummy-path'

    transport = http_logging.AsyncHttpTransport(
        host=host,
        path=path,
        ssl_enable=False,
    )

    assert transport.url == f'http://{host}/{path}'

    transport = http_logging.AsyncHttpTransport(
        host=host,
        path=path,
        ssl_enable=True,
    )

    assert transport.url == f'https://{host}/{path}'

    transport = http_logging.AsyncHttpTransport(
        host=host,
        port=port,
        path=path,
        ssl_enable=True,
    )

    assert transport.url == f'https://{host}:{port}/{path}'


def test_headers_property():
    transport = http_logging.AsyncHttpTransport(
        host='dummy-host.com',
    )

    transport.get_custom_headers = mock.Mock(return_value={})

    assert transport.headers == {'Content-Type': 'application/json'}

    transport.get_custom_headers = mock.Mock(return_value={'foo': 'bar'})

    assert transport.headers == {
        'Content-Type': 'application/json',
        'foo': 'bar',
    }


def test_get_custom_headers():
    transport = http_logging.AsyncHttpTransport(
        host='dummy-host.com',
    )

    assert transport.get_custom_headers() == {}

    dummy_headers = {'foo': 'bar'}
    mock_custom_headers = mock.Mock(return_value=dummy_headers)

    transport = http_logging.AsyncHttpTransport(
        host='dummy-host.com',
        custom_headers=mock_custom_headers,
    )

    assert transport.get_custom_headers() == dummy_headers


@mock.patch('http_logging.logger')
@mock.patch('http_logging.requests')
def test_send_success_request(mock_requests, mock_logger):
    mock_response = mock.Mock()
    mock_response.ok = False
    mock_post = mock.Mock(return_value=mock_response)
    mock_requests.Session().post = mock_post

    transport = http_logging.AsyncHttpTransport(
        host='dummy-host.com',
        use_logging=False,
        ssl_enable=True,
    )

    events = mock.Mock()
    batches = [mock.Mock(), mock.Mock(), mock.Mock()]

    transport._AsyncHttpTransport__batches = mock.Mock(return_value=batches)

    transport.send(events=events, use_logging=False)

    transport._AsyncHttpTransport__batches.assert_called_with(events)
    mock_logger.debug.assert_not_called()
    mock_requests.Session.assert_called_with()

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


@mock.patch('http_logging.requests')
def test_send_failed_request(mock_requests):
    mock_response = mock.Mock()
    mock_response.ok = False  # Simulate failed request
    mock_post = mock.Mock(return_value=mock_response)
    mock_requests.Session().post = mock_post

    transport = http_logging.AsyncHttpTransport(
        host='dummy-host.com',
        use_logging=False,
    )

    events = mock.Mock()
    batches = [mock.Mock()]

    transport._AsyncHttpTransport__batches = mock.Mock(return_value=batches)

    transport.send(events=events, use_logging=False)

    assert len(mock_post.mock_calls) == 1

    mock_requests.Session().close.assert_called_with()
    mock_response.raise_for_status.assert_called_with()


@mock.patch('http_logging.json')
@mock.patch('http_logging.logger')
@mock.patch('http_logging.requests.Session')
def test_send_using_logging(mock_session, mock_logger, mock_json):
    connection_error = requests.exceptions.ConnectionError()
    mock_post = mock.Mock(side_effect=connection_error)
    mock_session().post = mock_post

    transport = http_logging.AsyncHttpTransport(
        host='dummy-host.com',
        use_logging=True,
    )

    events = mock.Mock()
    batch_length = 123
    batch_size = 456
    batch = mock.MagicMock()
    batch.__len__.return_value = batch_length

    serialized_batch = mock.MagicMock()
    serialized_batch.__len__.return_value = batch_size
    mock_json.dumps().encode.return_value = serialized_batch

    transport._AsyncHttpTransport__batches = mock.Mock(return_value=[batch])

    try:
        transport.send(events=events, use_logging=False)
    except requests.exceptions.ConnectionError:
        pytest.fail('Uncaught requests.exceptions.ConnectionError')

    debug_msg = 'Batch length: %s, Batch size: %s'
    mock_logger.debug.assert_called_with(debug_msg, batch_length, batch_size)
    mock_logger.exception.assert_called_with(connection_error)
