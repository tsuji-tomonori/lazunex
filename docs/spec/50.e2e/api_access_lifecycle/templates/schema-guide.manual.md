# templates YAML schema guide

## 対象ファイル

- `templates/steps/*.manual.yaml`

## 役割

API 呼び出し template を定義する。`flow.manual.yaml` の `steps[].template` と `template.id` を一致させる。

## Schema

```yaml
schema_version: 1
template:
  id: post_projects
  operation_id: createProject
  method: POST
  path: /projects

request:
  headers:
    Authorization: Bearer ${tokens.project_owner_management_token}
    Idempotency-Key: ${case.case_id}-create-project
    Content-Type: application/json
  body:
    from_sample:
      module: app.apis.projects.create_project.samples
      object: CREATE_PROJECT_REQUEST_SAMPLE

captures:
  projectId: $.projectId
  projectApiKey: $.apiKey.value
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `template.id` | template ID。`flow.manual.yaml` から参照される。 |
| `template.operation_id` | API operation ID。 |
| `template.method` | HTTP method。 |
| `template.path` | API path。 |
| `request.headers` | 共通 header と認証 placeholder。 |
| `request.body.from_sample` | API sample object への参照。 |
| `captures` | response から取り出す値の JSONPath。 |

## 書くべきこと

- header には token 実値を書かず、`${tokens.*}` を使う。
- request body は sample 参照を基本にし、E2E 固有値は data YAML で表す。
- `captures` は `flow.manual.yaml` の `steps[].captures` と揃える。
- Runtime API の URL など環境依存値は `${runtime_invoke_url}` のような placeholder にする。
