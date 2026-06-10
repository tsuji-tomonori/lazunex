from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import yaml

from tools.e2e_models import FLOW_ID, TARGET_CASES
from tools.generate_e2e_scenarios import parse_component_variant


def as_mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else {}


def as_sequence(value: object) -> Sequence[object]:
    return cast(Sequence[object], value) if isinstance(value, list | tuple) else ()


def load_yaml(path: Path) -> Mapping[str, object]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return as_mapping(loaded)


def component_root(root: Path, component_id: str) -> Path:
    return root / FLOW_ID / "components" / component_id


def data_tags(root: Path, component_id: str, data_id: str) -> set[str]:
    content = load_yaml(component_root(root, component_id) / "data.manual.yaml")
    for item in as_sequence(content.get("data_profiles")):
        data = as_mapping(item)
        if data.get("id") == data_id:
            return {tag for tag in as_sequence(data.get("tags")) if isinstance(tag, str)}
    return set()


def evidence_ids(root: Path, component_id: str) -> set[str]:
    content = load_yaml(component_root(root, component_id) / "evidences.manual.yaml")
    return {
        str(evidence.get("id"))
        for item in as_sequence(content.get("evidences"))
        for evidence in [as_mapping(item)]
        if isinstance(evidence.get("id"), str)
    }


def binding_matches(
    binding: Mapping[str, object],
    *,
    action_id: str,
    state_id: str,
    tags: set[str],
) -> bool:
    when = as_mapping(binding.get("when"))
    if when.get("action") not in (None, action_id):
        return False
    if when.get("state") not in (None, state_id):
        return False
    required_tags = {
        tag
        for tag in as_sequence(as_mapping(when.get("data_tags")).get("include"))
        if isinstance(tag, str)
    }
    return required_tags <= tags


def matching_bindings(
    root: Path,
    *,
    component_id: str,
    action_id: str,
    state_id: str,
    tags: set[str],
) -> list[Mapping[str, object]]:
    content = load_yaml(component_root(root, component_id) / "bindings.manual.yaml")
    return [
        binding
        for item in as_sequence(content.get("bindings"))
        for binding in [as_mapping(item)]
        if binding_matches(binding, action_id=action_id, state_id=state_id, tags=tags)
    ]


def check_case_evidences(root: Path = Path("docs/spec/50.e2e")) -> list[str]:
    errors: list[str] = []
    evidence_id_cache: dict[str, set[str]] = {}
    for target_case in TARGET_CASES:
        for variant_id in target_case.selected_variants:
            component_id, action_id, _project_id, _api_id, state_id, data_id = (
                parse_component_variant(variant_id)
            )
            tags = data_tags(root, component_id, data_id)
            bindings = matching_bindings(
                root,
                component_id=component_id,
                action_id=action_id,
                state_id=state_id,
                tags=tags,
            )
            if not bindings:
                errors.append(f"{target_case.case_id}: no evidence binding for {variant_id}")
                continue
            refs = [
                ref
                for binding in bindings
                for evidence_ref in as_sequence(binding.get("evidences"))
                for ref in [as_mapping(evidence_ref).get("ref")]
                if isinstance(ref, str)
            ]
            if not refs:
                errors.append(f"{target_case.case_id}: empty evidence binding for {variant_id}")
                continue
            valid_ids = evidence_id_cache.setdefault(
                component_id,
                evidence_ids(root, component_id),
            )
            for ref in refs:
                if ref not in valid_ids:
                    errors.append(
                        f"{target_case.case_id}: unknown evidence {component_id}.{ref}"
                    )
        scenario_path = root / FLOW_ID / "cases" / target_case.filename
        if scenario_path.exists():
            scenario = scenario_path.read_text(encoding="utf-8")
            marker = "### Component Evidence"
            next_marker = "### Runtime期待"
            if marker not in scenario:
                errors.append(f"{target_case.case_id}: missing Component Evidence section")
            else:
                evidence_section = scenario.split(marker, maxsplit=1)[1]
                if next_marker in evidence_section:
                    evidence_section = evidence_section.split(next_marker, maxsplit=1)[0]
                if "\n| E" not in evidence_section:
                    errors.append(f"{target_case.case_id}: empty Component Evidence section")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    errors = check_case_evidences()
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
