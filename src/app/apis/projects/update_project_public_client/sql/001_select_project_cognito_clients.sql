SELECT
    c.project_cognito_client_id,
    c.project_id,
    c.client_type,
    c.cognito_user_pool_id,
    c.app_client_id,
    c.app_client_name,
    c.allowed_oauth_flows,
    c.base_allowed_scopes,
    c.access_token_validity,
    c.access_token_unit,
    c.id_token_validity,
    c.id_token_unit,
    c.refresh_token_validity,
    c.refresh_token_unit,
    c.refresh_token_rotation_enabled,
    c.retry_grace_period_seconds,
    c.enable_token_revocation,
    c.row_version
FROM project_cognito_clients AS c
JOIN projects AS p
    ON p.project_id = c.project_id
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = :actor_principal_id
WHERE c.project_id = :project_id
  AND c.client_type = 'PUBLIC_PKCE'
  AND (
      p.owner_principal_id = :actor_principal_id
      OR pm.member_role IN ('OWNER', 'ADMIN')
  );
