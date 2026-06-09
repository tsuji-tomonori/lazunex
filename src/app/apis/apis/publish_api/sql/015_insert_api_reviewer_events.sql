-- API公開登録の処理結果として、API reviewerイベントを追加する。
INSERT INTO api_reviewer_events (
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
    @api_reviewer_id,
    COALESCE((
        SELECT next_event_seq
        FROM (
            SELECT MAX(event_seq) + 1 AS next_event_seq
            FROM api_reviewer_events
            WHERE aggregate_id = @api_reviewer_id
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
