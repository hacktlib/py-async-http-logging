# Asynchronous HTTP Logging

Non-blocking HTTP handler for Python `logging` with local SQLite buffer/cache.

> This library was written for [Hackt CLI](https://hackt.app/?utm_source=github&utm_medium=gitlink&utm_campaign=oss-py-async-http-logging) and open sourced for anyone interested.

![Test Coverage](https://raw.githubusercontent.com/hacktlib/py-async-http-logging/main/coverage.svg)
![Maintained](https://img.shields.io/maintenance/yes/2021)
[![Maintainability](https://img.shields.io/codeclimate/maintainability/hacktlib/py-async-http-logging)](https://codeclimate.com/github/hacktlib/py-async-http-logging)
[![Technical Debt](https://img.shields.io/codeclimate/tech-debt/hacktlib/py-async-http-logging)](https://codeclimate.com/github/hacktlib/py-async-http-logging)
[![Issues](https://img.shields.io/codeclimate/issues/hacktlib/py-async-http-logging)](https://codeclimate.com/github/hacktlib/py-async-http-logging/issues?category=complexity&engine_name%5B%5D=structure&engine_name%5B%5D=duplication)

[![Requirements Status](https://requires.io/github/hacktlib/py-async-http-logging/requirements.svg?branch=main)](https://requires.io/github/hacktlib/py-async-http-logging/requirements/?branch=main)
[![PyPI](https://img.shields.io/pypi/v/http_logging)](https://pypi.org/project/http_logging/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

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
from http_logging import AsyncHttpHandler, HttpHost

log_handler = AsyncHttpHandler(http_host=HttpHost(name='your-domain.com'))

logger = logging.getLogger()
logger.addHandler(log_handler)

# Works with simple log messages like:
logger.info('Some useful information...')

# Can also handle extra fields:
logger.warning('You\'ve been warned!', extra={'foo': 'bar'})

# And, of course, captures exception with full stack-trace
try:
    1/0
except Exception as exc:
    logger.error('Ooops!', exc_info=exc)
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
        "stack_trace": null,
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
        "message": "You've been warned!",
        "level": {
            "number": 30,
            "name": "WARNING"
        },
        "stack_trace": null,
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
        "stack_trace": "Traceback (most recent call last):\n  File \"/path/to/your/python/script.py\", line 17, in function_name\n    1/0\nZeroDivisionError: division by zero\n",
        "sourcecode": {
            "pathname": "/path/to/your/python/script.py",
            "function": "function_name",
            "line": 17
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
