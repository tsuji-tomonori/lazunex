from __future__ import annotations

from pathlib import Path

from app_tool.docs.generate_tool_docs import generate, rendered_outputs
from app_tool.registry import all_tool_specs


def test_rendered_tool_docs_include_all_registered_tools(tmp_path: Path) -> None:
    rendered = rendered_outputs(tmp_path)

    assert tmp_path / "tools-list.gen.md" in rendered
    assert tmp_path / "usage.gen.md" in rendered
    assert tmp_path / "artifacts.gen.md" in rendered
    assert tmp_path / "execution-flow.gen.md" in rendered
    assert tmp_path / "testcase-spec.gen.md" in rendered
    usage = rendered[tmp_path / "usage.gen.md"]
    artifacts = rendered[tmp_path / "artifacts.gen.md"]
    tools_list = rendered[tmp_path / "tools-list.gen.md"]
    for spec in all_tool_specs():
        assert tmp_path / spec.name / "basic-design_gen.md" in rendered
        assert tmp_path / spec.name / "unit-test-spec_gen.md" in rendered
        assert f"`{spec.name}`" in usage
        assert f"`{spec.name}`" in artifacts
        assert f"| `{spec.name}` | {spec.summary} |" in tools_list


def test_generate_tool_docs_check_mode_detects_stale_outputs(tmp_path: Path) -> None:
    assert generate(check=True, output_dir=tmp_path) == 1

    assert generate(check=False, output_dir=tmp_path) == 0

    assert generate(check=True, output_dir=tmp_path) == 0
