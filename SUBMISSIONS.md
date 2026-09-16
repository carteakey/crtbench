# 📺 CRTBench Submission Guidelines

Thank you for contributing to **CRTBench** (formerly PlumberBench)! This benchmark tracks the state-of-the-art in LLM procedural game generation, 2D physics feel, and 3D spatial projection.

---

## 📜 Golden Rules of CRTBench

To maintain benchmark integrity, all submissions must satisfy the following:

1. **Strict One-Shot Generation**:
   - The game must be produced in **exactly one inference turn** from the model.
   - **Disqualified**: Multi-turn iterative conversations (*"Fix the jumping bug"*, *"Now add sound effects"*).
   - **Disqualified**: Human modifications, formatting touch-ups, or bug fixes. The code committed must be byte-for-byte identical to the model's raw output.
   - **Disqualified**: Agentic tool use during generation (e.g. searching Google, running unit tests, or using code interpreters).

2. **Single-File Self-Contained Artifact**:
   - Web entries must be a single `.html` file with embedded `<style>` and `<script>`.
   - Python entries must be a single self-contained `.py` script (e.g. Pygame).
   - **Zero External Network Dependencies**: No external images, audio `.mp3`/`.wav` files, sprite sheets, or CDN script imports (`<script src="...">`). All visual sprites and audio sounds must be procedurally generated.

3. **Normalized Metadata Taxonomy & Transparency**:
   To keep CRTBench clean, searchable, and professional, submissions must adhere to the following normalization standards:
   - **Inference Harness (`harness`)**: The software runner or agent framework orchestrating inference. Use canonical names only:
     - `Antigravity` (for any runs generated within Antigravity — do *not* append suffixes like "Pro Engine" or "Interactive").
     - `llama.cpp` (for local GGUF runs via llama-server / llama-cli).
     - `vLLM` (for local vLLM serving).
     - `Ollama` (for local Ollama runner).
     - `Frontier API` (for direct vendor API calls to OpenAI, Anthropic, Google, etc.).
   - **Hardware Compute (`hardware`)**: The physical accelerator or cloud execution tier:
     - Local hardware format: `RTX <Model> <VRAM>` (e.g., `RTX 4090 24GB`, `RTX 3070 8GB`, `Framework Desktop`, `Apple Silicon M3 Max 128GB`).
     - Cloud frontier format: `Frontier Cloud API`.
     - *Important*: Agent or harness names (like `Antigravity`) belong in `harness`, NEVER in `hardware`.
   - **Reasoning / Thinking Effort (`thinkingEffort`)**: Standardized deliberation taxonomy:
     - `Standard One-Shot` (for non-reasoning or standard zero-shot prompts).
     - `<N>k CoT Budget` (for models with explicit token deliberation caps, e.g. `10k CoT Budget`, `60k CoT Deliberation`).
     - `High CoT Deliberation` / `Light Reasoning CoT` (for tiered reasoning levels).
   - **Model License (`license` & `isOpenSource`)**:
     - `open` (`isOpenSource: true`) for open-weights models runnable on consumer GPUs.
     - `proprietary` (`isOpenSource: false`) for closed frontier API models.

4. **Creative Title Policy (No Trademark Names in Title)**:
   - Do **not** include "Mario" or other trademarked names in your submission's title.
   - Use creative, distinct titles (e.g. *Three Worlds Odyssey*, *Super Pixel Bros*, *The 2.6k Deluxe Platformer*, *The Matrix Bros*, *Circus Jumper*). The prompt itself may mention the benchmark prompt as-is.

---

## 📝 Recommended Benchmark Prompts

You can use any single prompt, but for direct comparability across models, we recommend one of these three standardized prompts:

### 1. The Zero-Shot Minimal Standard
```text
Write a complete, playable Super Mario clone in a single file. Include running, jumping physics, platforms, blocks, and enemies.
```

### 2. The Strict NES Specification (ChopSticks Style)
```text
Write a fully functional, complete clone of Super Mario Bros game (the famous NES game)
- Clone must work in a web browser, index.html, no server
- Decent replica of the graphics assets.
- Colorful and playable.
- Controls with keyboard up, down, left, right, spacebar to jump, shift to speed up
```

### 3. The Deliberation Budget Standard (Potato / cc8.pl Style)
```text
Make a side-scrolling platformer game like Super Mario Bros. using HTML/CSS/JS in a single HTML file. Plan the implementation briefly within the reasoning budget. Then output only the complete HTML file. Do not use tools or provide explanations.
```

---

## 📦 Three Ways to Submit

### Option 1: In-Browser Submission Studio (Recommended)
1. Open the [PlumberBench Web App](https://kartikeychauhan.github.io/plumberbench/) or run locally via `python3 -m http.server 8000`.
2. Click **`➕ Submit Run`** in the top navigation bar.
3. Fill in your model, hardware, prompt, and paste your single-file HTML code.
4. Click **`🛡️ Run Preflight Validation`** — the studio checks for external dependencies, computes code size/lines, and formats the entry.
5. Click **`📋 Copy data.json Entry`** and open a pull request!

---

### Option 2: Automated CLI Submission Tool
Use the bundled Python submission script to automatically copy files, take a headless preview screenshot, and validate:
```bash
python3 scripts/submit.py \
  --file path/to/your_game.html \
  --id my_model_quest \
  --title "Kingdom Jumper" \
  --author "u/YourHandle" \
  --model "MyModel-70B-Instruct" \
  --harness "llama.cpp Master" \
  --effort "60k CoT Deliberation" \
  --hardware "Local RTX 4090 24GB" \
  --source "https://reddit.com/r/LocalLLaMA/..." \
  --prompt "Write a complete, playable Super Mario clone in a single file..."
```

---

### Option 3: Manual Pull Request
1. Fork the repository and create a branch (`git checkout -b submit/my-model-mario`).
2. Add your raw game file to `games/<id>.html`.
3. Take a preview screenshot and save it to `previews/<id>.png` (recommended 960x600).
4. Add your entry to `data.json` matching the schema above.
5. Run the validator:
   ```bash
   python3 scripts/validate.py
   ```
6. Commit, push, and open a Pull Request! All PRs are automatically tested via GitHub Actions CI (`.github/workflows/validate-submission.yml`).

