from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

FLOW_ID = "api_access_lifecycle"
FLOW_TITLE = "API access lifecycle"
E2E_SPEC_ROOT = Path("docs/spec/50.e2e") / FLOW_ID
COMPONENT_IDS = (
    "api_catalog",
    "project_workspace",
    "access_request_workflow",
    "review_decision",
    "entitlement_provisioning",
    "runtime_authorization",
    "audit_recovery",
)


@dataclass(frozen=True)
class E2eStep:
    step_id: str
    operation: str
    method: str
    path: str
    template: str
    captures: tuple[str, ...] = ()


@dataclass(frozen=True)
class E2eTarget:
    target_id: str
    title: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class E2eRuntimeAssertion:
    project_id: str
    api_id: str
    expected: str


@dataclass(frozen=True)
class E2eTargetCase:
    case_id: str
    title: str
    coverage_group: str
    goal_component: str
    goal_variant: str
    selected_variants: tuple[str, ...]
    runtime_assertions: tuple[E2eRuntimeAssertion, ...] = ()

    @property
    def filename(self) -> str:
        slug = re.sub(r"[^0-9A-Za-z]+", "_", self.goal_variant).strip("_").lower()
        return f"{self.case_id}_{slug}.gen.md"


@dataclass(frozen=True)
class E2eComponentVariant:
    component_id: str
    action_id: str
    project_id: str | None
    api_id: str | None
    state_id: str
    data_id: str
    continue_flow: bool

    @property
    def variant_id(self) -> str:
        parts = [self.component_id, self.action_id]
        if self.project_id is not None:
            parts.append(self.project_id)
        if self.api_id is not None:
            parts.append(self.api_id)
        parts.append(self.state_id)
        return f"{'.'.join(parts)}@{self.data_id}"


FLOW_STEPS: tuple[E2eStep, ...] = (
    E2eStep("S000", "healthCheck", "GET", "/health", "get_health"),
    E2eStep("S001", "publishApi", "POST", "/apis", "post_apis", ("apiId", "apiStageId")),
    E2eStep("S002", "listApis", "GET", "/apis", "get_apis"),
    E2eStep("S003", "getApi", "GET", "/apis/${apiId}", "get_api"),
    E2eStep("S010", "createProject", "POST", "/projects", "post_projects", ("projectId",)),
    E2eStep("S011", "listProjects", "GET", "/projects", "get_projects"),
    E2eStep("S012", "getProject", "GET", "/projects/${projectId}", "get_project"),
    E2eStep(
        "S013",
        "updateProjectPublicClient",
        "PATCH",
        "/projects/${projectId}/public-client",
        "patch_project_public_client",
    ),
    E2eStep(
        "S020",
        "createApiAccessRequest",
        "POST",
        "/projects/${projectId}/api-access-requests",
        "post_api_access_requests",
        ("accessRequestId",),
    ),
    E2eStep(
        "S021",
        "listProjectApiAccessRequests",
        "GET",
        "/projects/${projectId}/api-access-requests",
        "get_project_api_access_requests",
    ),
    E2eStep(
        "S030",
        "approveApiAccessRequest",
        "POST",
        "/api-access-requests/${accessRequestId}/approve",
        "approve_api_access_request",
        ("subscriptionId", "operationId"),
    ),
    E2eStep(
        "S031",
        "rejectApiAccessRequest",
        "POST",
        "/api-access-requests/${accessRequestId}/reject",
        "reject_api_access_request",
    ),
    E2eStep(
        "S040",
        "listProjectSubscriptions",
        "GET",
        "/projects/${projectId}/subscriptions",
        "get_project_subscriptions",
    ),
    E2eStep("S050", "invokeRuntimeApi", "GET", "${runtime_invoke_url}", "invoke_runtime_api"),
)


PROJECT_TARGETS: tuple[E2eTarget, ...] = (
    E2eTarget(
        "project_A",
        "Project A",
        ("normal_project", "public_client_enabled", "confidential_client_enabled"),
    ),
    E2eTarget(
        "project_B",
        "Project B",
        ("normal_project", "public_client_enabled", "confidential_client_enabled"),
    ),
    E2eTarget(
        "project_C",
        "Project C",
        ("normal_project", "public_client_enabled", "confidential_client_enabled"),
    ),
)

