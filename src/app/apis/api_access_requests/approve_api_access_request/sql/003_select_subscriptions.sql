SELECT
    subscription_id,
    project_id,
    api_id,
    api_stage_id,
    approved_auth_mode,
    approved_by,
    approved_at
FROM project_api_subscriptions
WHERE project_id = :project_id
  AND api_stage_id = :api_stage_id
LIMIT 1;
