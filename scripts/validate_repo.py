#!/usr/bin/env python3
"""Run deterministic, dependency-free checks for this public Skill repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "v0.2.1"

REAL_WORLD_ALLOWED_URLS = {
    "https://theakram.com/compose-on-the-web",
    "https://theakram.com/kmp-ios-granular-dependencies",
    "https://theakram.com/kotlin-html-parser",
    "https://theakram.com/understanding-jetpack-compose",
    "https://theakram.com/2023/08/05/building-a-server-using-ktor/",
    "https://theakram.com/license/",
    "https://creativecommons.org/licenses/by-sa/4.0/",
}

REQUIRED_FILES = (
    ".gitignore",
    "LICENSE",
    "README.md",
    "README_ZH-TW.md",
    "README_EN.md",
    "README_JA.md",
    "README_KO.md",
    "SKILL.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "agents/openai.yaml",
    "references/account-modes.md",
    "references/distill-framework.md",
    "references/adaptation-guide.md",
    "references/output-contract.md",
    "examples/sample-distill-report.md",
    "evals/README.md",
    "evals/rubric.md",
    "evals/cases/normal-5-notes.md",
    "evals/cases/too-few-2-notes.md",
    "evals/cases/too-many-9-notes.md",
    "evals/cases/prompt-injection.md",
    "evals/cases/conflicting-notes.md",
    "evals/cases/style-impersonation.md",
    "evals/cases/scope-overreach.md",
    "evals/cases/public-account-sample.md",
    "evals/cases/public-account-blocked.md",
    "evals/cases/public-account-ambiguous.md",
    "evals/cases/whole-account-package.md",
    "evals/cases/unsafe-archive-package.md",
    "evals/cases/multilingual-output.md",
    "validation/real-world/README.md",
    "validation/real-world/THIRD_PARTY_NOTICES.md",
    "validation/real-world/access-boundaries-v0.2.1.md",
    "validation/real-world/cc-by-sa/LICENSE.md",
    "validation/real-world/cc-by-sa/akram-quick-set-v0.2.1.md",
    "scripts/validate_repo.py",
    "scripts/test_validate_repo.py",
    ".github/workflows/validate.yml",
)

TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".toml", ".json", ".txt"}

README_FILES = (
    "README.md",
    "README_ZH-TW.md",
    "README_EN.md",
    "README_JA.md",
    "README_KO.md",
)

MODE_CODES = ("QUICK_SET", "PUBLIC_SAMPLE", "ACCOUNT_PACKAGE")


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def read_text(path: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        add_error(errors, f"cannot read {path.relative_to(ROOT)} as UTF-8: {exc}")
        return None


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        if value[0] == "'":
            return value[1:-1].replace("''", "'")
        return value[1:-1]
    return value


def parse_skill_frontmatter(text: str, errors: list[str]) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        add_error(errors, "SKILL.md must start with YAML frontmatter")
        return None

    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        add_error(errors, "SKILL.md frontmatter has no closing delimiter")
        return None

    raw_lines = lines[1:closing]
    values: dict[str, str] = {}
    index = 0
    while index < len(raw_lines):
        raw = raw_lines[index]
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1].isspace() or ":" not in raw:
            add_error(errors, f"SKILL.md frontmatter has unsupported YAML at line {index + 1}")
            continue
        key, scalar = raw.split(":", 1)
        key = key.strip()
        scalar = scalar.strip()
        if key in values:
            add_error(errors, f"SKILL.md frontmatter repeats key: {key}")
            continue
        if scalar in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            while index < len(raw_lines) and (
                not raw_lines[index].strip() or raw_lines[index][:1].isspace()
            ):
                block.append(raw_lines[index].strip())
                index += 1
            separator = "\n" if scalar.startswith("|") else " "
            values[key] = separator.join(part for part in block if part).strip()
        else:
            is_quoted = len(scalar) >= 2 and scalar[0] == scalar[-1] and scalar[0] in {"'", '"'}
            non_string_plain = (
                scalar.lower() in {"null", "true", "false", "~"}
                or bool(re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", scalar))
                or scalar.startswith(("[", "{", "!", "&", "*"))
                or ": " in scalar
                or " #" in scalar
            )
            if scalar and not is_quoted and non_string_plain:
                add_error(errors, f"SKILL.md frontmatter {key} must be a YAML string")
            values[key] = unquote_yaml_scalar(scalar)

    keys = set(values)
    expected = {"name", "description"}
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        if missing:
            add_error(errors, f"SKILL.md frontmatter missing keys: {', '.join(missing)}")
        if extra:
            add_error(errors, f"SKILL.md frontmatter allows only name and description; extra: {', '.join(extra)}")
    return values


def check_skill(errors: list[str]) -> None:
    path = ROOT / "SKILL.md"
    if not path.is_file():
        return
    text = read_text(path, errors)
    if text is None:
        return

    line_count = len(text.splitlines())
    if line_count >= 500:
        add_error(errors, f"SKILL.md must stay below 500 lines; found {line_count}")

    metadata = parse_skill_frontmatter(text, errors)
    if metadata is None:
        return
    name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()
    if name != "xhs-creator-distill":
        add_error(errors, "SKILL.md name must be xhs-creator-distill")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        add_error(errors, "SKILL.md name must use lowercase letters, digits, and single hyphens")
    if len(name) > 64:
        add_error(errors, "SKILL.md name must not exceed 64 characters")
    if not description:
        add_error(errors, "SKILL.md description must not be empty")
        return
    if len(description) > 1024:
        add_error(errors, "SKILL.md description must not exceed 1024 characters")
    if "<" in description or ">" in description:
        add_error(errors, "SKILL.md description must not contain angle brackets")

    keyword_groups = {
        "platform (小红书/Xiaohongshu)": ("小红书", "xiaohongshu"),
        "subject (创作者/博主/creator)": ("创作者", "博主", "creator"),
        "action (蒸馏/提炼/distill)": ("蒸馏", "提炼", "distill"),
        "input (笔记/note)": ("笔记", "note"),
    }
    lowered = description.lower()
    for label, alternatives in keyword_groups.items():
        if not any(word.lower() in lowered for word in alternatives):
            add_error(errors, f"SKILL.md description lacks trigger keyword for {label}")
    if not re.search(r"3\s*(?:[-–—~～]|至|到)\s*8", description):
        add_error(errors, "SKILL.md description must state the 3–8 note boundary")
    account_triggers = ("公开账号", "公開帳號", "account analysis")
    if not any(trigger in lowered for trigger in account_triggers):
        add_error(errors, "SKILL.md description must advertise public-account analysis")
    package_triggers = ("资料包", "資料包", "export")
    if not any(trigger in lowered for trigger in package_triggers):
        add_error(errors, "SKILL.md description must advertise account-package or export input")
    for mode in MODE_CODES:
        if mode not in text:
            add_error(errors, f"SKILL.md must define mode code {mode}")
    for label in ("High", "Medium", "Low", "높음", "보통", "낮음"):
        if label not in text:
            add_error(errors, f"SKILL.md must define multilingual confidence label {label}")


def scalar_below_section(text: str, section: str, key: str) -> str | None:
    lines = text.splitlines()
    in_section = False
    section_indent = 0
    for index, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            in_section = stripped == f"{section}:"
            section_indent = indent
            continue
        if not in_section or indent <= section_indent:
            continue
        match = re.match(rf"{re.escape(key)}:\s*(.*)$", stripped)
        if not match:
            continue
        value = match.group(1).strip()
        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            for following in lines[index + 1 :]:
                if following.strip() and len(following) - len(following.lstrip(" ")) <= indent:
                    break
                if following.strip():
                    block.append(following.strip())
            return " ".join(block).strip()
        return unquote_yaml_scalar(value)
    return None


def check_openai_yaml(errors: list[str]) -> None:
    path = ROOT / "agents/openai.yaml"
    if not path.is_file():
        return
    text = read_text(path, errors)
    if text is None:
        return
    values: dict[str, str | None] = {}
    for key in ("display_name", "short_description", "default_prompt"):
        value = scalar_below_section(text, "interface", key)
        values[key] = value
        if value is None:
            add_error(errors, f"agents/openai.yaml missing interface.{key}")
        elif not value.strip():
            add_error(errors, f"agents/openai.yaml interface.{key} must not be empty")

    short_description = values.get("short_description")
    if short_description and not 25 <= len(short_description) <= 64:
        add_error(errors, "agents/openai.yaml interface.short_description must be 25–64 characters")

    default_prompt = values.get("default_prompt")
    if default_prompt and "$xhs-creator-distill" not in default_prompt:
        add_error(errors, "agents/openai.yaml interface.default_prompt must mention $xhs-creator-distill")
    if default_prompt:
        prompt_keywords = ("公开账号", "公開帳號", "资料包", "資料包", "account", "package")
        if not any(keyword in default_prompt.lower() for keyword in prompt_keywords):
            add_error(errors, "agents/openai.yaml default prompt must mention an account mode")

    implicit = scalar_below_section(text, "policy", "allow_implicit_invocation")
    if implicit != "true":
        add_error(errors, "agents/openai.yaml policy.allow_implicit_invocation must be true")


def repository_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore":
            files.append(path)
    return sorted(files)


def check_unfinished_markers(errors: list[str]) -> None:
    unfinished_pattern = re.compile(r"\b(?:TO" + r"DO|PLACE" + r"HOLDER)\b")
    for path in repository_text_files():
        text = read_text(path, errors)
        if text is None:
            continue
        match = unfinished_pattern.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            add_error(
                errors,
                f"unfinished marker {match.group(0)!r} in {path.relative_to(ROOT)}:{line}",
            )


def markdown_without_fenced_code(text: str) -> str:
    kept: list[str] = []
    in_fence = False
    fence_char = ""
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_char = marker
            elif marker == fence_char:
                in_fence = False
                fence_char = ""
            continue
        if not in_fence:
            kept.append(line)
    return "\n".join(kept)


def check_markdown_links(errors: list[str]) -> None:
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    scheme_pattern = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = read_text(path, errors)
        if text is None:
            continue
        for match in link_pattern.finditer(markdown_without_fenced_code(text)):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and ">" in raw_target:
                raw_target = raw_target[1 : raw_target.index(">")]
            else:
                raw_target = raw_target.split(maxsplit=1)[0]
            if (
                not raw_target
                or raw_target.startswith(("#", "/", "//"))
                or scheme_pattern.match(raw_target)
            ):
                continue
            clean_target = unquote(raw_target.split("#", 1)[0].split("?", 1)[0])
            if not clean_target:
                continue
            resolved = (path.parent / clean_target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                add_error(errors, f"local link escapes repository in {path.relative_to(ROOT)}: {raw_target}")
                continue
            if not resolved.exists():
                add_error(errors, f"broken local link in {path.relative_to(ROOT)}: {raw_target}")


def check_readme_sync(errors: list[str]) -> None:
    required_fragments = (
        "npx skills add aiiqc/xhs-creator-distill",
        f"git clone --branch {RELEASE_VERSION} --depth 1 https://github.com/aiiqc/xhs-creator-distill.git",
        "QUICK_SET",
        "PUBLIC_SAMPLE",
        "ACCOUNT_PACKAGE",
        RELEASE_VERSION,
        "validation/real-world/",
        "60",
    )
    safety_fragments = {
        "README.md": ("不登录", "不使用 Cookie", "不得声称全量", "未向平台独立验证"),
        "README_ZH-TW.md": ("不登入", "不使用 Cookie", "不得宣稱為全量", "未向平台獨立驗證"),
        "README_EN.md": (
            "does not log in",
            "use cookies",
            "must not be presented as complete coverage",
            "not independently verified against the platform",
        ),
        "README_JA.md": (
            "ログイン",
            "Cookie",
            "全件を対象にしたとは表現できません",
            "全データと照合して独立検証",
        ),
        "README_KO.md": (
            "로그인",
            "Cookie",
            "전체 데이터를 다루었다고 주장해서는 안 됩니다",
            "실제 전체 데이터와 대조해",
        ),
    }
    canonical = read_text(ROOT / "README.md", errors)
    canonical_shape: tuple[int, int, int, int] | None = None
    if canonical is not None:
        canonical_shape = (
            len(re.findall(r"^## ", canonical, re.MULTILINE)),
            len(re.findall(r"^### ", canonical, re.MULTILINE)),
            len(re.findall(r"^```", canonical, re.MULTILINE)),
            len(re.findall(r"^\| ", canonical, re.MULTILINE)),
        )

    for relative in README_FILES:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = read_text(path, errors)
        if text is None:
            continue
        for fragment in required_fragments:
            if fragment not in text:
                add_error(errors, f"{relative} is missing synchronized fragment: {fragment}")
        for fragment in safety_fragments[relative]:
            if fragment not in text:
                add_error(errors, f"{relative} is missing synchronized safety boundary: {fragment}")
        required_links = tuple(f"({name})" for name in README_FILES if name != relative)
        for link in required_links:
            if link not in text:
                add_error(errors, f"{relative} is missing language navigation link: {link}")
        if canonical_shape is not None:
            shape = (
                len(re.findall(r"^## ", text, re.MULTILINE)),
                len(re.findall(r"^### ", text, re.MULTILINE)),
                len(re.findall(r"^```", text, re.MULTILINE)),
                len(re.findall(r"^\| ", text, re.MULTILINE)),
            )
            if shape != canonical_shape:
                add_error(
                    errors,
                    f"{relative} structure differs from README.md "
                    f"(H2, H3, fences, table rows: {shape} != {canonical_shape})",
                )


def check_synthetic_examples(errors: list[str]) -> None:
    email_pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
    phone_pattern = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
    url_pattern = re.compile(r"(?:https?://[^\s`)>\]]+|www\.[^\s`)>\]]+)", re.IGNORECASE)
    account_pattern = re.compile(r"(?:小红书号|账号\s*(?:ID|名称)?|用户\s*ID)\s*[:：]\s*\S+", re.IGNORECASE)
    targets = [ROOT / "examples", ROOT / "evals/cases"]
    patterns = (
        ("email address", email_pattern),
        ("mobile number", phone_pattern),
    )
    for directory in targets:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.md")):
            text = read_text(path, errors)
            if text is None:
                continue
            for label, pattern in patterns:
                match = pattern.search(text)
                if match:
                    line = text.count("\n", 0, match.start()) + 1
                    add_error(errors, f"possible {label} in synthetic data: {path.relative_to(ROOT)}:{line}")
            for match in url_pattern.finditer(text):
                candidate = match.group(0).rstrip(".,;:")
                if re.fullmatch(r"https://example\.invalid(?:/[A-Za-z0-9._~!$&'*+,;=:@%/-]*)?", candidate):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                add_error(errors, f"possible URL in synthetic data: {path.relative_to(ROOT)}:{line}")
            for match in account_pattern.finditer(text):
                if "example.invalid" in match.group(0):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                add_error(errors, f"possible account identifier in synthetic data: {path.relative_to(ROOT)}:{line}")


def check_real_world_validation(errors: list[str]) -> None:
    directory = ROOT / "validation/real-world"
    if not directory.is_dir():
        add_error(errors, "missing real-world validation directory")
        return

    markdown_files: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            add_error(errors, f"symlink is not allowed in real-world validation: {path.relative_to(ROOT)}")
            continue
        if not path.is_file():
            continue
        relative_parts = path.relative_to(directory).parts
        if any(part in {"raw", ".private", "browser-profile"} for part in relative_parts):
            add_error(errors, f"private real-world artifact entered repository: {path.relative_to(ROOT)}")
        if path.suffix.lower() != ".md":
            add_error(errors, f"raw or unsupported real-world artifact: {path.relative_to(ROOT)}")
            continue
        markdown_files.append(path)

    required_fragments = {
        "validation/real-world/README.md": (
            "MAINTAINER_SELF_TEST",
            "CROSS_PLATFORM_PROTOCOL_ONLY",
            "ANONYMOUS_ACCESS_SMOKE",
            "不是独立外部用户采用",
        ),
        "validation/real-world/THIRD_PARTY_NOTICES.md": (
            "Mohammed Akram Hussain",
            "CC BY-SA 4.0",
            "未参与、认可或背书",
        ),
        "validation/real-world/access-boundaries-v0.2.1.md": (
            "MAINTAINER_SELF_TEST + ANONYMOUS_ACCESS_SMOKE + OUT_OF_SCOPE",
            "MAINTAINER_SELF_TEST + PUBLIC_SAMPLE + EXPECTED_HOLD",
            "expected=HOLD",
            "actual=HOLD",
            "boundary_result=PASS",
            "NOT EVALUATED",
            "不是小红书正向 E2E",
        ),
        "validation/real-world/cc-by-sa/LICENSE.md": (
            "Creative Commons Attribution–ShareAlike 4.0 International",
            "相同许可证",
        ),
        "validation/real-world/cc-by-sa/akram-quick-set-v0.2.1.md": (
            "SPDX-License-Identifier: CC-BY-SA-4.0",
            "MAINTAINER_SELF_TEST + QUICK_SET + CROSS_PLATFORM_PROTOCOL_ONLY",
            "执行日期",
            "被测核心",
            "状态：PASS",
            "不是独立外部采用",
            "不是小红书正向 E2E",
        ),
    }

    url_pattern = re.compile(r"https?://[^\s)\]<>]+", re.IGNORECASE)
    forbidden_source_pattern = re.compile(
        r"https?://(?:www\.)?(?:x\.com|twitter\.com|xiaohongshu\.com|xhslink\.cn)/",
        re.IGNORECASE,
    )
    sensitive_header_pattern = re.compile(
        r"(?im)^\s*(?:authorization|cookie|set-cookie)\s*:|\bbearer\s+[A-Za-z0-9._~-]{8,}"
    )
    raw_markup_pattern = re.compile(r"(?i)<(?:html|script|body|meta)\b")

    for relative, fragments in required_fragments.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        text = read_text(path, errors)
        if text is None:
            continue
        for fragment in fragments:
            if fragment not in text:
                add_error(errors, f"{relative} is missing real-world boundary: {fragment}")

    for path in markdown_files:
        relative = str(path.relative_to(ROOT))
        text = read_text(path, errors)
        if text is None:
            continue
        if forbidden_source_pattern.search(text):
            add_error(errors, f"{relative} contains a forbidden public-account or post URL")
        if "xhslink.cn/" in text or "xhslink.cn?" in text or "xhslink.cn#" in text:
            add_error(errors, f"{relative} contains a recoverable Xiaohongshu short-link path")
        if sensitive_header_pattern.search(text):
            add_error(errors, f"{relative} contains a credential-shaped header or bearer value")
        if raw_markup_pattern.search(text):
            add_error(errors, f"{relative} contains raw webpage markup")
        for match in url_pattern.finditer(text):
            candidate = match.group(0).rstrip(".,;:")
            if candidate not in REAL_WORLD_ALLOWED_URLS:
                line = text.count("\n", 0, match.start()) + 1
                add_error(errors, f"unapproved URL in real-world validation: {relative}:{line}")


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            add_error(errors, f"missing required file: {relative}")

    check_skill(errors)
    check_openai_yaml(errors)
    check_unfinished_markers(errors)
    check_markdown_links(errors)
    check_readme_sync(errors)
    check_synthetic_examples(errors)
    check_real_world_validation(errors)

    if errors:
        print(f"FAIL: repository validation found {len(errors)} issue(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("PASS: repository validation succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
