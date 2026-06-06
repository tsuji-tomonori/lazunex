from __future__ import annotations

from pathlib import Path

from tools.check_api_exception_summaries import check_api_exception_summaries


def write_file(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_check_api_exception_summaries_reports_missing_api_summary(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    integrations_root = tmp_path / "integrations"
    write_file(
        api_root,
        "projects/create_project/functions.py",
        """
def validate_request():
    raise ValueError("invalid")

def save_request():
    raise ApiFunctionError(status.HTTP_400_BAD_REQUEST, "invalid")
""",
    )

    issues = check_api_exception_summaries(api_root, integrations_root)

    assert [issue.message for issue in issues] == [
        "API functions must raise ApiFunctionError with summary",
        "ApiFunctionError must receive a non-empty literal summary keyword",
    ]


def test_check_api_exception_summaries_accepts_summarized_errors(tmp_path: Path) -> None:
    api_root = tmp_path / "apis"
    integrations_root = tmp_path / "integrations"
    write_file(
        api_root,
        "projects/create_project/functions.py",
        """
def validate_request():
    raise ApiFunctionError(
        status.HTTP_400_BAD_REQUEST,
        "invalid",
        summary="入力が不正な場合。",
    )
""",
    )
    write_file(
        api_root,
        "projects/common.py",
        """
def validate_common():
    raise ApiFunctionError(status.HTTP_400_BAD_REQUEST, "invalid", summary="共通入力が不正な場合。")
""",
    )
    write_file(
        integrations_root,
        "common_errors.py",
        """
class ExternalApiError(RuntimeError):
    summary = "外部APIでエラーが発生した場合。"

class ExternalApiUnavailableError(ExternalApiError):
    summary = "外部APIが利用できない場合。"
""",
    )

    assert check_api_exception_summaries(api_root, integrations_root) == []
