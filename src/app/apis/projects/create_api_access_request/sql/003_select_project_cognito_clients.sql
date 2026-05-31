SELECT
    project_cognito_client_id,
    project_id,
    client_type,
    cognito_user_pool_id,
    app_client_id,
    base_allowed_scopes
FROM project_cognito_clients
WHERE project_id = @project_id
  AND client_type IN ('PUBLIC_PKCE', 'CONFIDENTIAL_CLIENT_CREDENTIALS')
ORDER BY client_type;
