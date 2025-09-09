import logging
import time
from contextlib import contextmanager
from typing import Any, Dict


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        h.setFormatter(fmt)
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger


@contextmanager
def RequestContext(**kwargs):
    # No-op context that could enrich logs with request_id, etc.
    try:
        yield
    finally:
        pass


@contextmanager
def PerformanceTimer(logger: logging.Logger, name: str, **fields):
    start = time.perf_counter()
    try:
        yield
    finally:
        dur_ms = (time.perf_counter() - start) * 1000
        logger.info(f"perf::{name} took {dur_ms:.1f}ms")


def log_agent_activity(agent: str, activity: str, **fields: Any) -> None:
    get_logger(f"agent.{agent}").info(f"activity={activity} {fields}")


def log_agent_error(agent: str, err: Exception, context: Dict[str, Any]) -> None:
    get_logger(f"agent.{agent}").error(f"error={err} ctx={context}")

