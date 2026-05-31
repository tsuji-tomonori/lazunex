-- 同一Project/APIの審査中申請を検出するため、利用申請を取得する。
SELECT
    ar.access_request_id,
    ar.project_id,
    ar.api_id,
    ar.api_stage_id,
    ar.requested_auth_mode,
    ar.requested_by,
    ar.requested_at
FROM api_access_requests AS ar
WHERE ar.project_id = @project_id
  AND ar.api_stage_id = @api_stage_id
  AND NOT EXISTS (
      SELECT 1
      FROM api_access_reviews AS rv
      WHERE rv.access_request_id = ar.access_request_id
  )
ORDER BY ar.requested_at DESC
LIMIT 1;
