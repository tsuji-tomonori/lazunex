from __future__ import annotations

from pathlib import Path

from tools.generate_api_pytest_cases import generate, rendered_outputs, unit_test_specs


def write_unit_spec(docs_root: Path) -> None:
    path = docs_root / "projects" / "create_project" / "unit-test_gen.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(
            [
                "# create_project unit test factors",
                "",
                "- Operation: `createProject`",
                "- Endpoint: `POST /projects`",
                "",
                "| Case ID | 処理 | 発生条件 | 期待観点 |",
                "| --- | --- | --- | --- |",
                "| `R001` | Depends | header missing | HTTP 401 |",
                "| `R002` | validation | invalid body | HTTP 422 |",
                "",
                "## 2. 直積したテストケース一覧",
                "",
                "| Case ID | F01 |",
                "| --- | --- |",
                "| `TC001` | `成立` |",
                "",
                "## 3. テスト詳細",
                "",
                "### TC001",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_unit_test_specs_extracts_case_ids(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    write_unit_spec(docs_root)

    specs = unit_test_specs(docs_root)

    assert len(specs) == 1
    assert specs[0].operation_id == "createProject"
    assert specs[0].case_ids == ("R001", "R002", "TC001")


def test_rendered_outputs_generate_collectable_pytest(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    write_unit_spec(docs_root)

    outputs = rendered_outputs(docs_root, tmp_path / "generated")
    content = next(iter(outputs.values()))

    assert "OPERATION_ID = 'createProject'" in content
    assert "    'R001'," in content
    assert "    'TC001'," in content
    assert "@pytest.mark.parametrize" in content


def test_generate_check_detects_changed_output(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    output_root = tmp_path / "generated"
    write_unit_spec(docs_root)

    assert generate(docs_root=docs_root, output_root=output_root, check=True) == 1
    assert generate(docs_root=docs_root, output_root=output_root, check=False) == 0
    assert generate(docs_root=docs_root, output_root=output_root, check=True) == 0
