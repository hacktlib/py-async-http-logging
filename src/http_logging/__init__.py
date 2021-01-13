import copy
import json
import logging
import os
import sys
from typing import Callable, Dict, List, Optional, Union

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


class AsyncHttpHandler(AsynchronousLogstashHandler):

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        path: Optional[str] = None,
        timeout: int = TIMEOUT,
        database_path: str = DATABASE_PATH,
        transport: Transport = None,
        formatter: logging.Formatter = None,
        custom_headers: Callable = None,
        ssl_enable: bool = True,
        ssl_verify: bool = True,
        keyfile=None,
        certfile=None,
        ca_certs=None,
        enable: bool = True,
        event_ttl: int = None,
        encoding: str = ENCODING,
        use_logging: bool = False,
        **kwargs,
    ):
        # Default to customized HTTP Transport
        if transport is None:
            transport = AsyncHttpTransport(
                host=host,
                port=port,
                path=path,
                timeout=timeout,
                ssl_enable=ssl_enable,
                ssl_verify=ssl_verify,
                use_logging=use_logging,
                custom_headers=custom_headers,
            )

        super().__init__(
            host=host,
            port=port or HTTPS_PORT if ssl_enable else HTTP_PORT,
            database_path=database_path,
            transport=transport,
            ssl_enable=ssl_enable,
            ssl_verify=ssl_verify,
            keyfile=keyfile,
            certfile=certfile,
            ca_certs=ca_certs,
            enable=enable,
            event_ttl=event_ttl,
            encoding=encoding,
            **kwargs,
        )

        # Default to HttpLogFormatter
        if formatter is None:
            formatter = HttpLogFormatter()

        self.formatter = formatter


class AsyncHttpTransport(HttpTransport):

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        path: Optional[str] = None,
        timeout: Union[None, float] = TimeoutNotSet,
        ssl_enable: bool = True,
        ssl_verify: Union[bool, str] = True,
        use_logging: bool = False,
        custom_headers: Callable = None,
        **kwargs
    ):
        super().__init__(
            host=host,
            port=port,
            timeout=timeout,
            ssl_enable=ssl_enable,
            ssl_verify=ssl_verify,
            use_logging=use_logging,
            **kwargs,
        )

        self.__batches = super()._HttpTransport__batches

        self._path = path
        self._custom_headers = custom_headers

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
            'sourcecode': {
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
