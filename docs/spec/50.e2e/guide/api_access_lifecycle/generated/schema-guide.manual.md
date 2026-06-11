# generated YAML schema guide

## 対象ファイル

- `generated/effective_factor_matrix.manual.yaml`
- `generated/effective_variants.manual.yaml`
- `generated/effective_step_bindings.manual.yaml`
- `generated/effective_cases.manual.yaml`

## 役割

名前に `generated` を含むが、現在は `.manual.yaml` として repository に保持している入力・確認用 YAML。旧 factor scenario と component target case の選択 variant を確認するために使う。

## `effective_cases.manual.yaml`

```yaml
schema_version: 1
flow: api_access_lifecycle
cases:
  - id: TC001
    slug: happy_approve_and_runtime_success
    kind: happy
    tier: smoke_sandbox
    terminal_step: '-'
    scenario: cases/TC001_happy_approve_and_runtime_success.gen.md
    selected_variants:
      - health_check_result.success@default

target_cases:
  - id: TC_TARGET_001
    title: API_A api_catalog.publish_api published@api_default を主役にする
    coverage_group: component_variant
    goal_component: api_catalog
    goal_variant: api_catalog.publish_api.API_A.published@api_default
    selected_variants:
      - api_catalog.publish_api.API_A.published@api_default
```

## `effective_factor_matrix.manual.yaml`

```yaml
schema_version: 1
flow: api_access_lifecycle
factors:
  publish_api_result:
    variants:
      - id: publish_api_result.success@default
        factor_id: F010
        element: success
        data: default
        steps:
          - post_apis
```

## 記載内容

| フィールド | 内容 |
|---|---|
| `flow` | 対象 flow ID。 |
| `cases[].id` | 旧 smoke case ID。 |
| `cases[].selected_variants` | `<factor_slug>.<element>@<data>` の選択。 |
| `target_cases[].id` | component coverage case ID。 |
| `target_cases[].goal_component` | 主役 component。 |
| `target_cases[].goal_variant` | 主役 component variant ID。 |
| `target_cases[].selected_variants` | 前提 variant と主役 variant。 |
| `runtime_assertions` | Runtime API の allowed/denied 期待。 |

## 書くべきこと

- `selected_variants` は factor variant または component variant ID を正確に書く。
- component coverage の最新 target case は `src/tools/e2e_models.py` の component 定義から組み立てられるため、YAML と生成結果に差がある場合は generator 側を確認する。
- smoke case の tier は `smoke_sandbox`, `sandbox`, `local_fake`, `doc_only` の既存分類に合わせる。
- scenario の実ファイルは `cases/*.gen.md` として生成されるため手編集しない。
