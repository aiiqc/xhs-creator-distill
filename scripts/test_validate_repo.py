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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
