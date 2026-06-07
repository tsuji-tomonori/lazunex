from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture

from tools.check_api_router_unit_test_factors import (
    UnitTestCaseExpectation,
    build_arg_parser,
    check_api_router_unit_test_factors,
    expected_function_name,
    main,
    parse_unit_test_cases,
    render_issues,
)


def write_spec(root: Path, body: str) -> Path:
    path = root / "projects" / "create_project" / "unit-test_gen.md"
    path.parent.mkdir(parents=True)
    path.write_text(body, encoding="utf-8")
    return path


def write_router_test(root: Path, body: str) -> Path:
    path = root / "projects" / "create_project" / "test_router.py"
    path.parent.mkdir(parents=True)
    path.write_text(body, encoding="utf-8")
    return path


SPEC = """
### TC001

| 要因 | 要素 | 期待観点 |
| --- | --- | --- |
| `F01` 条件分岐 | 成立 | HTTP 403 error response: caller cannot create project |

### TC002

| 要因 | 要素 | 期待観点 |
| --- | --- | --- |
| `F01` 条件分岐 | 不成立 | 条件不成立側または後続処理を継続する。 |

### TC003

| 要因 | 要素 | 期待観点 |
| --- | --- | --- |
| `F02` 例外処理 | 発生する | router error response |
"""


ROUTER_TEST = """
import pytest


@pytest.mark.anyio
async def test_tc001_create_project_router_matches_unit_test_gen(
    router_db_harness,
    router_auth_headers,
    monkeypatch,
) -> None:
    async def raise_expected_error(*args, **kwargs) -> None:
        raise ApiFunctionError(403, "caller cannot create project")

    monkeypatch.setattr(
        "app.apis.projects.create_project.functions.validate_create_project_request",
        raise_expected_error,
    )
    response = await router_db_harness.client.post(
        "/projects",
        json={"projectName": "project"},
        headers=router_auth_headers("tc001-post"),
    )

    assert response.status_code == 403, response.text
    assert response.json()["error"]["details"][0]["reason"] == "caller cannot create project"


@pytest.mark.anyio
async def test_tc002_create_project_router_matches_unit_test_gen(
    router_db_harness,
    router_auth_headers,
) -> None:
    response = await router_db_harness.client.post(
        "/projects",
        json={"projectName": "project"},
        headers=router_auth_headers("tc002-post"),
    )

    assert response.status_code == 201, response.text


@pytest.mark.anyio
async def test_tc003_create_project_router_matches_unit_test_gen(
    router_db_harness,
    router_auth_headers,
    monkeypatch,
) -> None:
    async def raise_expected_error(*args, **kwargs) -> None:
        raise ApiFunctionError(500, "forced router error")

    monkeypatch.setattr(
        "app.apis.projects.create_project.functions.validate_create_project_request",
        raise_expected_error,
    )
    response = await router_db_harness.client.post(
        "/projects",
        json={"projectName": "project"},
        headers=router_auth_headers("tc003-post"),
    )

    assert response.status_code == 500, response.text
    assert response.json()["error"]["details"][0]["reason"] == "forced router error"
"""


def test_parse_unit_test_cases_extracts_expected_outcomes(tmp_path: Path) -> None:
    spec = write_spec(tmp_path, SPEC)

    assert parse_unit_test_cases(spec, success_status=201) == [
        UnitTestCaseExpectation("TC001", 403, "caller cannot create project"),
        UnitTestCaseExpectation("TC002", 201, None, expected_outcome="success"),
        UnitTestCaseExpectation("TC003", 500, None, router_error=True),
    ]


def test_expected_function_name_uses_tc_prefix() -> None:
    assert (
        expected_function_name("create_project", "TC001")
        == "test_tc001_create_project_router_matches_unit_test_gen"
    )


def test_check_api_router_unit_test_factors_accepts_matching_cases(tmp_path: Path) -> None:
    spec_root = tmp_path / "spec"
    test_root = tmp_path / "tests"
    write_spec(spec_root, SPEC)
    write_router_test(test_root, ROUTER_TEST)

    assert check_api_router_unit_test_factors(spec_root, test_root) == []


def test_check_api_router_unit_test_factors_reports_missing_and_mismatch(tmp_path: Path) -> None:
    spec_root = tmp_path / "spec"
    test_root = tmp_path / "tests"
    write_spec(spec_root, SPEC)
    write_router_test(
        test_root,
        """
import pytest


@pytest.mark.anyio
async def test_tc001_create_project_router_matches_unit_test_gen(router_db_harness) -> None:
    response = await router_db_harness.client.post("/projects")
    assert response.status_code == 200
""",
    )

    issues = check_api_router_unit_test_factors(spec_root, test_root)
    rendered = render_issues(issues)

    assert "TC001 must assert status_code == 403" in rendered
    assert "TC001 must include expected detail 'caller cannot create project'" in rendered
    assert "TC001 must assert expected detail 'caller cannot create project'" in rendered
    assert (
        "TC002 function 'test_tc002_create_project_router_matches_unit_test_gen' is missing"
        in rendered
    )
    assert (
        "TC003 function 'test_tc003_create_project_router_matches_unit_test_gen' is missing"
        in rendered
    )


def test_check_api_router_unit_test_factors_rejects_helper_only_test(tmp_path: Path) -> None:
    spec_root = tmp_path / "spec"
    test_root = tmp_path / "tests"
    write_spec(spec_root, SPEC)
    write_router_test(
        test_root,
        """
import pytest


@pytest.mark.anyio
async def test_tc001_create_project_router_matches_unit_test_gen(router_helper) -> None:
    await router_helper()
    assert True
""",
    )

    rendered = render_issues(check_api_router_unit_test_factors(spec_root, test_root))

    assert "TC001 must call router_db_harness.client API directly" in rendered
    assert "TC001 must assert status_code == 403" in rendered


def test_arg_parser_defaults_and_main(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    args = build_arg_parser().parse_args([])
    assert args.spec_root == Path("docs/spec/40.apis")
    assert args.test_root == Path("tests/app/apis")

    spec_root = tmp_path / "spec"
    test_root = tmp_path / "tests"
    write_spec(spec_root, SPEC)
    write_router_test(test_root, ROUTER_TEST)

    assert main(["--spec-root", str(spec_root), "--test-root", str(test_root)]) == 0
    assert capsys.readouterr().out == ""
