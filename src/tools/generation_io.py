from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


def changed_outputs(rendered: Mapping[Path, str]) -> list[Path]:
    return [
        path
        for path, content in rendered.items()
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]


def write_outputs(rendered: Mapping[Path, str]) -> None:
    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def render_changed(paths: list[Path]) -> str:
    return "\n".join(path.as_posix() for path in paths)


def check_outputs(rendered: Mapping[Path, str]) -> int:
    changed = changed_outputs(rendered)
    if changed:
        print(render_changed(changed))
        return 1
    return 0
