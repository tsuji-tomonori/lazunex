SELECT
    c.project_cognito_client_id,
    c.project_id,
    c.client_type,
    c.cognito_user_pool_id,
    c.app_client_id,
    c.base_allowed_scopes,
    c.allowed_oauth_flows,
    up.project_usage_plan_id,
    up.apigw_usage_plan_id
FROM project_cognito_clients AS c
INNER JOIN project_usage_plans AS up
    ON up.project_id = c.project_id
WHERE c.project_id = @project_id
  AND (
      (@approved_auth_mode = 'PUBLIC_PKCE' AND c.client_type = 'PUBLIC_PKCE')
      OR (@approved_auth_mode = 'CLIENT_CREDENTIALS' AND c.client_type = 'CONFIDENTIAL_CLIENT_CREDENTIALS')
      OR (@approved_auth_mode = 'BOTH')
  )
ORDER BY c.client_type;
