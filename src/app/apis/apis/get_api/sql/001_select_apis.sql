-- API詳細レスポンスを組み立てるため、API catalog情報を取得する。
SELECT
    a.api_id,
    a.api_code,
    a.name,
    a.description,
    a.provider_name,
    a.provider_contact,
    a.owner_principal_id,
    a.visibility,
    s.api_stage_id,
    s.aws_account_id,
    s.aws_region,
    s.apigw_rest_api_id,
    s.apigw_stage_name,
    s.invoke_url,
    s.custom_domain_url,
    s.api_key_required_observed,
    s.scope_config_observed,
    c.scope_name,
    c.scope_full_name,
    r.reviewer_principal_id,
    r.reviewer_role
FROM apis AS a
INNER JOIN api_gateway_stages AS s
    ON s.api_id = a.api_id
INNER JOIN api_cognito_scopes AS c
    ON c.api_id = a.api_id
INNER JOIN api_reviewers AS r
    ON r.api_id = a.api_id
WHERE a.api_id = @api_id
ORDER BY
    s.created_at ASC,
    r.reviewer_role ASC;
