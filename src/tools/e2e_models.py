from __future__ import annotations

from dataclasses import dataclass

FLOW_ID = "api_access_lifecycle"
FLOW_TITLE = "API access lifecycle"


@dataclass(frozen=True)
class E2eStep:
    step_id: str
    operation: str
    method: str
    path: str
    template: str
    captures: tuple[str, ...] = ()


@dataclass(frozen=True)
class E2eFactorElement:
    element_id: str
    label: str
    expected: str
    default: bool = False
    terminal: bool = False
    tier: str = "sandbox"


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
    E2eStep("S001", "publishApi", "POST", "/apis", "post_apis", ("apiId", "apiStageId")),
    E2eStep("S002", "listApis", "GET", "/apis", "get_apis"),
    E2eStep("S003", "getApi", "GET", "/apis/${apiId}", "get_api"),
    E2eStep("S010", "createProject", "POST", "/projects", "post_projects", ("projectId",)),
    E2eStep(
        "S020",
        "createApiAccessRequest",
        "POST",
        "/projects/${projectId}/api-access-requests",
        "post_api_access_requests",
        ("accessRequestId",),
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


FACTORS: tuple[E2eFactor, ...] = (
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
                tier="smoke_sandbox",
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
                tier="smoke_sandbox",
            ),
            E2eFactorElement(
                "missing",
                "Authorizationなし",
                "最初の管理APIでHTTP 401となり後続stepを実行しない。",
                terminal=True,
                tier="local_fake",
            ),
        ),
    ),
    E2eFactor(
        "F010",
        "publish_api_result",
        "API公開結果",
        "business_state",
        10,
        "post_apis",
        (
            E2eFactorElement(
                "success",
                "成功",
                "apiId、apiStageId、scopeFullNameを後続stepに渡せる。",
                default=True,
                tier="smoke_sandbox",
            ),
            E2eFactorElement(
                "duplicate_api_code",
                "duplicate apiCode",
                "POST /apisがHTTP 409となりProject作成以降を実行しない。",
                terminal=True,
            ),
        ),
    ),
    E2eFactor(
        "F020",
        "create_project_result",
        "Project作成結果",
        "business_state",
        20,
        "post_projects",
        (
            E2eFactorElement(
                "success",
                "成功",
                "projectId、API key、Cognito clientを後続stepに渡せる。",
                default=True,
                tier="smoke_sandbox",
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
    E2eFactor(
        "F030",
        "access_request_result",
        "利用申請結果",
        "business_state",
        30,
        "post_api_access_requests",
        (
            E2eFactorElement(
                "success",
                "新規成功",
                "PENDINGのaccessRequestIdを審査stepに渡せる。",
                default=True,
                tier="smoke_sandbox",
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
        requires=("F010.success", "F020.success"),
    ),
    E2eFactor(
        "F040",
        "review_decision",
        "審査結果",
        "business_state",
        40,
        "review_api_access_request",
        (
            E2eFactorElement(
                "approve",
                "approve",
                "subscriptionと外部provisioningが作成される。",
                default=True,
                tier="smoke_sandbox",
            ),
            E2eFactorElement(
                "reject",
                "reject",
                "REJECTEDとなりsubscriptionとAWS反映を作成しない。",
                terminal=True,
                tier="smoke_sandbox",
            ),
        ),
        requires=("F010.success", "F020.success", "F030.success"),
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
                tier="smoke_sandbox",
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
                tier="sandbox",
            ),
        ),
        requires=("F040.approve",),
    ),
    E2eFactor(
        "F060",
        "runtime_credential",
        "Runtime credentials",
        "runtime_auth",
        60,
        "invoke_runtime_api",
        (
            E2eFactorElement(
                "valid_token_valid_api_key",
                "正常token + API key",
                "Runtime APIが期待する2xxを返す。",
                default=True,
                tier="smoke_sandbox",
            ),
            E2eFactorElement(
                "scope_missing",
                "scopeなしtoken",
                "Runtime APIが認可エラーを返す。",
                tier="smoke_sandbox",
            ),
            E2eFactorElement(
                "api_key_missing",
                "API keyなし",
                "Runtime APIが認可エラーを返す。",
                tier="smoke_sandbox",
            ),
        ),
        requires=("F050.apigw_success_cognito_success",),
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
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F020", "success"),
            ("F030", "success"),
            ("F040", "approve"),
            ("F050", "apigw_success_cognito_success"),
            ("F060", "valid_token_valid_api_key"),
        ),
        (
            "post_apis",
            "post_projects",
            "post_api_access_requests",
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
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F020", "success"),
            ("F030", "success"),
            ("F040", "reject"),
        ),
        (
            "post_apis",
            "post_projects",
            "post_api_access_requests",
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
            ("F001", "non_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F020", "success"),
            ("F030", "success"),
            ("F040", "approve"),
        ),
        (
            "post_apis",
            "post_projects",
            "post_api_access_requests",
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
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F020", "success"),
            ("F030", "duplicate_pending"),
        ),
        ("post_apis", "post_projects", "post_api_access_requests"),
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
            ("F001", "provider_owner_reviewer"),
            ("F002", "valid"),
            ("F010", "success"),
            ("F020", "success"),
            ("F030", "success"),
            ("F040", "approve"),
            ("F050", "apigw_success_cognito_failed"),
        ),
        (
            "post_apis",
            "post_projects",
            "post_api_access_requests",
            "approve_api_access_request",
        ),
        (
            "approveがHTTP 502または503を返す。",
            "operation failedとretry可能なprovisioning stepを観測できる。",
        ),
    ),
)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def factor_by_id() -> dict[str, E2eFactor]:
    return {factor.factor_id: factor for factor in FACTORS}


def element_label(factor_id: str, element_id: str) -> str:
    factor = factor_by_id()[factor_id]
    for element in factor.elements:
        if element.element_id == element_id:
            return element.label
    raise KeyError(f"{factor_id}.{element_id}")
