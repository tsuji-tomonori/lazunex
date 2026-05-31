SELECT
    project_id,
    project_code,
    name,
    owner_principal_id
FROM projects
WHERE project_code = @project_code;
