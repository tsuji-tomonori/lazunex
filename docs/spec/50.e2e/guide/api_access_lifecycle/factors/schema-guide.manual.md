# factors YAML schema guide

## 対象ファイル

- `factors/F*_*.manual.yaml`
- `factors/*.factor.manual.yaml`
- `factors/effective_factors.manual.yaml`

## 役割

旧 factor ベース smoke ケースの要因表を定義する。component coverage の主入力ではないが、`generate_e2e_case_list` と旧 scenario 表示で使う。

## API result factor schema

```yaml
schema_version: 1

factor:
  id: F020
  slug: create_project_result
  title: "POST /projects Project作成結果"
  category: api_result
  order: 20
  owner_step: post_projects
  generated_from:
    - type: e2e_flow
      path: docs/spec/50.e2e/api_access_lifecycle/flow.manual.yaml

elements:
  - id: success
    label: "成功: project + API key + clients"
    default: true
    terminal: false
    expected:
      summary: "HTTP 201、projectId/API key/Cognito clientsを返却する。"

constraints:
  requires:
    - F010.success

pruning:
  after_terminal: true
  equivalent_if_same_terminal_step: true
```

## Factor family schema

```yaml
schema_version: 1

factor:
  id: project
  title: Project操作
  dimensions:
    target:
      source: targets/projects/*.target.manual.yaml
    operation:
      source: operations/project/*.operation.manual.yaml
    result:
      source: results/common/*.result.manual.yaml
    data:
      source: data/project/*.data.manual.yaml
```

## `effective_factors.manual.yaml`

```yaml
schema_version: 1
flow: api_access_lifecycle
factors:
  - id: F020
    slug: create_project_result
    title: "POST /projects Project作成結果"
    owner_step: post_projects
    elements:
      - success
      - duplicate_project_code
```

## 記載内容

- `factor.id` は `F000` 形式、`slug` はファイル名と合わせる。
- `owner_step` は `flow.manual.yaml` または template の step ID と揃える。
- `elements[].default: true` は標準経路、`terminal: true` は後続 step を止める失敗要素。
- `expected.summary` には HTTP status だけでなく、DB/外部反映/secret 非表示など確認観点を書く。
- `constraints.requires` には成立に必要な前提 factor element を書く。
- family 定義では target/operation/result/data の source glob を書く。
