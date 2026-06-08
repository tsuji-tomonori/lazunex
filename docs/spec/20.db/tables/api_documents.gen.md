# api_documents

APIに紐づくOpenAPI YAMLやREADMEなどのドキュメント配置情報を表す。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `api_document_id` | `CHAR(36)` | NO | PK | APIドキュメントID。 |
| `api_id` | `CHAR(36)` | NO | FK -> apis(api_id) | 紐づくAPI ID。 |
| `document_type` | `VARCHAR(20)` | NO |  | ドキュメント種別。OPENAPIまたはREADME。 |
| `version_label` | `VARCHAR(50)` | NO |  | ドキュメントの版ラベル。 |
| `s3_uri` | `TEXT` | NO |  | ドキュメントを保存したS3 URI。 |
| `sha256` | `VARCHAR(64)` | NO |  | ドキュメント内容のSHA-256ハッシュ。 |
| `source_filename` | `VARCHAR(255)` | NO |  | アップロード元ファイル名。 |
| `uploaded_by` | `VARCHAR(256)` | NO |  | アップロードしたprincipal。 |
| `uploaded_at` | `DATETIME(6)` | NO |  | アップロード日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
