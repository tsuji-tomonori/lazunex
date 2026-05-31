SELECT
    p.project_id,
    p.project_code,
    p.owner_principal_id
FROM projects AS p
LEFT JOIN project_members AS pm
    ON pm.project_id = p.project_id
    AND pm.member_principal_id = :actor_principal_id
WHERE p.project_id = :project_id
  AND (
      p.owner_principal_id = :actor_principal_id
      OR pm.member_role IN ('OWNER', 'ADMIN')
  );
