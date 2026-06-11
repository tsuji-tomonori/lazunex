# rules YAML schema guide

## 対象ファイル

- `rules/matrix.manual.yaml`
- `rules/pruning.manual.yaml`
- `rules/renderer.manual.yaml`

## 役割

variant/case 生成、枝刈り、Markdown レンダリングの方針を定義する。生成ツールがすべての項目を直接解釈しているわけではないが、レビュー時の期待仕様として扱い、`check_e2e_specs` が主要項目の存在を確認する。

## `matrix.manual.yaml`

```yaml
schema_version: 1

component_variant_generation:
  dimensions:
    project_workspace:
      project: all
      action: all
      state: all
      data: compatible

component_case_generation:
  default_strategy: component_variant_coverage
  strategies:
    - id: component_variant_coverage
      enabled: true
      strategy: additive
      one_case_per_variant: true

coverage_assertions:
  - id: all_component_variants_are_covered
    type: every_variant_has_case
    components: all
```

展開軸、ケース生成戦略、coverage assertion を書く。

## `pruning.manual.yaml`

```yaml
schema_version: 1

component_pruning:
  - id: stop_when_continue_flow_false
    description: component state の continue_flow が false の場合、依存する後続componentを除外する。

state_rules:
  - id: project_create_failure_stops_lifecycle
    when:
      component: project_workspace
      state: provision_failed
    skip_components:
      - access_request_workflow
```

後続除外、代表 target 化、到達不能前提の除外などを書く。

## `renderer.manual.yaml`

```yaml
schema_version: 1

case_markdown:
  output_dir: cases
  filename: ${case.id}_${case.slug}.gen.md
  sections:
    - id: targets
      title: 対象

evidence_numbering:
  prefix: E
  start: 1
```

case Markdown の section、番号付け、component から Markdown への対応を書く。

## 書くべきこと

- `matrix` には生成対象を増やす/絞る理由を書く。
- `pruning` にはケースを落とす条件と、期待結果が変わらない理由を書く。
- `renderer` には人間がレビューする Markdown の構造だけを書く。
- 実際の生成ロジックを変える必要がある場合は、YAML だけでなく `src/tools/e2e_models.py` や generator も確認する。
