INSERT INTO audit_events (
    audit_event_id,
    actor_principal_id,
    action,
    target_type,
    target_id,
    operation_id,
    source_ip,
    user_agent,
    details,
    created_at
) VALUES (
    @audit_event_id,
    @actor_principal_id,
    'PROJECT_PUBLIC_CLIENT_UPDATED',
    'PROJECT',
    @project_id,
    @operation_id,
    @source_ip,
    @user_agent,
    CAST(@details AS json),
    @now
);
