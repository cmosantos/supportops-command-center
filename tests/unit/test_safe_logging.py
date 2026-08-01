from supportops.safe_logging import REDACTED, redact_sensitive


def test_redaction_is_recursive_and_preserves_safe_fields() -> None:
    payload = {
        "password": "pw",
        "nested": {
            "token": "tok",
            "api-key": "key",
            "authorization": "Bearer value",
            "safe": "visible",
        },
        "items": [{"secret": "hidden"}, {"message": "kept"}],
    }

    result = redact_sensitive(payload)

    assert result == {
        "password": REDACTED,
        "nested": {
            "token": REDACTED,
            "api-key": REDACTED,
            "authorization": REDACTED,
            "safe": "visible",
        },
        "items": [{"secret": REDACTED}, {"message": "kept"}],
    }


def test_redaction_does_not_mutate_input() -> None:
    payload = {"token": "original"}

    redact_sensitive(payload)

    assert payload == {"token": "original"}
