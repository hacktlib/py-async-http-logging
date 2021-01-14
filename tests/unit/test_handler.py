import pytest

import http_logging
from http_logging.formatter import HttpLogFormatter
from http_logging.handler import AsyncHttpHandler
from http_logging.transport import AsyncHttpTransport


@pytest.fixture
def http_host():
    return http_logging.HttpHost(name='dummy-host.com')


def test_default_args(http_host):
    handler = AsyncHttpHandler(http_host=http_host)

    handler._setup_transport()

    assert handler._host == 'dummy-host.com'
    assert isinstance(handler._transport, AsyncHttpTransport)
    assert isinstance(handler.formatter, HttpLogFormatter)


def test_custom_formatter_and_transport(http_host):
    config = http_logging.ConfigLog()
    transport = AsyncHttpTransport(http_host=http_host, config=config)
    formatter = HttpLogFormatter()

    handler = AsyncHttpHandler(
        http_host=http_host,
        support_class=http_logging.SupportClass(
            http_host=http_host,
            config=config,
            _transport=transport,
            _formatter=formatter,
        ),
    )

    handler._setup_transport()

    assert handler._transport == transport
    assert handler.formatter == formatter
