-- 利用申請の審査担当を管理するため、API reviewerを追加する。
INSERT INTO api_reviewers (
    api_reviewer_id,
    api_id,
    reviewer_principal_id,
    reviewer_role,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @api_reviewer_id,
    @api_id,
    @reviewer_principal_id,
    @reviewer_role,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
