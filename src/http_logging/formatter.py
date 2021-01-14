import copy
import logging
from typing import Callable, Optional, Union

from logstash_async.formatter import LogstashFormatter


class HttpLogFormatter(LogstashFormatter):

    def __init__(
        self,
        *,  # Prevent usage of positional args
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
