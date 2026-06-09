# Lazunex

Lazunex is an internal API Hub and API access control service built with FastAPI.

## Local Setup

```bash
uv sync
uv run fastapi dev src/app/main.py
```

## Checks

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pyright
uv run --locked mypy src tests
uv run --locked pytest
```

## Project Tools

既存の個別 generator/checker はそのまま利用できる。通常は Tool Registry を経由する
統一 CLI を入口にする。

```bash
uv run app-codegen all
uv run app-docs generate
uv run app-archlint all
```

tools の使い方、入出力、実行順、テスト仕様は以下を生成して確認する。

```bash
uv run app-docs generate-tools
uv run app-docs generate-tools --check
```

- `docs/spec/tools/usage.gen.md`
- `docs/spec/tools/artifacts.gen.md`
- `docs/spec/tools/execution-flow.gen.md`
- `docs/spec/tools/testcase-spec.gen.md`

## Coding Rule Check

`docs/rule/coding/` contains source-level coding rules and a generated review
checklist. Regenerate and verify them with:

```bash
PYTHONPATH=src/tools python -m rulecheck generate \
  --rules-dir docs/rule/coding \
  --checklist docs/rule/coding/12_review_checklist.generated.md

PYTHONPATH=src/tools python -m rulecheck verify \
  --repo-root . \
  --rules-dir docs/rule/coding \
  --checklist docs/rule/coding/12_review_checklist.generated.md \
  --config config/rulecheck_config.example.json

PYTHONPATH=src/tools python -m rulecheck check \
  --repo-root . \
  --rules-dir docs/rule/coding \
  --config config/rulecheck_config.example.json \
  --must-only
```

## Docker

`compose.yaml` runs `app + db + aws-mock`. The application uses boto3 in all
environments; local compose points only the explicit Lazunex endpoint override
variables at the HTTP mock service:

```text
AWS_APIGATEWAY_ENDPOINT_URL=http://aws-mock:8080
AWS_COGNITO_IDP_ENDPOINT_URL=http://aws-mock:8080
AWS_SECRETS_MANAGER_ENDPOINT_URL=http://aws-mock:8080
```

Local certificates are not required for the default mock. `AWS_CA_BUNDLE_PATH`
is reserved for a future HTTPS mock override. In `ENV_NAME=prod` or
`ENV_NAME=production`, endpoint overrides are rejected at startup.

```bash
docker compose up --build
```

DBを初期状態から作り直す場合は、MySQL volume を削除してから起動します。
`src/db/ddl.sql` は `db` コンテナの初回起動時に投入されます。

```bash
docker compose down -v
docker compose up --build -d
curl -s http://localhost:8000/health
```

主要管理APIをまとめて確認する場合は、ローカル smoke を実行します。外部AWSには接続せず、
`app` からの API Gateway / Cognito / Secrets Manager 呼び出しは `aws-mock:8080`
へ送られます。

```bash
local/smoke/local_smoke.sh
```

ローカルでは Cognito JWT の代わりに、既存の開発用 caller header で呼び出し元を表します。

```http
X-Principal-Id: local-admin
X-Groups: hub-admin
X-Scopes: api-hub/local
Idempotency-Key: local-create-project-001
```

Project作成の最小例です。

```bash
curl -s -X POST http://localhost:8000/projects \
  -H 'Content-Type: application/json' \
  -H 'X-Principal-Id: local-admin' \
  -H 'X-Groups: hub-admin' \
  -H 'Idempotency-Key: local-create-project-001' \
  -d '{
    "projectCode": "payment-frontend",
    "name": "Payment Frontend",
    "description": "決済画面プロジェクト",
    "ownerPrincipalId": "user-12345",
    "departmentCode": "FIN",
    "usagePlan": {
      "defaultRateLimit": 100,
      "defaultBurstLimit": 200,
      "defaultQuotaLimit": 100000,
      "defaultQuotaPeriod": "MONTH"
    },
    "publicClient": {
      "callbackUrls": ["https://payment.example.internal/callback"],
      "logoutUrls": ["https://payment.example.internal/logout"],
      "accessTokenValidity": 15,
      "accessTokenUnit": "minutes",
      "idTokenValidity": 15,
      "idTokenUnit": "minutes",
      "refreshTokenValidity": 1,
      "refreshTokenUnit": "days",
      "refreshTokenRotationEnabled": true,
      "retryGracePeriodSeconds": 10
    },
    "confidentialClient": {
      "accessTokenValidity": 15,
      "accessTokenUnit": "minutes"
    }
  }'
```
