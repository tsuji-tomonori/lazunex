-- 承認結果と承認コメントを保持するため、利用申請レビューを追加する。
INSERT INTO api_access_reviews (
    access_review_id,
    access_request_id,
    decision,
    approved_auth_mode,
    reviewer_principal_id,
    review_comment,
    reviewed_at,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @access_review_id,
    @access_request_id,
    'APPROVED',
    @approved_auth_mode,
    @actor_principal_id,
    @review_comment,
    @now,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
