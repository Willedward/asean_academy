"""Production logging helpers with Railway-compatible structured output."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

_STRUCTURED_FIELDS = (
    "request_id",
    "http_method",
    "http_path",
    "http_status",
    "duration_ms",
    "release_sha",
    "deployment_id",
    "error_type",
    "target_user_id",
    "role",
    "invitation_id",
    "rate_limit_policy",
    "rate_limit_subject",
)


class RailwayJsonFormatter(logging.Formatter):
    """Emit one JSON object per line for Railway's Log Explorer."""

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
        }
        for field in _STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value
        if record.exc_info:
            event["exception_type"] = record.exc_info[0].__name__
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, separators=(",", ":"), default=str)


def configure_logging(*, level: str, log_format: str) -> None:
    """Configure only the application logger and leave server loggers intact."""

    logger = logging.getLogger("learning_api")
    logger.handlers.clear()
    handler = logging.StreamHandler()
    if log_format == "json":
        handler.setFormatter(RailwayJsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
