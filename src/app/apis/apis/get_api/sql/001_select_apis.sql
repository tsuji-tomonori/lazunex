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
    s.deployment_id,
    s.authorizer_id,
    s.api_key_required_observed,
    s.scope_config_observed,
    c.api_scope_id,
    c.scope_name,
    c.scope_full_name,
    c.scope_description,
    d.api_document_id,
    d.document_type,
    d.version_label,
    d.s3_uri,
    d.sha256,
    d.source_filename,
    r.api_reviewer_id,
    r.reviewer_principal_id,
    r.reviewer_role
FROM apis AS a
LEFT JOIN api_gateway_stages AS s
    ON s.api_id = a.api_id
LEFT JOIN api_cognito_scopes AS c
    ON c.api_id = a.api_id
LEFT JOIN api_documents AS d
    ON d.api_id = a.api_id
LEFT JOIN api_reviewers AS r
    ON r.api_id = a.api_id
WHERE a.api_id = @api_id
ORDER BY
    s.created_at ASC,
    d.uploaded_at DESC,
    r.reviewer_role ASC;
