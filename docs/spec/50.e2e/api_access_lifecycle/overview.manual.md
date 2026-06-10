# api_access_lifecycle E2E YAML overview

## 目的

このドキュメントは `docs/spec/50.e2e/api_access_lifecycle/` 配下の E2E 仕様 YAML の全体像を示す。各フォルダの YAML schema と記載方針は、各フォルダの `schema-guide.manual.md` を参照する。

E2E 仕様は JSON Schema ではなく、`src/tools/e2e_models.py`、`src/tools/generate_e2e_case_list.py`、`src/tools/generate_e2e_scenarios.py`、`src/tools/check_e2e_specs.py` が読む YAML shape として管理する。

## ディレクトリ構成

```text
docs/spec/50.e2e/api_access_lifecycle/
|-- flow.manual.yaml
|-- overview.manual.md
|-- case-list_gen.md
|-- case-variant-index_gen.md
|-- pruned-cases_gen.csv
|-- targets/
|   |-- schema-guide.manual.md
|   |-- apis/*.target.manual.yaml
|   `-- projects/*.target.manual.yaml
|-- components/
|   |-- schema-guide.manual.md
|   `-- <component>/
|       |-- component.manual.yaml
|       |-- actions.manual.yaml
|       |-- states.manual.yaml
|       |-- data.manual.yaml
|       |-- evidences.manual.yaml
|       `-- bindings.manual.yaml
|-- factors/
|   |-- schema-guide.manual.md
|   |-- F*_*.manual.yaml
|   |-- *.factor.manual.yaml
|   `-- effective_factors.manual.yaml
|-- operations/
|   |-- schema-guide.manual.md
|   `-- <factor>/*.operation.manual.yaml
|-- results/
|   |-- schema-guide.manual.md
|   `-- <group>/*.result.manual.yaml
|-- data/
|   |-- schema-guide.manual.md
|   `-- <factor>/*.data.manual.yaml
|-- evidences/
|   |-- schema-guide.manual.md
|   `-- <group>/*.evidence.manual.yaml
|-- bindings/
|   |-- schema-guide.manual.md
|   `-- *.bindings.manual.yaml
|-- steps/
|   |-- schema-guide.manual.md
|   `-- <group>/*.step.manual.yaml
|-- templates/
|   |-- schema-guide.manual.md
|   `-- steps/*.manual.yaml
|-- rules/
|   |-- schema-guide.manual.md
|   |-- matrix.manual.yaml
|   |-- pruning.manual.yaml
|   `-- renderer.manual.yaml
|-- generated/
|   |-- schema-guide.manual.md
|   `-- *.manual.yaml
`-- cases/*.gen.md
```

## 役割

| パス | 役割 | 主な利用元 |
|---|---|---|
| `flow.manual.yaml` | E2E フロー全体、API step、依存関係、case policy を定義する。 | `check_e2e_specs` |
| `targets/` | E2E で使う Project/API の論理対象と既定値を定義する。 | `generate_e2e_scenarios` |
| `components/` | component 単位の操作、状態、データ、エビデンス、binding を定義する。 | `e2e_models`, `generate_e2e_case_list`, `generate_e2e_scenarios`, `check_e2e_case_evidences` |
| `factors/` | 旧 factor ベース smoke ケースの要因と要素を定義する。 | `generate_e2e_case_list`, `generate_e2e_scenarios` |
| `operations/` | factor 操作の表示ラベルと見出しを定義する。 | `generate_e2e_scenarios` |
| `results/` | factor 操作結果の共通 result を定義する。 | `generate_e2e_case_list` |
| `data/` | 旧 factor scenario 用の request data を定義する。 | `generate_e2e_scenarios` |
| `evidences/` | 旧 factor scenario 用のエビデンス表示行を定義する。 | `generate_e2e_scenarios` |
| `bindings/` | 旧 factor の operation/result と evidence を対応づける。 | `generate_e2e_scenarios` |
| `steps/` | シナリオに出す手動 step 仕様を定義する。 | `generate_e2e_scenarios`, `check_e2e_specs` |
| `templates/` | API 呼び出し template を定義する。 | `check_e2e_specs` |
| `rules/` | variant/case 生成、枝刈り、Markdown レンダリング方針を定義する。 | `check_e2e_specs`, reviewer |
| `generated/` | 有効化済み factor/case/variant の入力・確認用 YAML を保持する。 | `generate_e2e_scenarios`, reviewer |
| `case-list_gen.md`, `case-variant-index_gen.md`, `cases/*.gen.md`, `pruned-cases_gen.csv` | 生成物。手編集しない。 | reviewer |

## 共通ルール

すべての手動 YAML は先頭に `schema_version: 1` を置く。ID は既存の命名に合わせ、component/action/state/data/evidence は snake_case、Project target は `project_A` 形式、API target は `API_A` 形式を使う。

placeholder は実値ではなく参照値を書く。代表例は `${case.id}`、`${project.id}`、`${api.id}`、`${foreach.api.id}`、`${project.defaults.projectCode}`、`${tokens.project_owner_management_token}`。secret、API key、client secret、runtime access token の実値は YAML、Markdown、ログに書かない。

component variant ID は次の形式で組み立てられる。

```text
<component>.<action>[.<project>][.<api>].<state>@<data>
```

例:

```text
project_workspace.create_project.project_A.provisioned@project_default
runtime_authorization.invoke_runtime_api.project_A.API_A.allowed@approved_runtime_credential
```

## `flow.manual.yaml`

`flow.manual.yaml` は root 直下の単一 YAML で、個別フォルダには属さない。E2E の API step、component 順序、依存関係、case policy を定義する。

```yaml
schema_version: 1
flow:
  id: api_access_lifecycle
  title: API access lifecycle
  description: API公開からRuntime API呼び出しまでの説明

steps:
  - id: S010
    operation_id: createProject
    method: POST
    path: /projects
    template: post_projects
    captures:
      - projectId

component_sequence:
  - api_catalog
  - project_workspace

component_dependencies:
  - id: request_requires_project_and_api
    from:
      component: access_request_workflow
      action: submit_request
    requires:
      - component: project_workspace
        same_project: true
        state: provisioned
```

`steps` には実行順の候補、API の `operation_id`、HTTP method/path、対応する `templates/steps/<template>.manual.yaml`、後続 step に渡す capture 名を書く。新しい API step を追加する場合は、`flow.manual.yaml`、`templates/steps/`、必要に応じて `steps/management_api/` または `steps/runtime_api/` を同時に更新する。

## 変更時の検証

```bash
uv run python -m tools.generate_e2e_case_list
uv run python -m tools.generate_e2e_scenarios
uv run python -m tools.check_e2e_specs
```

ドキュメントだけを変更した場合でも、最低限 `uv run python -m tools.check_e2e_specs` と `git diff --check` を実行する。
