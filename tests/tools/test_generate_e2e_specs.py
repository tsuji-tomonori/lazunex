from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from tools.check_e2e_case_evidences import check_case_evidences
from tools.check_e2e_specs import check_specs
from tools.e2e_models import CASES, FACTORS, FLOW_STEPS, TARGET_CASES
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
    variant_index = rendered[tmp_path / "api_access_lifecycle/case-variant-index_gen.md"]

    assert "## 0. 読み方" in content
    assert "## 1. 対象フロー" in content
    assert "## 2. Coverage summary" in content
    assert "## 3. コンポーネントごとの要素" in content
    assert "## 4. 枝刈り規則" in content
    assert "## 5. Smoke生成ケース一覧" in content
    assert "## 6. Component coverage summary" in content
    assert "## 7. Project x API matrix" in content
    assert "## 8. Cases by component" in content
    assert "case-variant-index_gen.md" in content
    assert "対象別生成ケース一覧" not in content
    assert "## 2. 旧factor互換表" not in content
    assert "| `api_catalog` | 5 | 5 | 2 | 100.0% |" in content
    assert "| `runtime_authorization` | 20 | 20 | 20 | 100.0% |" in content
    assert "### project_workspace Project Workspace" in content
    assert (
        "| 操作 | `create_project` | Projectを作成する | "
        "操作種別=コマンド, 既定状態=provisioned |"
    ) in content
    assert "| 状態 | `provisioned` | Project作成成功 | 後続継続=はい |" in content
    assert (
        "| データ | `project_default` | 標準Project | "
        "valid_project, has_public_client, has_confidential_client |"
    ) in content
    assert "| 要素ID | 既定要素 | 終端要素 | 期待観点 |" not in content
    assert "| ケースID | F000 | F001 | F002 | F010 |" not in content
    assert "| ID | 種別 | Tier | 目的 | 処理概要 | 終了条件 | 主なエビデンス | Link |" in content
    assert "<summary>Smokeケースの要因選択</summary>" in content
    assert "Goal Variant | Component Variant | Runtime期待 |" not in content
    assert "Goal Variant | Selected Variants | Runtime期待 |" in variant_index
    assert len(TARGET_CASES) == 35
    pruned_csv = rendered[tmp_path / "api_access_lifecycle/pruned-cases_gen.csv"]
    assert pruned_csv.startswith(
        "case_id,api_catalog[データ],api_catalog[操作],"
        "api_catalog[状態],project_workspace[データ],project_workspace[操作],"
        "project_workspace[状態],"
    )
    assert "runtime_authorization[データ]" in pruned_csv.splitlines()[0]
    assert pruned_csv.splitlines()[0].endswith("audit_recovery[状態]")
    assert "TC_TARGET_001,API A / 標準API,APIを公開する,API公開失敗" in pruned_csv
    assert (
        "TC_TARGET_002,"
        "API A / 未登録API,公開APIを探索する,"
        "API探索失敗,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-"
        in pruned_csv
    )
    assert "TC_TARGET_015,API A / 標準API,APIを公開する,API公開成功" in pruned_csv
    assert "TC_TARGET_016,API B / 標準API,APIを公開する,API公開成功" in pruned_csv
    assert "TC_TARGET_017,API C / 標準API,APIを公開する,API公開成功" in pruned_csv
    assert (
        "TC_TARGET_024,API A / 標準API,APIを公開する,"
        "API公開成功,Project A / 標準Project,"
        "Projectを作成する,Project作成成功,"
        in pruned_csv
    )
    assert (
        "Runtime APIを呼び出す,"
        "Runtime認証情報不正,-,-,-"
        in pruned_csv
    )
    assert "Project A / API A / scopeなしRuntime認証情報" in pruned_csv
    assert pruned_csv.count("\nTC_TARGET_") == 35
    assert "\nTC001," not in pruned_csv
    assert "cases/TC001_happy_approve_and_runtime_success.gen.md" not in pruned_csv
    assert "coverage_group" not in pruned_csv
    assert "goal_variant" not in pruned_csv
    assert "シナリオ" not in pruned_csv
    assert "api_default:" not in pruned_csv
    assert "publish_api:" not in pruned_csv
    assert "主な要因" not in content
    for step in FLOW_STEPS:
        assert f"`{step.operation}`" in content
        assert step.path in content
    for case in CASES:
        assert case.case_id in content
        assert case.case_id not in pruned_csv
    for target_case in TARGET_CASES:
        assert f"cases/{target_case.filename}" in content
        assert f"cases/{target_case.filename}" in variant_index
    assert "| 管理API呼び出し主体 | reviewer以外 |" in content
    assert "`TC_TARGET_001`" in content
    assert "`TC_TARGET_035`" in content
    assert "`component_variant`" not in content
    assert "`component_variant`" in variant_index
    assert "API AでAPIを公開し、API公開失敗を確認する" in content
    assert (
        "| Project A | `TC_TARGET_008` | `TC_TARGET_016` | `TC_TARGET_017` |"
        in content
    )
    assert (
        "`runtime_authorization.invoke_runtime_api.project_A.API_A.allowed"
        "@approved_runtime_credential`"
    ) not in content
    assert (
        "`runtime_authorization.invoke_runtime_api.project_A.API_A.allowed"
        "@approved_runtime_credential`"
    ) in variant_index
    assert (
        "`review_decision.approve_request.project_A.API_A.approved@approve_both`"
        in variant_index
    )
    assert "`project_A` / `API_B`: `denied`" in variant_index


