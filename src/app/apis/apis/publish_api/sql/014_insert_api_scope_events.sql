-- API公開登録の処理結果として、API scopeイベントを追加する。
INSERT INTO api_scope_events (
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
    @api_scope_id,
    COALESCE((
        SELECT MAX(event_seq) + 1
        FROM api_scope_events
        WHERE aggregate_id = @api_scope_id
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
