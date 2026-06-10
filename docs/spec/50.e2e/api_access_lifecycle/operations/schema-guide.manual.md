# operations YAML schema guide

## 対象ファイル

- `operations/project/*.operation.manual.yaml`
- `operations/access_request/*.operation.manual.yaml`
- `operations/review/*.operation.manual.yaml`

## 役割

旧 factor scenario の操作軸を定義する。`generate_e2e_scenarios` は `md.overview_label` や `md.detail_heading` を scenario Markdown の処理概要・詳細見出しに使う。

## Schema

```yaml
schema_version: 1

operation:
  id: create
  factor_id: project
  title: 作成

md:
  overview_label: ${project.id}を作成する
  detail_heading: Project作成APIを呼び出す
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `operation.id` | factor 内の操作 ID。 |
| `operation.factor_id` | 対象 factor family。例: `project`, `access_request`, `review`。 |
| `operation.title` | 操作名。 |
| `md.overview_label` | scenario の処理概要に出す文。 |
| `md.detail_heading` | scenario の詳細見出し。 |

## 書くべきこと

- 操作が command か review かなど、業務上の意味が分かる title にする。
- `overview_label` は `${project.id}`、`${api.id}` などの placeholder を使い、ケースごとの対象が読める文にする。
- API endpoint の詳細は `steps/` と `templates/` に寄せ、ここでは操作の表示情報に絞る。
