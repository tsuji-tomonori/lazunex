from __future__ import annotations

from uuid import UUID

from app.apis.sequence_types import (
    ApiAccessRequestRef,
    ApiAccessReviewRef,
    ApiCatalogMetadataRef,
    ApiReviewerRefs,
    ApiScopeRef,
    ApprovedAccessResourceRefs,
    CallerIdentity,
    CognitoAppClientRef,
    CognitoConfidentialClientRef,
    EventRef,
    IdempotencyRecordRef,
    OpenApiMetadataRef,
    ProjectRef,
    ProjectResourceRefs,
    ProvisioningOperationRef,
    SecretHashRefs,
    SequencePage,
    UsagePlanApiStageRef,
)


def rid(value: int) -> UUID:
    return UUID(int=value)


def test_sequence_types_keep_step_references() -> None:
    caller = CallerIdentity(
        principal_id="user-1",
        groups=("owners",),
        scopes=("lazunex/apis.read",),
    )
    page = SequencePage(items=("item-1", "item-2"), next_token="-".join(("next", "page")))
    idempotency = IdempotencyRecordRef(idempotency_key="key-1", operation_id=rid(1))
    operation = ProvisioningOperationRef(operation_id=rid(2))
    event = EventRef(event_id=rid(3))
    api = ApiCatalogMetadataRef(api_id=rid(4), api_stage_id=rid(5))
    scope = ApiScopeRef(scope_full_name="api:sample:invoke")
    reviewers = ApiReviewerRefs(reviewer_principal_ids=("reviewer-1",))
    openapi = OpenApiMetadataRef(s3_uri="s3://bucket/openapi.yaml", sha256="a" * 64)
    project = ProjectRef(project_id=rid(6))
    resources = ProjectResourceRefs(
        project_id=rid(7),
        api_key_id=rid(8),
        usage_plan_id=rid(9),
        public_client_id=rid(10),
        confidential_client_id=rid(11),
    )
    secrets = SecretHashRefs(
        api_key_last4="key4",
        confidential_client_secret_last4="sec" + "4",
    )
    client = CognitoAppClientRef(
        app_client_id="client-id",
        allowed_scopes=("api:sample:invoke",),
    )
    confidential_client = CognitoConfidentialClientRef(
        app_client_id="confidential-client-id",
        client_secret="client-secret-value",  # noqa: S106
    )
    usage_plan_stage = UsagePlanApiStageRef(usage_plan_api_stage_id=rid(12))
    access_request = ApiAccessRequestRef(
        access_request_id=rid(13),
        project_id=rid(14),
        api_id=rid(15),
        api_stage_id=rid(16),
    )
    review = ApiAccessReviewRef(review_id=rid(17))
    approved = ApprovedAccessResourceRefs(
        review_id=rid(18),
        subscription_id=rid(19),
        usage_plan_api_stage_id=rid(20),
        client_scope_ids=(rid(21),),
    )

    assert caller.principal_id == "user-1"
    assert page.items == ("item-1", "item-2")
    assert idempotency.operation_id == rid(1)
    assert operation.operation_id == rid(2)
    assert event.event_id == rid(3)
    assert api.api_stage_id == rid(5)
    assert scope.scope_full_name == "api:sample:invoke"
    assert reviewers.reviewer_principal_ids == ("reviewer-1",)
    assert openapi.sha256 == "a" * 64
    assert project.project_id == rid(6)
    assert resources.confidential_client_id == rid(11)
    assert secrets.api_key_last4 == "key4"
    assert client.allowed_scopes == ("api:sample:invoke",)
    assert confidential_client.client_secret == "client-secret-value"  # noqa: S105
    assert usage_plan_stage.usage_plan_api_stage_id == rid(12)
    assert access_request.access_request_id == rid(13)
    assert review.review_id == rid(17)
    assert approved.client_scope_ids == (rid(21),)
