from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.apis.base import sample_value
from app.apis.deps import get_caller_identity, get_request_context
from app.apis.projects.create_project import functions as api_functions
from app.apis.projects.create_project.samples import (
    CREATE_PROJECT_REQUEST_SAMPLE,
    CREATE_PROJECT_RESPONSE_SAMPLE,
    CREATE_PROJECT_STATUS_SAMPLES,
)
from app.apis.projects.create_project.schemas import CreateProjectRequest, CreateProjectResponse
from app.apis.responses import (
    error_responses,
    success_response,
)
from app.apis.router_errors import (
    ROUTER_HANDLED_EXCEPTIONS,
    api_error_response,
    error_response_for_router_error,
    has_existing_idempotency_result,
    router_log_context,
    status_code_for_router_error,
)
from app.apis.sequence_types import CallerIdentity, RequestContext
from app.core.logging import get_operation_logger
from app.db.session import get_session
from app.integrations.api_gateway_control.deps import get_api_gateway_control_client
from app.integrations.api_gateway_control.port import ApiGatewayControlPort
from app.integrations.identity.deps import get_identity_admin_client
from app.integrations.identity.port import IdentityAdminPort
from app.integrations.secret_values.deps import get_secret_values_client
from app.integrations.secret_values.port import SecretValuesPort

router = APIRouter()
ops_logger = get_operation_logger(__name__)


