"""DEPRECATED PARALLEL SUBSYSTEM (PR #14). Not imported by canonical AHOS.

Previously imported `ahos.utils` / `ahos.infrastructure` (a package path that
does not exist in this repository) and wrapped `requests` as a parallel
provider client. Canonical HTTP adapters live in `architecture/providers/`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseService(ABC):
    def __init__(self, name: str, base_url: str = "", api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key

    @abstractmethod
    def get_token_data(self, token_id: str) -> dict[str, Any]:
        raise NotImplementedError("non-canonical; use architecture.providers")

    def close(self) -> None:
        return None
