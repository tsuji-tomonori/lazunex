INSERT INTO project_cognito_client_urls (
    client_url_id,
    project_cognito_client_id,
    url_type,
    url,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @client_url_id,
    @project_cognito_client_id,
    @url_type,
    @url,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
