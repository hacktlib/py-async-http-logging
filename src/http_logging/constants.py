import os
import sys

from logstash_async.constants import constants as logstash_constants


HTTP_PORT = int(os.environ.get('ASYNC_LOG_HTTP_PORT', 80))
HTTPS_PORT = int(os.environ.get('ASYNC_LOG_HTTPS_PORT', 443))
DATABASE_PATH = os.environ.get('ASYNC_LOG_DATABASE_PATH', 'logging-cache.db')
TIMEOUT = float(os.environ.get('ASYNC_LOG_TIMEOUT', 5.0))
ENCODING = os.environ.get('ASYNC_LOG_ENCODING', sys.getfilesystemencoding())


# Override LogStash constants
logstash_constants.SOCKET_TIMEOUT = TIMEOUT

logstash_constants.QUEUE_CHECK_INTERVAL = float(
    os.environ.get('ASYNC_LOG_QUEUE_CHECK_INTERVAL', 1.0))

logstash_constants.QUEUED_EVENTS_FLUSH_INTERVAL = float(
    os.environ.get('ASYNC_LOG_QUEUED_EVENTS_FLUSH_INTERVAL', 5.0))

logstash_constants.QUEUED_EVENTS_FLUSH_COUNT = int(
    os.environ.get('ASYNC_LOG_QUEUED_EVENTS_FLUSH_COUNT', 10))

logstash_constants.QUEUED_EVENTS_BATCH_SIZE = int(
    os.environ.get('ASYNC_LOG_QUEUED_EVENTS_BATCH_SIZE', 10))

logstash_constants.DATABASE_TIMEOUT = float(
    os.environ.get('ASYNC_LOG_DATABASE_TIMEOUT', 2.5))
