import logging
from typing import Optional

from logstash_async.handler import AsynchronousLogstashHandler
from logstash_async.transport import Transport

import http_logging
from http_logging.secondary_classes import HttpHost


class AsyncHttpHandler(AsynchronousLogstashHandler):

    def __init__(
        self,
        *,  # Prevent usage of positional args
        http_host: Optional[http_logging.HttpHost] = None,
        support_class: Optional[http_logging.SupportClass] = None,
        transport_class: Optional[Transport] = None,
        formatter_class: Optional[logging.Formatter] = None,
        config: Optional[http_logging.ConfigLog] = None,
        **kwargs,
    ):
        if not http_host:
            http_host = HttpHost(name=None)

        self.http_host = http_host
        self.support_class = support_class
        self.config = config

        # Register this Handler as the HttpHost parent
        self.http_host.register_parent_handler(handler=self)

        # Set default ConfigLog params
        if self.config is None:
            self.config = http_logging.ConfigLog()

        # Set default support class
        if self.support_class is None:
            self.support_class = http_logging.SupportClass(
                http_host=http_host,
                config=config,
                _transport=transport_class,
                _formatter=formatter_class,
            )

        super().__init__(
            host=self.http_host.name,
            port=self.http_host.port,
            database_path=self.config.database_path,
            transport=self.support_class.transport,
            ssl_enable=self.config.security.ssl_enable,
            ssl_verify=self.config.security.ssl_verify,
            keyfile=self.config.security.keyfile,
            certfile=self.config.security.certfile,
            ca_certs=self.config.security.ca_certs,
            enable=self.config.enable,
            event_ttl=self.config.event_ttl,
            encoding=self.config.encoding,
            **kwargs,
        )

        self.formatter = self.support_class.formatter