def test_e2e_scenarios_keep_secret_placeholders(tmp_path: Path) -> None:
    rendered = scenario_outputs(tmp_path)
    assert {path.name for path in rendered} == {case.filename for case in TARGET_CASES}
    assert "TC001_happy_approve_and_runtime_success.gen.md" not in {
        path.name for path in rendered
    }
    target_case = next(
        case
        for case in TARGET_CASES
        if case.goal_variant
        == "runtime_authorization.invoke_runtime_api.project_A.API_A."
        "allowed@approved_runtime_credential"
    )
    content = rendered[tmp_path / "api_access_lifecycle/cases" / target_case.filename]

    assert "${project_api_key}" in content
    assert "${runtime_access_token}" in content
    assert "## 1. 対象" in content
    assert "## 2. 処理概要" in content
    assert "## 3. 処理詳細" in content
    assert "## 4. エビデンス" in content
    assert target_case.case_id in content
    assert target_case.goal_variant in content
    assert "### Component Variant 手順" in content
    assert "### Component Evidence" in content
    assert "| E1 | `api_catalog` |" in content
    assert "### 選択要素" in content
    assert "| Coverage Group | `component_variant` |" in content
    catalog = load_scenario_catalog()
    assert catalog.bindings[("review", "reject", "success")] == (
        "access_request_rejected",
        "other_api_not_callable",
    )
    project_a_md = cast(Mapping[str, object], catalog.targets["project_A"]["md"])
    target_section = cast(Mapping[str, object], project_a_md["target_section"])
    assert target_section["usage"] == "利用申請元Project"

    runtime_case = next(
        case for case in TARGET_CASES if "credential_invalid@scope_missing" in case.goal_variant
    )
    runtime_content = rendered[tmp_path / "api_access_lifecycle/cases" / runtime_case.filename]
    assert (
        "`runtime_authorization.invoke_runtime_api.project_A.API_A.credential_invalid"
        "@scope_missing`"
    ) in runtime_content
    assert "Runtime認証情報不正で呼び出せない" in runtime_content
    assert "| `project_A` | `API_A` | `denied` |" in runtime_content


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

    sources = [
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
    ]
    sources.extend(sorted((fixture_root / "components").glob("**/*.manual.yaml")))
    sources.extend(sorted((fixture_root / "steps" / "management_api").glob("*.manual.yaml")))
    sources.extend(sorted((fixture_root / "steps" / "runtime_api").glob("*.manual.yaml")))

    for source in sources:
        target = flow_root / source.relative_to(fixture_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    assert check_specs(tmp_path) == []
    assert check_case_evidences(tmp_path) == []
