from dataclasses import dataclass
import logging
import os
import sys
from typing import Callable

from logstash_async import constants
from logstash_async.transport import Transport

from .formatter import HttpLogFormatter
from .handler import AsyncHttpHandler
from .transport import AsyncHttpTransport


__all__ = [
    # Main classes
    'AsyncHttpHandler',
    'AsyncHttpTransport',
    'HttpLogFormatter',

    # Secondary classes
    'ConfigLog',
    'HttpHost',
    'HttpSecurity',
    'SupportClass',
]


logger = logging.getLogger('http-logging')


HTTP_PORT = int(os.environ.get('ASYNC_LOG_HTTP_PORT', 80))
HTTPS_PORT = int(os.environ.get('ASYNC_LOG_HTTPS_PORT', 443))
DATABASE_PATH = os.environ.get('ASYNC_LOG_DATABASE_PATH', 'logging-cache.db')
TIMEOUT = float(os.environ.get('ASYNC_LOG_TIMEOUT', 5.0))
ENCODING = os.environ.get('ASYNC_LOG_ENCODING', sys.getfilesystemencoding())


# Override constants
constants.SOCKET_TIMEOUT = TIMEOUT
constants.QUEUE_CHECK_INTERVAL = float(os.environ.get('ASYNC_LOG_QUEUE_CHECK_INTERVAL', 1.0))  # NOQA
constants.QUEUED_EVENTS_FLUSH_INTERVAL = float(os.environ.get('ASYNC_LOG_QUEUED_EVENTS_FLUSH_INTERVAL', 5.0))  # NOQA
constants.QUEUED_EVENTS_FLUSH_COUNT = int(os.environ.get('ASYNC_LOG_QUEUED_EVENTS_FLUSH_COUNT', 10))  # NOQA
constants.QUEUED_EVENTS_BATCH_SIZE = int(os.environ.get('ASYNC_LOG_QUEUED_EVENTS_BATCH_SIZE', 10))  # NOQA
constants.DATABASE_TIMEOUT = float(os.environ.get('ASYNC_LOG_DATABASE_TIMEOUT', 2.5))  # NOQA


@dataclass
class HttpHost:
    name: str
    _port: int = None
    path: str = None
    timeout: int = TIMEOUT

    @property
    def port(self) -> int:
        return self._port or self.default_port

    @property
    def default_port(self, ssl_enable: bool) -> int:
        return HTTPS_PORT if ssl_enable else HTTP_PORT


@dataclass
class HttpSecurity:
    ssl_enable: bool = True,
    ssl_verify: bool = True,
    keyfile: str = None,
    certfile: str = None,
    ca_certs: list = None,


@dataclass
class ConfigLog:
    database_path: str = DATABASE_PATH
    event_ttl: int = None
    use_logging: bool = False
    encoding: str = ENCODING
    custom_headers: Callable = None
    enable: bool = True,
    security: HttpSecurity = HttpSecurity()


@dataclass
class SupportClass:
    http_host: HttpHost
    config: ConfigLog = ConfigLog()
    _transport: Transport = None
    _formatter: logging.Formatter = None

    @property
    def transport(self):
        if self._transport is None:
            self._transport = AsyncHttpTransport(
                http_host=self.http_host,
                config=self.config,
            )
        return self._transport

    @property
    def formatter(self):
        if self._formatter is None:
            self._formatter = HttpLogFormatter()
        return self._formatter
