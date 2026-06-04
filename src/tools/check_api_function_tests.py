from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionCoverageIssue:
    source_path: Path
    test_path: Path
    function_name: str


def _top_level_functions(path: Path, include_private: bool) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        if node.name == "_sequence_placeholder":
            continue
        if not include_private and node.name.startswith("_"):
            continue
        names.append(node.name)
    return names


def _referenced_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.add(node.value)
    return names


def find_function_coverage_issues(
    source_root: Path = Path("src/app/apis"),
    test_root: Path = Path("tests/app/apis"),
    include_private: bool = False,
) -> list[FunctionCoverageIssue]:
    issues: list[FunctionCoverageIssue] = []
    for source_path in sorted(source_root.glob("**/functions.py")):
        relative_parent = source_path.relative_to(source_root).parent
        test_path = test_root / relative_parent / "test_functions.py"
        referenced_names = _referenced_names(test_path)
        for function_name in _top_level_functions(source_path, include_private):
            if function_name not in referenced_names:
                issues.append(
                    FunctionCoverageIssue(
                        source_path=source_path,
                        test_path=test_path,
                        function_name=function_name,
                    )
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check each API functions.py function has at least one test case reference."
    )
    parser.add_argument("--source-root", type=Path, default=Path("src/app/apis"))
    parser.add_argument("--test-root", type=Path, default=Path("tests/app/apis"))
    parser.add_argument("--include-private", action="store_true")
    args = parser.parse_args()

    issues = find_function_coverage_issues(
        source_root=args.source_root,
        test_root=args.test_root,
        include_private=args.include_private,
    )
    if not issues:
        print("All API functions have at least one test reference.")
        return 0

    for issue in issues:
        print(f"{issue.source_path}: {issue.function_name} is not referenced by {issue.test_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
