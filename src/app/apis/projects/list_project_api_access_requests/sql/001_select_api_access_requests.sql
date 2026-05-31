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
    a.name AS api_name,
    s.apigw_stage_name,
    rv.access_review_id,
    rv.decision,
    rv.approved_auth_mode,
    rv.reviewer_principal_id,
    rv.review_comment,
    rv.reviewed_at
FROM api_access_requests AS ar
JOIN projects AS p
    ON p.project_id = ar.project_id
JOIN apis AS a
    ON a.api_id = ar.api_id
JOIN api_gateway_stages AS s
    ON s.api_stage_id = ar.api_stage_id
LEFT JOIN api_access_reviews AS rv
    ON rv.access_request_id = ar.access_request_id
LEFT JOIN api_reviewers AS reviewer
    ON reviewer.api_id = ar.api_id
    AND reviewer.reviewer_principal_id = :actor_principal_id
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = :actor_principal_id
WHERE ar.project_id = :project_id
  AND (
      p.owner_principal_id = :actor_principal_id
      OR pm.project_member_id IS NOT NULL
      OR reviewer.api_reviewer_id IS NOT NULL
      OR :is_hub_admin = TRUE
  )
  AND (:decision IS NULL OR rv.decision = :decision)
  AND (:after_requested_at IS NULL OR ar.requested_at < :after_requested_at)
ORDER BY ar.requested_at DESC
LIMIT :limit;
