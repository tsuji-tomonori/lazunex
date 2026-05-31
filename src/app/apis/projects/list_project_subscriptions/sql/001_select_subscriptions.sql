-- Projectが利用可能なAPI一覧を返すため、承認済みsubscriptionを取得する。
SELECT
    sub.subscription_id,
    sub.api_id,
    sub.api_stage_id,
    sub.approved_auth_mode,
    sub.approved_at,
    a.api_code,
    a.name AS api_name,
    s.apigw_stage_name AS stage_name,
    s.invoke_url,
    api_scope.scope_full_name
FROM project_api_subscriptions AS sub
INNER JOIN projects AS p
    ON p.project_id = sub.project_id
INNER JOIN apis AS a
    ON a.api_id = sub.api_id
INNER JOIN api_gateway_stages AS s
    ON s.api_stage_id = sub.api_stage_id
INNER JOIN api_cognito_scopes AS api_scope
    ON api_scope.api_id = sub.api_id
LEFT JOIN project_cognito_client_scopes AS granted_scope
    ON granted_scope.subscription_id = sub.subscription_id
LEFT JOIN project_cognito_clients AS app_client
    ON app_client.project_cognito_client_id = granted_scope.project_cognito_client_id
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = @actor_principal_id
WHERE sub.project_id = @project_id
  AND (
      p.owner_principal_id = @actor_principal_id
      OR pm.project_member_id IS NOT NULL
      OR app_client.app_client_id = @app_client_id
      OR @is_hub_admin = TRUE
  )
  AND (@after_approved_at IS NULL OR sub.approved_at < @after_approved_at)
ORDER BY sub.approved_at DESC, a.api_code ASC
LIMIT @limit;
