-- 新規Projectの基本情報を保持するため、Projectを追加する。
INSERT INTO projects (
    project_id,
    project_code,
    name,
    description,
    owner_principal_id,
    department_code,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @project_id,
    @project_code,
    @name,
    @description,
    @owner_principal_id,
    @department_code,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
