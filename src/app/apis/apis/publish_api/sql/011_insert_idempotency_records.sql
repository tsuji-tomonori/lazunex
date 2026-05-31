-- API公開登録の処理結果として、冪等性レコードを追加する。
INSERT INTO idempotency_records (
    idempotency_record_id,
    idempotency_key,
    request_hash,
    operation_id,
    response_payload,
    expires_at,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @idempotency_record_id,
    @idempotency_key,
    @request_hash,
    @operation_id,
    CAST(@response_payload AS json),
    @expires_at,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
