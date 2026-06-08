from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ToolCategory = Literal["docs", "codegen", "lint", "check"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    command: str
    category: ToolCategory
    summary: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    depends_on: tuple[str, ...]
    check_supported: bool
    safe_to_run_in_ci: bool
    examples: tuple[str, ...]
