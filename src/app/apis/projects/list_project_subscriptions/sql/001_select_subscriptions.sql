SELECT
    sub.subscription_id,
    sub.project_id,
    sub.api_id,
    sub.api_stage_id,
    sub.access_request_id,
    sub.approved_auth_mode,
    sub.approved_by,
    sub.approved_at,
    a.api_code,
    a.name AS api_name,
    a.description AS api_description,
    s.aws_region,
    s.apigw_rest_api_id,
    s.apigw_stage_name,
    s.invoke_url,
    s.custom_domain_url,
    scope.scope_full_name,
    k.apigw_api_key_id,
    k.api_key_last4,
    client.app_client_id,
    client.client_type
FROM project_api_subscriptions AS sub
JOIN projects AS p
    ON p.project_id = sub.project_id
JOIN apis AS a
    ON a.api_id = sub.api_id
JOIN api_gateway_stages AS s
    ON s.api_stage_id = sub.api_stage_id
JOIN api_cognito_scopes AS scope
    ON scope.api_id = sub.api_id
LEFT JOIN project_api_keys AS k
    ON k.project_id = sub.project_id
LEFT JOIN project_cognito_client_scopes AS granted_scope
    ON granted_scope.subscription_id = sub.subscription_id
LEFT JOIN project_cognito_clients AS client
    ON client.project_cognito_client_id = granted_scope.project_cognito_client_id
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = :actor_principal_id
WHERE sub.project_id = :project_id
  AND (
      p.owner_principal_id = :actor_principal_id
      OR pm.project_member_id IS NOT NULL
      OR client.app_client_id = :app_client_id
      OR :is_hub_admin = TRUE
  )
  AND (:after_approved_at IS NULL OR sub.approved_at < :after_approved_at)
ORDER BY sub.approved_at DESC, a.api_code
LIMIT :limit;
