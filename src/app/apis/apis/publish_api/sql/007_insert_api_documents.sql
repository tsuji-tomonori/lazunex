INSERT INTO api_documents (
    api_document_id,
    api_id,
    document_type,
    version_label,
    s3_uri,
    sha256,
    source_filename,
    uploaded_by,
    uploaded_at,
    created_at,
    created_by,
    updated_at,
    updated_by,
    row_version
) VALUES (
    :api_document_id,
    :api_id,
    :document_type,
    :version_label,
    :s3_uri,
    :sha256,
    :source_filename,
    :actor_principal_id,
    :now,
    :now,
    :actor_principal_id,
    :now,
    :actor_principal_id,
    1
)
RETURNING api_document_id;
