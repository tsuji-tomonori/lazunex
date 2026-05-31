DELETE FROM project_cognito_client_urls
WHERE project_cognito_client_id = :project_cognito_client_id
  AND url_type = :url_type;
