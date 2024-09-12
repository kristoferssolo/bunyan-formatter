import json
import logging
import socket
import time
import traceback
from logging import Formatter, LogRecord
from pathlib import Path
from typing import Any, Optional

DEFAULT_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}

LEVEL_MAP = {
    logging.NOTSET: 10,
    logging.DEBUG: 20,
    logging.INFO: 30,
    logging.WARNING: 40,
    logging.ERROR: 50,
    logging.CRITICAL: 60,
}


class BunyanFormatter(Formatter):
    def __init__(self, project_name: str, project_root: Path) -> None:
        super().__init__()
        self.project_name = project_name
        self.project_root = project_root
        self.hostname = socket.gethostname()

    def format(self, record: LogRecord) -> str:
        file_path = Path(record.pathname)
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            relative_path = file_path

        log_entry = {
            "v": 0,
            "name": self.project_name,
            "msg": record.getMessage(),
            "level": LEVEL_MAP.get(record.levelno, record.levelno),
            "levelname": record.levelname,
            "hostname": self.hostname,
            "pid": record.process,
            "time": self.formatTime(record),
            "target": record.name,
            "line": record.lineno,
            "file": str(relative_path),
        }

        # Handle extra fields
        extra_fields = {k: v for k, v in record.__dict__.items() if k not in DEFAULT_FIELDS}
        if extra_fields:
            log_entry["extra"] = extra_fields

        # Handle exception information
        if record.exc_info and all(record.exc_info):
            log_entry["err"] = self._format_exception(record)

        return json.dumps(log_entry)

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:  # noqa: N802
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%dT%H:%M:%S", ct)
            s = f"{t}.{int(record.msecs):03d}Z"
        return s

    def _format_exception(self, record: LogRecord) -> dict[str, Any]:
        exc_info = record.exc_info

        if exc_info is None or len(exc_info) != 3:
            return {}

        exc_type, exc_value, exc_traceback = exc_info

        if exc_type is None or exc_value is None or exc_traceback is None:
            return {}

        stack = traceback.extract_tb(exc_traceback)

        return {
            "message": str(exc_value),
            "name": getattr(exc_type, "__name__", "UnknownException"),
            "stack": [
                {
                    "file": frame.filename,
                    "line": frame.lineno,
                    "function": frame.name,
                    "text": frame.line.strip() if frame.line is not None else "",
                }
                for frame in stack
            ],
        }
