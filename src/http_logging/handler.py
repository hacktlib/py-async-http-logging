from typing import Optional

from logstash_async.handler import AsynchronousLogstashHandler

from http_logging import ConfigLog, HttpHost, SupportClass


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