API_TARGETS: tuple[E2eTarget, ...] = (
    E2eTarget("API_A", "API A", ("published_api", "runtime_callable")),
    E2eTarget("API_B", "API B", ("published_api", "runtime_callable")),
    E2eTarget("API_C", "API C", ("published_api", "runtime_callable")),
)

def target_component_variant_id(
    component: str,
    action: str,
    project: E2eTarget | None,
    api: E2eTarget | None,
    state: str,
    data_id: str,
) -> str:
    parts = [component, action]
    if project is not None:
        parts.append(project.target_id)
    if api is not None:
        parts.append(api.target_id)
    parts.append(state)
    return f"{'.'.join(parts)}@{data_id}"


def as_mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, Mapping) else {}


def as_sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, list | tuple):
        return tuple(cast(list[object] | tuple[object, ...], value))
    return ()


def scalar_text(value: object, default: str = "-") -> str:
    return value if isinstance(value, str) else default


def string_set(value: object) -> set[str]:
    return {item for item in as_sequence(value) if isinstance(item, str)}


def load_component_yaml(component_id: str, filename: str) -> Mapping[str, object]:
    path = E2E_SPEC_ROOT / "components" / component_id / filename
    return as_mapping(yaml.safe_load(path.read_text(encoding="utf-8")))


def target_allowed(target_id: str | None, policy: str, target_type: str) -> bool:
    if target_id is None:
        return True
    if policy == "all":
        return True
    if policy == "canonical_pair":
        return target_id in {"project_A", "API_A"}
    if policy == "canonical_project" and target_type == "project":
        return target_id == "project_A"
    if policy == "canonical_api" and target_type == "api":
        return target_id == "API_A"
    return True


def target_coverage_policy(
    action: Mapping[str, object],
    state: Mapping[str, object],
    data_profile: Mapping[str, object],
) -> str:
    state_value = state.get("target_coverage")
    if isinstance(state_value, str):
        return state_value
    if state.get("continue_flow") is False:
        return "canonical_pair"
    for source in (data_profile, action):
        value = source.get("target_coverage")
        if isinstance(value, str):
            return value
    return "all"


def action_targets(
    action: Mapping[str, object],
    policy: str = "all",
) -> tuple[tuple[str | None, str | None], ...]:
    target = action.get("target")
    target_values = tuple(cast(list[object], target)) if isinstance(target, list) else (target,)
    target_ids = set(target_values)
    uses_project = "project" in target_ids
    uses_api = "api" in target_ids
    projects: tuple[E2eTarget | None, ...] = PROJECT_TARGETS if uses_project else (None,)
    apis: tuple[E2eTarget | None, ...] = API_TARGETS if uses_api else (None,)
    return tuple(
        (project_id, api_id)
        for project in projects
        for api in apis
        for project_id in [project.target_id if project is not None else None]
        for api_id in [api.target_id if api is not None else None]
        if target_allowed(project_id, policy, "project")
        and target_allowed(api_id, policy, "api")
    )


def compatible_with(value: str, allowed: object) -> bool:
    allowed_values = string_set(allowed)
    return not allowed_values or value in allowed_values


def action_state_compatible(action: Mapping[str, object], state: Mapping[str, object]) -> bool:
    action_id = scalar_text(action.get("id"))
    state_id = scalar_text(state.get("id"))
    return compatible_with(state_id, action.get("compatible_states")) and compatible_with(
        action_id, state.get("compatible_actions")
    )


def data_compatible(
    action: Mapping[str, object],
    state: Mapping[str, object],
    data_profile: Mapping[str, object],
) -> bool:
    action_id = scalar_text(action.get("id"))
    state_id = scalar_text(state.get("id"))
    data_tags = string_set(data_profile.get("tags"))
    required_tags = string_set(state.get("requires_data_tags"))
    return (
        compatible_with(action_id, data_profile.get("compatible_actions"))
        and compatible_with(state_id, data_profile.get("compatible_states"))
        and required_tags <= data_tags
    )


