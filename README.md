# Bunyan Formatter

<!-- toc -->

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
  * [Django](#django)
- [Examples](#examples)
  * [Basic Logging](#basic-logging)
  * [Error Logging with Exception](#error-logging-with-exception)
  * [Custom Fields](#custom-fields)
- [Contributing](#contributing)
- [License](#license)

<!-- tocstop -->

A custom formatter for Python's logging module that outputs logs in the Bunyan
JSON format.

## Description

This package provides a `BunyanFormatter` class that formats log records into
the Bunyan JSON format. Bunyan is a lightweight JSON logger for Node.js, but
this formatter allows you to use the same log format in Python projects.

Key features:

- Outputs logs in JSON format
- Includes project name, hostname, file path, line number, and other metadata
- Supports various log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Handles both project and external file paths

## Installation

To install the Bunyan Formatter package, run:

```bash
pip install bunyan-formatter
```

## Usage

Here's a basic example of how to use the Bunyan Formatter in your Python project:

```python
import logging
from bunyan_formatter import BunyanFormatter

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a handler and set the formatter
handler = logging.StreamHandler()
formatter = BunyanFormatter(project_name="MyProject", project_root="/path/to/my/project")
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Now you can use the logger
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
```

### Django

In your Django project's `settings.py` file, add the following logging configuration:

```python
BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "bunyan": {
            "()": BunyanFormatter,
            "project_name": "MyProject",
            "project_root": BASE_DIR,
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "bunyan",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "bunyan",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    },
}
```

## Examples

### Basic Logging

```python
logger.info("User logged in", extra={"username": "john_doe"})
```

Output:

```json
{
  "v": 0,
  "name": "MyProject",
  "msg": "User logged in",
  "level": 30,
  "levelname": "INFO",
  "hostname": "your-hostname",
  "target": "__main__",
  "line": 10,
  "file": "main.py",
  "extra": {
    "username": "john_doe"
  }
}
```

### Error Logging with Exception

```python
try:
    result = 1 / 0
except ZeroDivisionError as e:
    logger.exception("An error occurred", exc_info=True)
```

Output:

```json
{
  "v": 0,
  "name": "MyProject",
  "msg": "An error occurred",
  "level": 50,
  "levelname": "ERROR",
  "hostname": "your-hostname",
  "target": "__main__",
  "line": 15,
  "file": "main.py",
  "err": {
    "message": "division by zero",
    "name": "ZeroDivisionError",
    "stack": [
      // Stack trace here
    ]
  }
}
```

### Custom Fields

You can add custom fields to your log entries:

```python
logger.info("Order processed", extra={
    "order_id": 12345,
    "customer_id": 67890,
    "total_amount": 100.00
})
```

Output:

```json
{
  "v": 0,
  "name": "MyProject",
  "msg": "Order processed",
  "level": 30,
  "levelname": "INFO",
  "hostname": "your-hostname",
  "target": "__main__",
  "line": 20,
  "file": "main.py",
  "extra": {
    "order_id": 12345,
    "customer_id": 67890,
    "total_amount": 100.0
  }
}
```

## Contributing

Contributions are welcome! Please submit pull requests or issues on our GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
