import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import submit  # noqa: E402
import validate  # noqa: E402


def make_png(width=960, height=600):
    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = (b"\x00" + b"\x00" * (width * 4)) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def make_entry(root: Path, game_html="<!doctype html>\n<p>ok</p>\n", entry_id="test_game"):
    games = root / "games"
    previews = root / "previews"
    games.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)
    game_path = games / f"{entry_id}.html"
    preview_path = previews / f"{entry_id}.png"
    game_bytes = game_html.encode("utf-8")
    prompt = "Build a tiny game exactly as requested."
    game_path.write_bytes(game_bytes)
    preview_path.write_bytes(make_png())
    return {
        "id": entry_id,
        "title": "Test Game",
        "author": "Tester",
        "category": "Platformer",
        "badge": "Test",
        "file": f"games/{entry_id}.html",
        "vibeScore": 8.0,
        "vibeScoreType": "editorial",
        "size": validate.format_size(len(game_bytes)),
        "sizeBytes": len(game_bytes),
        "lines": validate.count_lines(game_bytes),
        "hardware": "API",
        "model": "Test Model",
        "harness": "API",
        "thinkingEffort": "None",
        "quant": "N/A",
        "promptStyle": "Community Submission",
        "prompt": prompt,
        "sourceName": "Test Source",
        "sourceUrl": "https://example.com/source",
        "ratings": {"nesCrunch": 8.0, "physicsFeel": 8.0, "ambition": 8.0},
        "elo": 1200,
        "matches": 0,
        "preview": f"previews/{entry_id}.png",
        "hidden": False,
        "genre": "platformer",
        "license": "proprietary",
        "isOpenSource": False,
        "modelAccess": "proprietary",
        "weightsLicense": None,
        "artifactLicense": None,
        "artifactSha256": hashlib.sha256(game_bytes).hexdigest(),
        "promptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.entry = make_entry(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def validate(self, data):
        messages = []
        result = validate.validate_dataset(data, self.root, emit=lambda message, status: messages.append((status, message)))
        return result, messages

    def test_valid_entry_checks_sizes_hashes_and_png(self):
        result, _ = self.validate([self.entry])
        self.assertEqual(result["errors"], 0)
        self.assertEqual(validate.png_dimensions((self.root / self.entry["preview"]).read_bytes()), (960, 600))

    def test_rejects_duplicate_ids_invalid_enums_and_metadata(self):
        invalid = copy.deepcopy(self.entry)
        invalid["genre"] = "doom"
        invalid["lines"] = "two"
        duplicate = copy.deepcopy(self.entry)
        result, messages = self.validate([invalid, duplicate])
        self.assertGreaterEqual(result["errors"], 3)
        text = "\n".join(message for _, message in messages)
        self.assertIn("Duplicate id", text)
        self.assertIn("genre must be one of", text)
        self.assertIn("lines must be a non-negative integer", text)

    def test_path_traversal_is_rejected_even_for_hidden_entries(self):
        hidden = copy.deepcopy(self.entry)
        hidden["hidden"] = True
        hidden["file"] = "games/../outside.html"
        result, messages = self.validate([hidden])
        self.assertGreater(result["errors"], 0)
        self.assertTrue(any("traversal" in message for _, message in messages))

    def test_hidden_entry_skips_missing_artifacts_but_keeps_schema_checks(self):
        hidden = copy.deepcopy(self.entry)
        hidden["hidden"] = True
        hidden["file"] = "games/removed.html"
        hidden["preview"] = "previews/removed.png"
        result, _ = self.validate([hidden])
        self.assertEqual(result["errors"], 0)

    def test_google_fonts_are_allowed_only_on_font_endpoints(self):
        html = """<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P" rel="stylesheet">
<link crossorigin href="https://fonts.gstatic.com" rel="preconnect">
<style>@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P');
@font-face { src: url(https://fonts.gstatic.com/s/font/v1/font.woff2); }</style>"""
        self.assertEqual(validate.inspect_html(html), [])
        bad = "<style>@import url('https://evil.example/font.css');</style>"
        self.assertTrue(validate.inspect_html(bad))
        wrong_google_path = "<style>.x{background:url(https://fonts.gstatic.com/images/bg.png)}</style>"
        self.assertTrue(validate.inspect_html(wrong_google_path))

    def test_detects_external_tags_css_and_network_apis_with_attribute_order_variants(self):
        html = """<script defer src="https://evil.example/app.js"></script>
<img alt="x" src="https://evil.example/image.png">
<video poster="https://evil.example/poster.png"></video>
<source type="audio/ogg" src="//evil.example/audio.ogg">
<iframe title="x" src="https://evil.example/frame"></iframe>
<object data="https://evil.example/app.bin"></object>
<embed src="https://evil.example/plugin.bin">
<style>.x { background: url(https://evil.example/bg.png); }</style>
<script>fetch('/endpoint');</script>"""
        findings = validate.inspect_html(html)
        self.assertGreaterEqual(len(findings), 9)
        self.assertTrue(any("fetch()" in finding for finding in findings))

    def test_checks_every_inline_script_and_ignores_comments(self):
        broken = "<script>const first = 1;</script><script>const second = ;</script>"
        findings = validate.inspect_html(broken)
        self.assertEqual(sum("syntax error" in finding for finding in findings), 1)
        commented = "<script>/* fetch('/endpoint'); */ const ok = 1;</script>"
        self.assertEqual(validate.inspect_html(commented), [])


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        (self.repo / "games").mkdir(parents=True)
        (self.repo / "previews").mkdir()
        (self.repo / "data.json").write_text("[]\n", encoding="utf-8")
        self.source = self.root / "source.html"
        self.source_bytes = b"<!doctype html>\n<p>byte exact</p>\n"
        self.source.write_bytes(self.source_bytes)
        self.overrides = (
            submit.REPO_ROOT,
            submit.DATA_JSON_PATH,
            submit.GAMES_DIR,
            submit.PREVIEWS_DIR,
        )
        submit.REPO_ROOT = self.repo
        submit.DATA_JSON_PATH = self.repo / "data.json"
        submit.GAMES_DIR = self.repo / "games"
        submit.PREVIEWS_DIR = self.repo / "previews"

    def tearDown(self):
        (submit.REPO_ROOT, submit.DATA_JSON_PATH, submit.GAMES_DIR, submit.PREVIEWS_DIR) = self.overrides
        self.temp.cleanup()

    def args(self, *extra):
        return [
            "--file", str(self.source), "--id", "new_entry", "--title", "New Entry",
            "--author", "Tester", "--model", "Test Model", "--license", "proprietary",
            "--source", "https://example.com/run", "--prompt", "Exact prompt text.",
            *extra,
        ]

    def test_rejects_path_traversal_and_missing_open_weight_metadata(self):
        self.assertNotEqual(submit.main(self.args("--id", "../escape")), 0)
        open_weight_args = self.args("--license", "open")
        self.assertNotEqual(submit.main(open_weight_args), 0)
        self.assertEqual((self.repo / "data.json").read_text(encoding="utf-8"), "[]\n")

    def test_missing_screenshot_fails_without_repository_mutation(self):
        real_which = submit.shutil.which
        with mock.patch.object(submit.shutil, "which", side_effect=lambda name: "/usr/bin/firefox" if name == "firefox" else real_which(name)), \
             mock.patch.object(submit.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="", stderr="")):
            result = submit.main(self.args())
        self.assertNotEqual(result, 0)
        self.assertEqual((self.repo / "data.json").read_text(encoding="utf-8"), "[]\n")
        self.assertFalse((self.repo / "games/new_entry.html").exists())
        self.assertFalse((self.repo / "previews/new_entry.png").exists())

    def test_successful_submit_preserves_game_bytes_and_hashes(self):
        real_which = submit.shutil.which
        real_run = submit.subprocess.run

        def fake_run(command, **kwargs):
            if command[0] == "/usr/bin/firefox":
                screenshot_path = Path(command[command.index("--screenshot") + 1])
                screenshot_path.write_bytes(make_png())
                return mock.Mock(returncode=0, stdout="", stderr="")
            return real_run(command, **kwargs)

        with mock.patch.object(submit.shutil, "which", side_effect=lambda name: "/usr/bin/firefox" if name == "firefox" else real_which(name)), \
             mock.patch.object(submit.subprocess, "run", side_effect=fake_run):
            result = submit.main(self.args())

        self.assertEqual(result, 0)
        game_path = self.repo / "games/new_entry.html"
        self.assertEqual(game_path.read_bytes(), self.source_bytes)
        saved = json.loads((self.repo / "data.json").read_text(encoding="utf-8"))[0]
        self.assertEqual(saved["sizeBytes"], len(self.source_bytes))
        self.assertEqual(saved["artifactSha256"], hashlib.sha256(self.source_bytes).hexdigest())
        self.assertEqual(saved["promptSha256"], hashlib.sha256(b"Exact prompt text.").hexdigest())


if __name__ == "__main__":
    unittest.main()
