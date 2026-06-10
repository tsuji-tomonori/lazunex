from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

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
class E2eApiFactorDefinition:
    factor_id: str
    slug: str
    title: str
    owner_step: str
    success_label: str
    success_expected: str
    failure_element_id: str
    failure_label: str
    failure_expected: str
    order: int
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class E2eFactorElement:
    element_id: str
    label: str
    expected: str
    default: bool = False
    terminal: bool = False


@dataclass(frozen=True)
class E2eFactor:
    factor_id: str
    slug: str
    title: str
    category: str
    order: int
    owner_step: str
    elements: tuple[E2eFactorElement, ...]
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class E2eFactorData:
    data_id: str
    title: str
    tags: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class E2eCase:
    case_id: str
    slug: str
    kind: str
    tier: str
    purpose: str
    terminal_step: str
    selected: tuple[tuple[str, str], ...]
    scenario_steps: tuple[str, ...]
    expected: tuple[str, ...]

    @property
    def filename(self) -> str:
        return f"{self.case_id}_{self.slug}.gen.md"


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


def api_factor(definition: E2eApiFactorDefinition) -> E2eFactor:
    return E2eFactor(
        definition.factor_id,
        definition.slug,
        definition.title,
        "api_result",
        definition.order,
        definition.owner_step,
        (
            E2eFactorElement(
                "success",
                definition.success_label,
                definition.success_expected,
                default=True,
            ),
            E2eFactorElement(
                definition.failure_element_id,
                definition.failure_label,
                definition.failure_expected,
                terminal=True,
            ),
        ),
        requires=definition.requires,
    )


DEFAULT_DATA = E2eFactorData("default", "標準データ", ("default",))


FACTOR_DATA: dict[str, tuple[E2eFactorData, ...]] = {
    "F030": (
        E2eFactorData(
            "both_auth_mode",
            "requestedAuthMode=BOTH",
            ("valid_request", "auth_mode_both"),
        ),
        E2eFactorData(
            "public_pkce_auth_mode",
            "requestedAuthMode=PUBLIC_PKCE",
            ("valid_request", "auth_mode_public_pkce"),
        ),
        E2eFactorData(
            "client_credentials_auth_mode",
            "requestedAuthMode=CLIENT_CREDENTIALS",
            ("valid_request", "auth_mode_client_credentials"),
        ),
    ),
    "F040": (
        E2eFactorData("approve_both", "BOTH承認", ("review_request", "auth_mode_both")),
        E2eFactorData(
            "approve_public_pkce",
            "PUBLIC_PKCE承認",
            ("review_request", "auth_mode_public_pkce"),
        ),
        E2eFactorData(
            "approve_client_credentials",
            "CLIENT_CREDENTIALS承認",
            ("review_request", "auth_mode_client_credentials"),
        ),
    ),
    "F041": (E2eFactorData("reject_default", "標準却下", ("review_request", "reject")),),
    "F061": (E2eFactorData("subscriptions_default", "標準subscriptions確認", ("read_model",)),),
    "F070": (E2eFactorData("runtime_default", "標準Runtime呼び出し", ("runtime",)),),
}


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

PROJECT_OPERATION_DATA: tuple[E2eFactorData, ...] = (
    E2eFactorData("create_default", "標準Project作成データ", ("valid_project_create",)),
    E2eFactorData(
        "update_redirect_url",
        "callback URL更新データ",
        ("valid_project_update", "redirect_url_update"),
    ),
    E2eFactorData("invalid_project_code", "不正Project code", ("invalid_project_create",)),
)


def data_for_factor(factor_id: str) -> tuple[E2eFactorData, ...]:
    return FACTOR_DATA.get(factor_id, (DEFAULT_DATA,))


def target_variant_id(
    factor: str,
    project: E2eTarget,
    api: E2eTarget | None,
    operation: str,
    element: str,
    data: E2eFactorData,
) -> str:
    parts = [factor, project.target_id]
    if api is not None:
        parts.append(api.target_id)
    parts.extend([operation, element])
    return f"{'.'.join(parts)}@{data.data_id}"


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
    return value if isinstance(value, Mapping) else {}


def as_sequence(value: object) -> tuple[object, ...]:
    return tuple(value) if isinstance(value, list | tuple) else ()


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
    target_ids = set(as_sequence(target)) if isinstance(target, list) else {target}
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
        states = string_set(as_mapping(as_goal).get("states"))
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


