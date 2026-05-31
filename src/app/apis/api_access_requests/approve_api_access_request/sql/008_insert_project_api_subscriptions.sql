INSERT INTO project_api_subscriptions (
    subscription_id,
    project_id,
    api_id,
    api_stage_id,
    access_request_id,
    approved_auth_mode,
    approved_by,
    approved_at,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    :subscription_id,
    :project_id,
    :api_id,
    :api_stage_id,
    :access_request_id,
    :approved_auth_mode,
    :actor_principal_id,
    :now,
    :now,
    :actor_principal_id,
    :now,
    :actor_principal_id,
    1
)
RETURNING subscription_id;
