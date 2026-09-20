#!/usr/bin/env python3
"""Validate CRTBench data and self-contained game artifacts."""

from __future__ import annotations

import json
import hashlib
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable
from urllib.parse import unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON_PATH = REPO_ROOT / "data.json"
GAMES_DIR = REPO_ROOT / "games"
PREVIEWS_DIR = REPO_ROOT / "previews"

REQUIRED_FIELDS = {
    "id", "title", "author", "category", "badge", "file", "vibeScore",
    "size", "lines", "hardware", "model", "harness", "thinkingEffort",
    "quant", "promptStyle", "prompt", "sourceName", "sourceUrl", "ratings",
    "elo", "matches", "preview", "hidden", "genre", "license", "isOpenSource",
    "modelAccess", "weightsLicense", "artifactLicense", "vibeScoreType", "sizeBytes",
    "artifactSha256", "promptSha256",
}
STRING_FIELDS = {
    "id", "title", "author", "category", "badge", "file", "size", "hardware",
    "model", "harness", "thinkingEffort", "quant", "promptStyle", "prompt",
    "sourceName", "sourceUrl", "preview", "genre", "license",
}
CANONICAL_HARNESSES = {"Antigravity", "llama.cpp", "vLLM", "Ollama", "API"}
CANONICAL_REASONING_TIERS = {"None", "Light", "Medium", "High", "Ultra"}
CANONICAL_GENRES = {"platformer", "raycaster", "maze", "puzzle", "other"}
CANONICAL_LICENSES = {"open", "proprietary"}
MODEL_ACCESS_TYPES = {"open_weights", "proprietary"}
VIBE_SCORE_TYPES = {"editorial", "community"}
BENCHMARK_STATUSES = {"eligible", "excluded"}
RATING_FIELDS = {"nesCrunch", "physicsFeel", "ambition"}
PREVIEW_SIZE = (960, 600)
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SIZE_RE = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)? KB$")

_CSS_COMMENT_RE = re.compile(r"/\*[\s\S]*?\*/")
_CSS_URL_RE = re.compile(r"url\(\s*(?P<quote>['\"]?)(?P<value>.*?)(?P=quote)\s*\)", re.IGNORECASE)
_CSS_IMPORT_RE = re.compile(
    r"@import\s+(?:url\(\s*(?P<url_quote>['\"]?)(?P<url>.*?)(?P=url_quote)\s*\)|"
    r"(?P<quote>['\"])(?P<quoted>.*?)(?P=quote))",
    re.IGNORECASE,
)
_URI_RE = re.compile(r"(?i)(?:https?|wss?|ws|ftp|file):/{1,2}|(?<!:)//[a-z0-9.-]+")


def log(message: str, status: str = "INFO") -> None:
    colors = {
        "INFO": "\033[94m", "PASS": "\033[92m", "WARN": "\033[93m",
        "FAIL": "\033[91m", "RESET": "\033[0m",
    }
    print(f"{colors.get(status, '')}[{status}]{colors['RESET']} {message}")


def format_size(size_bytes: int) -> str:
    """Return the canonical user-facing size used by the submitter."""
    return f"{round(size_bytes / 1024, 1):.1f} KB"


def count_lines(contents: bytes) -> int:
    """Count decoded text lines, matching the submission metadata calculation."""
    return len(contents.decode("utf-8-sig").splitlines())


