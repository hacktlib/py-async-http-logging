from unittest import mock

import http_logging


def test_default_args():
    handler = http_logging.AsyncHttpHandler(host='dummy-host.com')

    handler._setup_transport()

    assert handler._host == 'dummy-host.com'
    assert isinstance(handler._transport, http_logging.AsyncHttpTransport)
    assert isinstance(handler.formatter, http_logging.HttpLogFormatter)
    assert handler._port == http_logging.HTTPS_PORT


def test_custom_formatter_and_transport():
    transport = http_logging.AsyncHttpTransport(host='dummy-host.com')
    formatter = http_logging.HttpLogFormatter()

    handler = http_logging.AsyncHttpHandler(
        host='dummy-host.com',
        transport=transport,
        formatter=formatter,
    )

    handler._setup_transport()

    assert handler._transport == transport
    assert handler.formatter == formatter
