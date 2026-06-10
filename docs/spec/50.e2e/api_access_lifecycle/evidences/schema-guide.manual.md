# evidences YAML schema guide

## 対象ファイル

- `evidences/project/*.evidence.manual.yaml`
- `evidences/access_request/*.evidence.manual.yaml`
- `evidences/review/*.evidence.manual.yaml`
- `evidences/runtime/*.evidence.manual.yaml`

## 役割

旧 factor scenario 用のエビデンス表示行を定義する。component coverage のエビデンスは `components/<component>/evidences.manual.yaml` に書く。

## Schema

```yaml
schema_version: 1

evidence:
  id: project_search_hit
  title: プロジェクト検索でヒットする

md:
  evidence_row:
    viewpoint: Project作成結果
    timing: Project作成後
    evidence: Project一覧レスポンス
    collection: steps/management_api/list_projects.step.manual.yaml
    ok_condition: ${project.id} が検索結果に表示される。
    save_as: ${case.id}_E_project_search_${project.id}.json
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `evidence.id` | evidence ID。 |
| `evidence.title` | エビデンス名。 |
| `md.evidence_row.viewpoint` | 確認観点。 |
| `md.evidence_row.timing` | 収集タイミング。 |
| `md.evidence_row.evidence` | 残すエビデンスの種類。 |
| `md.evidence_row.collection` | 取得方法または参照 step。 |
| `md.evidence_row.ok_condition` | OK 判定条件。 |
| `md.evidence_row.save_as` | 保存名。 |

## 書くべきこと

- レスポンス、DB 状態、外部反映、Runtime 呼び出し結果など、後からレビュー可能な証跡を書く。
- `ok_condition` は人が判定できる具体条件にする。
- `save_as` には `${case.id}` と対象 ID を含め、ケース間で上書きしない。
- secret 実値を evidence 名や保存名に入れない。
