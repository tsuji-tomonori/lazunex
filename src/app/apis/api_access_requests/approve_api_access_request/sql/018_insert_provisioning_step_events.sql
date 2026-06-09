-- 利用申請承認の処理結果として、provisioning step eventsを追加する。
INSERT INTO provisioning_step_events (
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
    @operation_step_id,
    COALESCE((
        SELECT next_event_seq
        FROM (
            SELECT MAX(event_seq) + 1 AS next_event_seq
            FROM provisioning_step_events
            WHERE aggregate_id = @operation_step_id
        ) AS event_seq_source
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
