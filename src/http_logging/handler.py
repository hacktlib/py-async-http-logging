from typing import Optional

from logstash_async.handler import AsynchronousLogstashHandler

import http_logging


class AsyncHttpHandler(AsynchronousLogstashHandler):

    def __init__(
        self,
        *,  # Prevent usage of positional args
        http_host: http_logging.HttpHost,
        support_class: Optional[http_logging.SupportClass] = None,
        config: Optional[http_logging.ConfigLog] = None,
        **kwargs,
    ):
        self.http_host = http_host
        self.support_class = support_class
        self.config = config

        # Register this Handler as the HttpHost parent
        self.http_host.register_parent_handler(handler=self)

        # Set default ConfigLog params
        if self.config is None:
            self.config = http_logging.ConfigLog()

        # Set default support classes
        if self.support_class is None:
            self.support_class = http_logging.SupportClass(
                http_host=http_host,
                config=config,
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
