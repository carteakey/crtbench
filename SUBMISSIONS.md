# 📺 CRTBench Submission Guide

Bring a game, give it a good title, and tell us how it came to be. CRTBench is a community showcase as much as a benchmark, so prompts, models, harnesses, and hardware will vary. We keep the flavor; we try to keep the metadata honest.

## 🕹️ What belongs in the active roster?

The active browser roster is for single-file games generated in one model response. There is no canonical prompt: include the exact prompt used for your run, including any system prompt or relevant reasoning instructions you can share. If you made edits after generation, say so. One-shot and hardware details are contributor-reported; CRTBench does not independently reproduce every run.

Browser entries should be self-contained `.html` files with embedded style and game code. Generate art and sound in the file, or bundle them into it. External game images, audio files, sprite sheets, scripts, and runtime libraries are not allowed. **Google Fonts are okay**; a Google Fonts import does not make a game ineligible.

Keep the committed game artifact exactly as submitted when you are claiming an unedited model output. If a generated file needed fixes or cleanup, disclose that plainly rather than calling it raw output. Python and other interesting experiments may be preserved in the repository, but the active browser roster is for browser-playable entries.

## 🧾 Metadata: useful, not precious

Add one object to `data.json` and a file under `games/`. Keep field names and categories consistent so the cabinet stays searchable.

- **Title and author:** Give the game a memorable name and credit the author or submitter as they want to appear.
- **Track (`genre`):** Use `platformer`, `raycaster`, `maze`, or `puzzle` for the current cabinets.
- **Prompt:** Store the prompt actually used, not a standardized rewrite. Different prompts are expected.
- **Model and access (`model`, `modelAccess`):** Record the model name and use `open_weights` or `proprietary`. “Open weights” describes model access; it does not establish an open-source license.
- **Weights license (`weightsLicense`):** Give the exact license only when the model/version is known. Use `null` when it is unknown or not applicable; do not infer it from “open weights.”
- **Artifact license (`artifactLicense`):** The game file's license is separate from the model weights license. Record a contributor-provided license or use `null` if it was not supplied. The repository's MIT license does not fill in missing per-artifact or model-license information.
- **Harness (`harness`):** Use `Antigravity`, `llama.cpp`, `vLLM`, `Ollama`, or `API` when applicable. Harness is the software that ran the model.
- **Hardware (`hardware`):** For API-hosted models, use `API`. For local inference, name the physical machine or accelerator (for example, `RTX 4090 24GB`, `RTX 3070 8GB`, or `Framework Desktop`).
- **Reasoning effort (`thinkingEffort`):** Use `None`, `Light`, `Medium`, `High`, or `Ultra` when known. Preserve the actual setting as best you can; do not estimate a token budget from the tier name.
- **Quantization (`quant`):** Record the format for open-weight runs (for example, `Q4_K_M`, `UD-Q3_K_XL`, `FP8`, or `AD-4.27bpw`); use `N/A` when not applicable.
- **Source link (`sourceUrl` / `sourceName`):** Link the specific post, demo, or repository when available. If the only link is a general forum page or the committed artifact itself, label it that way. Links are contributor-supplied references, not independent verification.
- **Size and integrity (`sizeBytes`, `size`, `lines`, `artifactSha256`, `promptSha256`):** `sizeBytes` is the exact file byte count; `size` is the display size in 1024-byte units; `lines` counts decoded text lines. `artifactSha256` hashes the raw file bytes, and `promptSha256` hashes the exact UTF-8 prompt string. Refresh them whenever the file or prompt changes.
- **Benchmark status (`benchmarkStatus`, `benchmarkStatusReason`):** The submission helper starts entries as `eligible`. If an entry is kept for reference but excluded from the active roster, set `excluded` and give the reason; active entries remain eligible.

The compatibility fields `license` (`open` or `proprietary`) and `isOpenSource` remain for the current site and validator. They are legacy access-category flags, not the legal license of model weights or game code. Use the explicit fields above for any actual license names.

`vibeScoreType` labels the `vibeScore`: use `editorial` for a curator's note; use `community` only for a real shared community rating. The current `vibeScore`, `ratings`, and `vibeReview` values are editorial, not community votes. Each browser starts a game's local **Duel Elo** at 1200 and shows ranks immediately. Votes and Elo changes live in that browser's local storage; they are not aggregated across visitors. No minimum-match cutoff is used, so early ranks are just for fun. The site's MIT-licensed source and each game's license are separate questions.

## 📦 Submit a run

### Option 1: Browser submission studio

1. Open the [CRTBench web app](https://carteakey.github.io/crtbench/) or start it locally with `python3 -m http.server 8000`.
2. Click **➕ Submit Run**.
3. Enter the model, prompt, harness, hardware, and links you know; paste the one-file game.
4. Run preflight to check the artifact and prepare a `data.json` entry.
5. Open a pull request with the game, metadata, and (if available) a preview image.

### Option 2: CLI helper

The helper can copy a file, make a preview, and prepare metadata. Check the flags with:

```bash
python3 scripts/submit.py --help
```

### Option 3: Pull request

1. Fork the repo and create a branch.
2. Add the artifact at `games/<id>.html` and an optional preview at `previews/<id>.png`.
3. Add the corresponding metadata object to `data.json`.
4. Run `python3 scripts/validate.py` locally.
5. Open a pull request; GitHub Actions runs the validator.

Thanks for adding another cabinet to the arcade. 🎮
