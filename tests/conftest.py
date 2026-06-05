import json
import tempfile
from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import cast

import pytest
from _pytest.terminal import TerminalReporter
from coverage import Coverage
from coverage.exceptions import CoverageException, NoDataError
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.session import create_async_db_engine, create_session_factory, get_session
from app.main import create_app

C0_FAIL_UNDER = 95.0
C1_FAIL_UNDER = 90.0


def _coverage_totals() -> dict[str, int | float]:
    cov = Coverage(data_file=".coverage")
    cov.load()

    with tempfile.NamedTemporaryFile(suffix=".json") as report_file:
        cov.json_report(outfile=report_file.name)
        report_file.seek(0)
        report = json.load(report_file)

    return cast("dict[str, int | float]", report["totals"])


def _percent(covered: int | float, total: int | float) -> float:
    if total == 0:
        return 100.0
    return covered / total * 100


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int | pytest.ExitCode) -> None:
    config = session.config
    no_cov = config.getoption("--no-cov", default=False)
    collect_only = config.getoption("collectonly", default=False)
    if no_cov or collect_only:
        return

    raw_cov_sources = cast(
        "Sequence[str | Path] | None",
        config.getoption("--cov", default=()),
    )
    cov_sources = [Path(source).as_posix() for source in (raw_cov_sources or ())]
    if "src/tools" not in cov_sources:
        terminal = cast(
            "TerminalReporter | None",
            config.pluginmanager.getplugin("terminalreporter"),
        )
        if terminal is not None:
            terminal.write(
                "\nERROR: coverage target must include src/tools.\n",
                red=True,
                bold=True,
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        return

    try:
        totals = _coverage_totals()
    except (CoverageException, NoDataError, OSError, json.JSONDecodeError) as exc:
        terminal = cast(
            "TerminalReporter | None",
            config.pluginmanager.getplugin("terminalreporter"),
        )
        if terminal is not None:
            terminal.write(
                f"\nERROR: failed to read coverage totals for C0/C1 thresholds: {exc}\n",
                red=True,
                bold=True,
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        return

    c0 = _percent(totals["covered_lines"], totals["num_statements"])
    c1 = _percent(totals["covered_branches"], totals["num_branches"])
    failures: list[str] = []
    if c0 < C0_FAIL_UNDER:
        failures.append(f"C0 {c0:.2f}% is less than {C0_FAIL_UNDER:.2f}%")
    if c1 < C1_FAIL_UNDER:
        failures.append(f"C1 {c1:.2f}% is less than {C1_FAIL_UNDER:.2f}%")

    terminal = cast(
        "TerminalReporter | None",
        config.pluginmanager.getplugin("terminalreporter"),
    )
    if terminal is not None:
        terminal.write_sep("=", "coverage thresholds")
        terminal.write(f"C0 statement coverage: {c0:.2f}% / required {C0_FAIL_UNDER:.2f}%\n")
        terminal.write(f"C1 branch coverage: {c1:.2f}% / required {C1_FAIL_UNDER:.2f}%\n")

    if failures:
        if terminal is not None:
            terminal.write("\nERROR: " + "; ".join(failures) + "\n", red=True, bold=True)
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_db_engine("sqlite+aiosqlite:///:memory:")

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = create_session_factory(db_engine)

    async with session_factory() as session:
        yield session


@pytest.fixture
async def db_client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app = create_app()
    session_factory = create_session_factory(db_engine)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
