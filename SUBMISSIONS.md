# 🍄 PlumberBench Submission Guidelines

Thank you for contributing to **PlumberBench**! This benchmark tracks the state-of-the-art in LLM procedural game generation and physical reasoning.

---

## 📜 Golden Rules of PlumberBench

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

3. **Full Hardware & Inference Transparency**:
   - You must disclose:
     - Model Name & Version
     - Quantization / Precision (e.g. `UD-Q4_K_XL`, `Q8_0`, `FP16`, `bfloat16`)
     - Thinking / Reasoning Mode (e.g. CoT token count, reasoning effort)
     - Hardware (e.g. `RTX 3070 8GB`, `RTX 4090 24GB`, `Frontier Cloud API`)
     - Inference Engine (e.g. `llama.cpp`, `vLLM`, `Ollama`, `ExLlamaV2`)

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

## 📦 How to Submit a New Game

1. **Fork the Repository**:
   ```bash
   git clone https://github.com/kartikeychauhan/plumberbench.git
   cd plumberbench
   git checkout -b submit/my-model-mario
   ```

2. **Add Your Raw Game File**:
   Save your raw, unedited model output into `games/<id>.html` (or `games/<id>.py`).

3. **Add Entry to `data.json`**:
   Add an object to `data.json` following this schema:
   ```json
   {
     "id": "unique_model_id",
     "title": "Display Title of the Game",
     "author": "Your Name / Reddit Handle",
     "category": "NES Purist | Modern Indie | Circus Reskin",
     "badge": "Short 2-3 word highlight badge",
     "file": "games/unique_model_id.html",
     "baseVotes": 0,
     "vibeScore": 8.5,
     "size": "45.2 KB",
     "lines": 1200,
     "hardware": "Exact hardware specs",
     "model": "Full model identifier",
     "mode": "CoT budget / tokens / reasoning level",
     "promptStyle": "Minimal Zero-Shot | Strict NES Spec | Deliberation Budget",
     "prompt": "Exact user prompt fed into the model",
     "sourceName": "Reddit thread / benchmark run / blog post",
     "sourceUrl": "URL to original post or verification",
     "demoUrl": "Optional live web deployment URL",
     "vibeReview": "2-3 sentences evaluating gameplay feel, physics, audio, and visual quirks.",
     "ratings": {
       "nesCrunch": 8.5,
       "physicsFeel": 8.5,
       "ambition": 8.5
     },
     "elo": 1200,
     "matches": 0,
     "wins": 0,
     "preview": "previews/unique_model_id.png",
     "hidden": false
   }
   ```

4. **Verify Locally**:
   Run `python3 -m http.server 8000` and confirm your game launches cleanly in the arcade modal, the prompt drawer copies properly, and there are no console errors.

5. **Open a Pull Request**:
   Submit a PR with the title `feat: add <Model Name> Mario implementation`.
