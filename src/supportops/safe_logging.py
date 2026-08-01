"""Logging helpers that recursively redact sensitive fields."""

from collections.abc import Mapping, Sequence
from typing import Any, Final

REDACTED: Final = "[REDACTED]"
SENSITIVE_KEYS: Final = frozenset(
    {"password", "token", "secret", "api_key", "authorization"}
)


def _normalized_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_")


def redact_sensitive(value: Any) -> Any:
    """Return a recursively redacted copy while preserving safe data."""

    if isinstance(value, Mapping):
        return {
            key: REDACTED
            if _normalized_key(key) in SENSITIVE_KEYS
            else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive(item) for item in value]
    return value
