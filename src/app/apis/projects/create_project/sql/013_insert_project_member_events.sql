INSERT INTO project_member_events (
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
    :event_id,
    :project_member_id,
    COALESCE((
        SELECT MAX(event_seq) + 1
        FROM project_member_events
        WHERE aggregate_id = :project_member_id
    ), 1),
    :event_name,
    :actor_principal_id,
    :actor_type,
    :now,
    :reason,
    :correlation_id,
    :idempotency_key,
    CAST(:event_payload AS json)
)
RETURNING event_id;
