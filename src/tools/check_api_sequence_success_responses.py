from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

SUCCESS_RESPONSE_PATTERN = re.compile(r"API-->>User:\s+HTTP\s+2\d\d\b")
NORMAL_ACTION_PATTERN = re.compile(r"API->>(?:API|DB|R_[A-Za-z0-9_]+):")


@dataclass(frozen=True, order=True)
class ApiSequenceSuccessResponseIssue:
    path: Path
    message: str


def check_api_sequence_success_responses(
    docs_root: Path = Path("docs/spec/40.apis"),
) -> list[ApiSequenceSuccessResponseIssue]:
    issues: list[ApiSequenceSuccessResponseIssue] = []
    for path in sorted(docs_root.glob("*/*/sequence_gen.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        success_lines = [
            index
            for index, line in enumerate(lines, start=1)
            if SUCCESS_RESPONSE_PATTERN.search(line)
        ]
        if not success_lines:
            issues.append(
                ApiSequenceSuccessResponseIssue(
                    path=path,
                    message="sequence must include a successful 2xx response",
                )
            )
            continue
        action_lines = [
            index for index, line in enumerate(lines, start=1) if NORMAL_ACTION_PATTERN.search(line)
        ]
        if action_lines and max(success_lines) <= max(action_lines):
            issues.append(
                ApiSequenceSuccessResponseIssue(
                    path=path,
                    message="successful 2xx response must be rendered after normal processing",
                )
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check generated API sequences include successful 2xx responses."
    )
    parser.add_argument("--docs-root", type=Path, default=Path("docs/spec/40.apis"))
    args = parser.parse_args()

    issues = check_api_sequence_success_responses(args.docs_root)
    if not issues:
        print("All generated API sequences include successful 2xx responses.")
        return 0

    for issue in issues:
        print(f"{issue.path}: {issue.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
