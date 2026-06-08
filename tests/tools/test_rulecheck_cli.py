from __future__ import annotations

from pathlib import Path

from tools.rulecheck.cli import main


def test_rulecheck_cli_generate_verify_and_check(tmp_path: Path) -> None:
    rules_dir = tmp_path / "docs/rule/coding"
    rules_dir.mkdir(parents=True)
    (tmp_path / "README.md").write_text("# Sample\n", encoding="utf-8")
    rule_path = rules_dir / "00_sample.md"
    checklist_path = rules_dir / "12_review_checklist.generated.md"
    config_path = tmp_path / "config.json"

    rule_path.write_text(
        "# Sample\n\n"
        "## 実装すべき内容\n\n"
        "- `README.md` を配置する。\n\n"
        "## 機械チェック項目\n\n"
        "| Rule ID | Level | Checker | 対象 | 判定条件 |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| SAMPLE-DO-001 | MUST | `required_paths` | `README.md` | ファイルを配置する。 |\n",
        encoding="utf-8",
    )
    config_path.write_text('{"ambiguous_words": []}\n', encoding="utf-8")

    assert (
        main(
            [
                "generate",
                "--rules-dir",
                str(rules_dir),
                "--checklist",
                str(checklist_path),
            ]
        )
        == 0
    )
    assert "SAMPLE-DO-001" in checklist_path.read_text(encoding="utf-8")

    common_args = [
        "--repo-root",
        str(tmp_path),
        "--rules-dir",
        str(rules_dir),
        "--config",
        str(config_path),
    ]
    assert main(["verify", *common_args, "--checklist", str(checklist_path)]) == 0
    assert main(["check", *common_args, "--must-only"]) == 0
