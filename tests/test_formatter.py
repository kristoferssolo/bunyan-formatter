import json
import logging
from datetime import datetime
from io import StringIO
from logging import LogRecord, StreamHandler
from pathlib import Path
from typing import Optional
from unittest import TestCase
from unittest.mock import Mock, patch

from bunyan_formatter import BunyanFormatter


class TestBunyanFormatter(TestCase):
    @patch("socket.gethostname")
    def setUp(self, mock_gethostname: Optional[Mock]) -> None:
        if mock_gethostname is None:
            raise ValueError("mock_gethostname should not be None")
        mock_gethostname.return_value = "test_host"
        self.project_name = "test_project"
        self.project_root = Path("/path/to/project")
        self.formatter = BunyanFormatter(self.project_name, self.project_root)

    def create_log_record(self, level: int, msg: str, pathname: str) -> LogRecord:
        return LogRecord(name="test_logger", level=level, pathname=pathname, lineno=42, msg=msg, args=(), exc_info=None)

    def test_format_basic(self) -> None:
        record = self.create_log_record(logging.INFO, "Test message", "/path/to/project/test.py")

        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        assert log_entry["v"] == 0
        assert log_entry["name"] == self.project_name
        assert log_entry["msg"] == "Test message"
        assert log_entry["level"] == 30
        assert log_entry["levelname"] == "INFO"
        assert log_entry["hostname"] == "test_host"
        assert log_entry["target"] == "test_logger"
        assert log_entry["line"] == 42
        assert log_entry["file"] == "test.py"

    def test_format_different_levels(self) -> None:
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        expected_levels = [20, 30, 40, 50, 60]

        for level, expected in zip(levels, expected_levels, strict=False):
            record = self.create_log_record(level, f"Test {logging.getLevelName(level)}", "/path/to/project/test.py")
            formatted = self.formatter.format(record)
            log_entry = json.loads(formatted)
            assert log_entry["level"] == expected
            assert log_entry["levelname"] == logging.getLevelName(level)

    def test_format_file_outside_project(self) -> None:
        record = self.create_log_record(logging.INFO, "Test message", "/path/outside/project/test.py")
        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)
        assert log_entry["file"] == "/path/outside/project/test.py"

    def test_format_hostname_consistency(self) -> None:
        record1 = self.create_log_record(logging.INFO, "Message 1", "/path/to/project/test1.py")
        record2 = self.create_log_record(logging.INFO, "Message 2", "/path/to/project/test2.py")

        formatted1 = self.formatter.format(record1)
        formatted2 = self.formatter.format(record2)

        log_entry1 = json.loads(formatted1)
        log_entry2 = json.loads(formatted2)

        assert log_entry1["hostname"] == log_entry2["hostname"]

    def test_format_time(self) -> None:
        record = self.create_log_record(logging.INFO, "Test message", "/path/to/project/test.py")
        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        # Check if the time is in the correct format
        from datetime import datetime

        try:
            datetime.strptime(log_entry["time"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            self.fail("Time is not in the correct format")

    def test_format_exception(self) -> None:
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = StreamHandler(stream)
        handler.setFormatter(self.formatter)
        logger.addHandler(handler)

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")

        # Get the last logged message
        last_message = handler.stream.getvalue().splitlines()[-1]
        log_entry = json.loads(last_message)

        assert log_entry["v"] == 0
        assert log_entry["name"] == self.project_name
        assert log_entry["msg"] == "An error occurred"
        assert log_entry["level"] == 50
        assert log_entry["levelname"] == "ERROR"
        assert log_entry["hostname"] == "test_host"
        assert log_entry["target"] == "test_logger"
        assert "err" in log_entry
        assert "message" in log_entry["err"]
        assert "name" in log_entry["err"]
        assert "stack" in log_entry["err"]

    def test_format_custom_fields(self) -> None:
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = StreamHandler(stream)
        handler.setFormatter(self.formatter)
        logger.addHandler(handler)

        logger.info("User logged in", extra={"username": "john_doe", "ip_address": "192.168.1.100"})

        # Get the last logged message
        last_message = handler.stream.getvalue().splitlines()[-1]
        log_entry = json.loads(last_message)

        assert log_entry["v"] == 0
        assert log_entry["name"] == self.project_name
        assert log_entry["msg"] == "User logged in"
        assert log_entry["level"] == 30
        assert log_entry["levelname"] == "INFO"
        assert log_entry["target"] == "test_logger"
        assert "extra" in log_entry
        assert log_entry["extra"]["username"] == "john_doe"
        assert log_entry["extra"]["ip_address"] == "192.168.1.100"

    def test_format_nested_custom_fields(self) -> None:
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = StreamHandler(stream)
        handler.setFormatter(self.formatter)
        logger.addHandler(handler)

        nested_data = {
            "user": {"id": 123, "email": "user@example.com"},
            "action": "login",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("Complex action performed", extra={"data": nested_data})

        # Get the last logged message
        last_message = handler.stream.getvalue().splitlines()[-1]
        log_entry = json.loads(last_message)

        assert log_entry["v"] == 0
        assert log_entry["name"] == self.project_name
        assert log_entry["msg"] == "Complex action performed"
        assert log_entry["level"] == 30
        assert log_entry["levelname"] == "INFO"
        assert log_entry["target"] == "test_logger"
        assert "extra" in log_entry
        assert "data" in log_entry["extra"]
        assert isinstance(log_entry["extra"]["data"], dict)
        assert log_entry["extra"]["data"]["user"]["id"] == 123
        assert log_entry["extra"]["data"]["user"]["email"] == "user@example.com"
        assert log_entry["extra"]["data"]["action"] == "login"
        assert "timestamp" in log_entry["extra"]["data"]

    def test_format_exception_with_custom_fields(self) -> None:
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        stream = StringIO()
        handler = StreamHandler(stream)
        handler.setFormatter(self.formatter)
        logger.addHandler(handler)

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred", extra={"error_code": "E001", "user_id": 456})

        # Get the last logged message
        last_message = handler.stream.getvalue().splitlines()[-1]
        log_entry = json.loads(last_message)

        assert log_entry["v"] == 0
        assert log_entry["name"] == self.project_name
        assert log_entry["msg"] == "An error occurred"
        assert log_entry["level"] == 50
        assert log_entry["levelname"] == "ERROR"
        assert log_entry["hostname"] == "test_host"
        assert log_entry["target"] == "test_logger"
        assert "err" in log_entry
        assert "message" in log_entry["err"]
        assert "name" in log_entry["err"]
        assert "stack" in log_entry["err"]
        assert "extra" in log_entry
        assert log_entry["extra"]["error_code"] == "E001"
        assert log_entry["extra"]["user_id"] == 456
