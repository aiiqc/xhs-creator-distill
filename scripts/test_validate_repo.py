#!/usr/bin/env python3
"""Regression tests for repository validation security boundaries."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def copy_repository(destination: Path) -> None:
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )


def run_validator(repository: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/validate_repo.py"],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def assert_pass(label: str, mutate: Callable[[Path], None] | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix="xhs-validator-") as temporary:
        repository = Path(temporary) / "repository"
        copy_repository(repository)
        if mutate is not None:
            mutate(repository)
        result = run_validator(repository)
        if result.returncode != 0:
            raise AssertionError(f"{label} unexpectedly failed:\n{result.stderr}{result.stdout}")
        print(f"PASS {label}")


def assert_fail(label: str, expected: str, mutate: Callable[[Path], None]) -> None:
    with tempfile.TemporaryDirectory(prefix="xhs-validator-") as temporary:
        repository = Path(temporary) / "repository"
        copy_repository(repository)
        mutate(repository)
        result = run_validator(repository)
        combined = result.stderr + result.stdout
        if result.returncode == 0:
            raise AssertionError(f"{label} unexpectedly passed")
        if expected not in combined:
            raise AssertionError(f"{label} failed without expected message {expected!r}:\n{combined}")
        print(f"PASS {label}")


def write_extra(repository: Path, content: str) -> None:
    path = repository / "validation/real-world/extra.md"
    path.write_text(content, encoding="utf-8")


def main() -> int:
    assert_pass("baseline and allowlisted canonical URLs")
    assert_fail(
        "unapproved URL in additional Markdown",
        "unapproved URL in real-world validation",
        lambda repository: write_extra(repository, "Source: https://evil.example/path\n"),
    )
    assert_fail(
        "credential-shaped header in additional Markdown",
        "credential-shaped header or bearer value",
        lambda repository: write_extra(
            repository,
            "Authorization: Bearer not-a-real-token-value\n",
        ),
    )
    assert_fail(
        "raw webpage markup in additional Markdown",
        "contains raw webpage markup",
        lambda repository: write_extra(repository, "<html><body>fixture</body></html>\n"),
    )

    def add_symlink(repository: Path) -> None:
        target = repository / "README.md"
        link = repository / "validation/real-world/linked.md"
        link.symlink_to(target)

    assert_fail(
        "symlink in real-world validation",
        "symlink is not allowed in real-world validation",
        add_symlink,
    )

    def add_extra_demo_artifact(repository: Path) -> None:
        path = repository / "examples/account-package-demo/expected/extra.txt"
        path.write_text("unexpected\n", encoding="utf-8")

    assert_fail(
        "extra synthetic demo artifact",
        "must contain exactly the five adapter artifacts",
        add_extra_demo_artifact,
    )

    def remove_formula_escape(repository: Path) -> None:
        path = repository / "examples/account-package-demo/expected/inventory.csv"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "'=1+1 合成公式前缀标题",
                "=1+1 合成公式前缀标题",
            ),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "missing spreadsheet escape in synthetic demo",
        "does not prove spreadsheet prefix escaping",
        remove_formula_escape,
    )

    def add_demo_email(repository: Path) -> None:
        path = repository / "examples/account-package-demo/input/posts.csv"
        path.write_text(
            path.read_text(encoding="utf-8").replace("虚构示例创作者", "demo-person@example.com", 1),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "email-shaped value in synthetic demo",
        "possible email address in synthetic data",
        add_demo_email,
    )

    def add_extra_demo_input(repository: Path) -> None:
        path = repository / "examples/account-package-demo/input/real-export.json"
        path.write_text(
            '{"email":"real-person@example.com","url":"https://unapproved.example/path"}\n',
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "extra file in synthetic demo input",
        "input directory must contain exactly posts.csv",
        add_extra_demo_input,
    )

    def add_extra_demo_root_artifact(repository: Path) -> None:
        path = repository / "examples/account-package-demo/raw-export.json"
        path.write_text('{"unexpected":true}\n', encoding="utf-8", newline="\n")

    assert_fail(
        "extra file in synthetic demo root",
        "root must contain exactly README.md, input, and expected",
        add_extra_demo_root_artifact,
    )

    def add_demo_credential_shape(repository: Path) -> None:
        path = repository / "examples/account-package-demo/input/posts.csv"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "这是一篇完全虚构的教程正文",
            "这是一篇完全虚构的教程正文 FAKE_SECRET_ghp_0123456789abcdefghijklmn",
            1,
        )
        if mutated == original:
            raise AssertionError("credential fixture mutation target is missing")
        path.write_text(
            mutated,
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "credential-shaped value in synthetic demo",
        "credential-shaped content in synthetic demo",
        add_demo_credential_shape,
    )

    def add_unsafe_evidence_formula(repository: Path) -> None:
        path = repository / "examples/account-package-demo/expected/evidence-map.csv"
        path.write_text(
            path.read_text(encoding="utf-8").replace("'+P003", "+P003"),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "unsafe spreadsheet prefix in synthetic demo output",
        "unsafe spreadsheet prefix in synthetic demo output",
        add_unsafe_evidence_formula,
    )

    def add_extra_field_map_input(repository: Path) -> None:
        path = repository / "examples/field-map-demo/input/unreviewed-export.json"
        path.write_text('{"unexpected":true}\n', encoding="utf-8", newline="\n")

    assert_fail(
        "extra file in field-map demo input",
        "must contain exactly posts-export.csv and field-map.json",
        add_extra_field_map_input,
    )

    def change_field_map_spec(repository: Path) -> None:
        path = repository / "examples/field-map-demo/input/field-map.json"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace('"schema_version": "1.0"', '"schema_version": "9.9"'),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "field-map demo spec differs from reviewed input",
        "mapping file differs from the reviewed SHA-256",
        change_field_map_spec,
    )

    def add_field_map_demo_credential(repository: Path) -> None:
        path = repository / "examples/field-map-demo/input/posts-export.csv"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "完全虚构的映射测试正文",
            "完全虚构的映射测试正文 FAKE_SECRET_ghp_0123456789abcdefghijklmn",
            1,
        )
        if mutated == original:
            raise AssertionError("field-map credential fixture mutation target is missing")
        path.write_text(mutated, encoding="utf-8", newline="\n")

    assert_fail(
        "credential-shaped value in field-map demo",
        "credential-shaped content in field-map demo",
        add_field_map_demo_credential,
    )

    def add_unsafe_field_map_formula(repository: Path) -> None:
        path = repository / "examples/field-map-demo/expected/evidence-map.csv"
        path.write_text(
            path.read_text(encoding="utf-8").replace("'+M003", "+M003"),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "unsafe spreadsheet prefix in field-map demo output",
        "unsafe spreadsheet prefix in field-map demo output",
        add_unsafe_field_map_formula,
    )

    def corrupt_field_mapping_audit(repository: Path) -> None:
        path = repository / "examples/field-map-demo/expected/manifest.json"
        path.write_text(
            path.read_text(encoding="utf-8").replace('"applied": true', '"applied": false', 1),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "field-map manifest audit mismatch",
        "manifest mapping audit is inconsistent",
        corrupt_field_mapping_audit,
    )

    def drift_readme_version(repository: Path) -> None:
        path = repository / "README_EN.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("v0.4.3", "v0.4.9"),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "translated README version drift",
        "README_EN.md is missing synchronized fragment: v0.4.3",
        drift_readme_version,
    )

    def remove_readme_human_marker(repository: Path) -> None:
        path = repository / "README_EN.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "<!-- human-quickstart-start -->",
                "<!-- human-quickstart-drifted -->",
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "translated README human quickstart marker drift",
        "README_EN.md is missing synchronized fragment: <!-- human-quickstart-start -->",
        remove_readme_human_marker,
    )

    def inject_full_report_section_into_hold(repository: Path) -> None:
        path = repository / "examples/sample-hold-report.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n## 执行摘要\n\n不应出现。\n",
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "HOLD example cannot contain PASS-only sections",
        "HOLD example must not contain execution summary or five-layer report",
        inject_full_report_section_into_hold,
    )

    def remove_summary_evidence(repository: Path) -> None:
        path = repository / "examples/sample-distill-report.md"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace(
            "| 从时间紧、预算有限或复热失败等具体任务切入 | 推断 | N01, N02, N03, N04 | 高 |",
            "| 从时间紧、预算有限或复热失败等具体任务切入 | 推断 | 未提供 | 高 |",
            1,
        )
        if mutated == original:
            raise AssertionError("summary evidence mutation target is missing")
        path.write_text(mutated, encoding="utf-8", newline="\n")

    assert_fail(
        "PASS summary requires evidence",
        "execution summary row 1 is missing Nxx evidence",
        remove_summary_evidence,
    )

    def remove_filled_plan_evidence(repository: Path) -> None:
        path = repository / "examples/sample-filled-plan.csv"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace('"N01,N04"', '""', 1)
        if mutated == original:
            raise AssertionError("filled plan evidence mutation target is missing")
        path.write_text(mutated, encoding="utf-8", newline="\n")

    assert_fail(
        "filled plan requires evidence on every row",
        "filled plan example evidence_ids must be nonempty at row 1",
        remove_filled_plan_evidence,
    )

    def add_extra_filled_plan_column(repository: Path) -> None:
        path = repository / "examples/sample-filled-plan.csv"
        lines = path.read_text(encoding="utf-8").splitlines()
        lines[1] = lines[1] + ",unexpected"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    assert_fail(
        "filled plan rejects an extra CSV column without traceback",
        "filled plan example has malformed columns at row 1",
        add_extra_filled_plan_column,
    )

    def corrupt_account_report_mapping(repository: Path) -> None:
        path = repository / "examples/sample-account-package-report.md"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace("| `N01` | `S001` |", "| `N01` | `S999` |", 1)
        if mutated == original:
            raise AssertionError("account report mapping mutation target is missing")
        path.write_text(mutated, encoding="utf-8", newline="\n")

    assert_fail(
        "account-package report mapping must match golden evidence map",
        "account-package report mapping is inconsistent: N01 -> S001",
        corrupt_account_report_mapping,
    )

    def add_credential_shape_to_human_example(repository: Path) -> None:
        path = repository / "examples/sample-account-package-report.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\nFAKE_SECRET_ghp_0123456789abcdefghijklmn\n",
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "credential-shaped value in human-facing synthetic example",
        "credential-shaped content in synthetic data",
        add_credential_shape_to_human_example,
    )

    def drift_deterministic_eval_version(repository: Path) -> None:
        path = repository / "evals/cases/deterministic-package-adapter.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "xhs-creator-distill account-package adapter v0.4.3",
                "xhs-creator-distill account-package adapter v0.4.0",
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "deterministic eval adapter version drift",
        "evals/cases/deterministic-package-adapter.md is missing package-adapter contract: "
        "xhs-creator-distill account-package adapter v0.4.3",
        drift_deterministic_eval_version,
    )

    def remove_body_target_boundary(repository: Path) -> None:
        path = repository / "README_EN.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "`body` cannot be a map target",
                "`body` is accepted by the adapter",
            ),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "translated README body-target boundary drift",
        "README_EN.md is missing synchronized safety boundary: `body` cannot be a map target",
        remove_body_target_boundary,
    )

    def reverse_loaded_skill_root_boundary(repository: Path) -> None:
        path = repository / "README_EN.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "actually loaded `SKILL.md` path",
                "preconfigured environment variable",
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )

    assert_fail(
        "translated README loaded-Skill root boundary drift",
        "README_EN.md is missing synchronized safety boundary: actually loaded `SKILL.md` path",
        reverse_loaded_skill_root_boundary,
    )

    def remove_powershell_single_candidate_selection(repository: Path) -> None:
        path = repository / ".github/workflows/validate.yml"
        original = path.read_text(encoding="utf-8")
        mutated = original.replace("Select-Object -First 1", "Select-Object", 1)
        if mutated == original:
            raise AssertionError("PowerShell candidate-selection mutation target is missing")
        path.write_text(mutated, encoding="utf-8", newline="\n")

    assert_fail(
        "Windows PowerShell selects exactly one Python command",
        ".github/workflows/validate.yml is missing package-adapter contract: "
        "Select-Object -First 1",
        remove_powershell_single_candidate_selection,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
