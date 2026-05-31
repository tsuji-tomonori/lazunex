SELECT
    p.project_id,
    p.project_code,
    p.name,
    p.description,
    p.owner_principal_id,
    p.department_code,
    k.project_api_key_id,
    k.apigw_api_key_id,
    k.api_key_last4,
    up.project_usage_plan_id,
    up.apigw_usage_plan_id,
    pub.app_client_id AS public_app_client_id,
    conf.app_client_id AS confidential_app_client_id
FROM projects AS p
LEFT JOIN project_api_keys AS k
    ON k.project_id = p.project_id
LEFT JOIN project_usage_plans AS up
    ON up.project_id = p.project_id
LEFT JOIN project_cognito_clients AS pub
    ON pub.project_id = p.project_id
    AND pub.client_type = 'PUBLIC_PKCE'
LEFT JOIN project_cognito_clients AS conf
    ON conf.project_id = p.project_id
    AND conf.client_type = 'CONFIDENTIAL_CLIENT_CREDENTIALS'
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = @actor_principal_id
WHERE (
    p.owner_principal_id = @actor_principal_id
    OR pm.project_member_id IS NOT NULL
    OR @is_hub_admin = TRUE
)
  AND (@after_project_code IS NULL OR p.project_code > @after_project_code)
ORDER BY p.project_code
LIMIT @limit;
