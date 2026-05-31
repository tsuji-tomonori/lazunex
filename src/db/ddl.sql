CREATE TABLE hub_users (
    user_id uuid PRIMARY KEY,
    external_subject varchar(256) NOT NULL UNIQUE,
    email varchar(320) NOT NULL,
    display_name varchar(200) NOT NULL,
    department_code varchar(64) NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE hub_users IS 'Hub内の利用者、API提供者、審査者、プロジェクトメンバーを表す。状態はhub_user_eventsから導出する。';
-- COMMENT ON COLUMN hub_users.user_id IS 'Hub内ユーザーID。';
-- COMMENT ON COLUMN hub_users.external_subject IS 'Cognito subまたは社内IdPのsubject。';
-- COMMENT ON COLUMN hub_users.email IS 'メールアドレス。';
-- COMMENT ON COLUMN hub_users.display_name IS '表示名。';
-- COMMENT ON COLUMN hub_users.department_code IS '所属部門コード。';
-- COMMENT ON COLUMN hub_users.created_at IS '作成日時。';
-- COMMENT ON COLUMN hub_users.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN hub_users.updated_at IS '更新日時。';
-- COMMENT ON COLUMN hub_users.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN hub_users.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE apis (
    api_id uuid PRIMARY KEY,
    api_code varchar(100) NOT NULL UNIQUE,
    name varchar(200) NOT NULL, -- noqa: RF04
    description text NOT NULL, -- noqa: RF04
    provider_name varchar(200) NOT NULL,
    provider_contact varchar(320) NOT NULL,
    owner_principal_id varchar(256) NOT NULL,
    visibility varchar(20) NOT NULL,
    default_api_stage_id uuid,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE apis IS 'APIカタログの親情報を表す。公開、停止、廃止などの状態はapi_eventsから導出する。';
-- COMMENT ON COLUMN apis.api_id IS 'Lazunex内API ID。';
-- COMMENT ON COLUMN apis.api_code IS '人が読めるAPIコード。例: billing-api-v1。';
-- COMMENT ON COLUMN apis.name IS 'API表示名。';
-- COMMENT ON COLUMN apis.description IS 'APIの説明。';
-- COMMENT ON COLUMN apis.provider_name IS 'API提供チーム名。';
-- COMMENT ON COLUMN apis.provider_contact IS 'API提供者の問い合わせ先。';
-- COMMENT ON COLUMN apis.owner_principal_id IS 'APIオーナーのprincipal。';
-- COMMENT ON COLUMN apis.visibility IS '公開範囲。INTERNALまたはRESTRICTED。';
-- COMMENT ON COLUMN apis.default_api_stage_id IS '既定のAPI stage ID。';
-- COMMENT ON COLUMN apis.created_at IS '作成日時。';
-- COMMENT ON COLUMN apis.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN apis.updated_at IS '更新日時。';
-- COMMENT ON COLUMN apis.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN apis.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE api_gateway_stages (
    api_stage_id uuid PRIMARY KEY,
    api_id uuid NOT NULL REFERENCES apis (api_id),
    aws_account_id varchar(12) NOT NULL,
    aws_region varchar(32) NOT NULL,
    apigw_rest_api_id varchar(128) NOT NULL,
    apigw_stage_name varchar(128) NOT NULL,
    invoke_url text NOT NULL,
    custom_domain_url text,
    deployment_id varchar(128),
    authorizer_id varchar(128),
    api_key_required_observed boolean NOT NULL,
    scope_config_observed varchar(30) NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (aws_account_id, aws_region, apigw_rest_api_id, apigw_stage_name)
);

-- COMMENT ON TABLE api_gateway_stages IS 'API Gateway REST APIのstage、呼び出しURL、認可設定の観測結果を表す。利用可能状態はapi_stage_eventsから導出する。';
-- COMMENT ON COLUMN api_gateway_stages.api_stage_id IS 'API stage ID。';
-- COMMENT ON COLUMN api_gateway_stages.api_id IS '紐づくAPI ID。';
-- COMMENT ON COLUMN api_gateway_stages.aws_account_id IS 'API Gatewayが存在するAWSアカウントID。';
-- COMMENT ON COLUMN api_gateway_stages.aws_region IS 'API Gatewayが存在するAWSリージョン。例: ap-northeast-1。';
-- COMMENT ON COLUMN api_gateway_stages.apigw_rest_api_id IS 'API Gateway REST API ID。';
-- COMMENT ON COLUMN api_gateway_stages.apigw_stage_name IS 'API Gateway stage名。例: prod。';
-- COMMENT ON COLUMN api_gateway_stages.invoke_url IS 'execute-apiの呼び出しURL。';
-- COMMENT ON COLUMN api_gateway_stages.custom_domain_url IS 'カスタムドメインの呼び出しURL。';
-- COMMENT ON COLUMN api_gateway_stages.deployment_id IS 'API Gateway deployment ID。';
-- COMMENT ON COLUMN api_gateway_stages.authorizer_id IS 'Cognito authorizer ID。';
-- COMMENT ON COLUMN api_gateway_stages.api_key_required_observed IS 'API Gateway methodでAPI key必須が設定されているかの検証結果。';
-- COMMENT ON COLUMN api_gateway_stages.scope_config_observed IS 'Cognito scope設定の検証結果。VERIFIED、NOT_CONFIGURED、UNKNOWN。';
-- COMMENT ON COLUMN api_gateway_stages.created_at IS '作成日時。';
-- COMMENT ON COLUMN api_gateway_stages.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN api_gateway_stages.updated_at IS '更新日時。';
-- COMMENT ON COLUMN api_gateway_stages.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN api_gateway_stages.row_version IS '楽観ロック用の行バージョン。';

ALTER TABLE apis
    ADD CONSTRAINT fk_apis_default_api_stage
    FOREIGN KEY (default_api_stage_id) REFERENCES api_gateway_stages (api_stage_id);

CREATE TABLE api_cognito_scopes (
    api_scope_id uuid PRIMARY KEY,
    api_id uuid NOT NULL UNIQUE REFERENCES apis (api_id),
    cognito_user_pool_id varchar(55) NOT NULL,
    resource_server_identifier varchar(256) NOT NULL,
    scope_name varchar(256) NOT NULL, -- noqa: RF04
    scope_full_name varchar(600) NOT NULL UNIQUE,
    scope_description varchar(256) NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE api_cognito_scopes IS 'APIごとのCognito custom scopeを表す。削除や無効化の状態はapi_scope_eventsから導出する。';
-- COMMENT ON COLUMN api_cognito_scopes.api_scope_id IS 'API scope ID。';
-- COMMENT ON COLUMN api_cognito_scopes.api_id IS '紐づくAPI ID。';
-- COMMENT ON COLUMN api_cognito_scopes.cognito_user_pool_id IS 'Cognito User Pool ID。';
-- COMMENT ON COLUMN api_cognito_scopes.resource_server_identifier IS 'Cognito Resource Server識別子。例: api-hub。';
-- COMMENT ON COLUMN api_cognito_scopes.scope_name IS 'Resource Server内のscope名。例: api:{apiId}:invoke。';
-- COMMENT ON COLUMN api_cognito_scopes.scope_full_name IS 'Resource Server識別子を含むscope名。例: api-hub/api:{apiId}:invoke。';
-- COMMENT ON COLUMN api_cognito_scopes.scope_description IS 'scopeの説明。';
-- COMMENT ON COLUMN api_cognito_scopes.created_at IS '作成日時。';
-- COMMENT ON COLUMN api_cognito_scopes.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN api_cognito_scopes.updated_at IS '更新日時。';
-- COMMENT ON COLUMN api_cognito_scopes.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN api_cognito_scopes.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE api_documents (
    api_document_id uuid PRIMARY KEY,
    api_id uuid NOT NULL REFERENCES apis (api_id),
    document_type varchar(20) NOT NULL,
    version_label varchar(50) NOT NULL,
    s3_uri text NOT NULL,
    sha256 varchar(64) NOT NULL,
    source_filename varchar(255) NOT NULL,
    uploaded_by varchar(256) NOT NULL,
    uploaded_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE api_documents IS 'APIに紐づくOpenAPI YAMLやREADMEなどのドキュメント配置情報を表す。';
-- COMMENT ON COLUMN api_documents.api_document_id IS 'APIドキュメントID。';
-- COMMENT ON COLUMN api_documents.api_id IS '紐づくAPI ID。';
-- COMMENT ON COLUMN api_documents.document_type IS 'ドキュメント種別。OPENAPIまたはREADME。';
-- COMMENT ON COLUMN api_documents.version_label IS 'ドキュメントの版ラベル。';
-- COMMENT ON COLUMN api_documents.s3_uri IS 'ドキュメントを保存したS3 URI。';
-- COMMENT ON COLUMN api_documents.sha256 IS 'ドキュメント内容のSHA-256ハッシュ。';
-- COMMENT ON COLUMN api_documents.source_filename IS 'アップロード元ファイル名。';
-- COMMENT ON COLUMN api_documents.uploaded_by IS 'アップロードしたprincipal。';
-- COMMENT ON COLUMN api_documents.uploaded_at IS 'アップロード日時。';
-- COMMENT ON COLUMN api_documents.created_at IS '作成日時。';
-- COMMENT ON COLUMN api_documents.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN api_documents.updated_at IS '更新日時。';
-- COMMENT ON COLUMN api_documents.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN api_documents.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE api_reviewers (
    api_reviewer_id uuid PRIMARY KEY,
    api_id uuid NOT NULL REFERENCES apis (api_id),
    reviewer_principal_id varchar(256) NOT NULL,
    reviewer_role varchar(20) NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE api_reviewers IS 'APIごとの審査者割当を表す。追加や削除はapi_reviewer_eventsから導出する。';
-- COMMENT ON COLUMN api_reviewers.api_reviewer_id IS 'API審査者割当ID。';
-- COMMENT ON COLUMN api_reviewers.api_id IS '審査対象API ID。';
-- COMMENT ON COLUMN api_reviewers.reviewer_principal_id IS '審査者のprincipal。';
-- COMMENT ON COLUMN api_reviewers.reviewer_role IS '審査者の役割。PRIMARY、BACKUP、ADMIN。';
-- COMMENT ON COLUMN api_reviewers.created_at IS '作成日時。';
-- COMMENT ON COLUMN api_reviewers.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN api_reviewers.updated_at IS '更新日時。';
-- COMMENT ON COLUMN api_reviewers.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN api_reviewers.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE projects (
    project_id uuid PRIMARY KEY,
    project_code varchar(100) NOT NULL UNIQUE,
    name varchar(200) NOT NULL, -- noqa: RF04
    description text NOT NULL, -- noqa: RF04
    owner_principal_id varchar(256) NOT NULL,
    department_code varchar(64) NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE projects IS 'API利用単位となるプロジェクトを表す。状態はproject_eventsから導出する。';
-- COMMENT ON COLUMN projects.project_id IS 'Project ID。';
-- COMMENT ON COLUMN projects.project_code IS '人が読めるProjectコード。例: payment-frontend。';
-- COMMENT ON COLUMN projects.name IS 'プロジェクト名。';
-- COMMENT ON COLUMN projects.description IS 'プロジェクトの説明。';
-- COMMENT ON COLUMN projects.owner_principal_id IS 'プロジェクトオーナーのprincipal。';
-- COMMENT ON COLUMN projects.department_code IS '部門コード。';
-- COMMENT ON COLUMN projects.created_at IS '作成日時。';
-- COMMENT ON COLUMN projects.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN projects.updated_at IS '更新日時。';
-- COMMENT ON COLUMN projects.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN projects.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_members (
    project_member_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    member_principal_id varchar(256) NOT NULL,
    member_role varchar(20) NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (project_id, member_principal_id)
);

-- COMMENT ON TABLE project_members IS 'プロジェクトメンバーとProject内の役割を表す。状態はproject_member_eventsから導出する。';
-- COMMENT ON COLUMN project_members.project_member_id IS 'Project member ID。';
-- COMMENT ON COLUMN project_members.project_id IS '所属Project ID。';
-- COMMENT ON COLUMN project_members.member_principal_id IS 'メンバーのprincipal。';
-- COMMENT ON COLUMN project_members.member_role IS 'Project内の役割。OWNER、ADMIN、VIEWER。';
-- COMMENT ON COLUMN project_members.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_members.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_members.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_members.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_members.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_api_keys (
    project_api_key_id uuid PRIMARY KEY,
    project_id uuid NOT NULL UNIQUE REFERENCES projects (project_id),
    aws_account_id varchar(12) NOT NULL,
    aws_region varchar(32) NOT NULL,
    apigw_api_key_id varchar(128) NOT NULL UNIQUE,
    apigw_api_key_name varchar(255) NOT NULL,
    api_key_value_hash varchar(128) NOT NULL,
    api_key_hash_key_version integer NOT NULL,
    api_key_last4 varchar(8) NOT NULL,
    observed_enabled boolean NOT NULL,
    last_synced_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE project_api_keys IS 'ProjectごとのAPI Gateway API Keyの識別子、ハッシュ、末尾表示情報を表す。平文のAPI key値は保存しない。';
-- COMMENT ON COLUMN project_api_keys.project_api_key_id IS 'Project API Key ID。';
-- COMMENT ON COLUMN project_api_keys.project_id IS '紐づくProject ID。1 Projectにつき1 API key。';
-- COMMENT ON COLUMN project_api_keys.aws_account_id IS 'API keyが存在するAWSアカウントID。';
-- COMMENT ON COLUMN project_api_keys.aws_region IS 'API keyが存在するAWSリージョン。';
-- COMMENT ON COLUMN project_api_keys.apigw_api_key_id IS 'API Gateway API Key ID。';
-- COMMENT ON COLUMN project_api_keys.apigw_api_key_name IS 'API Gateway API Key名。';
-- COMMENT ON COLUMN project_api_keys.api_key_value_hash IS 'API key値のHMAC-SHA256などによるハッシュ。';
-- COMMENT ON COLUMN project_api_keys.api_key_hash_key_version IS 'API key値のハッシュ化に使ったpepperのバージョン。';
-- COMMENT ON COLUMN project_api_keys.api_key_last4 IS 'API key値の末尾表示用文字列。';
-- COMMENT ON COLUMN project_api_keys.observed_enabled IS 'API Gateway上でAPI keyが有効化されているかの観測結果。';
-- COMMENT ON COLUMN project_api_keys.last_synced_at IS 'API Gatewayとの最終同期日時。';
-- COMMENT ON COLUMN project_api_keys.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_api_keys.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_api_keys.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_api_keys.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_api_keys.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_usage_plans (
    project_usage_plan_id uuid PRIMARY KEY,
    project_id uuid NOT NULL UNIQUE REFERENCES projects (project_id),
    aws_account_id varchar(12) NOT NULL,
    aws_region varchar(32) NOT NULL,
    apigw_usage_plan_id varchar(128) NOT NULL UNIQUE,
    usage_plan_name varchar(255) NOT NULL,
    default_rate_limit integer,
    default_burst_limit integer,
    default_quota_limit integer,
    default_quota_period varchar(10),
    last_synced_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE project_usage_plans IS 'ProjectごとのAPI Gateway Usage Plan情報を表す。ライフサイクルはproject_usage_plan_eventsから導出する。';
-- COMMENT ON COLUMN project_usage_plans.project_usage_plan_id IS 'Project Usage Plan ID。';
-- COMMENT ON COLUMN project_usage_plans.project_id IS '紐づくProject ID。1 Projectにつき1 Usage Plan。';
-- COMMENT ON COLUMN project_usage_plans.aws_account_id IS 'Usage Planが存在するAWSアカウントID。';
-- COMMENT ON COLUMN project_usage_plans.aws_region IS 'Usage Planが存在するAWSリージョン。';
-- COMMENT ON COLUMN project_usage_plans.apigw_usage_plan_id IS 'API Gateway Usage Plan ID。';
-- COMMENT ON COLUMN project_usage_plans.usage_plan_name IS 'API Gateway Usage Plan名。';
-- COMMENT ON COLUMN project_usage_plans.default_rate_limit IS '通常時の1秒あたりリクエスト数上限。';
-- COMMENT ON COLUMN project_usage_plans.default_burst_limit IS '短時間の急増を許容するリクエスト数上限。';
-- COMMENT ON COLUMN project_usage_plans.default_quota_limit IS '指定期間内に利用できる総リクエスト数上限。';
-- COMMENT ON COLUMN project_usage_plans.default_quota_period IS '総リクエスト数上限を集計する期間。DAY、WEEK、MONTH。';
-- COMMENT ON COLUMN project_usage_plans.last_synced_at IS 'API Gatewayとの最終同期日時。';
-- COMMENT ON COLUMN project_usage_plans.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_usage_plans.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_usage_plans.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_usage_plans.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_usage_plans.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_usage_plan_keys (
    project_usage_plan_key_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    project_usage_plan_id uuid NOT NULL REFERENCES project_usage_plans (project_usage_plan_id),
    project_api_key_id uuid NOT NULL REFERENCES project_api_keys (project_api_key_id),
    apigw_usage_plan_key_id varchar(128) NOT NULL UNIQUE,
    apigw_usage_plan_id varchar(128) NOT NULL,
    apigw_api_key_id varchar(128) NOT NULL,
    provisioned_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (project_usage_plan_id, project_api_key_id)
);

-- COMMENT ON TABLE project_usage_plan_keys IS 'API Gateway API KeyとUsage Planの紐づけを表す。解除はproject_usage_plan_key_eventsから導出する。';
-- COMMENT ON COLUMN project_usage_plan_keys.project_usage_plan_key_id IS 'Usage Plan Key紐づけID。';
-- COMMENT ON COLUMN project_usage_plan_keys.project_id IS '紐づくProject ID。';
-- COMMENT ON COLUMN project_usage_plan_keys.project_usage_plan_id IS '紐づくProject Usage Plan ID。';
-- COMMENT ON COLUMN project_usage_plan_keys.project_api_key_id IS '紐づくProject API Key ID。';
-- COMMENT ON COLUMN project_usage_plan_keys.apigw_usage_plan_key_id IS 'API Gateway Usage Plan Key ID。';
-- COMMENT ON COLUMN project_usage_plan_keys.apigw_usage_plan_id IS 'API Gateway Usage Plan ID。';
-- COMMENT ON COLUMN project_usage_plan_keys.apigw_api_key_id IS 'API Gateway API Key ID。';
-- COMMENT ON COLUMN project_usage_plan_keys.provisioned_at IS 'AWSへ紐づけを反映した日時。';
-- COMMENT ON COLUMN project_usage_plan_keys.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_usage_plan_keys.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_usage_plan_keys.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_usage_plan_keys.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_usage_plan_keys.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_cognito_clients (
    project_cognito_client_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    client_type varchar(40) NOT NULL,
    cognito_user_pool_id varchar(55) NOT NULL,
    app_client_id varchar(128) NOT NULL UNIQUE,
    app_client_name varchar(128) NOT NULL,
    generate_secret boolean NOT NULL,
    client_secret_value_hash varchar(128),
    client_secret_hash_key_version integer,
    client_secret_last4 varchar(8),
    allowed_oauth_flows json NOT NULL,
    base_allowed_scopes json NOT NULL,
    access_token_validity integer NOT NULL,
    access_token_unit varchar(10) NOT NULL,
    id_token_validity integer,
    id_token_unit varchar(10),
    refresh_token_validity integer,
    refresh_token_unit varchar(10),
    refresh_token_rotation_enabled boolean NOT NULL,
    retry_grace_period_seconds integer,
    enable_token_revocation boolean NOT NULL,
    last_synced_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (project_id, client_type)
);

-- COMMENT ON TABLE project_cognito_clients IS 'Projectごとのpublicまたはconfidential Cognito App Clientを表す。client secret平文は保存しない。';
-- COMMENT ON COLUMN project_cognito_clients.project_cognito_client_id IS 'Project App Client ID。';
-- COMMENT ON COLUMN project_cognito_clients.project_id IS '紐づくProject ID。';
-- COMMENT ON COLUMN project_cognito_clients.client_type IS 'App Client種別。PUBLIC_PKCEまたはCONFIDENTIAL_CLIENT_CREDENTIALS。';
-- COMMENT ON COLUMN project_cognito_clients.cognito_user_pool_id IS 'Cognito User Pool ID。';
-- COMMENT ON COLUMN project_cognito_clients.app_client_id IS 'Cognito App Client ID。';
-- COMMENT ON COLUMN project_cognito_clients.app_client_name IS 'Cognito App Client名。';
-- COMMENT ON COLUMN project_cognito_clients.generate_secret IS 'Cognito App Client作成時にclient secretを生成するかどうか。publicではfalse、confidentialではtrue。';
-- COMMENT ON COLUMN project_cognito_clients.client_secret_value_hash IS 'client secret値のHMAC-SHA256などによるハッシュ。publicではNULL。';
-- COMMENT ON COLUMN project_cognito_clients.client_secret_hash_key_version IS 'client secret値のハッシュ化に使ったpepperのバージョン。publicではNULL。';
-- COMMENT ON COLUMN project_cognito_clients.client_secret_last4 IS 'client secret値の末尾表示用文字列。publicではNULL。';
-- COMMENT ON COLUMN project_cognito_clients.allowed_oauth_flows IS '許可するOAuthフロー。例: code、client_credentials。';
-- COMMENT ON COLUMN project_cognito_clients.base_allowed_scopes IS '初期状態で許可するscope。例: openid、email、profile。';
-- COMMENT ON COLUMN project_cognito_clients.access_token_validity IS 'access tokenの有効期間の値。';
-- COMMENT ON COLUMN project_cognito_clients.access_token_unit IS 'access tokenの有効期間単位。minutes、hours、days。';
-- COMMENT ON COLUMN project_cognito_clients.id_token_validity IS 'id tokenの有効期間の値。public client向け。';
-- COMMENT ON COLUMN project_cognito_clients.id_token_unit IS 'id tokenの有効期間単位。public client向け。';
-- COMMENT ON COLUMN project_cognito_clients.refresh_token_validity IS 'refresh tokenの有効期間の値。public client向け。';
-- COMMENT ON COLUMN project_cognito_clients.refresh_token_unit IS 'refresh tokenの有効期間単位。public client向け。';
-- COMMENT ON COLUMN project_cognito_clients.refresh_token_rotation_enabled IS 'refresh token rotationを有効にするかどうか。';
-- COMMENT ON COLUMN project_cognito_clients.retry_grace_period_seconds IS 'refresh token rotationの再試行猶予秒数。';
-- COMMENT ON COLUMN project_cognito_clients.enable_token_revocation IS 'token revocationを有効にするかどうか。';
-- COMMENT ON COLUMN project_cognito_clients.last_synced_at IS 'Cognitoとの最終同期日時。';
-- COMMENT ON COLUMN project_cognito_clients.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_cognito_clients.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_cognito_clients.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_cognito_clients.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_cognito_clients.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_cognito_client_urls (
    client_url_id uuid PRIMARY KEY,
    project_cognito_client_id uuid NOT NULL REFERENCES project_cognito_clients (project_cognito_client_id),
    url_type varchar(20) NOT NULL,
    url text NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (project_cognito_client_id, url_type, url)
);

-- COMMENT ON TABLE project_cognito_client_urls IS 'Cognito App Clientに設定するcallback URLとlogout URLを表す。URL差分は行更新とproject_cognito_client_eventsで追跡する。';
-- COMMENT ON COLUMN project_cognito_client_urls.client_url_id IS 'App Client URL ID。';
-- COMMENT ON COLUMN project_cognito_client_urls.project_cognito_client_id IS '紐づくProject App Client ID。';
-- COMMENT ON COLUMN project_cognito_client_urls.url_type IS 'URL種別。CALLBACKまたはLOGOUT。';
-- COMMENT ON COLUMN project_cognito_client_urls.url IS 'callback URLまたはlogout URL。';
-- COMMENT ON COLUMN project_cognito_client_urls.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_cognito_client_urls.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_cognito_client_urls.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_cognito_client_urls.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_cognito_client_urls.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE api_access_requests (
    access_request_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    api_id uuid NOT NULL REFERENCES apis (api_id),
    api_stage_id uuid NOT NULL REFERENCES api_gateway_stages (api_stage_id),
    requested_auth_mode varchar(30) NOT NULL,
    requested_reason text NOT NULL,
    requested_by varchar(256) NOT NULL,
    requested_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE api_access_requests IS 'ProjectとAPI stageの組み合わせに対する利用申請を表す。状態はaccess_request_eventsから導出する。';
-- COMMENT ON COLUMN api_access_requests.access_request_id IS '利用申請ID。';
-- COMMENT ON COLUMN api_access_requests.project_id IS '申請元Project ID。';
-- COMMENT ON COLUMN api_access_requests.api_id IS '申請対象API ID。';
-- COMMENT ON COLUMN api_access_requests.api_stage_id IS '申請対象API stage ID。';
-- COMMENT ON COLUMN api_access_requests.requested_auth_mode IS '申請した認証方式。PUBLIC_PKCE、CLIENT_CREDENTIALS、BOTH。';
-- COMMENT ON COLUMN api_access_requests.requested_reason IS '利用申請理由。';
-- COMMENT ON COLUMN api_access_requests.requested_by IS '申請者のprincipal。';
-- COMMENT ON COLUMN api_access_requests.requested_at IS '申請日時。';
-- COMMENT ON COLUMN api_access_requests.created_at IS '作成日時。';
-- COMMENT ON COLUMN api_access_requests.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN api_access_requests.updated_at IS '更新日時。';
-- COMMENT ON COLUMN api_access_requests.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN api_access_requests.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE api_access_reviews (
    access_review_id uuid PRIMARY KEY,
    access_request_id uuid NOT NULL REFERENCES api_access_requests (access_request_id),
    decision varchar(20) NOT NULL,
    approved_auth_mode varchar(30),
    reviewer_principal_id varchar(256) NOT NULL,
    review_comment text,
    reviewed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE api_access_reviews IS '利用申請に対する承認または却下の審査結果を表す事実テーブル。';
-- COMMENT ON COLUMN api_access_reviews.access_review_id IS '審査ID。';
-- COMMENT ON COLUMN api_access_reviews.access_request_id IS '審査対象の利用申請ID。';
-- COMMENT ON COLUMN api_access_reviews.decision IS '審査結果。APPROVEDまたはREJECTED。';
-- COMMENT ON COLUMN api_access_reviews.approved_auth_mode IS '承認された認証方式。却下時はNULL。';
-- COMMENT ON COLUMN api_access_reviews.reviewer_principal_id IS '審査者のprincipal。';
-- COMMENT ON COLUMN api_access_reviews.review_comment IS '審査コメント。';
-- COMMENT ON COLUMN api_access_reviews.reviewed_at IS '審査日時。';
-- COMMENT ON COLUMN api_access_reviews.created_at IS '作成日時。';
-- COMMENT ON COLUMN api_access_reviews.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN api_access_reviews.updated_at IS '更新日時。';
-- COMMENT ON COLUMN api_access_reviews.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN api_access_reviews.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_api_subscriptions (
    subscription_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    api_id uuid NOT NULL REFERENCES apis (api_id),
    api_stage_id uuid NOT NULL REFERENCES api_gateway_stages (api_stage_id),
    access_request_id uuid NOT NULL REFERENCES api_access_requests (access_request_id),
    approved_auth_mode varchar(30) NOT NULL,
    approved_by varchar(256) NOT NULL,
    approved_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (project_id, api_stage_id)
);

-- COMMENT ON TABLE project_api_subscriptions IS '承認済みのProjectとAPI stageの利用権を表す。状態はsubscription_eventsから導出する。';
-- COMMENT ON COLUMN project_api_subscriptions.subscription_id IS '利用権ID。';
-- COMMENT ON COLUMN project_api_subscriptions.project_id IS '利用権を持つProject ID。';
-- COMMENT ON COLUMN project_api_subscriptions.api_id IS '利用可能なAPI ID。';
-- COMMENT ON COLUMN project_api_subscriptions.api_stage_id IS '利用可能なAPI stage ID。';
-- COMMENT ON COLUMN project_api_subscriptions.access_request_id IS '利用権の元になった利用申請ID。';
-- COMMENT ON COLUMN project_api_subscriptions.approved_auth_mode IS '承認された認証方式。PUBLIC_PKCE、CLIENT_CREDENTIALS、BOTH。';
-- COMMENT ON COLUMN project_api_subscriptions.approved_by IS '承認者のprincipal。';
-- COMMENT ON COLUMN project_api_subscriptions.approved_at IS '承認日時。';
-- COMMENT ON COLUMN project_api_subscriptions.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_api_subscriptions.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_api_subscriptions.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_api_subscriptions.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_api_subscriptions.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_usage_plan_api_stages (
    usage_plan_api_stage_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    project_usage_plan_id uuid NOT NULL REFERENCES project_usage_plans (project_usage_plan_id),
    subscription_id uuid NOT NULL REFERENCES project_api_subscriptions (subscription_id),
    api_stage_id uuid NOT NULL REFERENCES api_gateway_stages (api_stage_id),
    apigw_rest_api_id varchar(128) NOT NULL,
    apigw_stage_name varchar(128) NOT NULL,
    provisioned_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE project_usage_plan_api_stages IS '承認時にProject Usage Planへ追加したAPI stageの紐づけを表す。状態はusage_plan_stage_eventsから導出する。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.usage_plan_api_stage_id IS 'Usage Plan stage紐づけID。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.project_id IS '紐づくProject ID。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.project_usage_plan_id IS '紐づくProject Usage Plan ID。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.subscription_id IS '紐づく利用権ID。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.api_stage_id IS '紐づくAPI stage ID。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.apigw_rest_api_id IS 'API Gateway REST API ID。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.apigw_stage_name IS 'API Gateway stage名。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.provisioned_at IS 'API Gatewayへ反映した日時。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_usage_plan_api_stages.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE project_cognito_client_scopes (
    project_cognito_client_scope_id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects (project_id),
    project_cognito_client_id uuid NOT NULL REFERENCES project_cognito_clients (project_cognito_client_id),
    api_scope_id uuid NOT NULL REFERENCES api_cognito_scopes (api_scope_id),
    subscription_id uuid NOT NULL REFERENCES project_api_subscriptions (subscription_id),
    scope_full_name varchar(600) NOT NULL,
    granted_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL,
    UNIQUE (project_cognito_client_id, api_scope_id)
);

-- COMMENT ON TABLE project_cognito_client_scopes IS '承認時にCognito App Clientへ付与したAPI scopeの紐づけを表す。状態はclient_scope_eventsから導出する。';
-- COMMENT ON COLUMN project_cognito_client_scopes.project_cognito_client_scope_id IS 'App Client scope紐づけID。';
-- COMMENT ON COLUMN project_cognito_client_scopes.project_id IS '紐づくProject ID。';
-- COMMENT ON COLUMN project_cognito_client_scopes.project_cognito_client_id IS 'scopeを付与したProject App Client ID。';
-- COMMENT ON COLUMN project_cognito_client_scopes.api_scope_id IS '付与したAPI Scope ID。';
-- COMMENT ON COLUMN project_cognito_client_scopes.subscription_id IS 'scope付与の元になった利用権ID。';
-- COMMENT ON COLUMN project_cognito_client_scopes.scope_full_name IS 'Resource Server識別子を含むscope名。';
-- COMMENT ON COLUMN project_cognito_client_scopes.granted_at IS 'Cognito App Clientへscopeを付与した日時。';
-- COMMENT ON COLUMN project_cognito_client_scopes.created_at IS '作成日時。';
-- COMMENT ON COLUMN project_cognito_client_scopes.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN project_cognito_client_scopes.updated_at IS '更新日時。';
-- COMMENT ON COLUMN project_cognito_client_scopes.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN project_cognito_client_scopes.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE provisioning_operations (
    operation_id uuid PRIMARY KEY,
    idempotency_key varchar(200) NOT NULL UNIQUE,
    operation_type varchar(50) NOT NULL,
    target_type varchar(50) NOT NULL,
    target_id uuid,
    request_payload json NOT NULL,
    result_payload json,
    retry_count integer NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE provisioning_operations IS 'CognitoやAPI GatewayなどAWSリソース反映処理の親operationを表す。同期実行でも記録する。';
-- COMMENT ON COLUMN provisioning_operations.operation_id IS 'AWS反映operation ID。';
-- COMMENT ON COLUMN provisioning_operations.idempotency_key IS '冪等性キー。';
-- COMMENT ON COLUMN provisioning_operations.operation_type IS 'operation種別。PUBLISH_API、CREATE_PROJECT、UPDATE_PUBLIC_CLIENT、APPROVE_ACCESS、REJECT_ACCESS。';
-- COMMENT ON COLUMN provisioning_operations.target_type IS '対象種別。API、PROJECT、ACCESS_REQUEST。';
-- COMMENT ON COLUMN provisioning_operations.target_id IS '対象ID。作成前など未確定の場合はNULL。';
-- COMMENT ON COLUMN provisioning_operations.request_payload IS '入力内容の記録。secret値は含めない。';
-- COMMENT ON COLUMN provisioning_operations.result_payload IS '結果summary。secret値は含めない。';
-- COMMENT ON COLUMN provisioning_operations.retry_count IS '同期再実行を含むリトライ回数。';
-- COMMENT ON COLUMN provisioning_operations.created_at IS '作成日時。';
-- COMMENT ON COLUMN provisioning_operations.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN provisioning_operations.updated_at IS '更新日時。';
-- COMMENT ON COLUMN provisioning_operations.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN provisioning_operations.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE provisioning_steps (
    operation_step_id uuid PRIMARY KEY,
    operation_id uuid NOT NULL REFERENCES provisioning_operations (operation_id),
    step_order integer NOT NULL,
    step_name varchar(100) NOT NULL,
    aws_service varchar(50) NOT NULL,
    aws_action varchar(100) NOT NULL,
    request_payload json,
    response_payload json,
    error_code varchar(100),
    error_message text,
    started_at timestamptz,
    finished_at timestamptz,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE provisioning_steps IS 'AWS反映operation内のAWS API呼び出し単位のstepを表す。状態はprovisioning_step_eventsから導出する。';
-- COMMENT ON COLUMN provisioning_steps.operation_step_id IS 'AWS反映step ID。';
-- COMMENT ON COLUMN provisioning_steps.operation_id IS '親operation ID。';
-- COMMENT ON COLUMN provisioning_steps.step_order IS 'operation内の実行順。';
-- COMMENT ON COLUMN provisioning_steps.step_name IS 'step名。例: CREATE_API_KEY。';
-- COMMENT ON COLUMN provisioning_steps.aws_service IS '呼び出し先AWSサービス。APIGATEWAY、COGNITO_IDP、SECRETS_MANAGER。';
-- COMMENT ON COLUMN provisioning_steps.aws_action IS '呼び出したAWS API名。';
-- COMMENT ON COLUMN provisioning_steps.request_payload IS 'AWS API入力内容。secret値はマスクする。';
-- COMMENT ON COLUMN provisioning_steps.response_payload IS 'AWS API出力内容。secret値はマスクする。';
-- COMMENT ON COLUMN provisioning_steps.error_code IS '失敗時のエラーコード。';
-- COMMENT ON COLUMN provisioning_steps.error_message IS '失敗時のエラーメッセージ。';
-- COMMENT ON COLUMN provisioning_steps.started_at IS 'step開始日時。';
-- COMMENT ON COLUMN provisioning_steps.finished_at IS 'step終了日時。';
-- COMMENT ON COLUMN provisioning_steps.created_at IS '作成日時。';
-- COMMENT ON COLUMN provisioning_steps.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN provisioning_steps.updated_at IS '更新日時。';
-- COMMENT ON COLUMN provisioning_steps.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN provisioning_steps.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE idempotency_records (
    idempotency_record_id uuid PRIMARY KEY,
    idempotency_key varchar(200) NOT NULL UNIQUE,
    request_hash varchar(128) NOT NULL,
    operation_id uuid REFERENCES provisioning_operations (operation_id),
    response_payload json,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL,
    created_by varchar(256) NOT NULL,
    updated_at timestamptz NOT NULL,
    updated_by varchar(256) NOT NULL,
    row_version integer NOT NULL
);

-- COMMENT ON TABLE idempotency_records IS '変更系APIの二重実行を防止するための冪等性記録を表す。';
-- COMMENT ON COLUMN idempotency_records.idempotency_record_id IS '冪等性記録ID。';
-- COMMENT ON COLUMN idempotency_records.idempotency_key IS 'クライアントが指定した冪等性キー。';
-- COMMENT ON COLUMN idempotency_records.request_hash IS 'request bodyのハッシュ。';
-- COMMENT ON COLUMN idempotency_records.operation_id IS '関連するAWS反映operation ID。';
-- COMMENT ON COLUMN idempotency_records.response_payload IS '成功時レスポンスの記録。secret値は初回以降返さない方針に注意する。';
-- COMMENT ON COLUMN idempotency_records.expires_at IS '冪等性記録の有効期限。';
-- COMMENT ON COLUMN idempotency_records.created_at IS '作成日時。';
-- COMMENT ON COLUMN idempotency_records.created_by IS '作成者のprincipal。';
-- COMMENT ON COLUMN idempotency_records.updated_at IS '更新日時。';
-- COMMENT ON COLUMN idempotency_records.updated_by IS '更新者のprincipal。';
-- COMMENT ON COLUMN idempotency_records.row_version IS '楽観ロック用の行バージョン。';

CREATE TABLE audit_events (
    audit_event_id uuid PRIMARY KEY,
    actor_principal_id varchar(256) NOT NULL,
    action varchar(100) NOT NULL, -- noqa: RF04
    target_type varchar(50) NOT NULL,
    target_id uuid NOT NULL,
    operation_id uuid REFERENCES provisioning_operations (operation_id),
    source_ip varchar(64),
    user_agent text,
    details json,
    created_at timestamptz NOT NULL
);

-- COMMENT ON TABLE audit_events IS '誰が、いつ、何に対して、どの操作を行ったかを追跡する監査イベントを表す。append-onlyで扱う。';
-- COMMENT ON COLUMN audit_events.audit_event_id IS '監査イベントID。';
-- COMMENT ON COLUMN audit_events.actor_principal_id IS '操作した主体のprincipal。';
-- COMMENT ON COLUMN audit_events.action IS '操作名。例: API_PUBLISHED、PROJECT_CREATED、ACCESS_APPROVED。';
-- COMMENT ON COLUMN audit_events.target_type IS '操作対象種別。API、PROJECT、ACCESS_REQUEST。';
-- COMMENT ON COLUMN audit_events.target_id IS '操作対象ID。';
-- COMMENT ON COLUMN audit_events.operation_id IS '関連するAWS反映operation ID。';
-- COMMENT ON COLUMN audit_events.source_ip IS '呼び出し元IPアドレス。';
-- COMMENT ON COLUMN audit_events.user_agent IS '呼び出し元User-Agent。';
-- COMMENT ON COLUMN audit_events.details IS '監査用の詳細情報。secret値は含めない。';
-- COMMENT ON COLUMN audit_events.created_at IS '監査イベント発生日時。';

CREATE TABLE hub_user_events (
    event_id uuid PRIMARY KEY,
    aggregate_id uuid NOT NULL,
    event_seq bigint NOT NULL,
    event_name varchar(128) NOT NULL,
    actor_principal_id varchar(256) NOT NULL,
    actor_type varchar(32) NOT NULL,
    occurred_at timestamptz NOT NULL,
    reason text,
    correlation_id varchar(128) NOT NULL,
    idempotency_key varchar(256),
    event_payload json,
    UNIQUE (aggregate_id, event_seq)
);

CREATE TABLE api_events LIKE hub_user_events;
CREATE TABLE api_stage_events LIKE hub_user_events;
CREATE TABLE api_scope_events LIKE hub_user_events;
CREATE TABLE api_reviewer_events LIKE hub_user_events;
CREATE TABLE project_events LIKE hub_user_events;
CREATE TABLE project_member_events LIKE hub_user_events;
CREATE TABLE project_api_key_events LIKE hub_user_events;
CREATE TABLE project_usage_plan_events LIKE hub_user_events;
CREATE TABLE project_usage_plan_key_events LIKE hub_user_events;
CREATE TABLE project_cognito_client_events LIKE hub_user_events;
CREATE TABLE access_request_events LIKE hub_user_events;
CREATE TABLE subscription_events LIKE hub_user_events;
CREATE TABLE usage_plan_stage_events LIKE hub_user_events;
CREATE TABLE client_scope_events LIKE hub_user_events;
CREATE TABLE provisioning_operation_events LIKE hub_user_events;
CREATE TABLE provisioning_step_events LIKE hub_user_events;

-- COMMENT ON TABLE hub_user_events IS 'Hubユーザーの状態遷移と事実を追記するイベントテーブル。';
-- COMMENT ON TABLE api_events IS 'APIの公開、公開失敗、停止、廃止などを追記するイベントテーブル。';
-- COMMENT ON TABLE api_stage_events IS 'API stageの登録、検証、検証失敗などを追記するイベントテーブル。';
-- COMMENT ON TABLE api_scope_events IS 'API scopeの作成、作成失敗、削除などを追記するイベントテーブル。';
-- COMMENT ON TABLE api_reviewer_events IS 'API審査者の割当、削除などを追記するイベントテーブル。';
-- COMMENT ON TABLE project_events IS 'Projectの作成要求、払い出し完了、払い出し失敗などを追記するイベントテーブル。';
-- COMMENT ON TABLE project_member_events IS 'Projectメンバーの追加、役割変更、削除などを追記するイベントテーブル。';
-- COMMENT ON TABLE project_api_key_events IS 'Project API keyの作成、ローテーション、無効化などを追記するイベントテーブル。';
-- COMMENT ON TABLE project_usage_plan_events IS 'Project Usage Planの作成、更新、失敗などを追記するイベントテーブル。';
-- COMMENT ON TABLE project_usage_plan_key_events IS 'Usage Plan Keyの作成、削除などを追記するイベントテーブル。';
-- COMMENT ON TABLE project_cognito_client_events IS 'Project App Clientの作成、更新、更新失敗などを追記するイベントテーブル。';
-- COMMENT ON TABLE access_request_events IS '利用申請の提出、承認処理中、承認、却下、失敗などを追記するイベントテーブル。';
-- COMMENT ON TABLE subscription_events IS '利用権の作成、払い出し完了、払い出し失敗、取消などを追記するイベントテーブル。';
-- COMMENT ON TABLE usage_plan_stage_events IS 'Usage PlanへのAPI stage追加、追加失敗、削除などを追記するイベントテーブル。';
-- COMMENT ON TABLE client_scope_events IS 'App Clientへのscope付与、付与失敗、削除などを追記するイベントテーブル。';
-- COMMENT ON TABLE provisioning_operation_events IS 'AWS反映operationの開始、成功、失敗、再実行などを追記するイベントテーブル。';
-- COMMENT ON TABLE provisioning_step_events IS 'AWS反映stepの開始、成功、失敗、スキップなどを追記するイベントテーブル。';

-- COMMENT ON COLUMN hub_user_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN hub_user_events.aggregate_id IS 'イベント対象集約ID。';
-- COMMENT ON COLUMN hub_user_events.event_seq IS '集約内のイベント連番。';
-- COMMENT ON COLUMN hub_user_events.event_name IS 'イベント名。例: project.created、access_request.approved。';
-- COMMENT ON COLUMN hub_user_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN hub_user_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN hub_user_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN hub_user_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN hub_user_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN hub_user_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN hub_user_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN api_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN api_events.aggregate_id IS 'イベント対象のAPI ID。';
-- COMMENT ON COLUMN api_events.event_seq IS 'APIごとのイベント連番。';
-- COMMENT ON COLUMN api_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN api_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN api_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN api_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN api_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN api_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN api_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN api_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN api_stage_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN api_stage_events.aggregate_id IS 'イベント対象のAPI stage ID。';
-- COMMENT ON COLUMN api_stage_events.event_seq IS 'API stageごとのイベント連番。';
-- COMMENT ON COLUMN api_stage_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN api_stage_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN api_stage_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN api_stage_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN api_stage_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN api_stage_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN api_stage_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN api_stage_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN api_scope_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN api_scope_events.aggregate_id IS 'イベント対象のAPI scope ID。';
-- COMMENT ON COLUMN api_scope_events.event_seq IS 'API scopeごとのイベント連番。';
-- COMMENT ON COLUMN api_scope_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN api_scope_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN api_scope_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN api_scope_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN api_scope_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN api_scope_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN api_scope_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN api_scope_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN api_reviewer_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN api_reviewer_events.aggregate_id IS 'イベント対象のAPI reviewer ID。';
-- COMMENT ON COLUMN api_reviewer_events.event_seq IS 'API reviewerごとのイベント連番。';
-- COMMENT ON COLUMN api_reviewer_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN api_reviewer_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN api_reviewer_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN api_reviewer_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN api_reviewer_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN api_reviewer_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN api_reviewer_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN api_reviewer_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN project_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN project_events.aggregate_id IS 'イベント対象のProject ID。';
-- COMMENT ON COLUMN project_events.event_seq IS 'Projectごとのイベント連番。';
-- COMMENT ON COLUMN project_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN project_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN project_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN project_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN project_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN project_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN project_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN project_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN project_member_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN project_member_events.aggregate_id IS 'イベント対象のProject member ID。';
-- COMMENT ON COLUMN project_member_events.event_seq IS 'Project memberごとのイベント連番。';
-- COMMENT ON COLUMN project_member_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN project_member_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN project_member_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN project_member_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN project_member_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN project_member_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN project_member_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN project_member_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN project_api_key_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN project_api_key_events.aggregate_id IS 'イベント対象のProject API key ID。';
-- COMMENT ON COLUMN project_api_key_events.event_seq IS 'Project API keyごとのイベント連番。';
-- COMMENT ON COLUMN project_api_key_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN project_api_key_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN project_api_key_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN project_api_key_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN project_api_key_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN project_api_key_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN project_api_key_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN project_api_key_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN project_usage_plan_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN project_usage_plan_events.aggregate_id IS 'イベント対象のProject Usage Plan ID。';
-- COMMENT ON COLUMN project_usage_plan_events.event_seq IS 'Project Usage Planごとのイベント連番。';
-- COMMENT ON COLUMN project_usage_plan_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN project_usage_plan_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN project_usage_plan_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN project_usage_plan_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN project_usage_plan_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN project_usage_plan_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN project_usage_plan_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN project_usage_plan_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN project_usage_plan_key_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN project_usage_plan_key_events.aggregate_id IS 'イベント対象のUsage Plan Key ID。';
-- COMMENT ON COLUMN project_usage_plan_key_events.event_seq IS 'Usage Plan Keyごとのイベント連番。';
-- COMMENT ON COLUMN project_usage_plan_key_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN project_usage_plan_key_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN project_usage_plan_key_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN project_usage_plan_key_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN project_usage_plan_key_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN project_usage_plan_key_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN project_usage_plan_key_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN project_usage_plan_key_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN project_cognito_client_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN project_cognito_client_events.aggregate_id IS 'イベント対象のProject App Client ID。';
-- COMMENT ON COLUMN project_cognito_client_events.event_seq IS 'Project App Clientごとのイベント連番。';
-- COMMENT ON COLUMN project_cognito_client_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN project_cognito_client_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN project_cognito_client_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN project_cognito_client_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN project_cognito_client_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN project_cognito_client_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN project_cognito_client_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN project_cognito_client_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN access_request_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN access_request_events.aggregate_id IS 'イベント対象の利用申請ID。';
-- COMMENT ON COLUMN access_request_events.event_seq IS '利用申請ごとのイベント連番。';
-- COMMENT ON COLUMN access_request_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN access_request_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN access_request_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN access_request_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN access_request_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN access_request_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN access_request_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN access_request_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN subscription_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN subscription_events.aggregate_id IS 'イベント対象の利用権ID。';
-- COMMENT ON COLUMN subscription_events.event_seq IS '利用権ごとのイベント連番。';
-- COMMENT ON COLUMN subscription_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN subscription_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN subscription_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN subscription_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN subscription_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN subscription_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN subscription_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN subscription_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN usage_plan_stage_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN usage_plan_stage_events.aggregate_id IS 'イベント対象のUsage Plan stage紐づけID。';
-- COMMENT ON COLUMN usage_plan_stage_events.event_seq IS 'Usage Plan stage紐づけごとのイベント連番。';
-- COMMENT ON COLUMN usage_plan_stage_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN usage_plan_stage_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN usage_plan_stage_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN usage_plan_stage_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN usage_plan_stage_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN usage_plan_stage_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN usage_plan_stage_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN usage_plan_stage_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN client_scope_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN client_scope_events.aggregate_id IS 'イベント対象のApp Client scope紐づけID。';
-- COMMENT ON COLUMN client_scope_events.event_seq IS 'App Client scope紐づけごとのイベント連番。';
-- COMMENT ON COLUMN client_scope_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN client_scope_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN client_scope_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN client_scope_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN client_scope_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN client_scope_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN client_scope_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN client_scope_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN provisioning_operation_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN provisioning_operation_events.aggregate_id IS 'イベント対象のAWS反映operation ID。';
-- COMMENT ON COLUMN provisioning_operation_events.event_seq IS 'AWS反映operationごとのイベント連番。';
-- COMMENT ON COLUMN provisioning_operation_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN provisioning_operation_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN provisioning_operation_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN provisioning_operation_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN provisioning_operation_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN provisioning_operation_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN provisioning_operation_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN provisioning_operation_events.event_payload IS 'イベント固有情報。secret値は含めない。';

-- COMMENT ON COLUMN provisioning_step_events.event_id IS 'イベントID。';
-- COMMENT ON COLUMN provisioning_step_events.aggregate_id IS 'イベント対象のAWS反映step ID。';
-- COMMENT ON COLUMN provisioning_step_events.event_seq IS 'AWS反映stepごとのイベント連番。';
-- COMMENT ON COLUMN provisioning_step_events.event_name IS 'イベント名。';
-- COMMENT ON COLUMN provisioning_step_events.actor_principal_id IS 'イベントを発生させた主体のprincipal。';
-- COMMENT ON COLUMN provisioning_step_events.actor_type IS 'イベント発生主体種別。USER、SYSTEM、CI。';
-- COMMENT ON COLUMN provisioning_step_events.occurred_at IS 'イベント発生日時。';
-- COMMENT ON COLUMN provisioning_step_events.reason IS 'イベントの理由またはコメント。';
-- COMMENT ON COLUMN provisioning_step_events.correlation_id IS 'API requestを横断して追跡する相関ID。';
-- COMMENT ON COLUMN provisioning_step_events.idempotency_key IS '関連する冪等性キー。';
-- COMMENT ON COLUMN provisioning_step_events.event_payload IS 'イベント固有情報。secret値は含めない。';

CREATE INDEX idx_projects_owner_principal_id ON projects (owner_principal_id);
CREATE INDEX idx_project_members_member_principal_id ON project_members (member_principal_id);
CREATE INDEX idx_api_access_requests_project_stage ON api_access_requests (project_id, api_stage_id);
CREATE INDEX idx_api_access_requests_requested_at ON api_access_requests (requested_at);
CREATE INDEX idx_project_api_subscriptions_project ON project_api_subscriptions (project_id);
CREATE INDEX idx_provisioning_operations_target ON provisioning_operations (target_type, target_id);
CREATE INDEX idx_audit_events_target ON audit_events (target_type, target_id);
