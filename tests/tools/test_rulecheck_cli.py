from __future__ import annotations

from pathlib import Path

from tools.rulecheck.builtin_checks import (
    branch_count,
    endpoint_business_argument_count,
    function_argument_count,
    local_variable_count,
    try_body_statement_count,
)
from tools.rulecheck.cli import main
from tools.rulecheck.config import load_config
from tools.rulecheck.models import CheckContext, RuleItem


def rule_item(checker: str) -> RuleItem:
    return RuleItem(
        id="TEST-001",
        level="MUST",
        text="test rule",
        source_path=Path("rule.md"),
        line_number=1,
        checkers=(checker,),
    )


def context(tmp_path: Path, config: dict[str, object]) -> CheckContext:
    return CheckContext(
        repo_root=tmp_path,
        rules_dir=tmp_path,
        config=config,
        items=(),
    )


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


def test_metric_exclude_globs_skip_generated_python(tmp_path: Path) -> None:
    generated = tmp_path / "src/app/apis/projects/create_project/generated/queries.py"
    generated.parent.mkdir(parents=True)
    generated.write_text(
        "def generated(a, b, c):\n"
        "    if a:\n"
        "        if b:\n"
        "            return c\n"
        "    return None\n",
        encoding="utf-8",
    )
    config = load_config(None)
    config["metrics"] = {
        "exclude_globs": ["src/app/**/generated/**/*.py"],
        "function_argument_count": [{"glob": "src/app/**/*.py", "max": 1}],
    }

    results = function_argument_count(
        rule_item("function_argument_count"),
        context(tmp_path, config),
    )

    assert results[0].status == "PASS"
    assert "checked 0 functions" in results[0].message


def test_endpoint_business_argument_count_excludes_fastapi_depends(tmp_path: Path) -> None:
    router = tmp_path / "src/app/apis/projects/create_project/router.py"
    router.parent.mkdir(parents=True)
    router.write_text(
        "from typing import Annotated\n"
        "from fastapi import APIRouter, Depends\n"
        "router = APIRouter()\n"
        "@router.post('/projects')\n"
        "async def create_project(request, caller: Annotated[str, Depends(object)], session):\n"
        "    return request\n",
        encoding="utf-8",
    )
    config = load_config(None)
    config["metrics"] = {
        "endpoint_business_argument_count": [
            {
                "glob": "src/app/apis/**/router.py",
                "max": 2,
                "function_kind": "endpoint",
            }
        ],
    }

    results = endpoint_business_argument_count(
        rule_item("endpoint_business_argument_count"),
        context(tmp_path, config),
    )

    assert results[0].status == "PASS"


def test_additional_metric_checkers_report_failures(tmp_path: Path) -> None:
    path = tmp_path / "src/tools/sample.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "def sample(a):\n"
        "    first = 1\n"
        "    second = 2\n"
        "    try:\n"
        "        one = 1\n"
        "        two = 2\n"
        "    except ValueError:\n"
        "        return first\n"
        "    if a:\n"
        "        return second\n"
        "    return None\n",
        encoding="utf-8",
    )
    config = load_config(None)
    config["metrics"] = {
        "try_body_statement_count": [{"glob": "src/tools/**/*.py", "max": 1}],
        "local_variable_count": [{"glob": "src/tools/**/*.py", "max": 2}],
        "branch_count": [{"glob": "src/tools/**/*.py", "max": 1}],
    }
    check_context = context(tmp_path, config)

    try_results = try_body_statement_count(rule_item("try_body_statement_count"), check_context)
    local_results = local_variable_count(rule_item("local_variable_count"), check_context)
    branch_results = branch_count(rule_item("branch_count"), check_context)

    assert try_results[0].status == "FAIL"
    assert local_results[0].status == "FAIL"
    assert branch_results[0].status == "FAIL"
