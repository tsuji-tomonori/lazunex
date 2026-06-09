from __future__ import annotations

from pathlib import Path

from tools.check_e2e_specs import check_specs
from tools.e2e_models import CASES, FACTORS, FLOW_STEPS
from tools.generate_e2e_case_list import rendered_outputs as case_list_outputs
from tools.generate_e2e_factor_yaml import rendered_outputs as factor_outputs
from tools.generate_e2e_scenarios import rendered_outputs as scenario_outputs
from tools.generation_io import write_outputs


def test_e2e_flow_steps_cover_generated_api_list() -> None:
    api_list = Path("docs/spec/40.apis/apis_list_gen.md").read_text(encoding="utf-8")
    documented_endpoints = {
        f"{method} {path}"
        for method, path in (
            (columns[2].strip(" `"), columns[3].strip(" `"))
            for line in api_list.splitlines()
            if line.startswith("| `")
            for columns in [line.split("|")]
        )
    }
    flow_endpoints = {
        f"{step.method} {step.path}"
        .replace("${apiId}", "{apiId}")
        .replace("${projectId}", "{projectId}")
        .replace("${accessRequestId}", "{accessRequestId}")
        for step in FLOW_STEPS
        if step.path.startswith("/")
    }

    assert documented_endpoints <= flow_endpoints


def test_e2e_factor_yaml_outputs_include_effective_factors(tmp_path: Path) -> None:
    rendered = factor_outputs(tmp_path)

    assert tmp_path / "api_access_lifecycle/factors/effective_factors.gen.yaml" in rendered
    assert tmp_path / "api_access_lifecycle/generated/effective_factor_matrix.gen.yaml" in rendered
    assert tmp_path / "api_access_lifecycle/generated/effective_variants.gen.yaml" in rendered
    assert tmp_path / "api_access_lifecycle/generated/effective_step_bindings.gen.yaml" in rendered
    assert tmp_path / "api_access_lifecycle/generated/effective_cases.gen.yaml" in rendered
    expected_factor_files = {
        f"{factor.factor_id}_{factor.slug}.gen.yaml" for factor in FACTORS
    }
    assert expected_factor_files.issubset({path.name for path in rendered})
    assert len(rendered) == len(FACTORS) + 5
    assert "terminal: true" in rendered[
        tmp_path / "api_access_lifecycle/factors/F040_approve_api_access_request_result.gen.yaml"
    ]
    matrix = rendered[
        tmp_path / "api_access_lifecycle/generated/effective_factor_matrix.gen.yaml"
    ]
    assert "access_request_result.success@both_auth_mode" in matrix
    assert "access_request_result.duplicate_pending@public_pkce_auth_mode" in matrix
    variants = rendered[
        tmp_path / "api_access_lifecycle/generated/effective_variants.gen.yaml"
    ]
    assert "project.project_A.create.success@create_default" in variants
    assert "access_request.project_A.API_A.apply.success@both_auth_mode" in variants
    assert "review.project_A.API_A.approve.success@approve_both" in variants
    bindings = rendered[
        tmp_path / "api_access_lifecycle/generated/effective_step_bindings.gen.yaml"
    ]
    assert "setup_pending_access_request" in bindings
    cases = rendered[tmp_path / "api_access_lifecycle/generated/effective_cases.gen.yaml"]
    assert "selected_variants:" in cases
    assert "TC_TARGET_001" in cases
    assert "runtime_assertions:" in cases


def test_e2e_case_list_links_scenarios(tmp_path: Path) -> None:
    rendered = case_list_outputs(tmp_path)
    content = rendered[tmp_path / "api_access_lifecycle/case-list_gen.md"]

    assert "## 0. 対象フロー" in content
    assert "## 3. 生成ケース一覧" in content
    assert "| 要素ID | 既定要素 | 終端要素 | 期待観点 |" in content
    assert "| ケースID | F000 | F001 | F002 | F010 |" in content
    assert "主な要因" not in content
    for step in FLOW_STEPS:
        assert f"`{step.operation}`" in content
        assert step.path in content
    for factor in FACTORS:
        assert f"### {factor.factor_id} {factor.title}" in content
    for case in CASES:
        assert f"cases/{case.filename}" in content
        assert case.case_id in rendered[tmp_path / "api_access_lifecycle/pruned-cases_gen.csv"]
    assert "| `TC003` | 成功: appが応答可能 | reviewer以外 |" in content


def test_e2e_scenarios_keep_secret_placeholders(tmp_path: Path) -> None:
    rendered = scenario_outputs(tmp_path)
    assert {path.name for path in rendered} == {case.filename for case in CASES}
    content = rendered[
        tmp_path
        / "api_access_lifecycle/cases/TC001_happy_approve_and_runtime_success.gen.md"
    ]

    assert "${project_api_key}" in content
    assert "${runtime_access_token}" in content
    assert "GET /projects/${projectId}/api-access-requests" in content
    assert "API呼び出し手順" in content


def test_check_e2e_specs_detects_complete_rendered_tree(tmp_path: Path) -> None:
    flow_root = tmp_path / "api_access_lifecycle"
    flow_root.mkdir(parents=True)
    (flow_root / "flow.manual.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    templates_root = flow_root / "templates" / "steps"
    templates_root.mkdir(parents=True)
    for step in FLOW_STEPS:
        (templates_root / f"{step.template}.manual.yaml").write_text(
            "schema_version: 1\n",
            encoding="utf-8",
        )
    write_outputs(factor_outputs(tmp_path))
    write_outputs(case_list_outputs(tmp_path))
    write_outputs(scenario_outputs(tmp_path))

    assert check_specs(tmp_path) == []
