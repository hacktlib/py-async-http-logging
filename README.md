# Asynchronous HTTP Logging

Non-blocking HTTP handler for Python `logging` with local SQLite buffer/cache.

> This library was written for [Hackt CLI](https://hackt.app/?utm_source=github&utm_medium=gitlink&utm_campaign=oss-py-async-http-logging) and open sourced for anyone interested.

![Test Coverage](https://raw.githubusercontent.com/hacktlib/py-async-http-logging/main/coverage.svg)
[![PyPI](https://img.shields.io/pypi/v/http_logging)](https://pypi.org/project/http_logging/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Requirements Status](https://requires.io/github/hacktlib/py-async-http-logging/requirements.svg?branch=main)](https://requires.io/github/hacktlib/py-async-http-logging/requirements/?branch=main)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-lightgrey)](https://github.com/hhatto/autopep8/)
[![Code Formatter](https://img.shields.io/badge/formatter-autopep8-lightgrey)](https://github.com/hhatto/autopep8/)
[![Test Framework](https://img.shields.io/badge/testing-pytest-lightgrey)](https://github.com/pytest-dev/pytest/)


## Documentation

Please refer to the [project Wiki](https://github.com/hacktlib/py-async-http-logging/wiki).


## Installation

> [Virtual environment](https://docs.python.org/3/tutorial/venv.html) is highly recommended.

```shell
pip install http_logging
```


## Basic usage

```python
import logging
from http_logging import AsyncHttpHandler

log_handler = AsyncHttpHandler(host='your-domain.com')

logger = logging.getLogger()
logger.addHandler(log_handler)

logger.info('Some useful information...')
logger.error('Ooops!')
```

These log messages are cached in a local SQLite database and periodically delivered (asynchronously, in a separate thread) to your host in a POST request with a body similar to this one:

```json
[
    {
        "type": "async-http-logging",
        "created": 1610393068.365492,
        "relative_created": 1505.5122375488281,
        "message": "Some useful information...",
        "level": {
            "number": 20,
            "name": "INFO"
        },
        "sourcecode": {
            "pathname": "/path/to/your/python/script.py",
            "function": "function_name",
            "line": 123
        },
        "process": {
            "id": 1234,
            "name": "MainProcess"
        },
        "thread": {
            "id": 1234567890,
            "name": "MainThread"
        }
    },
    {
        "type": "async-http-logging",
        "created": 1610393068.3663092,
        "relative_created": 1506.3292980194092,
        "message": "Ooops!",
        "level": {
            "number": 40,
            "name": "ERROR"
        },
        "sourcecode": {
            "pathname": "/path/to/your/python/script.py",
            "function": "function_name",
            "line": 456
        },
        "process": {
            "id": 1234,
            "name": "MainProcess"
        },
        "thread": {
            "id": 1234567890,
            "name": "MainThread"
        }
    }
]
```

In your backend, you can funnel these logs to wherever suits you best: database, ElasticSearch index, third-party monitoring service, etc.

Learn more about these and other features in the [project Wiki](https://github.com/hacktlib/py-async-http-logging/wiki).
