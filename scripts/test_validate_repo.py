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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