FACTORS: tuple[E2eFactor, ...] = (
    api_factor(
        E2eApiFactorDefinition(
            "F000",
            "health_check_result",
            "GET /health ヘルスチェック結果",
            "get_health",
            "成功: appが応答可能",
            "HTTP 200とstatus okを返し、管理API E2Eの前提となるアプリ疎通を確認する。",
            "unavailable",
            "失敗: app疎通不可",
            "HTTP 5xxまたは応答なしとして扱い、管理APIフローを開始しない。",
            0,
        )
    ),
    E2eFactor(
        "F001",
        "management_actor",
        "管理API呼び出し主体",
        "actor",
        1,
        "management_api",
        (
            E2eFactorElement(
                "provider_owner_reviewer",
                "provider + project owner + reviewer",
                "API公開、Project作成、審査をそれぞれ権限のある主体で実行する。",
                default=True,
            ),
            E2eFactorElement(
                "non_reviewer",
                "reviewer以外",
                "approve/rejectでHTTP 403となりsubscriptionを作成しない。",
                terminal=True,
            ),
        ),
    ),
    E2eFactor(
        "F002",
        "management_auth",
        "管理API認証",
        "auth",
        2,
        "management_api",
        (
            E2eFactorElement(
                "valid",
                "有効なmanagement token",
                "管理API呼び出しが認証を通過する。",
                default=True,
            ),
            E2eFactorElement(
                "missing",
                "Authorizationなし",
                "最初の管理APIでHTTP 401となり後続stepを実行しない。",
                terminal=True,
            ),
        ),
    ),
    E2eFactor(
        "F010",
        "publish_api_result",
        "POST /apis API公開結果",
        "api_result",
        10,
        "post_apis",
        (
            E2eFactorElement(
                "success",
                "成功: catalog + stage + scope",
                "HTTP 201、apiId/apiStageId/scopeFullName返却、API catalog保存、"
                "Cognito scope作成、audit/provisioning記録を確認する。",
                default=True,
            ),
            E2eFactorElement(
                "duplicate_api_code",
                "失敗: duplicate apiCode",
                "POST /apisがHTTP 409となりProject作成以降を実行しない。",
                terminal=True,
            ),
            E2eFactorElement(
                "apigw_stage_invalid",
                "失敗: APIGW設定不備",
                "API Gateway stage登録確認が失敗しHTTP 400/502を返し、catalog/scopeを作成しない。",
                terminal=True,
            ),
            E2eFactorElement(
                "cognito_scope_failed",
                "失敗: Cognito scope作成失敗",
                "Cognito scope作成失敗でHTTP 502/503を返し、"
                "provisioning operation failedを記録する。",
                terminal=True,
            ),
        ),
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F011",
            "list_apis_result",
            "GET /apis API一覧取得結果",
            "get_apis",
            "成功: 一覧に公開APIが現れる",
            "HTTP 200、itemsに公開済みapiId/apiCode/scopeが含まれる、"
            "pagination/filterが仕様どおり、secret値を含まない。",
            "filter_no_match",
            "失敗相当: filter不一致",
            "HTTP 200かつitems空配列を返し、後続getApiは既知apiIdを使って継続する。",
            11,
            requires=("F010.success",),
        )
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F012",
            "get_api_result",
            "GET /apis/{apiId} API詳細取得結果",
            "get_api",
            "成功: 公開API詳細を取得",
            "HTTP 200、apiId/apiStageId/scopeFullNameがPOST /apisの返却値と一致し、"
            "登録済みreviewer/stage情報を確認できる。",
            "not_found",
            "失敗: apiId不明",
            "HTTP 404を返し、Project作成以降のAPI間状態遷移を実行しない。",
            12,
            requires=("F010.success", "F011.success"),
        )
    ),
    E2eFactor(
        "F020",
        "create_project_result",
        "POST /projects Project作成結果",
        "api_result",
        20,
        "post_projects",
        (
            E2eFactorElement(
                "success",
                "成功: project + API key + clients",
                "HTTP 201、projectId/API key/Cognito clientsを返却、"
                "Usage Plan/API key/client secret hashを保存、"
                "secret実値は後続placeholderにのみ渡す。",
                default=True,
            ),
            E2eFactorElement(
                "duplicate_project_code",
                "duplicate projectCode",
                "POST /projectsがHTTP 409となり利用申請以降を実行しない。",
                terminal=True,
            ),
        ),
        requires=("F010.success",),
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F021",
            "list_projects_result",
            "GET /projects Project一覧取得結果",
            "get_projects",
            "成功: 作成Projectが一覧に現れる",
            "HTTP 200、itemsにprojectId/projectCodeが含まれる、"
            "callerの権限範囲に絞られる、secret/API key実値を含まない。",
            "filter_no_match",
            "失敗相当: filter不一致",
            "HTTP 200かつitems空配列を返し、後続getProjectは既知projectIdを使って継続する。",
            21,
            requires=("F020.success",),
        )
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F022",
            "get_project_result",
            "GET /projects/{projectId} Project詳細取得結果",
            "get_project",
            "成功: Project詳細を取得",
            "HTTP 200、projectId/client構成/公開client設定を取得、"
            "API key値とclient secret値は再表示しない。",
            "not_found",
            "失敗: projectId不明",
            "HTTP 404を返し、public client更新と利用申請以降を実行しない。",
            22,
            requires=("F020.success", "F021.success"),
        )
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F023",
            "update_project_public_client_result",
            "PATCH /projects/{projectId}/public-client 更新結果",
            "patch_project_public_client",
            "成功: public client設定更新 + 承認済みscope保持",
            "HTTP 200、callback/logout/token設定が更新され、"
            "既存AllowedOAuthScopesと承認済みscopeを消さない。",
            "invalid_redirect_uri",
            "失敗: redirect URI不正",
            "HTTP 400/409を返し、既存public client設定と承認済みscopeを変更しない。",
            23,
            requires=("F020.success", "F022.success"),
        )
    ),
    E2eFactor(
        "F030",
        "access_request_result",
        "POST /projects/{projectId}/api-access-requests 利用申請作成結果",
        "api_result",
        30,
        "post_api_access_requests",
        (
            E2eFactorElement(
                "success",
                "成功: PENDING申請作成",
                "HTTP 201、PENDINGのaccessRequestIdを返却、authMode/apiStageId/"
                "reviewer候補を保存、audit/access_request eventを記録する。",
                default=True,
            ),
            E2eFactorElement(
                "duplicate_pending",
                "重複pending",
                "2回目の申請がHTTP 409となり既存pending requestを保持する。",
                terminal=True,
            ),
            E2eFactorElement(
                "already_subscribed",
                "既存subscriptionあり",
                "申請または承認がHTTP 409となり二重subscriptionを作成しない。",
                terminal=True,
            ),
        ),
        requires=("F010.success", "F020.success", "F023.success"),
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F031",
            "list_project_api_access_requests_result",
            "GET /projects/{projectId}/api-access-requests 利用申請一覧取得結果",
            "get_project_api_access_requests",
            "成功: PENDING申請が一覧に現れる",
            "HTTP 200、itemsにaccessRequestId/apiId/requestedAuthMode/stateが含まれ、"
            "Project単位に絞られる。",
            "unauthorized_project",
            "失敗: Project権限なし",
            "HTTP 403を返し、審査API以降を実行しない。",
            31,
            requires=("F030.success",),
        )
    ),
    E2eFactor(
        "F040",
        "approve_api_access_request_result",
        "POST /api-access-requests/{accessRequestId}/approve 承認結果",
        "api_result",
        40,
        "approve_api_access_request",
        (
            E2eFactorElement(
                "success",
                "成功: APPROVED + subscription + 外部反映",
                "HTTP 200、APPROVED review/subscriptionを保存し、"
                "Usage Plan stageとCognito scopeを反映、"
                "audit/provisioning eventを記録する。",
                default=True,
            ),
            E2eFactorElement(
                "non_reviewer",
                "失敗: reviewer以外",
                "HTTP 403を返し、subscription作成、Usage Plan/Cognito反映、"
                "Runtime API呼び出しを実行しない。",
                terminal=True,
            ),
            E2eFactorElement(
                "not_pending",
                "失敗: PENDINGではない",
                "HTTP 409を返し、二重review/subscriptionを作成しない。",
                terminal=True,
            ),
        ),
        requires=("F010.success", "F020.success", "F030.success", "F031.success"),
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F041",
            "reject_api_access_request_result",
            "POST /api-access-requests/{accessRequestId}/reject 却下結果",
            "reject_api_access_request",
            "成功: REJECTED + 外部反映なし",
            "HTTP 200、REJECTED reviewを保存し、"
            "subscription/Usage Plan/Cognito scopeを作成しない。",
            "non_reviewer",
            "失敗: reviewer以外",
            "HTTP 403を返し、review状態と外部反映を変更しない。",
            41,
            requires=("F010.success", "F020.success", "F030.success", "F031.success"),
        )
    ),
    E2eFactor(
        "F050",
        "approve_provisioning_result",
        "承認時provisioning",
        "external_side_effect",
        50,
        "approve_api_access_request",
        (
            E2eFactorElement(
                "apigw_success_cognito_success",
                "APIGW成功 + Cognito成功",
                "Usage Plan stageとCognito scopeの両方が反映される。",
                default=True,
            ),
            E2eFactorElement(
                "apigw_success_cognito_failed",
                "APIGW成功 + Cognito失敗",
                "HTTP 502/503とoperation failedを観測しretry可能なstepを残す。",
                terminal=True,
            ),
            E2eFactorElement(
                "retry_after_partial_failure",
                "partial failure後のretry",
                "既存Usage Plan stageを再利用しCognito scope付与から再開する。",
            ),
        ),
        requires=("F040.success",),
    ),
    api_factor(
        E2eApiFactorDefinition(
            "F061",
            "list_project_subscriptions_result",
            "GET /projects/{projectId}/subscriptions Subscription一覧取得結果",
            "get_project_subscriptions",
            "成功: 承認済みsubscriptionが一覧に現れる",
            "HTTP 200、itemsにapiId/apiStageId/subscriptionId/scopeFullName/"
            "derivedState ACTIVEが含まれる。",
            "none_after_reject",
            "失敗相当: 却下後subscriptionなし",
            "HTTP 200かつitemsに対象apiIdが現れず、Runtime API呼び出しを実行しない。",
            61,
            requires=("F040.success", "F050.apigw_success_cognito_success"),
        )
    ),
    E2eFactor(
        "F070",
        "runtime_credential",
        "Runtime credentials",
        "runtime_auth",
        70,
        "invoke_runtime_api",
        (
            E2eFactorElement(
                "valid_token_valid_api_key",
                "正常token + API key",
                "Runtime APIが期待する2xxを返す。",
                default=True,
            ),
            E2eFactorElement(
                "scope_missing",
                "scopeなしtoken",
                "Runtime APIが認可エラーを返す。",
            ),
            E2eFactorElement(
                "api_key_missing",
                "API keyなし",
                "Runtime APIが認可エラーを返す。",
            ),
        ),
        requires=("F061.success",),
    ),
)


