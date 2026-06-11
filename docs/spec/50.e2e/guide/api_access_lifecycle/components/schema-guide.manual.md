# components YAML schema guide

## 対象ファイル

- `components/<component>/component.manual.yaml`
- `components/<component>/actions.manual.yaml`
- `components/<component>/states.manual.yaml`
- `components/<component>/data.manual.yaml`
- `components/<component>/evidences.manual.yaml`
- `components/<component>/bindings.manual.yaml`

## 役割

component coverage の中心になる定義群。component の責務、操作、状態、入力データ、証明すべきエビデンス、step/evidence binding をまとめる。`src/tools/e2e_models.py` は action/state/data の互換条件から component variant を生成する。

## `component.manual.yaml`

```yaml
schema_version: 1

component:
  id: project_workspace
  title: Project Workspace
  purpose: >
    API利用単位となるProjectを作成する。
  aggregate:
    - Project

business_invariants:
  - id: secret_returned_once
    text: API key値とclient secret値は初回レスポンス以外で再表示しない。

targets:
  primary:
    - project
```

component 自体の責務、関係する aggregate、守るべき業務不変条件、主対象を書く。

## `actions.manual.yaml`

```yaml
schema_version: 1

actions:
  - id: create_project
    title: Projectを作成する
    operation_type: command
    default_result: provisioned
    target: project
    compatible_states:
      - provisioned
      - provision_failed
    requires:
      state:
        project: provisioned
    case_generation:
      as_goal: true
```

| フィールド | 内容 |
|---|---|
| `id` | action ID。variant ID の action 部分になる。 |
| `title` | ケース一覧に出す表示名。 |
| `operation_type` | `command`, `query`, `side_effect`, `evidence` のいずれか。 |
| `default_result` | 代表成功 state。 |
| `target` | `project`、`api`、またはその配列。 |
| `compatible_states` | 組み合わせ可能な state ID。 |
| `requires` | 実行前に必要な状態。レビュー用の明示情報。 |
| `case_generation` | goal case 化の制御。query/evidence では特に明示する。 |

## `states.manual.yaml`

```yaml
schema_version: 1

states:
  - id: provisioned
    title: Project作成成功
    continue_flow: true
    compatible_actions:
      - create_project
    provides:
      variables:
        - ${project.id}.projectId

  - id: provision_failed
    title: Project作成失敗
    continue_flow: false
    compatible_actions:
      - create_project
    target_coverage: canonical_project
```

`continue_flow: true` は後続 component の前提にできる状態、`false` はそこで止まる状態を表す。失敗系で対象差が意味を持たない場合は `target_coverage: canonical_project`、`canonical_api`、`canonical_pair` を使う。

## `data.manual.yaml`

```yaml
schema_version: 1

data_profiles:
  - id: project_default
    title: 標準Project
    coverage_role: canonical_success
    compatible_actions:
      - create_project
    compatible_states:
      - provisioned
      - provision_failed
    target_coverage: all
    tags:
      - valid_project
    request:
      body:
        projectCode: ${project.defaults.projectCode}
```

`compatible_actions`、`compatible_states`、`tags` は variant 生成と evidence binding の条件になる。request には placeholder と sample 由来の値を書き、実 secret は書かない。

## `evidences.manual.yaml`

```yaml
schema_version: 1

evidences:
  - id: project_search_hit
    title: プロジェクト検索でヒットする
    collector:
      step: steps/management_api/list_projects.step.manual.yaml
      bind:
        keyword: ${project.defaults.projectCode}
    ok_condition: ${project.id} が検索結果に表示され、derivedState=ACTIVEである。
    save_as: ${case.id}_E_project_search_${project.id}.json
```

component state を証明するエビデンスを書く。`collector.step` は収集に使う step、`ok_condition` は判定条件、`save_as` は保存名。

## `bindings.manual.yaml`

```yaml
schema_version: 1

bindings:
  - id: create_project_provisioned
    when:
      action: create_project
      state: provisioned
      data_tags:
        include:
          - valid_project
    steps:
      - ref: steps/management_api/create_project.step.manual.yaml
    evidences:
      - ref: project_search_hit
```

`when.action`、`when.state`、`when.data_tags.include` が variant に一致した binding は、scenario の各 Step 内にある「エビデンス」説明に使われる。各 component variant には少なくとも 1 つの evidence binding を用意する。

## 書くべきこと

- action と state の互換条件を双方向で揃える。
- state の `continue_flow` を業務フロー継続可否として明確にする。
- data tag は binding 条件として使うため、意味が分かる名前にする。
- failure state では、後続に進まない理由と確認すべきレスポンスを evidence に書く。
- 新しい action/state/data を追加したら、必ず binding と evidence も追加する。
