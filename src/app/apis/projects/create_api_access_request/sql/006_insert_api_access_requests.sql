INSERT INTO api_access_requests (
    access_request_id,
    project_id,
    api_id,
    api_stage_id,
    requested_auth_mode,
    requested_reason,
    requested_by,
    requested_at,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    :access_request_id,
    :project_id,
    :api_id,
    :api_stage_id,
    :requested_auth_mode,
    :requested_reason,
    :actor_principal_id,
    :now,
    :now,
    :actor_principal_id,
    :now,
    :actor_principal_id,
    1
)
RETURNING access_request_id;
