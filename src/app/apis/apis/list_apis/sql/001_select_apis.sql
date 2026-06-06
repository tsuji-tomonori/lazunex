-- 参照可能なAPI一覧を返すため、検索条件に合うAPI catalog情報を取得する。
SELECT
    a.api_id,
    a.api_code,
    a.name,
    a.description,
    a.provider_name,
    a.visibility,
    s.api_stage_id,
    s.apigw_stage_name,
    s.invoke_url,
    c.scope_full_name
FROM apis AS a
INNER JOIN api_gateway_stages AS s
    ON s.api_stage_id = a.default_api_stage_id
INNER JOIN api_cognito_scopes AS c
    ON c.api_id = a.api_id
WHERE (@visibility IS NULL OR a.visibility = @visibility)
  AND (
      @keyword IS NULL
      OR LOWER(a.name) LIKE LOWER(@keyword)
      OR LOWER(a.api_code) LIKE LOWER(@keyword)
  )
  AND (@after_api_code IS NULL OR a.api_code > @after_api_code)
ORDER BY a.api_code
LIMIT @limit;
