"""DEPRECATED PARALLEL SUBSYSTEM (PR #14). Not imported by canonical AHOS.

Canonical logging: `architecture/runtime/logging.py` (JSON, run_id).
This module no longer creates log files or reads a SECRET_KEY.
"""
from __future__ import annotations

import logging


def setup_logger(name: str = "ahos.deprecated", **_: object) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


logger = setup_logger()
