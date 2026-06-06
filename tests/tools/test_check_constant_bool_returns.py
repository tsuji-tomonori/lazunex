from __future__ import annotations

from pathlib import Path

from tools.check_constant_bool_returns import check_constant_bool_returns


def test_check_constant_bool_returns_reports_single_literal_value(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    path.write_text(
        """
async def has_duplicate() -> bool:
    if True:
        raise ValueError("duplicate")
    return False

def is_ready() -> bool:
    return True

def has_mixed_result(flag: bool) -> bool:
    if flag:
        return True
    return False

def has_dynamic_result(rows: list[object]) -> bool:
    if rows:
        return bool(rows)
    return False

def get_value() -> str:
    return "False"
""",
        encoding="utf-8",
    )

    issues = check_constant_bool_returns(path)

    assert [(issue.function_name, issue.constant_value) for issue in issues] == [
        ("has_duplicate", False),
        ("is_ready", True),
    ]
