#!/usr/bin/env bash
set -euo pipefail

base_url="${BASE_URL:-http://localhost:8000}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

json_value() {
  python -c 'import json, sys; data=json.load(open(sys.argv[1])); print(data[sys.argv[2]])' "$1" "$2"
}

request_json() {
  local method="$1"
  local path="$2"
  local idempotency_key="$3"
  local body_file="$4"
  local output_file="$5"
  local expected_status="$6"
  local principal_id="${7:-local-admin}"
  local groups="${8:-hub-admin}"
  local status_code

  status_code="$(
    curl -sS \
      -o "$output_file" \
      -w "%{http_code}" \
      -X "$method" \
      "$base_url$path" \
      -H "Content-Type: application/json" \
      -H "X-Principal-Id: $principal_id" \
      -H "X-Groups: $groups" \
      -H "Idempotency-Key: $idempotency_key" \
      --data-binary "@$body_file"
  )"
  if [[ "$status_code" != "$expected_status" ]]; then
    echo "$method $path returned $status_code, expected $expected_status" >&2
    cat "$output_file" >&2
    exit 1
  fi
}

wait_for_health() {
  for _ in {1..60}; do
    if curl -fsS "$base_url/health" >/dev/null; then
      return
    fi
    sleep 2
  done
  echo "health check did not become ready: $base_url/health" >&2
  exit 1
}

docker compose down -v
docker compose up --build -d
wait_for_health

cat >"$tmp_dir/create_project.json" <<'JSON'
{
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
}
JSON

request_json POST /projects local-create-project-001 "$tmp_dir/create_project.json" \
  "$tmp_dir/create_project_response.json" 201
project_id="$(json_value "$tmp_dir/create_project_response.json" projectId)"

cat >"$tmp_dir/publish_api.json" <<'JSON'
{
  "apiCode": "billing-api-v1",
  "name": "Billing API",
  "description": "社内請求API",
  "providerName": "Finance Platform Team",
  "providerContact": "finance-platform@example.com",
  "ownerPrincipalId": "user-12345",
  "visibility": "INTERNAL",
  "apigw": {
    "awsAccountId": "123456789012",
    "awsRegion": "ap-northeast-1",
    "restApiId": "abc123def4",
    "stageName": "prod",
    "invokeUrl": "https://abc123def4.execute-api.ap-northeast-1.amazonaws.com/prod",
    "customDomainUrl": "https://billing-api.internal.example.com",
    "authorizerId": "auth123",
    "scopeAttachmentMode": "PATCH_ALL_METHODS"
  },
  "reviewers": [
    {
      "reviewerPrincipalId": "reviewer-001",
      "reviewerRole": "PRIMARY"
    }
  ],
  "openapiDocument": {
    "s3Uri": "s3://lazunex-openapi/billing-api-v1/openapi.yaml",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  }
}
JSON

request_json POST /apis local-publish-api-001 "$tmp_dir/publish_api.json" \
  "$tmp_dir/publish_api_response.json" 201
api_id="$(json_value "$tmp_dir/publish_api_response.json" apiId)"
api_stage_id="$(json_value "$tmp_dir/publish_api_response.json" apiStageId)"

cat >"$tmp_dir/create_access_request.json" <<JSON
{
  "apiId": "$api_id",
  "apiStageId": "$api_stage_id",
  "requestedAuthMode": "BOTH",
  "requestedReason": "決済画面から請求情報を参照するため"
}
JSON

request_json POST "/projects/$project_id/api-access-requests" local-create-access-request-001 \
  "$tmp_dir/create_access_request.json" "$tmp_dir/create_access_response.json" 201 \
  user-12345 ""
access_request_id="$(json_value "$tmp_dir/create_access_response.json" accessRequestId)"

cat >"$tmp_dir/approve_access_request.json" <<'JSON'
{
  "approvedAuthMode": "BOTH",
  "reviewComment": "利用目的を確認済み"
}
JSON

request_json POST "/api-access-requests/$access_request_id/approve" local-approve-access-request-001 \
  "$tmp_dir/approve_access_request.json" "$tmp_dir/approve_access_response.json" 200 \
  reviewer-001 ""

plain_secret_count="$(
  docker compose exec -T db mysql -uapp_user -papp_password app_db -N -e \
    "SELECT \
       (SELECT COUNT(*) FROM project_api_keys WHERE api_key_value_hash = 'mock-api-key-secret-value') + \
       (SELECT COUNT(*) FROM project_cognito_clients WHERE client_secret_value_hash = 'mock-client-secret-value');"
)"
if [[ "$plain_secret_count" != "0" ]]; then
  echo "plain API key or client secret value was stored in DB" >&2
  exit 1
fi

echo "local smoke passed: project=$project_id api=$api_id accessRequest=$access_request_id"
