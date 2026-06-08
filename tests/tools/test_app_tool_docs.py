from __future__ import annotations

from pathlib import Path

from app_tool.docs.generate_tool_docs import generate, rendered_outputs
from app_tool.registry import all_tool_specs


def test_rendered_tool_docs_include_all_registered_tools(tmp_path: Path) -> None:
    rendered = rendered_outputs(tmp_path)

    assert set(rendered) == {
        tmp_path / "usage.gen.md",
        tmp_path / "artifacts.gen.md",
        tmp_path / "execution-flow.gen.md",
        tmp_path / "testcase-spec.gen.md",
    }
    usage = rendered[tmp_path / "usage.gen.md"]
    artifacts = rendered[tmp_path / "artifacts.gen.md"]
    for spec in all_tool_specs():
        assert f"`{spec.name}`" in usage
        assert f"`{spec.name}`" in artifacts


def test_generate_tool_docs_check_mode_detects_stale_outputs(tmp_path: Path) -> None:
    assert generate(check=True, output_dir=tmp_path) == 1

    assert generate(check=False, output_dir=tmp_path) == 0

    assert generate(check=True, output_dir=tmp_path) == 0
