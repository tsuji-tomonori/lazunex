from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import yaml

from tools.check_e2e_case_evidences import check_case_evidences
from tools.e2e_models import (
    API_TARGETS,
    CASES,
    COMPONENT_IDS,
    FACTORS,
    FLOW_ID,
    FLOW_STEPS,
    PROJECT_TARGETS,
    TARGET_CASES,
    build_component_variants,
)

COMPONENT_FILES = (
    "component.manual.yaml",
    "actions.manual.yaml",
    "states.manual.yaml",
    "data.manual.yaml",
    "evidences.manual.yaml",
    "bindings.manual.yaml",
)

MANAGEMENT_API_STEPS = (
    "publish_api",
    "list_apis",
    "get_api",
    "create_project",
    "update_project_public_client",
    "create_access_request",
    "list_access_requests",
    "approve_access_request",
    "reject_access_request",
    "list_projects",
    "get_project",
    "list_subscriptions",
)


def check_specs(root: Path = Path("docs/spec/50.e2e")) -> list[str]:
    flow_root = root / FLOW_ID
    errors: list[str] = []
    required_paths = [
        flow_root / "flow.manual.yaml",
        flow_root / "case-list_gen.md",
        flow_root / "pruned-cases_gen.csv",
        flow_root / "targets" / "projects" / "project_A.target.manual.yaml",
        flow_root / "targets" / "projects" / "project_B.target.manual.yaml",
        flow_root / "targets" / "projects" / "project_C.target.manual.yaml",
        flow_root / "targets" / "apis" / "API_A.target.manual.yaml",
        flow_root / "targets" / "apis" / "API_B.target.manual.yaml",
        flow_root / "targets" / "apis" / "API_C.target.manual.yaml",
        flow_root / "factors" / "project.factor.manual.yaml",
        flow_root / "factors" / "access_request.factor.manual.yaml",
        flow_root / "factors" / "review.factor.manual.yaml",
        flow_root / "operations" / "project" / "create.operation.manual.yaml",
        flow_root / "operations" / "project" / "update.operation.manual.yaml",
        flow_root / "operations" / "access_request" / "apply.operation.manual.yaml",
        flow_root / "operations" / "review" / "approve.operation.manual.yaml",
        flow_root / "operations" / "review" / "reject.operation.manual.yaml",
        flow_root / "steps" / "project" / "create_project.step.manual.yaml",
        flow_root / "steps" / "access_request" / "create_access_request.step.manual.yaml",
        flow_root / "steps" / "review" / "approve_access_request.step.manual.yaml",
        flow_root / "steps" / "review" / "reject_access_request.step.manual.yaml",
        flow_root / "steps" / "runtime" / "invoke_api.step.manual.yaml",
        flow_root / "evidences" / "project" / "project_search_hit.evidence.manual.yaml",
        flow_root / "evidences" / "access_request" / "access_request_listed.evidence.manual.yaml",
        flow_root / "evidences" / "review" / "access_request_approved.evidence.manual.yaml",
        flow_root / "evidences" / "review" / "access_request_rejected.evidence.manual.yaml",
        flow_root / "evidences" / "runtime" / "current_api_callable.evidence.manual.yaml",
        flow_root / "evidences" / "runtime" / "other_api_not_callable.evidence.manual.yaml",
        flow_root / "bindings" / "project.bindings.manual.yaml",
        flow_root / "bindings" / "access_request.bindings.manual.yaml",
        flow_root / "bindings" / "review.bindings.manual.yaml",
        flow_root / "bindings" / "runtime.bindings.manual.yaml",
        flow_root / "rules" / "renderer.manual.yaml",
        flow_root / "rules" / "matrix.manual.yaml",
        flow_root / "rules" / "pruning.manual.yaml",
        flow_root / "factors" / "effective_factors.manual.yaml",
        flow_root / "generated" / "effective_factor_matrix.manual.yaml",
        flow_root / "generated" / "effective_variants.manual.yaml",
        flow_root / "generated" / "effective_step_bindings.manual.yaml",
        flow_root / "generated" / "effective_cases.manual.yaml",
    ]
    required_paths.extend(
        flow_root / "factors" / f"{factor.factor_id}_{factor.slug}.manual.yaml"
        for factor in FACTORS
    )
    required_paths.extend(flow_root / "cases" / case.filename for case in TARGET_CASES)
    required_paths.extend(
        flow_root / "templates" / "steps" / f"{step.template}.manual.yaml"
        for step in FLOW_STEPS
    )
    required_paths.extend(
        flow_root / "components" / component_id / filename
        for component_id in COMPONENT_IDS
        for filename in COMPONENT_FILES
    )
    required_paths.extend(
        flow_root / "steps" / "management_api" / f"{step_id}.step.manual.yaml"
        for step_id in MANAGEMENT_API_STEPS
    )
    required_paths.append(
        flow_root / "steps" / "runtime_api" / "invoke_runtime_api.step.manual.yaml"
    )

    for path in required_paths:
        if not path.exists():
            errors.append(f"missing: {path.as_posix()}")
            continue
        if path.suffix == ".yaml":
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                errors.append(f"invalid yaml: {path.as_posix()}: {exc}")

    case_list_path = flow_root / "case-list_gen.md"
    if case_list_path.exists():
        case_list = case_list_path.read_text(encoding="utf-8")
        for case in TARGET_CASES:
            link = f"cases/{case.filename}"
            if link not in case_list:
                errors.append(f"case-list missing link: {link}")

    flow_path = flow_root / "flow.manual.yaml"
    if flow_path.exists():
        flow = yaml.safe_load(flow_path.read_text(encoding="utf-8"))
        dependencies: set[str] = set()
        if isinstance(flow, Mapping):
            flow_mapping = cast(Mapping[str, object], flow)
            raw_dependencies = flow_mapping.get("dependencies", [])
            if isinstance(raw_dependencies, list):
                for dependency in cast(list[object], raw_dependencies):
                    if isinstance(dependency, Mapping):
                        dependency_mapping = cast(Mapping[str, object], dependency)
                        dependency_id = dependency_mapping.get("id")
                        if isinstance(dependency_id, str):
                            dependencies.add(dependency_id)
        for dependency_id in (
            "access_request_requires_project",
            "review_requires_access_request",
            "project_update_requires_project_create",
        ):
            if dependency_id not in dependencies:
                errors.append(f"flow missing dependency: {dependency_id}")
        component_sequence = flow_mapping.get("component_sequence")
        if not isinstance(component_sequence, list):
            errors.append("flow missing component_sequence")
        else:
            for component_id in COMPONENT_IDS:
                if component_id not in component_sequence:
                    errors.append(f"flow component_sequence missing: {component_id}")
        component_dependencies = {
            dependency_mapping.get("id")
            for dependency in as_list(flow_mapping.get("component_dependencies"))
            if isinstance(dependency, Mapping)
            for dependency_mapping in [cast(Mapping[str, object], dependency)]
        }
        for dependency_id in (
            "request_requires_project_and_api",
            "review_requires_pending_request",
            "entitlement_requires_approved_review",
            "runtime_allowed_requires_entitlement",
        ):
            if dependency_id not in component_dependencies:
                errors.append(f"flow missing component dependency: {dependency_id}")

    matrix_path = flow_root / "rules" / "matrix.manual.yaml"
    if matrix_path.exists():
        matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        if isinstance(matrix, Mapping):
            component_variant_generation = as_mapping(
                matrix.get("component_variant_generation")
            )
            component_dimensions = as_mapping(component_variant_generation.get("dimensions"))
            for component_id in COMPONENT_IDS:
                if component_id not in component_dimensions:
                    errors.append(f"matrix missing component dimension: {component_id}")
            component_case_generation = as_mapping(matrix.get("component_case_generation"))
            strategies = {
                strategy_mapping.get("id")
                for strategy in as_list(component_case_generation.get("strategies"))
                if isinstance(strategy, Mapping)
                for strategy_mapping in [cast(Mapping[str, object], strategy)]
            }
            for strategy_id in (
                "smoke",
                "component_variant_coverage",
                "interaction_coverage",
            ):
                if strategy_id not in strategies:
                    errors.append(f"matrix missing component case strategy: {strategy_id}")
            assertion_types = {
                assertion_mapping.get("type")
                for assertion in as_list(matrix.get("coverage_assertions"))
                if isinstance(assertion, Mapping)
                for assertion_mapping in [cast(Mapping[str, object], assertion)]
            }
            for assertion_type in (
                "every_variant_has_case",
                "every_target_has_case",
            ):
                if assertion_type not in assertion_types:
                    errors.append(f"matrix missing coverage assertion: {assertion_type}")

    component_variants = build_component_variants()
    variant_ids = {variant.variant_id for variant in component_variants}
    covered_goal_variants = {target_case.goal_variant for target_case in TARGET_CASES}
    missing_variants = sorted(variant_ids - covered_goal_variants)
    for variant_id in missing_variants:
        errors.append(f"component variant missing target case: {variant_id}")
    unknown_goal_variants = sorted(covered_goal_variants - variant_ids)
    for variant_id in unknown_goal_variants:
        errors.append(f"target case has unknown component variant: {variant_id}")
    covered_projects = {
        project.target_id
        for project in PROJECT_TARGETS
        if any(f".{project.target_id}." in target_case.goal_variant for target_case in TARGET_CASES)
    }
    for project in PROJECT_TARGETS:
        if project.target_id not in covered_projects:
            errors.append(f"target project missing target case: {project.target_id}")
    covered_apis = {
        api.target_id
        for api in API_TARGETS
        if any(f".{api.target_id}." in target_case.goal_variant for target_case in TARGET_CASES)
    }
    for api in API_TARGETS:
        if api.target_id not in covered_apis:
            errors.append(f"target api missing target case: {api.target_id}")
    runtime_states = {
        target_case.goal_variant.split("@", maxsplit=1)[0].rsplit(".", maxsplit=1)[-1]
        for target_case in TARGET_CASES
        if target_case.goal_component == "runtime_authorization"
    }
    for state_id in ("allowed", "denied"):
        if state_id not in runtime_states:
            errors.append(f"runtime_authorization state missing target case: {state_id}")

    factor_ids = {factor.factor_id for factor in FACTORS}
    factor_elements = {
        factor.factor_id: {element.element_id for element in factor.elements} for factor in FACTORS
    }
    for case in CASES:
        for factor_id, element_id in case.selected:
            if factor_id not in factor_ids:
                errors.append(f"{case.case_id}: unknown factor {factor_id}")
                continue
            if element_id not in factor_elements[factor_id]:
                errors.append(f"{case.case_id}: unknown element {factor_id}.{element_id}")
    for case in TARGET_CASES:
        scenario_path = flow_root / "cases" / case.filename
        if scenario_path.exists():
            scenario = scenario_path.read_text(encoding="utf-8")
            if "${project_api_key}" not in scenario:
                errors.append(f"{case.case_id}: scenario does not keep project_api_key placeholder")
            if "${runtime_access_token}" not in scenario:
                errors.append(
                    f"{case.case_id}: scenario does not keep runtime_access_token placeholder"
                )
            if case.goal_variant not in scenario:
                errors.append(f"{case.case_id}: scenario does not include goal variant")
            if case.case_id not in scenario:
                errors.append(f"{case.case_id}: scenario title does not include case id")
            for heading in (
                "## 1. 対象",
                "## 2. 処理概要",
                "## 3. 処理詳細",
                "## 4. エビデンス",
            ):
                if heading not in scenario:
                    errors.append(f"{case.case_id}: scenario missing heading {heading}")
    errors.extend(check_case_evidences(root))
    return errors


def as_mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, Mapping) else {}


def as_list(value: object) -> list[object]:
    return cast(list[object], value) if isinstance(value, list) else []


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    errors = check_specs()
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
