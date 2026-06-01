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
