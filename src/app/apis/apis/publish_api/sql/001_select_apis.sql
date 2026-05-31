-- API codeの重複登録を防ぐため、既存APIを取得する。
SELECT
    api_id,
    api_code,
    name,
    default_api_stage_id
FROM apis
WHERE api_code = @api_code;
