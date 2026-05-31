-- 参照可能なProject一覧を返すため、検索条件に合うProjectを取得する。
SELECT
    p.project_id,
    p.project_code,
    p.name,
    p.description,
    p.owner_principal_id,
    p.department_code,
    COUNT(sub.subscription_id) AS subscription_count
FROM projects AS p
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = @actor_principal_id
LEFT JOIN project_api_subscriptions AS sub
    ON sub.project_id = p.project_id
WHERE (
    p.owner_principal_id = @actor_principal_id
    OR pm.project_member_id IS NOT NULL
    OR @is_hub_admin = TRUE
)
  AND (@after_project_code IS NULL OR p.project_code > @after_project_code)
GROUP BY
    p.project_id,
    p.project_code,
    p.name,
    p.description,
    p.owner_principal_id,
    p.department_code
ORDER BY p.project_code
LIMIT @limit;
