-- public clientのURL設定を最新化するため、既存のProject Cognito client URLを削除する。
DELETE FROM project_cognito_client_urls
WHERE project_cognito_client_id = @project_cognito_client_id
  AND url_type = @url_type;
