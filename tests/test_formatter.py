import json
import logging
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from bunyan_formatter import BunyanFormatter


class TestBunyanFormatter(TestCase):
    def setUp(self):
        self.project_name = "test_project"
        self.project_root = Path("/path/to/project")
        self.formatter = BunyanFormatter(self.project_name, self.project_root)

    def create_log_record(self, level, msg, pathname):
        return logging.LogRecord(
            name="test_logger", level=level, pathname=pathname, lineno=42, msg=msg, args=(), exc_info=None
        )

    @patch("socket.gethostname")
    def test_format_basic(self, mock_gethostname):
        mock_gethostname.return_value = "test_host"
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

    def test_format_different_levels(self):
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        expected_levels = [20, 30, 40, 50, 60]

        for level, expected in zip(levels, expected_levels):
            record = self.create_log_record(level, f"Test {logging.getLevelName(level)}", "/path/to/project/test.py")
            formatted = self.formatter.format(record)
            log_entry = json.loads(formatted)
            assert log_entry["level"] == expected
            assert log_entry["levelname"] == logging.getLevelName(level)

    def test_format_file_outside_project(self):
        record = self.create_log_record(logging.INFO, "Test message", "/path/outside/project/test.py")
        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)
        assert log_entry["file"] == "/path/outside/project/test.py"

    @patch("socket.gethostname")
    def test_format_hostname_consistency(self, mock_gethostname):
        mock_gethostname.return_value = "test_host"
        record1 = self.create_log_record(logging.INFO, "Message 1", "/path/to/project/test1.py")
        record2 = self.create_log_record(logging.INFO, "Message 2", "/path/to/project/test2.py")

        formatted1 = self.formatter.format(record1)
        formatted2 = self.formatter.format(record2)

        log_entry1 = json.loads(formatted1)
        log_entry2 = json.loads(formatted2)

        assert log_entry1["hostname"] == log_entry2["hostname"]

    def test_format_time(self):
        record = self.create_log_record(logging.INFO, "Test message", "/path/to/project/test.py")
        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        # Check if the time is in the correct format
        from datetime import datetime

        try:
            datetime.strptime(log_entry["time"], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            self.fail("Time is not in the correct format")
