# data YAML schema guide

## 対象ファイル

- `data/project/*.data.manual.yaml`
- `data/access_request/*.data.manual.yaml`
- `data/review/*.data.manual.yaml`

## 役割

旧 factor scenario 用の request data を定義する。component coverage の `components/<component>/data.manual.yaml` とは別物で、旧 `generated/effective_cases.manual.yaml` の `selected_variants` の `@data` から参照される。

## Schema

```yaml
schema_version: 1

data:
  id: create_default
  title: 標準Project作成データ
  request:
    path:
      projectId: ${project.id}.projectId
    body:
      projectCode: ${project.defaults.projectCode}
      name: ${project.defaults.name}
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `data.id` | data ID。`selected_variants` の `@data` に入る。 |
| `data.title` | scenario の request 欄に出す表示名。 |
| `data.request.path` | path parameter。 |
| `data.request.query` | query parameter。 |
| `data.request.body` | request body。 |

## 書くべきこと

- `${case.id}`、`${project.id}`、`${api.id}` などの placeholder を使い、ケース間で衝突しない値にする。
- Project/API target の `defaults` から参照できる値は重複して書かず、`${project.defaults.*}` や `${api.defaults.*}` で参照する。
- secret、API key 実値、client secret 実値、runtime token 実値は書かない。
- component coverage の data 追加が主目的なら、まず `components/<component>/data.manual.yaml` を更新する。
