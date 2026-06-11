# bindings YAML schema guide

## 対象ファイル

- `bindings/*.bindings.manual.yaml`

## 役割

旧 factor scenario で、factor の operation/result と evidence を対応づける。component coverage の binding は `components/<component>/bindings.manual.yaml` に書く。

## Schema

```yaml
schema_version: 1

factor_id: project
bindings:
  - id: create_project_success
    when:
      operation: create
      result: success
    evidences:
      - ref: evidences/project/project_search_hit.evidence.manual.yaml
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `factor_id` | 対象 factor family。 |
| `bindings[].id` | binding ID。 |
| `bindings[].when.operation` | operation ID。 |
| `bindings[].when.result` | result ID。 |
| `bindings[].evidences[].ref` | evidence YAML への参照。 |

## 書くべきこと

- operation/result の組み合わせごとに、scenario に出す evidence を並べる。
- `evidences[].ref` は `evidences/**/*.evidence.manual.yaml` の実ファイルに合わせる。
- component coverage の追加では、このフォルダではなく `components/<component>/bindings.manual.yaml` を優先する。
