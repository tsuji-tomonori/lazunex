-- 承認者が対象APIのreviewerか確認するため、API reviewerを取得する。
SELECT
    api_reviewer_id,
    api_id,
    reviewer_principal_id,
    reviewer_role
FROM api_reviewers
WHERE api_id = @api_id
  AND (
      reviewer_principal_id = @actor_principal_id
      OR @is_hub_admin = TRUE
  )
ORDER BY reviewer_role
LIMIT 1;
