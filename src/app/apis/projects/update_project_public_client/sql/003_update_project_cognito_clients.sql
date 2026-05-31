-- public client設定の更新内容とversionを反映するため、Project Cognito clientを更新する。
UPDATE project_cognito_clients
SET
    access_token_validity = @access_token_validity,
    access_token_unit = @access_token_unit,
    id_token_validity = @id_token_validity,
    id_token_unit = @id_token_unit,
    refresh_token_validity = @refresh_token_validity,
    refresh_token_unit = @refresh_token_unit,
    refresh_token_rotation_enabled = @refresh_token_rotation_enabled,
    retry_grace_period_seconds = @retry_grace_period_seconds,
    enable_token_revocation = @enable_token_revocation,
    last_synced_at = @now,
    updated_at = @now,
    updated_by = @actor_principal_id,
    row_version = row_version + 1
WHERE project_cognito_client_id = @project_cognito_client_id
  AND row_version = @row_version;
