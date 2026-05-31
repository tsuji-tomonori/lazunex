SELECT
    p.project_id,
    p.project_code,
    p.name,
    p.description,
    p.owner_principal_id,
    p.department_code,
    k.project_api_key_id,
    k.aws_account_id AS api_key_aws_account_id,
    k.aws_region AS api_key_aws_region,
    k.apigw_api_key_id,
    k.apigw_api_key_name,
    k.api_key_last4,
    k.observed_enabled,
    up.project_usage_plan_id,
    up.aws_account_id AS usage_plan_aws_account_id,
    up.aws_region AS usage_plan_aws_region,
    up.apigw_usage_plan_id,
    up.usage_plan_name,
    up.default_rate_limit,
    up.default_burst_limit,
    up.default_quota_limit,
    up.default_quota_period,
    c.project_cognito_client_id,
    c.client_type,
    c.cognito_user_pool_id,
    c.app_client_id,
    c.app_client_name,
    c.generate_secret,
    c.client_secret_last4,
    c.allowed_oauth_flows,
    c.base_allowed_scopes,
    c.access_token_validity,
    c.access_token_unit,
    c.id_token_validity,
    c.id_token_unit,
    c.refresh_token_validity,
    c.refresh_token_unit,
    c.refresh_token_rotation_enabled,
    u.client_url_id,
    u.url_type,
    u.url
FROM projects AS p
LEFT JOIN project_api_keys AS k
    ON k.project_id = p.project_id
LEFT JOIN project_usage_plans AS up
    ON up.project_id = p.project_id
LEFT JOIN project_cognito_clients AS c
    ON c.project_id = p.project_id
LEFT JOIN project_cognito_client_urls AS u
    ON u.project_cognito_client_id = c.project_cognito_client_id
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = :actor_principal_id
WHERE p.project_id = :project_id
  AND (
      p.owner_principal_id = :actor_principal_id
      OR pm.project_member_id IS NOT NULL
      OR :is_hub_admin = TRUE
  )
ORDER BY c.client_type, u.url_type, u.url;
