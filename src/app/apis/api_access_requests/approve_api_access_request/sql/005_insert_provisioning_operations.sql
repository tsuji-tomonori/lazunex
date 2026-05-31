INSERT INTO provisioning_operations (
    operation_id,
    idempotency_key,
    operation_type,
    target_type,
    target_id,
    request_payload,
    result_payload,
    retry_count,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    @operation_id,
    @idempotency_key,
    'APPROVE_ACCESS',
    'ACCESS_REQUEST',
    @access_request_id,
    CAST(@request_payload AS json),
    NULL,
    0,
    @now,
    @actor_principal_id,
    @now,
    @actor_principal_id,
    1
);
