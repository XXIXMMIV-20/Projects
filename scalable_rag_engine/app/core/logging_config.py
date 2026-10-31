import json
import logging
import sys
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Serializes standard Python log records into structured JSON strings.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "request_id"):
            log_payload["request_id"] = record.request_id

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)

def setup_logging(log_level: int = logging.INFO):
    """Configures the root logger to output structured JSON to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    logging.getLogger("uvicorn.access").handlers = [handler]    