def standalone_case_enabled(
    action: Mapping[str, object],
    state: Mapping[str, object],
    data_profile: Mapping[str, object],
) -> bool:
    case_generation = as_mapping(action.get("case_generation"))
    for case in as_sequence(case_generation.get("standalone_cases")):
        case_mapping = as_mapping(case)
        if (
            scalar_text(case_mapping.get("state")) == scalar_text(state.get("id"))
            and scalar_text(case_mapping.get("data")) == scalar_text(data_profile.get("id"))
        ):
            return True
    return False


def action_goal_enabled(
    action: Mapping[str, object],
    state: Mapping[str, object],
    data_profile: Mapping[str, object],
) -> bool:
    case_generation = as_mapping(action.get("case_generation"))
    as_goal = case_generation.get("as_goal")
    if isinstance(as_goal, bool):
        return as_goal or standalone_case_enabled(action, state, data_profile)
    if isinstance(as_goal, Mapping):
        states = string_set(cast(Mapping[str, object], as_goal).get("states"))
        return scalar_text(state.get("id")) in states
    operation_type = scalar_text(action.get("operation_type"))
    if operation_type in {"query", "evidence"}:
        return standalone_case_enabled(action, state, data_profile)
    return True


def should_generate_variant(
    action: Mapping[str, object],
    state: Mapping[str, object],
    data_profile: Mapping[str, object],
) -> bool:
    coverage_role = scalar_text(data_profile.get("coverage_role"))
    if coverage_role == "evidence_probe" and not standalone_case_enabled(
        action, state, data_profile
    ):
        return False
    return action_goal_enabled(action, state, data_profile)


def build_component_variants() -> tuple[E2eComponentVariant, ...]:
    variants: list[E2eComponentVariant] = []
    for component_id in COMPONENT_IDS:
        actions_doc = load_component_yaml(component_id, "actions.manual.yaml")
        states_doc = load_component_yaml(component_id, "states.manual.yaml")
        data_doc = load_component_yaml(component_id, "data.manual.yaml")
        actions = [as_mapping(action) for action in as_sequence(actions_doc.get("actions"))]
        states = [as_mapping(state) for state in as_sequence(states_doc.get("states"))]
        data_profiles = [
            as_mapping(data_profile)
            for data_profile in as_sequence(data_doc.get("data_profiles"))
        ]
        for action in actions:
            action_id = scalar_text(action.get("id"))
            for state in states:
                if not action_state_compatible(action, state):
                    continue
                state_id = scalar_text(state.get("id"))
                continue_flow = state.get("continue_flow")
                for data_profile in data_profiles:
                    if not data_compatible(action, state, data_profile):
                        continue
                    if not should_generate_variant(action, state, data_profile):
                        continue
                    policy = target_coverage_policy(action, state, data_profile)
                    for project_id, api_id in action_targets(action, policy):
                        variants.append(
                            E2eComponentVariant(
                                component_id,
                                action_id,
                                project_id,
                                api_id,
                                state_id,
                                scalar_text(data_profile.get("id")),
                                continue_flow if isinstance(continue_flow, bool) else False,
                            )
                        )
    return tuple(variants)


def default_project_variant(project_id: str) -> str:
    return (
        "project_workspace.create_project."
        f"{project_id}.provisioned@project_default"
    )


def default_api_variant(api_id: str) -> str:
    return f"api_catalog.publish_api.{api_id}.published@api_default"


def default_access_request_variant(project_id: str, api_id: str) -> str:
    return (
        "access_request_workflow.submit_request."
        f"{project_id}.{api_id}.submitted@request_both_auth"
    )


def default_approve_variant(project_id: str, api_id: str) -> str:
    return f"review_decision.approve_request.{project_id}.{api_id}.approved@approve_both"


def default_reject_variant(project_id: str, api_id: str) -> str:
    return f"review_decision.reject_request.{project_id}.{api_id}.rejected@reject_default"


def default_entitlement_variant(project_id: str, api_id: str) -> str:
    return (
        "entitlement_provisioning.provision_entitlement."
        f"{project_id}.{api_id}.provisioned@approved_both_entitlement"
    )


