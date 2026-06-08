from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

NormLevel = Literal["MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY"]
CheckStatus = Literal["PASS", "FAIL", "MANUAL", "SKIP"]


def _empty_details() -> dict[str, Any]:
    return {}


@dataclass(frozen=True)
class RuleItem:
    id: str
    level: NormLevel
    text: str
    source_path: Path
    line_number: int
    checkers: tuple[str, ...]

    @property
    def source_ref(self) -> str:
        return f"{self.source_path.as_posix()}:{self.line_number}"

    @property
    def is_must(self) -> bool:
        return self.level in {"MUST", "MUST NOT"}


@dataclass(frozen=True)
class CheckResult:
    checker: str
    status: CheckStatus
    message: str
    path: Path | None = None
    line: int | None = None
    rule_id: str | None = None
    details: dict[str, Any] = field(default_factory=_empty_details)

    def display(self, repo_root: Path | None = None) -> str:
        location = ""
        if self.path is not None:
            path = self.path
            if repo_root is not None:
                try:
                    path = path.relative_to(repo_root)
                except ValueError:
                    pass
            location = path.as_posix()
            if self.line is not None:
                location = f"{location}:{self.line}"
            location = f" {location}"
        rule = f" {self.rule_id}" if self.rule_id else ""
        return f"[{self.status}] {self.checker}{rule}{location} - {self.message}"


@dataclass(frozen=True)
class CheckContext:
    repo_root: Path
    rules_dir: Path
    config: dict[str, Any]
    items: tuple[RuleItem, ...]
