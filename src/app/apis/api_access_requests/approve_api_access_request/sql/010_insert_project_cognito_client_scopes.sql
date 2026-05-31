-- Cognito clientにAPI実行scopeを許可するため、Project Cognito client scopeを追加する。
INSERT INTO project_cognito_client_scopes (
    project_cognito_client_scope_id,
    project_id,
    project_cognito_client_id,
    api_scope_id,
    subscription_id,
    scope_full_name,
    granted_at,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @project_cognito_client_scope_id,
    @project_id,
    @project_cognito_client_id,
    @api_scope_id,
    @subscription_id,
    @scope_full_name,
    @now,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
