import logging

import pytest

from matchday_bot.config import configure_logging, normalize_log_level


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, "INFO"),
        ("", "INFO"),
        ("   ", "INFO"),
        ("debug", "DEBUG"),
        ("WARN", "WARNING"),
        ("info", "INFO"),
        ("VERBOSE", "INFO"),
        ("20", 20),
    ],
)
def test_normalize_log_level(raw: str | None, expected: int | str) -> None:
    assert normalize_log_level(raw) == expected


def test_configure_logging_invalid_level_fallback() -> None:
    configure_logging("", run_id="test-run")
    logger = logging.getLogger("test.logger")
    logger.info("logging should not crash")
