from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from tools.e2e_models import CASES, FACTORS, FLOW_ID, FLOW_STEPS


def check_specs(root: Path = Path("docs/spec/50.e2e")) -> list[str]:
    flow_root = root / FLOW_ID
    errors: list[str] = []
    required_paths = [
        flow_root / "flow.manual.yaml",
        flow_root / "case-list_gen.md",
        flow_root / "pruned-cases_gen.csv",
        flow_root / "factors" / "effective_factors.gen.yaml",
    ]
    required_paths.extend(
        flow_root / "factors" / f"{factor.factor_id}_{factor.slug}.gen.yaml"
        for factor in FACTORS
    )
    required_paths.extend(flow_root / "cases" / case.filename for case in CASES)
    required_paths.extend(
        flow_root / "templates" / "steps" / f"{step.template}.manual.yaml"
        for step in FLOW_STEPS
    )

    for path in required_paths:
        if not path.exists():
            errors.append(f"missing: {path.as_posix()}")

    case_list_path = flow_root / "case-list_gen.md"
    if case_list_path.exists():
        case_list = case_list_path.read_text(encoding="utf-8")
        for case in CASES:
            link = f"cases/{case.filename}"
            if link not in case_list:
                errors.append(f"case-list missing link: {link}")

    factor_ids = {factor.factor_id for factor in FACTORS}
    factor_elements = {
        factor.factor_id: {element.element_id for element in factor.elements} for factor in FACTORS
    }
    for case in CASES:
        for factor_id, element_id in case.selected:
            if factor_id not in factor_ids:
                errors.append(f"{case.case_id}: unknown factor {factor_id}")
                continue
            if element_id not in factor_elements[factor_id]:
                errors.append(f"{case.case_id}: unknown element {factor_id}.{element_id}")
        scenario_path = flow_root / "cases" / case.filename
        if scenario_path.exists():
            scenario = scenario_path.read_text(encoding="utf-8")
            if "${project_api_key}" not in scenario:
                errors.append(f"{case.case_id}: scenario does not keep project_api_key placeholder")
            if case.case_id not in scenario:
                errors.append(f"{case.case_id}: scenario title does not include case id")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    errors = check_specs()
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
