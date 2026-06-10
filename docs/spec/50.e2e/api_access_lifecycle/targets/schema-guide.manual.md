# targets YAML schema guide

## 対象ファイル

- `targets/projects/*.target.manual.yaml`
- `targets/apis/*.target.manual.yaml`

## 役割

E2E で使う Project/API の論理対象と既定値を定義する。target ID は component variant ID に入るため、既存ケースや生成物への影響が大きい。既存 target の rename は避け、新しい観点が必要な場合は target 追加として扱う。

## Schema

```yaml
schema_version: 1

target:
  type: project
  id: project_A
  title: Project A
  display_name: project_A
  description: E2Eで利用する標準Project A

md:
  target_section:
    resource_type: Project
    usage: 利用申請元Project
    show_variables:
      - projectId
      - projectApiKey

defaults:
  projectCode: e2e-${case.id}-project-a
  name: E2E Project A
  ownerPrincipalId: ${actors.project_owner_A}
  departmentCode: E2E-A
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `target.type` | `project` または `api`。 |
| `target.id` | target ID。Project は `project_A`、API は `API_A` 形式にする。 |
| `target.title` | ケース一覧やレビューで読む名称。 |
| `target.display_name` | 表示上の短い名前。 |
| `target.description` | 対象の意図。正常系、未登録、権限差などを書く。 |
| `md.target_section.resource_type` | scenario Markdown の対象表に出す種別。 |
| `md.target_section.usage` | この target を何に使うか。 |
| `md.target_section.show_variables` | scenario Markdown に表示する主要変数。 |
| `defaults` | data YAML や request body から参照する既定値。 |

## 書くべきこと

- target ごとの業務上の違いを書く。
- `defaults` には `${case.id}` を含め、ケース間で衝突しない値にする。
- secret、API key 実値、client secret 実値は書かない。
- API target では `apiCode`、`name`、runtime endpoint や stage 参照など、API 公開・Runtime 呼び出しで必要な既定値を書く。
