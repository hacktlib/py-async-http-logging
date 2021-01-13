import copy
from dataclasses import dataclass
import json
import logging
import os
import sys
from typing import Callable, List, Optional, Union

from logstash_async import constants
from logstash_async.formatter import LogstashFormatter
from logstash_async.handler import AsynchronousLogstashHandler
from logstash_async.transport import HttpTransport, TimeoutNotSet, Transport
import requests


logger = logging.getLogger(__name__)

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


class AsyncHttpHandler(AsynchronousLogstashHandler):

    def __init__(
        self,
        http_host: HttpHost,
        support_class: Optional[SupportClass] = None,
        config: Optional[ConfigLog] = None,
        **kwargs,
    ):
        self.http_host = http_host
        self.support_class = support_class
        self.config = config

        # Set default ConfigLog params
        if self.config is None:
            self.config = ConfigLog()

        # Set default support classes
        if self.support_class is None:
            self.support_class = SupportClass(
                http_host=http_host,
                config=config,
            )

        super().__init__(
            host=http_host.host,
            port=http_host.port,
            database_path=config.database_path,
            transport=support_class.transport,
            ssl_enable=config.security.ssl_enable,
            ssl_verify=config.security.ssl_verify,
            keyfile=config.security.keyfile,
            certfile=config.security.certfile,
            ca_certs=config.security.ca_certs,
            enable=config.enable,
            event_ttl=config.event_ttl,
            encoding=config.encoding,
            **kwargs,
        )

        self.formatter = support_class.formatter


class AsyncHttpTransport(HttpTransport):

    def __init__(
        self,
        http_host: HttpHost,
        config: ConfigLog = ConfigLog(),
        **kwargs
    ):
        super().__init__(
            host=http_host.host,
            port=http_host.port,
            timeout=http_host.timeout,
            ssl_enable=config.security.ssl_enable,
            ssl_verify=config.security.ssl_verify,
            use_logging=config.use_logging,
            **kwargs,
        )

        self.__batches = super()._HttpTransport__batches

        self._path = http_host.path
        self._custom_headers = config.custom_headers

    @property
    def url(self) -> str:
        protocol = 'https' if self._ssl_enable else 'http'
        port = f':{self._port}' if type(self._port) is int else ''
        path = f'/{self._path}' if type(self._path) is str else ''

        return f'{protocol}://{self._host}{port}{path}'

    @property
    def headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            **self.get_custom_headers(),
        }

    def get_custom_headers(self) -> dict:
        if not callable(self._custom_headers):
            return {}
        return self._custom_headers()

    def send(self, events: list, use_logging: bool = False, **kwargs) -> None:
        self.__session = requests.Session()

        for batch in self.__batches(events):
            if self._use_logging or use_logging:
                logger.debug(
                    'Batch length: %s, Batch size: %s',
                    len(batch),
                    len(json.dumps(batch).encode('utf8')),
                )

            try:
                response = self.__session.post(
                    self.url,
                    headers=self.headers,
                    json=batch,
                    verify=self._ssl_verify,
                    timeout=self._timeout,
                )

                if not response.ok:
                    self.__session.close()
                    response.raise_for_status()

            except requests.exceptions.ConnectionError as exc:
                if self._use_logging or use_logging:
                    logger.exception(exc)

        self.__session.close()


class HttpLogFormatter(LogstashFormatter):

    def __init__(
        self,
        message_type: str = 'async-http-log',
        tags: Optional[list] = None,
        fully_qualified_domain_name: Union[str, bool] = False,
        extension: Callable = None,
        extra_prefix: str = 'extra',
        extra: Optional[dict] = None,
        ensure_ascii: bool = True,
        metadata: Optional[dict] = None,
    ) -> None:
        super().__init__(
            message_type=message_type,
            tags=tags,
            fqdn=fully_qualified_domain_name,
            extra_prefix=extra_prefix,
            extra=extra,
            ensure_ascii=ensure_ascii,
            metadata=metadata,
        )

        self._extension = extension
        self._default_log_record_keys = None

    @property
    def default_log_record_keys(self):
        '''Extract __dict__.keys from a dummy LogRecord object'''
        if self._default_log_record_keys is None:
            dummy_record = logging.LogRecord(
                name="INFO",
                level=20,
                pathname="/",
                lineno=1,
                msg="Message",
                args=(),
                exc_info=None,
            )

            self._default_log_record_keys = dummy_record.__dict__.keys()

        return self._default_log_record_keys

    def build_log_message(self, record: logging.LogRecord):
        return {
            'type': self._message_type,
            'created': record.created,
            'relative_created': record.relativeCreated,
            'message': record.getMessage(),
            'level': {
                'number': record.levelno,
                'name': record.levelname,
            },
            'stack_trace': self._format_exception(record.exc_info),
            'source_code': {
                'pathname': record.pathname,
                'function': record.funcName,
                'line': record.lineno,
            },
            'process': {
                'id': record.process,
                'name': record.processName,
            },
            'thread': {
                'id': record.thread,
                'name': record.threadName,
            },
        }

    def format(self, record: logging.LogRecord):
        message = self.build_log_message(record=record)

        message = self._get_extra_fields(message, record)

        return self._serialize(message)

    def _get_extra_fields(
        self,
        message: dict,
        record: logging.LogRecord,
    ) -> dict:
        message = copy.deepcopy(message)

        extra = {
            key: getattr(record, key)
            for key in record.__dict__.keys()
            if key not in self.default_log_record_keys
        }

        if len(extra) > 0:
            message[self._extra_prefix] = extra

        return message
