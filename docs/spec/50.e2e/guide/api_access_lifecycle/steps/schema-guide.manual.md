# steps YAML schema guide

## 対象ファイル

- `steps/management_api/*.step.manual.yaml`
- `steps/runtime_api/*.step.manual.yaml`

## 役割

scenario Markdown に出す実行手順と capture を定義する。`steps/management_api/` は管理 API 呼び出し、`steps/runtime_api/` は Runtime API 呼び出しを表す。

## Schema

```yaml
schema_version: 1

step:
  id: management_create_project
  title: Project作成APIを呼び出す
  phase: exercise
  operation_id: createProject
  endpoint: POST /projects

prerequisites:
  - text: Cognito管理API用tokenを取得できる。

request:
  source: components/project_workspace/data.manual.yaml#project_default.request

expect:
  response:
    status: ${result.expected_status}

capture:
  ${project.id}.projectId: $.projectId
  ${project.id}.projectApiKey: $.apiKey.apiKeyValue

md:
  detail_section:
    description: Project作成結果を確認する。
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `step.id` | step ID。生成ツールの lookup key になる。 |
| `step.title` | 手順名。 |
| `step.phase` | `setup`, `exercise`, `verify` などの段階。 |
| `step.operation_id` | API 実装の operation ID。 |
| `step.endpoint` | `METHOD /path` または Runtime 呼び出し名。 |
| `prerequisites` | step 前提。 |
| `request.source` | request data の出どころ。 |
| `expect` | HTTP status/body や業務状態の期待。 |
| `capture` | 後続 step に渡す値と JSONPath。 |
| `md.detail_section.description` | scenario 詳細の説明。 |

## 書くべきこと

- `operation_id` と endpoint は API 実装・OpenAPI と合わせる。
- `capture` は secret 実値ではなく placeholder 変数として扱う。
- request body の詳細は data または template に寄せ、step には出どころを書く。
- management API と runtime API はフォルダを分ける。
