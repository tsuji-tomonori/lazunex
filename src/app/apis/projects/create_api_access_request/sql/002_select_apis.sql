SELECT
    a.api_id,
    a.api_code,
    a.name,
    a.visibility,
    s.api_stage_id,
    s.apigw_rest_api_id,
    s.apigw_stage_name,
    c.api_scope_id,
    c.scope_full_name,
    r.reviewer_principal_id
FROM apis AS a
JOIN api_gateway_stages AS s
    ON s.api_stage_id = COALESCE(:api_stage_id, a.default_api_stage_id)
    AND s.api_id = a.api_id
JOIN api_cognito_scopes AS c
    ON c.api_id = a.api_id
LEFT JOIN api_reviewers AS r
    ON r.api_id = a.api_id
    AND r.reviewer_role = 'PRIMARY'
WHERE a.api_id = :api_id;
