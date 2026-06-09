from __future__ import annotations

from pathlib import Path

from tools.check_e2e_specs import check_specs
from tools.generate_e2e_case_list import rendered_outputs as case_list_outputs
from tools.generate_e2e_factor_yaml import rendered_outputs as factor_outputs
from tools.generate_e2e_scenarios import rendered_outputs as scenario_outputs
from tools.generation_io import write_outputs


def test_e2e_factor_yaml_outputs_include_effective_factors(tmp_path: Path) -> None:
    rendered = factor_outputs(tmp_path)

    assert tmp_path / "api_access_lifecycle/factors/effective_factors.gen.yaml" in rendered
    assert any(path.name == "F040_review_decision.gen.yaml" for path in rendered)
    assert "terminal: true" in rendered[
        tmp_path / "api_access_lifecycle/factors/F040_review_decision.gen.yaml"
    ]


def test_e2e_case_list_links_scenarios(tmp_path: Path) -> None:
    rendered = case_list_outputs(tmp_path)
    content = rendered[tmp_path / "api_access_lifecycle/case-list_gen.md"]

    assert "## 0. 対象フロー" in content
    assert "## 3. 生成ケース一覧" in content
    assert "cases/TC001_happy_approve_and_runtime_success.gen.md" in content
    assert "TC005" in rendered[tmp_path / "api_access_lifecycle/pruned-cases_gen.csv"]


def test_e2e_scenarios_keep_secret_placeholders(tmp_path: Path) -> None:
    rendered = scenario_outputs(tmp_path)
    content = rendered[
        tmp_path
        / "api_access_lifecycle/cases/TC001_happy_approve_and_runtime_success.gen.md"
    ]

    assert "${project_api_key}" in content
    assert "${runtime_access_token}" in content
    assert "API呼び出し手順" in content


def test_check_e2e_specs_detects_complete_rendered_tree(tmp_path: Path) -> None:
    flow_root = tmp_path / "api_access_lifecycle"
    flow_root.mkdir(parents=True)
    (flow_root / "flow.manual.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    write_outputs(factor_outputs(tmp_path))
    write_outputs(case_list_outputs(tmp_path))
    write_outputs(scenario_outputs(tmp_path))

    assert check_specs(tmp_path) == []
