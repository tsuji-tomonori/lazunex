from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiContract:
    operation_id: str
    markdown_slug: str
    auth_mode: str
    business_summary: str
    permissions: tuple[str, ...] = ()
    sequence_assertions: tuple[str, ...] = ()
