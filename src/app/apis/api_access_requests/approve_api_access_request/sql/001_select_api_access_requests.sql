SELECT
    ar.access_request_id,
    ar.project_id,
    ar.api_id,
    ar.api_stage_id,
    ar.requested_auth_mode,
    ar.requested_reason,
    ar.requested_by,
    ar.requested_at,
    p.project_code,
    p.owner_principal_id,
    a.api_code,
    a.name AS api_name,
    s.apigw_rest_api_id,
    s.apigw_stage_name,
    scope.api_scope_id,
    scope.scope_full_name
FROM api_access_requests AS ar
JOIN projects AS p
    ON p.project_id = ar.project_id
JOIN apis AS a
    ON a.api_id = ar.api_id
JOIN api_gateway_stages AS s
    ON s.api_stage_id = ar.api_stage_id
JOIN api_cognito_scopes AS scope
    ON scope.api_id = ar.api_id
WHERE ar.access_request_id = :access_request_id
  AND NOT EXISTS (
      SELECT 1
      FROM api_access_reviews AS rv
      WHERE rv.access_request_id = ar.access_request_id
  );
