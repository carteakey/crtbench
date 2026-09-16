#!/usr/bin/env python3
"""
CRTBench Submission & Dataset Validator
Ensures benchmark integrity:
1. data.json schema validation
2. Game file existence and self-containment (zero external network assets)
3. JavaScript syntax verification
4. Preview screenshot verification
"""

import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON_PATH = os.path.join(REPO_ROOT, "data.json")
GAMES_DIR = os.path.join(REPO_ROOT, "games")
PREVIEWS_DIR = os.path.join(REPO_ROOT, "previews")

REQUIRED_FIELDS = [
    "id", "title", "author", "category", "badge", "file",
    "vibeScore", "size", "lines", "hardware", "model",
    "promptStyle", "prompt", "sourceName", "sourceUrl",
    "ratings", "elo", "matches", "preview", "hidden", "genre"
]

FORBIDDEN_EXTERNAL_PATTERNS = [
    re.compile(r'<script\s+[^>]*src=["\'](http|\/\/)', re.IGNORECASE),
    re.compile(r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*href=["\'](http|\/\/)', re.IGNORECASE),
    re.compile(r'<img\s+[^>]*src=["\'](http|\/\/)', re.IGNORECASE),
    re.compile(r'<audio\s+[^>]*src=["\'](http|\/\/)', re.IGNORECASE),
]

def log(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "PASS": "\033[92m",
        "WARN": "\033[93m",
        "FAIL": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}[{status}]{colors['RESET']} {msg}")

def validate():
    errors = 0
    warnings = 0

    log("Validating CRTBench dataset and game implementations...", "INFO")

    if not os.path.exists(DATA_JSON_PATH):
        log("data.json not found!", "FAIL")
        return 1

    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            log(f"Invalid JSON format in data.json: {e}", "FAIL")
            return 1

    log(f"Found {len(data)} total entries in data.json", "INFO")

    active_count = 0
    for idx, item in enumerate(data):
        gid = item.get("id", f"entry_{idx}")
        # 1. Field validation
        for field in REQUIRED_FIELDS:
            if field not in item:
                log(f"[{gid}] Missing required field: '{field}'", "FAIL")
                errors += 1

        # 2. File validation
        game_rel_path = item.get("file", "")
        game_abs_path = os.path.join(REPO_ROOT, game_rel_path)
        if not os.path.exists(game_abs_path):
            log(f"[{gid}] Game file does not exist: {game_rel_path}", "FAIL")
            errors += 1
            continue

        # 3. Hidden check
        if item.get("hidden"):
            log(f"[{gid}] Archived / Hidden entry ({game_rel_path})", "INFO")
            continue

        active_count += 1

        # 4. Preview validation
        preview_rel_path = item.get("preview", "")
        preview_abs_path = os.path.join(REPO_ROOT, preview_rel_path)
        if not os.path.exists(preview_abs_path):
            log(f"[{gid}] Preview image missing: {preview_rel_path}", "FAIL")
            errors += 1

        # 5. External asset check (HTML games only)
        if game_abs_path.endswith(".html"):
            with open(game_abs_path, "r", encoding="utf-8", errors="ignore") as gf:
                content = gf.read()

            # Check external script / image / audio tags
            for pat in FORBIDDEN_EXTERNAL_PATTERNS:
                matches = pat.findall(content)
                if matches:
                    log(f"[{gid}] Disqualified: External network asset detected in {game_rel_path}", "FAIL")
                    errors += 1

            # Check JS syntax via node
            js_script_match = re.search(r'<script(?:\s+type=["\']text/javascript["\'])?>([\s\S]*?)<\/script>', content, re.IGNORECASE)
            if js_script_match:
                script_body = js_script_match.group(1)
                proc = subprocess.run(
                    ["node", "-e", "new Function(process.argv[1]);", script_body],
                    capture_output=True,
                    text=True
                )
                if proc.returncode != 0:
                    log(f"[{gid}] JavaScript syntax error in {game_rel_path}: {proc.stderr.strip()}", "FAIL")
                    errors += 1

    if errors == 0:
        log(f"All {active_count} active entries passed validation with zero errors! 🎉", "PASS")
        return 0
    else:
        log(f"Validation failed with {errors} error(s).", "FAIL")
        return 1

if __name__ == "__main__":
    sys.exit(validate())
