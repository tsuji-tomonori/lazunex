from __future__ import annotations

from pathlib import Path

from .builtin_checks import REGISTRY
from .config import load_config
from .models import CheckContext, CheckResult
from .rule_parser import parse_rules_dir


def evaluate_items(
    repo_root: Path,
    rules_dir: Path,
    config_path: Path | None = None,
    must_only: bool = False,
) -> list[CheckResult]:
    config = load_config(config_path)
    items = parse_rules_dir(rules_dir)
    if must_only:
        items = tuple(item for item in items if item.is_must)
    context = CheckContext(repo_root=repo_root, rules_dir=rules_dir, config=config, items=items)
    results: list[CheckResult] = []
    for item in items:
        if not item.checkers:
            results.append(
                CheckResult(
                    checker="rule_has_checker_tag",
                    status="FAIL" if item.is_must else "MANUAL",
                    message="rule item has no checker tag",
                    path=rules_dir / item.source_path,
                    line=item.line_number,
                    rule_id=item.id,
                )
            )
            continue
        for checker_name in item.checkers:
            checker = REGISTRY.get(checker_name)
            if checker is None:
                results.append(
                    CheckResult(
                        checker=checker_name,
                        status="FAIL" if item.is_must else "MANUAL",
                        message="unknown checker name",
                        path=rules_dir / item.source_path,
                        line=item.line_number,
                        rule_id=item.id,
                    )
                )
                continue
            try:
                results.extend(checker(item, context))
            except Exception as error:  # pragma: no cover - fail-safe for CI output
                results.append(
                    CheckResult(
                        checker=checker_name,
                        status="FAIL",
                        message=f"checker raised {type(error).__name__}: {error}",
                        path=rules_dir / item.source_path,
                        line=item.line_number,
                        rule_id=item.id,
                    )
                )
    return results
