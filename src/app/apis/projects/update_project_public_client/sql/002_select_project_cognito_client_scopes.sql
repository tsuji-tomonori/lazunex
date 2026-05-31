SELECT
    pcs.project_cognito_client_scope_id,
    pcs.project_cognito_client_id,
    pcs.api_scope_id,
    pcs.subscription_id,
    pcs.scope_full_name,
    pcs.granted_at
FROM project_cognito_client_scopes AS pcs
WHERE pcs.project_cognito_client_id = :project_cognito_client_id
ORDER BY pcs.scope_full_name;
