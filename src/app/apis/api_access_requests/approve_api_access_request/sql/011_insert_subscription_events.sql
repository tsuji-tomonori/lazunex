-- 利用申請承認の処理結果として、subscriptionイベントを追加する。
INSERT INTO subscription_events (
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
    @subscription_id,
    COALESCE((
        SELECT MAX(event_seq) + 1
        FROM subscription_events
        WHERE aggregate_id = @subscription_id
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
