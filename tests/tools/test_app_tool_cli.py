from __future__ import annotations

import pytest

from app_tool import cli
from app_tool.registry import spec_by_name
from app_tool.runner import python_module_args


def test_docs_main_delegates_generate_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def fake_generate_tool_docs(*, check: bool) -> int:
        calls.append(check)
        return 0

    monkeypatch.setattr(cli, "generate_tool_docs", fake_generate_tool_docs)

    assert cli.docs_main(["generate-tools", "--check"]) == 0
    assert calls == [True]


def test_python_module_args_adds_check_for_docs_generator() -> None:
    spec = spec_by_name("generate_api_sequences")

    args = python_module_args(spec, check=True)

    assert args[-3:] == ["-m", "tools.generate_api_sequences", "--check"]


def test_python_module_args_adds_check_for_codegen_generator() -> None:
    spec = spec_by_name("generate_queries")

    args = python_module_args(spec, check=True)

    assert args[-3:] == ["-m", "tools.generate_queries", "--check"]