def png_dimensions(contents: bytes) -> tuple[int, int] | None:
    """Read and validate a PNG IHDR without requiring an image library."""
    if len(contents) < 45 or contents[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    offset = 8
    dimensions: tuple[int, int] | None = None
    saw_idat = False
    saw_iend = False
    first_chunk = True
    while offset + 12 <= len(contents):
        length = struct.unpack(">I", contents[offset:offset + 4])[0]
        chunk_type = contents[offset + 4:offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(contents):
            return None
        chunk_data = contents[data_start:data_end]
        expected_crc = struct.unpack(">I", contents[data_end:crc_end])[0]
        actual_crc = zlib.crc32(contents[offset + 4:data_end]) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            return None
        if first_chunk:
            if chunk_type != b"IHDR" or length != 13:
                return None
            dimensions = struct.unpack(">II", chunk_data[:8])
            first_chunk = False
        elif chunk_type == b"IHDR":
            return None
        if chunk_type == b"IDAT":
            saw_idat = True
        if chunk_type == b"IEND":
            if length != 0:
                return None
            saw_iend = True
            offset = crc_end
            break
        offset = crc_end
    if not dimensions or dimensions[0] <= 0 or dimensions[1] <= 0:
        return None
    if not saw_idat or not saw_iend or offset != len(contents):
        return None
    return dimensions


def _is_number(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _absolute_http_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def _decode_css_escapes(value: str) -> str:
    def hex_escape(match: re.Match[str]) -> str:
        try:
            codepoint = int(match.group(1), 16)
            return "\uFFFD" if codepoint == 0 or codepoint > 0x10FFFF else chr(codepoint)
        except ValueError:
            return "\uFFFD"

    value = re.sub(r"\\([0-9a-fA-F]{1,6})\s?", hex_escape, value)
    return re.sub(r"\\(.)", r"\1", value, flags=re.DOTALL)


def _decode_js_escapes(value: str) -> str:
    value = value.replace(r"\/", "/")
    value = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), value)
    value = re.sub(r"\\u\{([0-9a-fA-F]{1,6})\}", lambda m: chr(int(m.group(1), 16)), value)
    value = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), value)
    return value


def _is_inline_url(value: str) -> bool:
    value = value.strip().strip("\"'")
    if not value or value.startswith("#"):
        return True
    try:
        scheme = urlsplit(value).scheme.lower()
    except ValueError:
        return False
    return scheme in {"data", "blob", "about", "javascript"}


def _google_fonts_url_allowed(value: str, context: str, rel: str = "") -> bool:
    """Allow only Google Fonts stylesheet/font endpoints in CSS and link tags."""
    value = value.strip().strip("\"'")
    if value.startswith("//"):
        value = "https:" + value
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
            return False
        path = unquote(parsed.path or "/")
    except ValueError:
        return False

    link_rel = {token.lower() for token in rel.split()}
    if context == "link" and link_rel.intersection({"preconnect", "dns-prefetch"}):
        return host in {"fonts.googleapis.com", "fonts.gstatic.com"} and path in {"", "/"}

    if host == "fonts.googleapis.com":
        return context in {"link", "css-import"} and re.fullmatch(r"/css2?/?", path) is not None
    if host == "fonts.gstatic.com":
        extension = Path(path).suffix.lower()
        return context in {"link", "css-url"} and path.startswith("/s/") and extension in {
            ".woff", ".woff2", ".ttf", ".otf", ".eot",
        }
    return False


def _resource_is_external(value: str, context: str, rel: str = "") -> bool:
    value = value.strip().strip("\"'")
    if _is_inline_url(value):
        return False
    if _google_fonts_url_allowed(value, context, rel):
        return False
    return True


def _css_dependencies(css: str) -> list[tuple[str, str]]:
    css = _decode_css_escapes(_CSS_COMMENT_RE.sub("", css))
    imports: list[tuple[int, int, str]] = []
    urls: list[tuple[int, int, str]] = []
    for match in _CSS_IMPORT_RE.finditer(css):
        value = match.group("url") if match.group("url") is not None else match.group("quoted")
        imports.append((match.start(), match.end(), value.strip()))
    for match in _CSS_URL_RE.finditer(css):
        urls.append((match.start(), match.end(), match.group("value").strip()))

    dependencies = [(value, "css-import") for _, _, value in imports]
    for start, end, value in urls:
        if any(import_start <= start and end <= import_end for import_start, import_end, _ in imports):
            continue
        dependencies.append((value, "css-url"))
    return dependencies


