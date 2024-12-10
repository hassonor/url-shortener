import json
import logging
import sys

from infrastructure.config import settings


class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # If extra fields provided via record.args as a dict, merge them
        if record.args and isinstance(record.args, dict):
            log_record.update(record.args)
        return json.dumps(log_record)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = JSONLogFormatter()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)  # Adjust as needed (DEBUG, INFO, WARN, etc.)
    root.handlers = [handler]


setup_logging()
