-- Project owner/memberを管理するため、Project memberを追加する。
INSERT INTO project_members (
    project_member_id,
    project_id,
    member_principal_id,
    member_role,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @project_member_id,
    @project_id,
    @member_principal_id,
    @member_role,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
