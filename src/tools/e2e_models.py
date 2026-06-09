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


def element_label(factor_id: str, element_id: str) -> str:
    factor = factor_by_id()[factor_id]
    for element in factor.elements:
        if element.element_id == element_id:
            return element.label
    raise KeyError(f"{factor_id}.{element_id}")
