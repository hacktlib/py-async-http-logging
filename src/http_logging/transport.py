import json
import logging
from typing import List, Union

from logstash_async.transport import HttpTransport
import requests

from http_logging import ConfigLog, HttpHost


logger = logging.getLogger('http-logging')


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

    def send(self, events: list, **kwargs) -> None:
        self.__session = requests.Session()

        for batch in self.__batches(events):
            self.log_batch(batch=batch)
            self.send_batch(batch=batch)

        self.__session.close()

    def log_http_request(
        self,
        method: str,
        content: Union[str, Exception],
        **kwargs,
    ) -> None:
        if self._use_logging:
            getattr(logger, method)(content, **kwargs)

    def log_batch(self, batch: List[dict]) -> None:
        options = (len(batch), len(json.dumps(batch).encode('utf8')))
        message = 'Batch length: %s, Batch size: %s' % options
        self.log_http_request('debug', message)

    def send_batch(self, batch: dict) -> None:
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
        except requests.exceptions.RequestException as exc:
            self.log_http_request('exception', exc)
