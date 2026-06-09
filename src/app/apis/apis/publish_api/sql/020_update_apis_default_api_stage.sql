-- API Gateway stage追加後に、API catalogの既定stageを設定する。
UPDATE apis
SET
    default_api_stage_id = @api_stage_id,
    updated_at = @now,
    updated_by = @actor_principal_id,
    row_version = row_version + 1
WHERE api_id = @api_id;
