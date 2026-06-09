from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from tools.check_e2e_specs import check_specs
from tools.e2e_models import CASES, FACTORS, FLOW_STEPS
from tools.generate_e2e_case_list import rendered_outputs as case_list_outputs
from tools.generate_e2e_scenarios import load_scenario_catalog
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


def test_e2e_case_list_links_scenarios(tmp_path: Path) -> None:
    rendered = case_list_outputs(tmp_path)
    content = rendered[tmp_path / "api_access_lifecycle/case-list_gen.md"]

    assert "## 0. 対象フロー" in content
    assert "## 3. 生成ケース一覧" in content
    assert "## 4. 対象別生成ケース一覧" in content
    assert "| 要素ID | 既定要素 | 終端要素 | 期待観点 |" in content
    assert "| ケースID | F000 | F001 | F002 | F010 |" in content
    assert "| ケースID | 目的 | Project | API | 選択Variant | Runtime期待 |" in content
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
    assert "`TC_TARGET_001`" in content
    assert "`review.project_A.API_A.approve.success@approve_both`" in content
    assert "`project_A` / `API_B`: `denied`" in content


def test_e2e_scenarios_keep_secret_placeholders(tmp_path: Path) -> None:
    rendered = scenario_outputs(tmp_path)
    assert {path.name for path in rendered} == {case.filename for case in CASES}
    content = rendered[
        tmp_path
        / "api_access_lifecycle/cases/TC001_happy_approve_and_runtime_success.gen.md"
    ]

    assert "${project_api_key}" in content
    assert "${runtime_access_token}" in content
    assert "## 1. 対象" in content
    assert "## 2. 処理概要" in content
    assert "## 3. 処理詳細" in content
    assert "## 4. エビデンス" in content
    assert "| Project | `project_A` | Project A | 利用申請元Project |" in content
    assert (
        "project_Aを作成する → project_Aのpublic client redirect URLを更新する → "
        "project_AからAPI_Aへ利用申請する"
    ) in content
    assert "GET /projects/{projectId}/api-access-requests" in content
    assert "API呼び出し手順" in content
    assert "| Step | API | Request | 目的 | 期待 | Capture |" in content
    assert "標準データ (`default`)" in content
    assert "requestedAuthMode=BOTH (`both_auth_mode`)" in content
    assert "API_B Runtime APIレスポンス" in content
    catalog = load_scenario_catalog()
    assert catalog.bindings[("review", "reject", "success")] == (
        "access_request_rejected",
        "other_api_not_callable",
    )
    project_a_md = cast(Mapping[str, object], catalog.targets["project_A"]["md"])
    target_section = cast(Mapping[str, object], project_a_md["target_section"])
    assert target_section["usage"] == "利用申請元Project"

    reject_content = rendered[
        tmp_path / "api_access_lifecycle/cases/TC002_reject_request_and_no_subscription.gen.md"
    ]
    assert "API_A Runtime APIレスポンス" in reject_content
    assert "TC002_E_runtime_project_A_API_C_denied.json" in reject_content


def test_check_e2e_specs_detects_complete_rendered_tree(tmp_path: Path) -> None:
    flow_root = tmp_path / "api_access_lifecycle"
    flow_root.mkdir(parents=True)
    fixture_root = Path("docs/spec/50.e2e/api_access_lifecycle")
    (flow_root / "flow.manual.yaml").write_text(
        (fixture_root / "flow.manual.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    templates_root = flow_root / "templates" / "steps"
    templates_root.mkdir(parents=True)
    for step in FLOW_STEPS:
        (templates_root / f"{step.template}.manual.yaml").write_text(
            "schema_version: 1\n",
            encoding="utf-8",
        )
    write_outputs(case_list_outputs(tmp_path))
    write_outputs(scenario_outputs(tmp_path))

    for source in [
        fixture_root / "targets" / "projects" / "project_A.target.manual.yaml",
        fixture_root / "targets" / "projects" / "project_B.target.manual.yaml",
        fixture_root / "targets" / "projects" / "project_C.target.manual.yaml",
        fixture_root / "targets" / "apis" / "API_A.target.manual.yaml",
        fixture_root / "targets" / "apis" / "API_B.target.manual.yaml",
        fixture_root / "targets" / "apis" / "API_C.target.manual.yaml",
        fixture_root / "factors" / "project.factor.manual.yaml",
        fixture_root / "factors" / "access_request.factor.manual.yaml",
        fixture_root / "factors" / "review.factor.manual.yaml",
        fixture_root / "factors" / "effective_factors.manual.yaml",
        fixture_root / "operations" / "project" / "create.operation.manual.yaml",
        fixture_root / "operations" / "project" / "update.operation.manual.yaml",
        fixture_root / "operations" / "access_request" / "apply.operation.manual.yaml",
        fixture_root / "operations" / "review" / "approve.operation.manual.yaml",
        fixture_root / "operations" / "review" / "reject.operation.manual.yaml",
        fixture_root / "steps" / "project" / "create_project.step.manual.yaml",
        fixture_root / "steps" / "access_request" / "create_access_request.step.manual.yaml",
        fixture_root / "steps" / "review" / "approve_access_request.step.manual.yaml",
        fixture_root / "steps" / "review" / "reject_access_request.step.manual.yaml",
        fixture_root / "steps" / "runtime" / "invoke_api.step.manual.yaml",
        fixture_root / "evidences" / "project" / "project_search_hit.evidence.manual.yaml",
        fixture_root
        / "evidences"
        / "access_request"
        / "access_request_listed.evidence.manual.yaml",
        fixture_root / "evidences" / "review" / "access_request_approved.evidence.manual.yaml",
        fixture_root / "evidences" / "review" / "access_request_rejected.evidence.manual.yaml",
        fixture_root / "evidences" / "runtime" / "current_api_callable.evidence.manual.yaml",
        fixture_root / "evidences" / "runtime" / "other_api_not_callable.evidence.manual.yaml",
        fixture_root / "bindings" / "project.bindings.manual.yaml",
        fixture_root / "bindings" / "access_request.bindings.manual.yaml",
        fixture_root / "bindings" / "review.bindings.manual.yaml",
        fixture_root / "bindings" / "runtime.bindings.manual.yaml",
        fixture_root / "rules" / "renderer.manual.yaml",
        fixture_root / "rules" / "matrix.manual.yaml",
        fixture_root / "rules" / "pruning.manual.yaml",
        fixture_root / "generated" / "effective_factor_matrix.manual.yaml",
        fixture_root / "generated" / "effective_variants.manual.yaml",
        fixture_root / "generated" / "effective_step_bindings.manual.yaml",
        fixture_root / "generated" / "effective_cases.manual.yaml",
        *[
            fixture_root / "factors" / f"{factor.factor_id}_{factor.slug}.manual.yaml"
            for factor in FACTORS
        ],
    ]:
        target = flow_root / source.relative_to(fixture_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    assert check_specs(tmp_path) == []
