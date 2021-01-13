from dataclasses import dataclass
import logging
from typing import Callable

from logstash_async.transport import Transport

import http_logging.constants as constants


logger = logging.getLogger('http-logging')


@dataclass
class HttpHost:
    name: str
    _port: int = None
    path: str = None
    timeout: int = constants.TIMEOUT
    _parentHandler = None

    @property
    def port(self) -> int:
        return self._port or self.default_port

    @property
    def default_port(self) -> int:
        return constants.HTTPS_PORT if self.ssl_enable else constants.HTTP_PORT

    @property
    def ssl_enable(self) -> bool:
        if not self._parentHandler:
            return True

        return self._parentHandler.config.security.ssl_enable

    def get_parent_handler(self) -> 'AsyncHttpHandler':
        return self._parentHandler

    def register_parent_handler(
        self,
        handler: 'AsyncHttpHandler',
    ) -> None:
        self._parentHandler = handler


@dataclass
class HttpSecurity:
    ssl_enable: bool = True,
    ssl_verify: bool = True,
    keyfile: str = None,
    certfile: str = None,
    ca_certs: list = None,


@dataclass
class ConfigLog:
    database_path: str = constants.DATABASE_PATH
    event_ttl: int = None
    use_logging: bool = False
    encoding: str = constants.ENCODING
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
        import http_logging.transport

        if self._transport is None:
            self._transport = http_logging.transport.AsyncHttpTransport(
                http_host=self.http_host,
                config=self.config,
            )
        return self._transport

    @property
    def formatter(self):
        import http_logging.formatter

        if self._formatter is None:
            self._formatter = http_logging.formatter.HttpLogFormatter()
        return self._formatter