CASES: tuple[E2eCase, ...] = (
    E2eCase(
        "TC001",
        "happy_approve_and_runtime_success",
        "happy",
        "smoke_sandbox",
        "API公開から承認、subscriptions確認、Runtime API呼び出し成功までを通す。",
        "-",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "success"),
            ("F023", "success"),
            ("F030", "success"),
            ("F031", "success"),
            ("F040", "success"),
            ("F050", "apigw_success_cognito_success"),
            ("F061", "success"),
            ("F070", "valid_token_valid_api_key"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
            "patch_project_public_client",
            "post_api_access_requests",
            "get_project_api_access_requests",
            "approve_api_access_request",
            "get_project_subscriptions",
            "invoke_runtime_api",
        ),
        (
            "API catalog、project、request、subscription、scope、Usage Planが一貫して作成される。",
            "Runtime APIが期待する2xxを返す。",
        ),
    ),
    E2eCase(
        "TC002",
        "reject_request_and_no_subscription",
        "branch",
        "smoke_sandbox",
        "利用申請を却下し、subscriptionとAWS反映が作成されないことを確認する。",
        "reject_api_access_request",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "success"),
            ("F023", "success"),
            ("F030", "success"),
            ("F031", "success"),
            ("F041", "success"),
            ("F061", "none_after_reject"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
            "patch_project_public_client",
            "post_api_access_requests",
            "get_project_api_access_requests",
            "reject_api_access_request",
            "get_project_subscriptions",
        ),
        (
            "reviewがREJECTEDになる。",
            "subscriptionが作成されずRuntime API呼び出しを実行しない。",
        ),
    ),
    E2eCase(
        "TC003",
        "approve_by_non_reviewer_is_403",
        "negative",
        "sandbox",
        "reviewer以外の主体によるapproveが拒否されることを確認する。",
        "approve_api_access_request",
        (
            ("F000", "success"),
            ("F001", "non_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "success"),
            ("F023", "success"),
            ("F030", "success"),
            ("F031", "success"),
            ("F040", "non_reviewer"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
            "patch_project_public_client",
            "post_api_access_requests",
            "get_project_api_access_requests",
            "approve_api_access_request",
        ),
        (
            "approveがHTTP 403を返す。",
            "subscriptionが作成されず後続Runtime API呼び出しを実行しない。",
        ),
    ),
    E2eCase(
        "TC004",
        "duplicate_access_request_is_409",
        "negative",
        "sandbox",
        "重複する利用申請が409となり既存pending requestが保持されることを確認する。",
        "post_api_access_requests",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "success"),
            ("F023", "success"),
            ("F030", "duplicate_pending"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
            "patch_project_public_client",
            "post_api_access_requests",
        ),
        ("2回目の申請がHTTP 409を返す。", "既存pending requestが上書きされない。"),
    ),
    E2eCase(
        "TC005",
        "approve_cognito_update_failed_is_retryable",
        "negative",
        "sandbox",
        "承認時にCognito更新が失敗した場合の部分失敗とretry可能性を確認する。",
        "approve_api_access_request",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "success"),
            ("F023", "success"),
            ("F030", "success"),
            ("F031", "success"),
            ("F040", "success"),
            ("F050", "apigw_success_cognito_failed"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
            "patch_project_public_client",
            "post_api_access_requests",
            "get_project_api_access_requests",
            "approve_api_access_request",
        ),
        (
            "approveがHTTP 502または503を返す。",
            "operation failedとretry可能なprovisioning stepを観測できる。",
        ),
    ),
    E2eCase(
        "TC006",
        "get_api_unknown_id_is_404",
        "negative",
        "local_fake",
        "公開API詳細取得で不明apiIdが404となり後続状態遷移を止める。",
        "get_api",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "not_found"),
        ),
        ("get_health", "post_apis", "get_apis", "get_api"),
        ("GET /apis/{apiId}がHTTP 404を返す。", "Project作成以降を実行しない。"),
    ),
    E2eCase(
        "TC007",
        "get_project_unknown_id_is_404",
        "negative",
        "local_fake",
        "Project詳細取得で不明projectIdが404となり利用申請以降を止める。",
        "get_project",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "not_found"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
        ),
        ("GET /projects/{projectId}がHTTP 404を返す。", "public client更新以降を実行しない。"),
    ),
    E2eCase(
        "TC008",
        "public_client_update_keeps_approved_scope",
        "branch",
        "sandbox",
        "public client更新後も承認済みscopeを保持する。",
        "-",
        (
            ("F000", "success"),
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F011", "success"),
            ("F012", "success"),
            ("F020", "success"),
            ("F021", "success"),
            ("F022", "success"),
            ("F023", "success"),
            ("F030", "success"),
            ("F031", "success"),
            ("F040", "success"),
            ("F050", "apigw_success_cognito_success"),
            ("F061", "success"),
        ),
        (
            "get_health",
            "post_apis",
            "get_apis",
            "get_api",
            "post_projects",
            "get_projects",
            "get_project",
            "patch_project_public_client",
            "post_api_access_requests",
            "get_project_api_access_requests",
            "approve_api_access_request",
            "get_project_subscriptions",
            "patch_project_public_client",
            "get_project",
        ),
        (
            "public client設定更新後も承認済みscopeが残る。",
            "subscriptionsのACTIVE状態が維持される。",
        ),
    ),
)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def factor_by_id() -> dict[str, E2eFactor]:
    return {factor.factor_id: factor for factor in FACTORS}


