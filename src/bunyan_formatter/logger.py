import json
import logging
import socket
from logging import Formatter, LogRecord
from pathlib import Path


class BunyanFormatter(Formatter):
    LEVEL_MAP = {
        logging.NOTSET: 10,
        logging.DEBUG: 20,
        logging.INFO: 30,
        logging.WARNING: 40,
        logging.ERROR: 50,
        logging.CRITICAL: 60,
    }

    def __init__(self, project_name: str, project_root: Path) -> None:
        super().__init__()
        self.project_name = project_name
        self.project_root = project_root
        self.hostname = socket.gethostname()

    def format(self, record: LogRecord) -> str:
        hostname = socket.gethostname()

        file_path = Path(record.pathname)
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            relative_path = file_path

        log_entry = {
            "v": 0,
            "name": self.project_name,
            "msg": record.getMessage(),
            "level": self.LEVEL_MAP.get(record.levelno, record.levelno),
            "levelname": record.levelname,
            "hostname": hostname,
            "pid": record.process,
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "target": record.name,
            "line": record.lineno,
            "file": str(relative_path),
        }

        return json.dumps(log_entry)
