"""Safe logging: API keys are redacted and transcripts are never logged."""
import logging
import os
import re

_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret)\s*[=:]\s*)\S+"),
]


def redact(text: str) -> str:
    text = _PATTERNS[0].sub("[REDACTED]", text)
    text = _PATTERNS[1].sub("[REDACTED]", text)
    return _PATTERNS[2].sub(r"\1[REDACTED]", text)


class _RedactFilter(logging.Filter):
    def filter(self, record):
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


def get_logger(name: str = "recaproom") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handler.addFilter(_RedactFilter())
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger
