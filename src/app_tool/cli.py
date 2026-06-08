from __future__ import annotations

import argparse
from collections.abc import Sequence

from .docs.generate_tool_docs import generate as generate_tool_docs
from .registry import specs_by_category
from .runner import run_specs


def docs_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app-docs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate project documentation.")
    generate_parser.add_argument("--check", action="store_true")

    tool_docs_parser = subparsers.add_parser("generate-tools", help="Generate tools documentation.")
    tool_docs_parser.add_argument("--check", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "generate-tools":
        return generate_tool_docs(check=args.check)

    tool_docs_exit = generate_tool_docs(check=args.check)
    if tool_docs_exit != 0:
        return tool_docs_exit
    return run_specs(specs_by_category("docs"), check=args.check)


def codegen_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app-codegen")
    subparsers = parser.add_subparsers(dest="command", required=True)
    all_parser = subparsers.add_parser("all", help="Run all code generators.")
    all_parser.add_argument("--check", action="store_true")

    args = parser.parse_args(argv)
    return run_specs(specs_by_category("codegen"), check=args.check)


def archlint_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app-archlint")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("all", help="Run all architecture checks.")

    parser.parse_args(argv)
    return run_specs(specs_by_category("lint"), check=False)