def _mask_javascript(source: str) -> tuple[str, list[str]]:
    """Mask strings, comments, and regular expressions while preserving code tokens."""
    out = list(source)
    literals: list[str] = []
    length = len(source)
    i = 0
    can_start_regex = True

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if out[position] not in "\r\n":
                out[position] = " "

    while i < length:
        char = source[i]
        next_char = source[i + 1] if i + 1 < length else ""

        if char.isspace():
            i += 1
            continue
        if char == "/" and next_char == "/":
            start = i
            i += 2
            while i < length and source[i] not in "\r\n":
                i += 1
            blank(start, i)
            continue
        if char == "/" and next_char == "*":
            start = i
            i += 2
            while i < length and source[i:i + 2] != "*/":
                i += 1
            i = min(length, i + 2)
            blank(start, i)
            continue
        if char in "'\"`":
            quote = char
            start = i
            i += 1
            value_start = i
            while i < length:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == quote:
                    break
                i += 1
            literals.append(source[value_start:min(i, length)])
            if i < length:
                i += 1
            blank(start, i)
            can_start_regex = False
            continue
        if char == "/" and can_start_regex and next_char not in {"", "=", "/", "*"}:
            start = i
            i += 1
            in_character_class = False
            while i < length:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == "[":
                    in_character_class = True
                elif source[i] == "]":
                    in_character_class = False
                elif source[i] == "/" and not in_character_class:
                    i += 1
                    while i < length and source[i].isalpha():
                        i += 1
                    break
                elif source[i] in "\r\n":
                    break
                i += 1
            blank(start, i)
            can_start_regex = False
            continue

        if char.isalpha() or char in "_$":
            start = i
            i += 1
            while i < length and (source[i].isalnum() or source[i] in "_$"):
                i += 1
            token = source[start:i]
            can_start_regex = token in {
                "return", "throw", "case", "delete", "void", "typeof", "instanceof",
                "in", "of", "yield", "await", "new", "else", "do", "typeof",
            }
            continue
        if char.isdigit():
            i += 1
            while i < length and (source[i].isalnum() or source[i] in "._"):
                i += 1
            can_start_regex = False
            continue
        if char in ")]}":
            can_start_regex = False
        elif char in "([{,;:?=!*%&|^~<>+-":
            can_start_regex = True
        elif char == ".":
            can_start_regex = False
        elif char == "/":
            can_start_regex = True
        i += 1

    return "".join(out), literals


def _javascript_network_findings(source: str) -> list[str]:
    code, literals = _mask_javascript(source)
    findings: list[str] = []
    for value in literals:
        decoded = _decode_js_escapes(value)
        match = _URI_RE.search(decoded)
        if match:
            findings.append(f"external URL literal {match.group(0)!r} in inline JavaScript")

    patterns = (
        (r"\bfetch\s*(?:\(|\.)", "fetch() can access a runtime network resource"),
        (r"\bXMLHttpRequest\b", "XMLHttpRequest can access a runtime network resource"),
        (r"\bWebSocket\b", "WebSocket can open a runtime network connection"),
        (r"\bEventSource\b", "EventSource can open a runtime network connection"),
        (r"\bsendBeacon\s*\(", "sendBeacon() can send a runtime network request"),
        (r"\bimportScripts\s*\(", "importScripts() can load a runtime network resource"),
        (r"\b(?:SharedWorker|Worker)\s*\(", "Worker() can load a runtime script resource"),
        (r"\bimport\s*\(", "dynamic import() can load a runtime module resource"),
    )
    for pattern, message in patterns:
        if re.search(pattern, code):
            findings.append(message)
    if re.search(r"\bimport\s+", code) or re.search(r"\bexport\s+(?:\*|\{)[\s\S]*?\bfrom\b", code):
        findings.append("module import/export can load a runtime script resource")
    return list(dict.fromkeys(findings))