def prerequisites_for_component_variant(variant: E2eComponentVariant) -> tuple[str, ...]:
    project_id = variant.project_id
    api_id = variant.api_id
    prerequisites: list[str] = []
    if variant.component_id == "api_catalog":
        if variant.action_id == "browse_api" and api_id is not None:
            prerequisites.append(default_api_variant(api_id))
    elif variant.component_id == "project_workspace":
        if variant.action_id == "update_public_client" and project_id is not None:
            prerequisites.append(default_project_variant(project_id))
    elif variant.component_id == "access_request_workflow" and project_id and api_id:
        prerequisites.extend((default_api_variant(api_id), default_project_variant(project_id)))
    elif variant.component_id == "review_decision" and project_id and api_id:
        prerequisites.extend(
            (
                default_api_variant(api_id),
                default_project_variant(project_id),
                default_access_request_variant(project_id, api_id),
            )
        )
    elif variant.component_id == "entitlement_provisioning" and project_id and api_id:
        prerequisites.extend(
            (
                default_api_variant(api_id),
                default_project_variant(project_id),
                default_access_request_variant(project_id, api_id),
                (
                    default_reject_variant(project_id, api_id)
                    if variant.state_id == "not_provisioned"
                    else default_approve_variant(project_id, api_id)
                ),
            )
        )
    elif variant.component_id == "runtime_authorization" and project_id and api_id:
        prerequisites.extend(
            (
                default_api_variant(api_id),
                default_project_variant(project_id),
                default_access_request_variant(project_id, api_id),
                default_approve_variant(project_id, api_id),
                default_entitlement_variant(project_id, api_id),
            )
        )
    elif variant.component_id == "audit_recovery":
        if api_id is not None:
            prerequisites.append(default_api_variant(api_id))
        if project_id is not None:
            prerequisites.append(default_project_variant(project_id))
    return tuple(dict.fromkeys(item for item in prerequisites if item != variant.variant_id))


def component_variant_title(variant: E2eComponentVariant) -> str:
    targets = " / ".join(
        target
        for target in (variant.project_id, variant.api_id)
        if target is not None
    )
    target_label = f"{targets} " if targets else ""
    return (
        f"{target_label}{variant.component_id}.{variant.action_id} "
        f"{variant.state_id}@{variant.data_id} を主役にする"
    )


def target_case_runtime_assertions(
    project: E2eTarget,
    allowed_api: E2eTarget | None,
) -> tuple[E2eRuntimeAssertion, ...]:
    return tuple(
        E2eRuntimeAssertion(
            project.target_id,
            api.target_id,
            "allowed" if allowed_api == api else "denied",
        )
        for api in API_TARGETS
    )


def embedded_goal_variant(variant: E2eComponentVariant) -> bool:
    embedded_goals = {
        ("api_catalog", "publish_api", "published", "api_default"),
        ("project_workspace", "create_project", "provisioned", "project_default"),
        (
            "access_request_workflow",
            "submit_request",
            "submitted",
            "request_both_auth",
        ),
        ("review_decision", "approve_request", "approved", "approve_both"),
    }
    return (
        variant.component_id,
        variant.action_id,
        variant.state_id,
        variant.data_id,
    ) in embedded_goals


def build_target_cases() -> tuple[E2eTargetCase, ...]:
    cases: list[E2eTargetCase] = []
    for variant in build_component_variants():
        if embedded_goal_variant(variant):
            continue
        selected_variants = (
            *prerequisites_for_component_variant(variant),
            variant.variant_id,
        )
        runtime_assertions: tuple[E2eRuntimeAssertion, ...] = ()
        if (
            variant.component_id == "runtime_authorization"
            and variant.project_id is not None
            and variant.api_id is not None
        ):
            runtime_assertions = (
                E2eRuntimeAssertion(
                    variant.project_id,
                    variant.api_id,
                    "allowed" if variant.state_id == "allowed" else "denied",
                ),
            )
        cases.append(
            E2eTargetCase(
                f"TC_TARGET_{len(cases) + 1:03d}",
                component_variant_title(variant),
                "component_variant",
                variant.component_id,
                variant.variant_id,
                selected_variants,
                runtime_assertions,
            )
        )
    return tuple(cases)


TARGET_CASES = build_target_cases()


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
