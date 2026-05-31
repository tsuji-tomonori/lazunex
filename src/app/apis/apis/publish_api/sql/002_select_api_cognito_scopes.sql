-- custom scopeの重複登録を防ぐため、既存API Cognito scopeを取得する。
SELECT
    api_scope_id,
    api_id,
    cognito_user_pool_id,
    resource_server_identifier,
    scope_name,
    scope_full_name
FROM api_cognito_scopes
WHERE scope_full_name = @scope_full_name;
