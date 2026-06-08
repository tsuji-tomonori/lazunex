from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from .models import CheckResult


def summarize(results: Iterable[CheckResult]) -> Counter[str]:
    return Counter(result.status for result in results)


def render_report(results: list[CheckResult], repo_root: Path) -> str:
    counts = summarize(results)
    lines = [
        f"PASS={counts.get('PASS', 0)} FAIL={counts.get('FAIL', 0)} "
        f"MANUAL={counts.get('MANUAL', 0)} SKIP={counts.get('SKIP', 0)}"
    ]
    for result in results:
        if result.status == "PASS":
            continue
        lines.append(result.display(repo_root))
    return "\n".join(lines)
