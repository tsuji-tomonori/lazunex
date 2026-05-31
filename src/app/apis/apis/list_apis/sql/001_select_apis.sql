SELECT
    a.api_id,
    a.api_code,
    a.name,
    a.description,
    a.provider_name,
    a.provider_contact,
    a.visibility,
    s.api_stage_id,
    s.aws_region,
    s.apigw_rest_api_id,
    s.apigw_stage_name,
    s.invoke_url,
    s.custom_domain_url,
    c.scope_full_name,
    r.reviewer_principal_id
FROM apis AS a
LEFT JOIN api_gateway_stages AS s
    ON s.api_stage_id = a.default_api_stage_id
LEFT JOIN api_cognito_scopes AS c
    ON c.api_id = a.api_id
LEFT JOIN api_reviewers AS r
    ON r.api_id = a.api_id
    AND r.reviewer_role = 'PRIMARY'
WHERE (@visibility IS NULL OR a.visibility = @visibility)
  AND (
      @keyword IS NULL
      OR LOWER(a.name) LIKE LOWER(@keyword)
      OR LOWER(a.api_code) LIKE LOWER(@keyword)
  )
  AND (@after_api_code IS NULL OR a.api_code > @after_api_code)
ORDER BY a.api_code
LIMIT @limit;
