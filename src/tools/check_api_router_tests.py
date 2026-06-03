from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class RouterTestIssue:
    router_path: Path
    expected_test_path: Path
    message: str


def router_files(api_root: Path) -> list[Path]:
    return sorted(api_root.glob("*/*/router.py"))


def expected_router_test_path(
    router_path: Path,
    *,
    api_root: Path,
    test_root: Path,
) -> Path:
    return test_root / router_path.relative_to(api_root).parent / "test_router.py"


def check_api_router_tests(api_root: Path, test_root: Path) -> list[RouterTestIssue]:
    issues: list[RouterTestIssue] = []
    for router_path in router_files(api_root):
        expected_path = expected_router_test_path(
            router_path,
            api_root=api_root,
            test_root=test_root,
        )
        if not expected_path.exists():
            issues.append(
                RouterTestIssue(
                    router_path=router_path,
                    expected_test_path=expected_path,
                    message="router.py requires sibling test_router.py under tests/app/apis",
                )
            )
    return sorted(issues)


def render_issues(issues: Sequence[RouterTestIssue]) -> str:
    return "\n".join(
        f"{issue.router_path}: {issue.message}: expected {issue.expected_test_path}"
        for issue in issues
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check every API router.py has a matching test_router.py."
    )
    parser.add_argument(
        "--api-root",
        type=Path,
        default=Path("src/app/apis"),
        help="API root containing {domain}/{api}/router.py files.",
    )
    parser.add_argument(
        "--test-root",
        type=Path,
        default=Path("tests/app/apis"),
        help="Test root mirroring src/app/apis.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    issues = check_api_router_tests(args.api_root, args.test_root)
    if issues:
        print(render_issues(issues))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