def variant_id(factor: E2eFactor, element: E2eFactorElement, data: E2eFactorData) -> str:
    return f"{factor.slug}.{element.element_id}@{data.data_id}"


def binding_steps(factor: E2eFactor, element: E2eFactorElement) -> tuple[str, ...]:
    if factor.factor_id == "F030" and element.element_id == "duplicate_pending":
        return ("setup_pending_access_request", factor.owner_step)
    if factor.factor_id == "F030" and element.element_id == "already_subscribed":
        return ("setup_active_subscription", factor.owner_step)
    if factor.factor_id == "F040" and element.element_id == "not_pending":
        return ("setup_reviewed_access_request", factor.owner_step)
    return (factor.owner_step,)


def binding_expectations(factor: E2eFactor, element: E2eFactorElement) -> tuple[str, ...]:
    expectations = [f"{factor.slug}.{element.element_id}"]
    if element.terminal:
        expectations.append("common.no_later_steps")
    return tuple(expectations)


def selected_variant_id(factor_id: str, element_id: str) -> str:
    factor = factor_by_id()[factor_id]
    for element in factor.elements:
        if element.element_id == element_id:
            return variant_id(factor, element, data_for_factor(factor_id)[0])
    raise KeyError(f"{factor_id}.{element_id}")


def element_label(factor_id: str, element_id: str) -> str:
    factor = factor_by_id()[factor_id]
    for element in factor.elements:
        if element.element_id == element_id:
            return element.label
    raise KeyError(f"{factor_id}.{element_id}")
