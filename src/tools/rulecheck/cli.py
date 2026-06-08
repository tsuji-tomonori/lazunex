from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .builtin_checks import normative_no_ambiguous_words, rule_has_checker_tag
from .checklist import generate, verify_generated
from .config import load_config
from .evaluator import evaluate_items
from .models import CheckContext, CheckResult
from .report import render_report
from .rule_parser import parse_rules_dir


def _nonzero_for(results: list[CheckResult], fail_on_manual: bool = False) -> int:
    if any(result.status == "FAIL" for result in results):
        return 1
    if fail_on_manual and any(result.status == "MANUAL" for result in results):
        return 1
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    items = generate(args.rules_dir, args.checklist)
    print(f"generated checklist items: {len(items)}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    errors = verify_generated(args.rules_dir, args.checklist)
    config = load_config(args.config)
    items = parse_rules_dir(args.rules_dir)
    context = CheckContext(
        repo_root=args.repo_root, rules_dir=args.rules_dir, config=config, items=items
    )
    synthetic = items[0] if items else None
    results: list[CheckResult] = []
    if synthetic is not None:
        results.extend(rule_has_checker_tag(synthetic, context))
        results.extend(normative_no_ambiguous_words(synthetic, context))
    for error in errors:
        results.append(CheckResult("generated_checklist_synced", "FAIL", error))
    if not errors:
        results.append(
            CheckResult("generated_checklist_synced", "PASS", "generated checklist is current")
        )
    print(render_report(results, args.repo_root))
    return _nonzero_for(results)


def cmd_check(args: argparse.Namespace) -> int:
    results = evaluate_items(
        repo_root=args.repo_root,
        rules_dir=args.rules_dir,
        config_path=args.config,
        must_only=args.must_only,
    )
    print(render_report(results, args.repo_root))
    return _nonzero_for(results, fail_on_manual=args.fail_on_manual)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rulecheck", description="Generate and check machine-readable coding-rule checklists."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser(
        "generate", help="Generate embedded and central review checklists from rule Markdown."
    )
    gen.add_argument("--rules-dir", type=Path, required=True)
    gen.add_argument("--checklist", type=Path, required=True)
    gen.set_defaults(func=cmd_generate)

    verify = sub.add_parser("verify", help="Verify generated checklists and rule syntax.")
    verify.add_argument("--repo-root", type=Path, default=Path("."))
    verify.add_argument("--rules-dir", type=Path, required=True)
    verify.add_argument("--checklist", type=Path, required=True)
    verify.add_argument("--config", type=Path, default=None)
    verify.set_defaults(func=cmd_verify)

    check = sub.add_parser(
        "check", help="Run static checks referenced by generated checklist items."
    )
    check.add_argument("--repo-root", type=Path, required=True)
    check.add_argument("--rules-dir", type=Path, required=True)
    check.add_argument("--config", type=Path, default=None)
    check.add_argument("--must-only", action="store_true")
    check.add_argument("--fail-on-manual", action="store_true")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.repo_root = getattr(args, "repo_root", Path(".")).resolve()
    args.rules_dir = args.rules_dir.resolve()
    args.checklist = getattr(args, "checklist", Path(".")).resolve()
    args.config = args.config.resolve() if getattr(args, "config", None) is not None else None
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
