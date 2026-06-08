from __future__ import annotations

import shlex
import subprocess
import sys
from collections.abc import Iterable

from .specs import ToolSpec


def python_module_args(spec: ToolSpec, *, check: bool = False) -> list[str]:
    parts = shlex.split(spec.command)
    module = ""
    for index, part in enumerate(parts):
        if part == "-m" and index + 1 < len(parts):
            module = parts[index + 1]
            break
    if not module:
        raise ValueError(f"{spec.name}: command must contain '-m <module>'")

    args = [sys.executable, "-m", module]
    if check and spec.check_supported:
        args.append("--check")
    return args


def run_specs(specs: Iterable[ToolSpec], *, check: bool = False) -> int:
    exit_code = 0
    for spec in specs:
        if check and not spec.check_supported:
            print(f"SKIP {spec.name}: --check is not supported")
            continue
        print(f"RUN {spec.name}")
        completed = subprocess.run(  # noqa: S603
            python_module_args(spec, check=check),
            check=False,
        )
        if completed.returncode != 0:
            exit_code = completed.returncode
            break
    return exit_code
