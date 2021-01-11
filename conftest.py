from dataclasses import dataclass
import os
import pathlib
import sys
import time

import pexpect
import pytest


LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8768
LOCAL_SERVER_FILEPATH = 'tests/integration/localserver.py'
LOCAL_SERVER_TIMEOUT = 60


@dataclass
class LocalHost:
    host: str
    port: int
    filepath: int
    timeout: int
    secure: bool = False
    database_path: str = 'logging-cache.db'

    @property
    def protocol(self):
        return 'https' if self.secure else 'http'

    @property
    def url(self):
        return f'{self.protocol}://{self.host}:{self.port}'

    @property
    def all_responses_url(self):
        return f'{self.url}/get_all_responses'

    @property
    def last_response_url(self):
        return f'{self.url}/last_response'

    @property
    def clear_response_cache_url(self):
        return f'{self.url}/clear_response_cache'


@pytest.fixture(scope='session')
def localhost():
    return LocalHost(
        host=LOCAL_HOST,
        port=LOCAL_PORT,
        filepath=LOCAL_SERVER_FILEPATH,
        timeout=LOCAL_SERVER_TIMEOUT,
    )


@pytest.fixture(scope='session')
def run_localserver(localhost):
    print('Starting localserver...')

    # Remove cache from previous runs
    current_path = pathlib.Path(__file__).parent.absolute()
    database_path = os.path.join(current_path, localhost.database_path)
    if os.path.isfile(database_path):
        os.remove(database_path)

    # Run localserver
    _server = pexpect.spawnu(
        f'python {localhost.filepath} {str(localhost.port)}',
        timeout=localhost.timeout,
        logfile=sys.stdout
    )

    # Time for server start up, otherwise initial connections can be refused
    time.sleep(1)

    _server.expect('>> wait...', async_=True)

    yield

    if '_server' in locals().keys() and _server.isalive():
        print('Terminating localserver...')
        _server.close(force=True)
