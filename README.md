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
