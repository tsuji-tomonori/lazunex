INSERT INTO client_scope_events (
    event_id,
    aggregate_id,
    event_seq,
    event_name,
    actor_principal_id,
    actor_type,
    occurred_at,
    reason,
    correlation_id,
    idempotency_key,
    event_payload
) VALUES (
    @event_id,
    @project_cognito_client_scope_id,
    COALESCE((
        SELECT MAX(event_seq) + 1
        FROM client_scope_events
        WHERE aggregate_id = @project_cognito_client_scope_id
    ), 1),
    @event_name,
    @actor_principal_id,
    @actor_type,
    @now,
    @reason,
    @correlation_id,
    @idempotency_key,
    CAST(@event_payload AS json)
);
