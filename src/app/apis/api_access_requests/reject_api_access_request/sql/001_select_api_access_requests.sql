-- 却下対象の利用申請と現在状態を確認するため、利用申請を取得する。
SELECT
    ar.access_request_id,
    ar.project_id,
    ar.api_id,
    ar.api_stage_id,
    ar.requested_auth_mode,
    ar.requested_reason,
    ar.requested_by,
    ar.requested_at,
    a.api_code,
    a.name AS api_name
FROM api_access_requests AS ar
INNER JOIN apis AS a
    ON a.api_id = ar.api_id
WHERE ar.access_request_id = @access_request_id
  AND NOT EXISTS (
      SELECT 1
      FROM api_access_reviews AS rv
      WHERE rv.access_request_id = ar.access_request_id
  );