@router.post(
    "/projects",
    operation_id="createProject",
    summary="プロジェクトを作成する",
    description=(
        "API利用単位となるプロジェクトを作成し、API keyとCognito app clientを払い出します。"
    ),
    response_model=CreateProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: success_response(CREATE_PROJECT_RESPONSE_SAMPLE),
        **error_responses(
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_409_CONFLICT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            samples=CREATE_PROJECT_STATUS_SAMPLES,
        ),
    },
    tags=["projects"],
)
async def create_project(
    request: Annotated[
        CreateProjectRequest,
        Body(openapi_examples={"default": {"value": sample_value(CREATE_PROJECT_REQUEST_SAMPLE)}}),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    caller: Annotated[CallerIdentity, Depends(get_caller_identity)],
    api_gateway_control: Annotated[
        ApiGatewayControlPort,
        Depends(get_api_gateway_control_client),
    ],
    identity_admin: Annotated[IdentityAdminPort, Depends(get_identity_admin_client)],
    secret_values: Annotated[SecretValuesPort, Depends(get_secret_values_client)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateProjectResponse | JSONResponse:
    try:
        validated_request = await api_functions.validate_create_project_request(request)
        if not await api_functions.has_project_creation_permission(caller):
            ops_logger.warning(
                "createProject.caller_cannot_create_project",
                catalog_id="M001",
                summary="呼び出し元がProjectを作成できないため、リクエストを拒否した。",
                status_code=status.HTTP_403_FORBIDDEN,
                detail="caller cannot create project",
                when="呼び出し元がProject作成権限を持たない場合。",
                why_production="Project作成の認可拒否を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "error.code, error.message",
                operator_action="actorPrincipalIdとProject作成権限を確認する。",
                runbook="RUNBOOK-authorization-forbidden",
                context=router_log_context(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="caller cannot create project",
                    caller=caller,
                    request_context=request_context,
                ),
            )
            return api_error_response(status.HTTP_403_FORBIDDEN, "caller cannot create project")
        idempotency_record = await api_functions.get_idempotency_record(
            idempotency_key, session
        )
        if has_existing_idempotency_result(idempotency_record):
            ops_logger.warning(
                "createProject.idempotency_key_already_used",
                catalog_id="M005",
                summary="Idempotency-Keyが既に処理結果へ紐づいているため、リクエストを拒否した。",
                status_code=status.HTTP_409_CONFLICT,
                detail="idempotency key is already used",
                when="Idempotency-Keyに対応する処理結果が既に存在する場合。",
                why_production="冪等性キーの再利用やリトライ衝突を運用で追跡するため。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "error.code, error.message",
                operator_action="Idempotency-Key、operationId、既存responsePayloadを確認する。",
                runbook="RUNBOOK-state-conflict-idempotency",
                context=router_log_context(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="idempotency key is already used",
                    caller=caller,
                    request_context=request_context,
                ),
            )
            return api_error_response(
                status.HTTP_409_CONFLICT,
                "idempotency key is already used",
            )
        operation = await api_functions.create_project_provisioning_operation(
            validated_request,
            idempotency_key,
            caller,
            session,
        )
        await api_functions.create_idempotency_record(
            idempotency_key,
            operation,
            validated_request,
            caller,
            session,
        )
        api_key = await api_functions.create_api_gateway_api_key(
            validated_request,
            operation,
            api_gateway_control,
        )
        usage_plan_id = await api_functions.create_api_gateway_usage_plan(
            validated_request,
            operation,
            api_gateway_control,
        )
        usage_plan_key_id = await api_functions.create_api_gateway_usage_plan_key(
            api_key,
            usage_plan_id,
            api_gateway_control,
        )
        public_client_id = await api_functions.create_cognito_public_app_client(
            validated_request,
            identity_admin,
        )
        confidential_client = await api_functions.create_cognito_confidential_app_client(
            validated_request,
            identity_admin,
        )
        secret_hashes = await api_functions.hash_project_secrets(
            api_key.api_key_value,
            confidential_client.client_secret,
            secret_values,
        )
        resources = await api_functions.save_project_resources(
            validated_request,
            api_key,
            usage_plan_id,
            usage_plan_key_id,
            public_client_id,
            confidential_client,
            secret_hashes,
            operation,
            caller,
            session,
        )
        await api_functions.append_project_lifecycle_events(
            resources,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_provisioning_events(
            operation,
            caller,
            request_context,
            idempotency_key,
            session,
        )
        await api_functions.append_audit_event(
            resources, caller, request_context, operation, session
        )
        try:
            await session.commit()
        except IntegrityError as error:
            ops_logger.error(
                "createProject.db_integrity_error",
                catalog_id="M003",
                summary="DB整合性違反によりProject作成のcommitが失敗した。",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="database integrity error",
                when="Project作成のDB transaction commitでIntegrityErrorを捕捉した場合。",
                check_procedure="traceId/requestIdでログを検索し、"
                "project/provisioning/idempotencyの重複や参照整合性を確認する。",
                remediation_procedure="DB内不整合を特定し、DBパッチまたはデータ補正を行う。"
                "補正後、冪等性状態を確認してから同一Idempotency-Keyで再実行する。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "error.code, error.message, error.exceptionType",
                operator_action="Project関連テーブル、provisioning/idempotency、"
                "制約違反対象を確認し、パッチ適用手順を作成してデータ補正を行う。",
                runbook="RUNBOOK-db-data-repair",
                context=router_log_context(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="database integrity error",
                    caller=caller,
                    request_context=request_context,
                    error=error,
                ),
            )
            return api_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "database integrity error",
            )
        except SQLAlchemyError as error:
            ops_logger.error(
                "createProject.db_commit_failed",
                catalog_id="M004",
                summary="DB commit失敗によりProject作成を確定できなかった。",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database commit failed",
                when="Project作成のDB transaction commitでSQLAlchemyErrorを捕捉した場合。",
                check_procedure="traceId/requestIdでログを検索し、DB接続、timeout、"
                "transaction rollback状態を確認する。",
                remediation_procedure="DB一時障害またはcommit失敗として扱い、rollbackを確認する。"
                "利用者へ同一Idempotency-Keyでの再実行を依頼する。",
                context_model="traceId, actorPrincipalId, api.statusCode, "
                "error.code, error.message, error.exceptionType",
                operator_action="DB接続状態、transaction rollback、idempotency状態を確認し、"
                "必要に応じて利用者へ再実行を案内する。",
                runbook="RUNBOOK-db-commit-retry",
                context=router_log_context(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="database commit failed",
                    caller=caller,
                    request_context=request_context,
                    error=error,
                ),
            )
            return api_error_response(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "database commit failed",
            )
        return await api_functions.build_create_project_response(
            resources,
            api_key.api_key_value,
            confidential_client,
            operation,
        )
    except ROUTER_HANDLED_EXCEPTIONS as error:
        ops_logger.error(
            "createProject.router_error",
            catalog_id="M002",
            summary="Routerで捕捉した例外によりProject作成が失敗した。",
            when="ROUTER_HANDLED_EXCEPTIONSを捕捉した場合。",
            check_procedure="traceId/requestIdでログを検索し、"
            "routerで捕捉された例外種別とidempotency keyを確認する。",
            remediation_procedure="原因を特定し、冪等性状態を確認してから"
            "同一Idempotency-Keyで再実行する。",
            context_model="traceId, actorPrincipalId, api.statusCode, "
            "error.code, error.message, error.exceptionType",
            operator_action="同一routeの5xx率、直近deploy、DB/AWS依存の状態を確認する。",
            runbook="RUNBOOK-unexpected-api-failure",
            context=router_log_context(
                status_code=status_code_for_router_error(error),
                detail=str(error),
                caller=caller,
                request_context=request_context,
                error=error,
            ),
        )
        return error_response_for_router_error(error)
