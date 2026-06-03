-- Idempotency-Keyに対応する既存レコードを取得する。
SELECT
    idempotency_record_id,
    idempotency_key,
    request_hash,
    operation_id,
    response_payload,
    expires_at,
    created_at
FROM idempotency_records
WHERE idempotency_key = @idempotency_key;
