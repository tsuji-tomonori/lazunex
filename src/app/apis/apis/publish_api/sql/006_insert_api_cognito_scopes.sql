INSERT INTO api_cognito_scopes (
    api_scope_id,
    api_id,
    cognito_user_pool_id,
    resource_server_identifier,
    scope_name,
    scope_full_name,
    scope_description,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @api_scope_id,
    @api_id,
    @cognito_user_pool_id,
    @resource_server_identifier,
    @scope_name,
    @scope_full_name,
    @scope_description,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
