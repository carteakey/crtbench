#!/usr/bin/env python3
"""Stage, validate, and atomically add a CRTBench game submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import validate as dataset_validator

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON_PATH = REPO_ROOT / "data.json"
GAMES_DIR = REPO_ROOT / "games"
PREVIEWS_DIR = REPO_ROOT / "previews"
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Submit a one-shot game artifact to CRTBench")
    parser.add_argument("--file", required=True, help="Path to the raw HTML game file")
    parser.add_argument("--id", required=True, help="Unique safe identifier, e.g. model_run_01")
    parser.add_argument("--title", required=True, help="Game display title")
    parser.add_argument("--genre", choices=sorted(dataset_validator.CANONICAL_GENRES), default="platformer")
    parser.add_argument("--license", choices=["open", "proprietary"], default="open", help="Model access category")
    parser.add_argument("--weights-license", default=None, help="Model weights license, if known")
    parser.add_argument("--artifact-license", default=None, help="Generated game artifact license, if known")
    parser.add_argument("--author", required=True, help="Author name or handle")
    parser.add_argument("--model", required=True, help="Model identifier")
    parser.add_argument("--harness", default="llama.cpp", choices=sorted(dataset_validator.CANONICAL_HARNESSES))
    parser.add_argument("--effort", default="None", choices=sorted(dataset_validator.CANONICAL_REASONING_TIERS))
    parser.add_argument("--hardware", default="", help="Physical accelerator for open-weight models")
    parser.add_argument("--quant", default="", help="Quantization for open-weight models")
    parser.add_argument("--source", required=True, help="Source URL for this run")
    parser.add_argument("--prompt", required=True, help="Exact prompt fed to the model")
    parser.add_argument("--category", default="NES Purist")
    parser.add_argument("--badge", default="Community Submission")
    parser.add_argument("--demo", default="", help="Optional live web demo URL")
    parser.add_argument("--vibe", type=float, default=8.5, help="Editorial vibe score (1.0–10.0)")
    parser.add_argument("--force", action="store_true", help="Replace an existing ID or output file")
    return parser


def _is_http_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def _load_data(path: Path) -> tuple[list[dict], str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return [], f"Unable to read existing data.json: {exc}"
    if not isinstance(value, list):
        return [], "Existing data.json must contain a top-level array."
    if any(not isinstance(entry, dict) for entry in value):
        return [], "Every existing data.json entry must be an object."
    return value, None


def _normalized_relpath(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return value


def _check_collisions(args: argparse.Namespace, data: list[dict], game_path: Path, preview_path: Path) -> str | None:
    destination_game = f"games/{args.id}.html"
    destination_preview = f"previews/{args.id}.png"
    duplicate_ids = [entry for entry in data if entry.get("id") == args.id]
    duplicate_files = [
        entry for entry in data
        if _normalized_relpath(entry.get("file")) == destination_game
        or _normalized_relpath(entry.get("preview")) == destination_preview
    ]
    existing_outputs = [path for path in (game_path, preview_path) if path.exists()]
    collisions = []
    if duplicate_ids:
        collisions.append("an existing data entry has this ID")
    if duplicate_files:
        collisions.append("an existing data entry references this output file")
    if existing_outputs:
        collisions.append("an output file already exists on disk")
    if collisions and not args.force:
        return "; ".join(collisions) + ". Pass --force to replace the existing target."
    return None


def _write_sibling_temp(target: Path, contents: bytes) -> Path:
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.submit-", dir=str(target.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
        os.chmod(temp_path, mode)
        return temp_path
    except BaseException:
        try:
            temp_path.unlink(missing_ok=True)
        finally:
            raise


def _atomic_commit(files: list[tuple[Path, bytes]], expected_game: tuple[Path, bytes]) -> None:
    """Replace destination files together as closely as the filesystem permits."""
    originals: dict[Path, bytes | None] = {}
    staged: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for target, contents in files:
            if not target.parent.is_dir():
                raise OSError(f"destination directory does not exist: {target.parent}")
            originals[target] = target.read_bytes() if target.is_file() else None
            staged[target] = _write_sibling_temp(target, contents)

        # Keep the index update last so readers never see a record before its artifacts.
        for target, _ in files:
            os.replace(staged[target], target)
            staged.pop(target, None)
            replaced.append(target)

        game_path, expected_bytes = expected_game
        if game_path.read_bytes() != expected_bytes:
            raise OSError("committed game file is not byte-identical to the submitted source")
    except BaseException:
        for target in reversed(replaced):
            previous = originals[target]
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    restore = _write_sibling_temp(target, previous)
                    os.replace(restore, target)
            except OSError:
                # Keep the original exception visible; restoration issues are reported separately.
                print(f"Warning: could not restore {target} after an interrupted submission.", file=sys.stderr)
        raise
    finally:
        for temp_path in staged.values():
            temp_path.unlink(missing_ok=True)


def _make_entry(args: argparse.Namespace, game_bytes: bytes, preview_rel_path: str) -> dict:
    open_weights = args.license == "open"
    hardware = args.hardware.strip() if open_weights else "API"
    quant = args.quant.strip() if open_weights else "N/A"
    access = "open_weights" if open_weights else "proprietary"
    prompt_sha256 = hashlib.sha256(args.prompt.encode("utf-8")).hexdigest()
    entry = {
        "id": args.id,
        "title": args.title.strip(),
        "genre": args.genre,
        "license": args.license,
        "isOpenSource": open_weights,
        "modelAccess": access,
        "weightsLicense": args.weights_license.strip() if args.weights_license and args.weights_license.strip() else None,
        "artifactLicense": args.artifact_license.strip() if args.artifact_license and args.artifact_license.strip() else None,
        "author": args.author.strip(),
        "category": args.category.strip(),
        "badge": args.badge.strip(),
        "file": f"games/{args.id}.html",
        "baseVotes": 0,
        "vibeScore": args.vibe,
        "vibeScoreType": "editorial",
        "size": dataset_validator.format_size(len(game_bytes)),
        "sizeBytes": len(game_bytes),
        "lines": dataset_validator.count_lines(game_bytes),
        "artifactSha256": hashlib.sha256(game_bytes).hexdigest(),
        "promptSha256": prompt_sha256,
        "hardware": hardware,
        "model": args.model.strip(),
        "harness": args.harness,
        "thinkingEffort": args.effort,
        "quant": quant,
        "mode": args.effort,
        "promptStyle": "Community Submission",
        "prompt": args.prompt,
        "sourceName": "Community Submission",
        "sourceUrl": args.source.strip(),
        "vibeReview": f"One-shot {args.genre} generated by {args.model.strip()} via {args.harness} on {hardware}.",
        "ratings": {"nesCrunch": 8.0, "physicsFeel": 8.5, "ambition": 8.5},
        "elo": 1200,
        "matches": 0,
        "wins": 0,
        "preview": preview_rel_path,
        "hidden": False,
        "benchmarkStatus": "eligible",
    }
    if args.demo.strip():
        entry["demoUrl"] = args.demo.strip()
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    def fail(message: str) -> int:
        print(f"Error: {message}", file=sys.stderr)
        return 1

    if not SAFE_ID_RE.fullmatch(args.id):
        return fail(f"ID must match {SAFE_ID_RE.pattern!r}; path separators and traversal are not allowed.")
    if not args.title.strip() or not args.author.strip() or not args.model.strip() or not args.prompt.strip():
        return fail("title, author, model, and prompt must not be blank.")
    if not 1 <= args.vibe <= 10:
        return fail("vibe score must be between 1.0 and 10.0.")
    if not _is_http_url(args.source):
        return fail("source must be an absolute HTTP(S) URL.")
    if args.demo and not _is_http_url(args.demo):
        return fail("demo must be an absolute HTTP(S) URL.")

    if args.license == "open":
        hardware = args.hardware.strip()
        quant = args.quant.strip()
        if not hardware or hardware.upper() == "API" or "cloud" in hardware.lower():
            return fail("open-weight submissions require physical --hardware (for example, 'RTX 4090 24GB').")
        if not quant or quant.upper() == "N/A":
            return fail("open-weight submissions require --quant (for example, Q4_K_M or FP8).")

    source_path = Path(args.file).expanduser()
    if not source_path.is_file():
        return fail(f"game file does not exist or is not a regular file: {source_path}")
    if source_path.suffix.lower() not in {".html", ".htm"}:
        return fail("--file must point to an HTML game file.")
    try:
        source_bytes = source_path.read_bytes()
        dataset_validator.count_lines(source_bytes)
    except (OSError, UnicodeDecodeError) as exc:
        return fail(f"could not read the submitted game as UTF-8 text: {exc}")

    data, load_error = _load_data(DATA_JSON_PATH)
    if load_error:
        return fail(load_error)

    game_rel_path = f"games/{args.id}.html"
    preview_rel_path = f"previews/{args.id}.png"
    dest_game = GAMES_DIR / f"{args.id}.html"
    dest_preview = PREVIEWS_DIR / f"{args.id}.png"
    collision_error = _check_collisions(args, data, dest_game, dest_preview)
    if collision_error:
        return fail(collision_error)

    firefox = shutil.which("firefox")
    if firefox is None:
        return fail("Firefox is required to create the preview screenshot.")

    with tempfile.TemporaryDirectory(prefix="crtbench-submit-") as temp_name:
        stage_root = Path(temp_name)
        staged_game = stage_root / "games" / f"{args.id}.html"
        staged_preview = stage_root / "previews" / f"{args.id}.png"
        profile_dir = stage_root / "firefox-profile"
        staged_game.parent.mkdir()
        staged_preview.parent.mkdir()
        shutil.copyfile(source_path, staged_game)
        if staged_game.read_bytes() != source_bytes:
            return fail("staging changed the submitted game bytes.")

        firefox_cmd = [
            firefox,
            "--headless",
            "--no-remote",
            "--profile", str(profile_dir),
            "--screenshot", str(staged_preview),
            "--window-size=960,600",
            staged_game.resolve().as_uri(),
        ]
        try:
            screenshot = subprocess.run(
                firefox_cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return fail(f"Firefox could not capture the preview: {exc}")

        if not staged_preview.is_file() or staged_preview.stat().st_size == 0:
            detail = (screenshot.stderr or screenshot.stdout).strip()
            return fail("preview screenshot was not created" + (f": {detail}" if detail else "."))
        preview_dimensions = dataset_validator.png_dimensions(staged_preview.read_bytes())
        if preview_dimensions != dataset_validator.PREVIEW_SIZE:
            return fail(f"preview must be a valid {dataset_validator.PREVIEW_SIZE[0]}x{dataset_validator.PREVIEW_SIZE[1]} PNG; got {preview_dimensions}.")

        new_entry = _make_entry(args, source_bytes, preview_rel_path)
        # --force replaces the matching record; any other records are preserved.
        updated_data = [entry for entry in data if entry.get("id") != args.id]
        updated_data.append(new_entry)
        json_bytes = (json.dumps(updated_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

        result = dataset_validator.validate_dataset(
            updated_data,
            repo_root=REPO_ROOT,
            path_overrides={
                dest_game.resolve(strict=False): staged_game,
                dest_preview.resolve(strict=False): staged_preview,
            },
        )
        if result["errors"]:
            return fail("staged submission failed dataset validation; repository files were not changed.")

        try:
            _atomic_commit(
                [
                    (dest_game, staged_game.read_bytes()),
                    (dest_preview, staged_preview.read_bytes()),
                    (DATA_JSON_PATH, json_bytes),
                ],
                expected_game=(dest_game, source_bytes),
            )
        except OSError as exc:
            return fail(f"could not commit the validated submission: {exc}")

    print("\nSubmission added and validated.")
    print(f"  Game ID: {args.id}")
    print(f"  Game file: {game_rel_path}")
    print(f"  Preview: {preview_rel_path}")
    print("\nNext steps:")
    print(f"  git add data.json {game_rel_path} {preview_rel_path}")
    print(f"  git commit -m 'feat: submit {args.model.strip()} {args.genre} game'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
