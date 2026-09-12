"""Small structured logging helpers for local development."""

import json
import logging
import time
from contextlib import contextmanager


LOGGER = logging.getLogger("vellum")


def configure_logging():
    """Configure one readable JSON logger without changing application policy."""
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate = False


def log_event(event, **fields):
    configure_logging()
    payload = {"event": event, **fields}
    LOGGER.info(json.dumps(payload, sort_keys=True, default=str))


@contextmanager
def measure_stage(stage, **fields):
    """Log a stage duration in milliseconds and yield a mutable timing holder."""
    started = time.perf_counter()
    timing = {}
    try:
        yield timing
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        timing["latency_ms"] = elapsed_ms
        log_event("pipeline_stage", stage=stage, latency_ms=elapsed_ms, **fields)
