-- 承認処理の開始と完了を追跡するため、利用申請イベントを追加する。
INSERT INTO access_request_events (
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
    @access_request_id,
    COALESCE((
        SELECT next_event_seq
        FROM (
            SELECT MAX(event_seq) + 1 AS next_event_seq
            FROM access_request_events
            WHERE aggregate_id = @access_request_id
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
