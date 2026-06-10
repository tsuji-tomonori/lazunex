# results YAML schema guide

## 対象ファイル

- `results/common/*.result.manual.yaml`
- `results/review/*.result.manual.yaml`

## 役割

旧 factor 操作の結果軸を定義する。factor family の `dimensions.result.source` から参照される。

## Schema

```yaml
schema_version: 1

result:
  id: success
  title: 成功
  expected_status: 200
  continue_flow: true
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `result.id` | result ID。 |
| `result.title` | 表示名。 |
| `result.expected_status` | 期待 HTTP status。 |
| `result.continue_flow` | 後続 step を継続できるか。 |

## 書くべきこと

- 正常系は `continue_flow: true`、失敗系や却下で後続を止める場合は `false` を明示する。
- review 固有の成功結果など、common と意味が違う result は `results/review/` に分ける。
- status code だけで業務状態が表せない場合は、factor の `expected.summary` または evidence 側に補足を書く。