def _srcset_candidates(value: str) -> list[str]:
    """Split srcset candidates without treating a data URL's comma as a separator."""
    candidates: list[str] = []
    index = 0
    length = len(value)
    while index < length:
        while index < length and (value[index].isspace() or value[index] == ","):
            index += 1
        if index >= length:
            break
        start = index
        if value[index:index + 5].lower() == "data:":
            while index < length and not value[index].isspace():
                index += 1
        else:
            while index < length and not value[index].isspace() and value[index] != ",":
                index += 1
        url = value[start:index].strip()
        if url:
            candidates.append(url)
        while index < length and value[index] != ",":
            index += 1
        if index < length:
            index += 1
    return candidates


def _is_javascript_type(value: str) -> bool:
    normalized = value.split(";", 1)[0].strip().lower()
    return normalized in {
        "", "module", "text/javascript", "application/javascript", "text/ecmascript",
        "application/ecmascript", "application/x-javascript",
    } or normalized.endswith("+javascript")


def _check_javascript_syntax(
    source: str,
    node_executable: str | None,
    module: bool = False,
) -> str | None:
    if not node_executable:
        return "Node.js is required to validate inline JavaScript syntax"
    input_type = "module" if module else "commonjs"
    try:
        proc = subprocess.run(
            [node_executable, "--check", f"--input-type={input_type}"],
            input=source,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"could not check inline JavaScript syntax: {exc}"
    if proc.returncode == 0:
        return None
    return (proc.stderr or proc.stdout or "JavaScript syntax check failed").strip()


class _HTMLRuntimeScanner(HTMLParser):
    RESOURCE_ATTRIBUTES = {
        "script": {"src"},
        "link": {"href"},
        "img": {"src", "srcset"},
        "audio": {"src"},
        "video": {"src", "poster"},
        "source": {"src", "srcset"},
        "iframe": {"src"},
        "object": {"data", "codebase"},
        "embed": {"src"},
        "track": {"src"},
        "input": {"src"},
        "base": {"href"},
        "image": {"href", "xlink:href"},
        "use": {"href", "xlink:href"},
        "feimage": {"href", "xlink:href"},
    }

    def __init__(self, node_executable: str | None, depth: int = 0):
        super().__init__(convert_charrefs=True)
        self.node_executable = node_executable
        self.depth = depth
        self.findings: list[str] = []
        self._script: dict[str, str] | None = None
        self._style: list[str] | None = None

    def _check_css(self, css: str, label: str) -> None:
        for url, context in _css_dependencies(css):
            if _resource_is_external(url, context):
                self.findings.append(f"{label} references external CSS resource {url!r}")

    def _check_javascript(self, source: str, label: str, module: bool = False) -> None:
        self.findings.extend(f"{label}: {item}" for item in _javascript_network_findings(source))
        syntax_error = _check_javascript_syntax(source, self.node_executable, module=module)
        if syntax_error:
            self.findings.append(f"{label} has a syntax error: {syntax_error}")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_tag(tag.lower(), attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_tag(tag.lower(), attrs)

    def _handle_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        rel = attr_map.get("rel", "")
        for name in self.RESOURCE_ATTRIBUTES.get(tag, set()):
            value = attr_map.get(name)
            if value is None:
                continue
            values: Iterable[str]
            if name == "srcset":
                values = _srcset_candidates(value)
            else:
                values = (value,)
            for resource in values:
                if _resource_is_external(resource, "link" if tag == "link" else "html", rel):
                    self.findings.append(f"<{tag}> {name} references external runtime resource {resource!r}")

        if tag == "iframe" and "srcdoc" in attr_map:
            if self.depth >= 5:
                self.findings.append("nested iframe srcdoc depth exceeds 5")
            else:
                nested = _HTMLRuntimeScanner(self.node_executable, self.depth + 1)
                nested.feed(attr_map["srcdoc"])
                nested.close()
                self.findings.extend(f"<iframe srcdoc>: {item}" for item in nested.findings)

        style_attr = attr_map.get("style")
        if style_attr:
            self._check_css(style_attr, "style attribute")

        for name, value in attr_map.items():
            if name.startswith("on") and value.strip():
                handler = f"function __crtbench_handler(event) {{\n{value}\n}}"
                self._check_javascript(handler, f"inline {name} handler")

        if tag == "script":
            self._script = {"type": attr_map.get("type", ""), "body": ""}
        elif tag == "style":
            self._style = []

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script["body"] += data
        if self._style is not None:
            self._style.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self._script is not None:
            script = self._script
            self._script = None
            body = script["body"]
            script_type = script["type"]
            if body.strip() and _is_javascript_type(script_type):
                self._check_javascript(body, "inline <script>", module=script_type.split(";", 1)[0].strip().lower() == "module")
        elif tag == "style" and self._style is not None:
            self._check_css("".join(self._style), "<style>")
            self._style = None


def inspect_html(contents: str, node_executable: str | None = None) -> list[str]:
    scanner = _HTMLRuntimeScanner(node_executable or shutil.which("node"))
    scanner.feed(contents)
    scanner.close()
    return scanner.findings


def _resolve_data_path(
    repo_root: Path,
    raw_path: object,
    expected_directory: str,
) -> tuple[Path | None, str | None]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, "path must be a non-empty string"
    if "\\" in raw_path or "\x00" in raw_path:
        return None, "path must use normalized forward-slash separators"
    pure = PurePosixPath(raw_path)
    if pure.is_absolute() or re.match(r"^[a-zA-Z]:", raw_path):
        return None, "absolute paths are not allowed"
    if pure.as_posix() != raw_path or any(part in {"", ".", ".."} for part in pure.parts):
        return None, "path must not contain traversal or non-canonical segments"
    if not pure.parts or pure.parts[0] != expected_directory:
        return None, f"path must be inside {expected_directory}/"

    root = repo_root.resolve(strict=False)
    expected_root = (root / expected_directory).resolve(strict=False)
    try:
        expected_root.relative_to(root)
    except ValueError:
        return None, f"{expected_directory}/ resolves outside the repository"

    resolved = root.joinpath(*pure.parts).resolve(strict=False)
    try:
        resolved.relative_to(expected_root)
    except ValueError:
        return None, f"path resolves outside {expected_directory}/"
    return resolved, None


def _overrides_by_path(path_overrides: dict[object, object] | None) -> dict[Path, Path]:
    overrides: dict[Path, Path] = {}
    for original, staged in (path_overrides or {}).items():
        original_path = Path(original)
        if not original_path.is_absolute():
            original_path = REPO_ROOT / original_path
        overrides[original_path.resolve(strict=False)] = Path(staged).resolve(strict=False)
    return overrides


def validate_dataset(
    data: object,
    repo_root: Path | str = REPO_ROOT,
    path_overrides: dict[object, object] | None = None,
    emit: Callable[[str, str], None] = log,
    node_executable: str | None = None,
) -> dict[str, int]:
    """Validate parsed data and referenced files; return counts for callers/tests."""
    root = Path(repo_root)
    overrides = _overrides_by_path(path_overrides)
    errors = 0
    warnings = 0
    display_active = 0
    eligible = 0
    excluded = 0

    def fail(message: str) -> None:
        nonlocal errors
        errors += 1
        emit(message, "FAIL")

    def warn(message: str) -> None:
        nonlocal warnings
        warnings += 1
        emit(message, "WARN")

    if not isinstance(data, list):
        fail("Top-level data.json value must be an array.")
        return {"errors": errors, "warnings": warnings, "active": 0, "eligible": 0, "excluded": 0}

    emit(f"Validating {len(data)} data entr{'y' if len(data) == 1 else 'ies'}...", "INFO")
    seen_ids: set[str] = set()

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            fail(f"[entry_{index}] Entry must be a JSON object.")
            continue
        raw_id = item.get("id")
        gid = raw_id if isinstance(raw_id, str) and raw_id else f"entry_{index}"

        for field in sorted(REQUIRED_FIELDS - item.keys()):
            fail(f"[{gid}] Missing required field: '{field}'.")

        for field in STRING_FIELDS:
            if field not in item:
                continue
            if not isinstance(item[field], str) or not item[field].strip():
                fail(f"[{gid}] Field '{field}' must be a non-empty string.")

        if isinstance(raw_id, str) and raw_id:
            if not SAFE_ID_RE.fullmatch(raw_id):
                fail(f"[{gid}] id must match {SAFE_ID_RE.pattern!r}.")
            if raw_id in seen_ids:
                fail(f"[{gid}] Duplicate id.")
            seen_ids.add(raw_id)

        for field in ("title", "author", "category", "badge", "model", "promptStyle", "prompt", "sourceName"):
            if field in item and isinstance(item[field], str) and not item[field].strip():
                fail(f"[{gid}] Field '{field}' must not be blank.")

        if "vibeScore" in item and (not _is_number(item["vibeScore"]) or not 1 <= item["vibeScore"] <= 10):
            fail(f"[{gid}] vibeScore must be a number from 1 to 10.")
        if "size" in item and isinstance(item["size"], str) and not SIZE_RE.fullmatch(item["size"]):
            fail(f"[{gid}] size must use the format '<number> KB'.")
        if "lines" in item and (type(item["lines"]) is not int or item["lines"] < 0):
            fail(f"[{gid}] lines must be a non-negative integer.")
        if "harness" in item and (not isinstance(item["harness"], str) or item["harness"] not in CANONICAL_HARNESSES):
            fail(f"[{gid}] harness must be one of {sorted(CANONICAL_HARNESSES)}.")
        if "thinkingEffort" in item and (not isinstance(item["thinkingEffort"], str) or item["thinkingEffort"] not in CANONICAL_REASONING_TIERS):
            fail(f"[{gid}] thinkingEffort must be one of {sorted(CANONICAL_REASONING_TIERS)}.")
        if "genre" in item and (not isinstance(item["genre"], str) or item["genre"] not in CANONICAL_GENRES):
            fail(f"[{gid}] genre must be one of {sorted(CANONICAL_GENRES)}.")
        if "license" in item and (not isinstance(item["license"], str) or item["license"] not in CANONICAL_LICENSES):
            fail(f"[{gid}] license must be one of {sorted(CANONICAL_LICENSES)}.")
        if "modelAccess" in item and (not isinstance(item["modelAccess"], str) or item["modelAccess"] not in MODEL_ACCESS_TYPES):
            fail(f"[{gid}] modelAccess must be one of {sorted(MODEL_ACCESS_TYPES)}.")
        if "vibeScoreType" in item and (not isinstance(item["vibeScoreType"], str) or item["vibeScoreType"] not in VIBE_SCORE_TYPES):
            fail(f"[{gid}] vibeScoreType must be one of {sorted(VIBE_SCORE_TYPES)}.")
        for field in ("weightsLicense", "artifactLicense"):
            if field in item and item[field] is not None and (not isinstance(item[field], str) or not item[field].strip()):
                fail(f"[{gid}] {field} must be a non-empty string or null.")
        if "isOpenSource" in item and type(item["isOpenSource"]) is not bool:
            fail(f"[{gid}] isOpenSource must be a boolean.")
        if isinstance(item.get("license"), str) and item.get("license") in CANONICAL_LICENSES and type(item.get("isOpenSource")) is bool:
            if item["isOpenSource"] != (item["license"] == "open"):
                fail(f"[{gid}] license and isOpenSource disagree.")
        if isinstance(item.get("modelAccess"), str) and item["modelAccess"] in MODEL_ACCESS_TYPES:
            if type(item.get("isOpenSource")) is bool and item["isOpenSource"] != (item["modelAccess"] == "open_weights"):
                fail(f"[{gid}] modelAccess and isOpenSource disagree.")
            expected_model_access = "open_weights" if item.get("license") == "open" else "proprietary"
            if isinstance(item.get("license"), str) and item["license"] in CANONICAL_LICENSES and item["modelAccess"] != expected_model_access:
                fail(f"[{gid}] modelAccess and license disagree.")

        if "hardware" in item and isinstance(item["hardware"], str):
            hardware = item["hardware"].strip()
            if item.get("isOpenSource") is True and (hardware.upper() == "API" or "cloud" in hardware.lower()):
                fail(f"[{gid}] Open-weight models must specify physical accelerator hardware.")
            if item.get("isOpenSource") is False and hardware != "API":
                fail(f"[{gid}] Proprietary models must specify hardware as 'API'.")
        if "quant" in item and isinstance(item["quant"], str):
            quant = item["quant"].strip()
            if item.get("isOpenSource") is True and (not quant or quant.upper() == "N/A"):
                fail(f"[{gid}] Open-weight models must specify quantization.")
            if item.get("isOpenSource") is False and quant.upper() != "N/A":
                fail(f"[{gid}] Proprietary models must specify quant as 'N/A'.")

        for field in ("elo",):
            if field in item and (not _is_number(item[field]) or item[field] < 0):
                fail(f"[{gid}] {field} must be a finite non-negative number.")
        for field in ("matches", "baseVotes", "wins"):
            if field in item and (type(item[field]) is not int or item[field] < 0):
                fail(f"[{gid}] {field} must be a non-negative integer.")
        if type(item.get("matches")) is int and type(item.get("wins")) is int and item["wins"] > item["matches"]:
            fail(f"[{gid}] wins cannot exceed matches.")

        ratings = item.get("ratings")
        if not isinstance(ratings, dict):
            fail(f"[{gid}] ratings must be an object.")
        else:
            for rating in RATING_FIELDS:
                value = ratings.get(rating)
                if not _is_number(value) or not 0 <= value <= 10:
                    fail(f"[{gid}] ratings.{rating} must be a number from 0 to 10.")

        if not isinstance(item.get("hidden"), bool):
            fail(f"[{gid}] hidden must be a boolean.")
        if "sizeBytes" in item and (type(item["sizeBytes"]) is not int or item["sizeBytes"] < 0):
            fail(f"[{gid}] sizeBytes must be a non-negative integer.")
        for field in ("artifactSha256", "promptSha256"):
            if field in item and (not isinstance(item[field], str) or re.fullmatch(r"[a-f0-9]{64}", item[field]) is None):
                fail(f"[{gid}] {field} must be a lowercase 64-character SHA-256 hex digest.")
        hidden = item.get("hidden") is True
        benchmark_status = item.get("benchmarkStatus", "eligible")
        if not isinstance(benchmark_status, str) or benchmark_status not in BENCHMARK_STATUSES:
            fail(f"[{gid}] benchmarkStatus must be one of {sorted(BENCHMARK_STATUSES)}.")
        elif benchmark_status == "excluded":
            excluded += 1
            reason = item.get("benchmarkStatusReason")
            if not isinstance(reason, str) or not reason.strip():
                fail(f"[{gid}] excluded entries require a non-empty benchmarkStatusReason.")
        elif not hidden:
            eligible += 1

        if "sourceUrl" in item and isinstance(item["sourceUrl"], str) and not _absolute_http_url(item["sourceUrl"]):
            fail(f"[{gid}] sourceUrl must be an absolute HTTP(S) URL.")
        if "demoUrl" in item and (not isinstance(item["demoUrl"], str) or not _absolute_http_url(item["demoUrl"])):
            fail(f"[{gid}] demoUrl must be an absolute HTTP(S) URL when present.")
        if "vibeReview" in item and not isinstance(item["vibeReview"], str):
            fail(f"[{gid}] vibeReview must be a string when present.")
        if "mode" in item and not isinstance(item["mode"], str):
            fail(f"[{gid}] mode must be a string when present.")

        game_path, game_path_error = _resolve_data_path(root, item.get("file"), "games")
        preview_path, preview_path_error = _resolve_data_path(root, item.get("preview"), "previews")
        if game_path_error:
            fail(f"[{gid}] Invalid game file path: {game_path_error}.")
        if preview_path_error:
            fail(f"[{gid}] Invalid preview path: {preview_path_error}.")

        if hidden:
            emit(f"[{gid}] Hidden/archive entry; schema and path safety checked, artifact checks skipped.", "INFO")
            continue

        display_active += 1
        if game_path is None or preview_path is None:
            continue

        actual_game = overrides.get(game_path, game_path)
        actual_preview = overrides.get(preview_path, preview_path)
        if not actual_game.is_file():
            fail(f"[{gid}] Game file does not exist: {item.get('file')}.")
            continue
        if not actual_preview.is_file():
            fail(f"[{gid}] Preview image missing: {item.get('preview')}.")

        try:
            game_bytes = actual_game.read_bytes()
        except OSError as exc:
            fail(f"[{gid}] Unable to read game file: {exc}.")
            continue
        expected_size = format_size(len(game_bytes))
        if item.get("size") != expected_size:
            fail(f"[{gid}] size metadata is {item.get('size')!r}; expected {expected_size!r}.")
        if item.get("sizeBytes") != len(game_bytes):
            fail(f"[{gid}] sizeBytes metadata is {item.get('sizeBytes')!r}; expected {len(game_bytes)}.")
        actual_artifact_sha256 = hashlib.sha256(game_bytes).hexdigest()
        if item.get("artifactSha256") != actual_artifact_sha256:
            fail(f"[{gid}] artifactSha256 does not match the exact game-file bytes.")
        prompt_value = item.get("prompt")
        if isinstance(prompt_value, str):
            actual_prompt_sha256 = hashlib.sha256(prompt_value.encode("utf-8")).hexdigest()
            if item.get("promptSha256") != actual_prompt_sha256:
                fail(f"[{gid}] promptSha256 does not match the exact UTF-8 prompt string.")
        try:
            expected_lines = count_lines(game_bytes)
        except UnicodeDecodeError as exc:
            fail(f"[{gid}] Game file is not valid UTF-8 text: {exc}.")
            expected_lines = None
        if expected_lines is not None and item.get("lines") != expected_lines:
            fail(f"[{gid}] lines metadata is {item.get('lines')!r}; expected {expected_lines}.")

        if actual_preview.is_file():
            try:
                dimensions = png_dimensions(actual_preview.read_bytes())
            except OSError as exc:
                dimensions = None
                fail(f"[{gid}] Unable to read preview: {exc}.")
            if dimensions is None:
                fail(f"[{gid}] Preview must be a valid PNG image.")
            elif dimensions != PREVIEW_SIZE:
                fail(f"[{gid}] Preview dimensions are {dimensions}; expected {PREVIEW_SIZE}.")

        if actual_game.suffix.lower() in {".html", ".htm"}:
            try:
                html = game_bytes.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                fail(f"[{gid}] HTML game is not valid UTF-8 text: {exc}.")
                continue
            for finding in inspect_html(html, node_executable=node_executable):
                if benchmark_status == "excluded" and "syntax error" not in finding.lower():
                    warn(f"[{gid}] Declared excluded; runtime dependency finding: {finding}.")
                else:
                    fail(f"[{gid}] Disqualified: {finding}.")

    emit(
        f"Scanned {display_active} visible entr{'y' if display_active == 1 else 'ies'} "
        f"({eligible} eligible, {excluded} excluded).",
        "INFO",
    )
    if errors == 0:
        emit(f"Validation passed with {warnings} warning(s).", "PASS")
    else:
        emit(f"Validation failed with {errors} error(s) and {warnings} warning(s).", "FAIL")
    return {"errors": errors, "warnings": warnings, "active": display_active, "eligible": eligible, "excluded": excluded}


def validate() -> int:
    if not DATA_JSON_PATH.is_file():
        log("data.json not found!", "FAIL")
        return 1
    try:
        with DATA_JSON_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        log(f"Unable to load data.json: {exc}", "FAIL")
        return 1
    result = validate_dataset(data, repo_root=REPO_ROOT)
    return 0 if result["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(validate())
