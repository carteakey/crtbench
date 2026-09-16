# 🍄 PlumberBench

> **The One-Shot Retro 2D Platformer Benchmark for Large Language Models**  
> *"Criteria: Strict One-Shot. Scoring: Pure Vibes & Blind ELO Duels."*

[![Leaderboard](https://img.shields.io/badge/PlumberBench-ELO_Leaderboard-e52521?style=for-the-badge&logo=nintendo)](https://github.com/kartikeychauhan/plumberbench)
[![One Shot](https://img.shields.io/badge/Format-Strict_One--Shot-f8c300?style=for-the-badge)](SUBMISSIONS.md)
[![Blind Arena](https://img.shields.io/badge/Vibe_Arena-Blind_Duel_ELO-58a6ff?style=for-the-badge)](index.html)
[![Active Roster](https://img.shields.io/badge/Active_Entries-9_Contenders-2ea043?style=for-the-badge)](games/)
[![Disciplines](https://img.shields.io/badge/Disciplines-Platformer_%7C_Raycaster-8250df?style=for-the-badge)](index.html)

---

## 🎯 The PlumberBench Manifesto

Standard LLM benchmarks (HumanEval, SWE-bench, GSM8K) measure narrow syntax verification or unit test satisfaction. None of them measure **experiential coherence**: can a model produce something that actually *feels good to play*?

PlumberBench evaluates models across multiple fundamental game architecture disciplines:
1. **🏃 2D Platformer Track (Continuous Newtonian Physics):** Bounding-box penetration resolution, jump velocity accumulators, coyote buffer frames, variable jump heights, tilemap collision, and Web Audio chiptune synthesis.
2. **🔫 2.5D Raycaster Track (3D Spatial Geometry & Trigonometry):** DDA (Digital Differential Analysis) grid traversal, ray angle stepping, fish-eye distortion correction ($\text{dist} \times \cos(\theta)$), vertical scanline slicing, and billboard sprite depth-buffering.
3. **👻 Arcade Maze Track (Discrete Graph Traversal - Planned):** Grid containment, intersection decision trees, and ghost AI finite state machines (Chase, Scatter, Frightened).
4. **🧱 Falling Blocks Track (Matrix Transformations - Planned):** 2D matrix rotations, Super Rotation System (SRS) kick tables, and line clearing loops.

---

## ⚡ Active Web Leaderboard (9 Contenders)

All active contenders are strict **single-prompt, single-file HTML/JS/CSS games** with zero dependencies. ELO ratings initialize at baseline **1200** and evolve dynamically through fair **In-Genre Blind Duels**.

| Rank | Contender | Discipline | Model & Harness | Thinking Effort & Hardware | Base ELO | Vibe | Radar (Crunch / Phys / Amb) | Official Source Links |
| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 🥇 | [Three Worlds Odyssey](games/gpt6_astra_high.html) | 🏃 Platformer | **GPT-6 Astra**<br>`Frontier API` | **High Reasoning CoT**<br>`Frontier Cloud API` | **1200** | 9.4 | 7.5 / 9.5 / 9.8 | [Run Artifact](games/gpt6_astra_high.html) |
| 🥈 | [The 2.6k Deluxe Platformer](games/gemini38_flash_full.html) | 🏃 Platformer | **Gemini 3.8 Flash**<br>`Antigravity CLI` | **Full CoT Deliberation**<br>`Antigravity Pro Engine` | **1200** | 9.1 | 9.5 / 9.6 / 9.2 | [Run Artifact](games/gemini38_flash_full.html) |
| 🥉 | [Operation Wolf3D](games/gemini38_pro_wolf_raycaster.html) | 🔫 Raycaster | **Gemini 3.8 Pro**<br>`Antigravity Pro` | **High CoT Deliberation**<br>`Frontier Cloud API` | **1200** | 9.2 | 9.0 / 9.3 / 9.5 | [Run Artifact](games/gemini38_pro_wolf_raycaster.html) |
| 4 | [Super Pixel Bros (Course 1-1)](games/qwen38_flash_3070_potato.html) | 🏃 Platformer | **Qwen3.8-Flash-Next**<br>`llama.cpp (cc8.pl)` | **10k CoT Budget (xhigh)**<br>`RTX 3070 8GB + 80GB DDR4` | **1200** | 8.9 | 9.2 / 8.9 / 8.8 | [Reddit Thread](https://www.reddit.com/r/LocalLLaMA/comments/1wbchyj/qwen38_27b_made_mario_with_a_single_prompt_o/) &bull; [Author's Live Demo](https://www.cc8.pl/mario-q38-flash.html) |
| 5 | [The Matrix Bros (Cyber Edition)](games/ornith35b_matrix_bros.html) | 🏃 Platformer | **Ornith-1.5-35B**<br>`llama.cpp (u/TimelordQ)` | **Direct Zero-Shot**<br>`Local RTX 3090 24GB` | **1200** | 8.8 | 8.8 / 8.7 / 9.3 | [Reddit Thread](https://www.reddit.com/r/LocalLLaMA/comments/1wbchyj/qwen38_27b_made_mario_with_a_single_prompt_o/) &bull; [GitHub Demo](https://timelordq.github.io/The-Matrix-Bros/index.html) |
| 6 | [Qwen 27B Tiiny NES Replica](games/qwen38_27b_chopsticks.html) | 🏃 Platformer | **Qwen3.8-27B**<br>`llama.cpp (u/ChopSticksPlease)` | **Standard One-Shot**<br>`Local RTX 3090 24GB` | **1200** | 8.7 | 9.0 / 8.6 / 8.5 | [Reddit Thread](https://www.reddit.com/r/LocalLLaMA/comments/1wbchyj/qwen38_27b_made_mario_with_a_single_prompt_o/) &bull; [Tiiny Host Demo](https://indigo-carmencita-27.tiiny.site/) |
| 7 | [The 60,000-Token Monolith](games/qwen38_gold_60k.html) | 🏃 Platformer | **Qwen3.8-Flash-Next**<br>`llama.cpp Master (L3MS)` | **60k CoT Deliberation (59m)**<br>`Local RTX 4070 12GB` | **1200** | 8.5 | 9.2 / 8.0 / 9.4 | [L3MS Run](games/qwen38_gold_60k.html) |
| 8 | [Super Meadow: A Little Adventure](games/gpt6_astra_light.html) | 🏃 Platformer | **GPT-6 Astra**<br>`Frontier API` | **Light Reasoning CoT**<br>`Frontier Cloud API` | **1200** | 8.6 | 6.0 / 9.2 / 8.8 | [Run Artifact](games/gpt6_astra_light.html) |
| 9 | [Circus Jumper](games/qwen38_27b_circus_mikenonect.html) | 🏃 Platformer | **Qwen3.8-27B**<br>`llama.cpp (u/MikeNonect)` | **Overnight Batch (Q8)**<br>`Framework Desktop` | **1200** | 8.4 | 5.5 / 8.8 / 9.0 | [Reddit Thread (629 upvotes)](https://www.reddit.com/r/LocalLLaMA/comments/1vp438p/if_you_would_have_told_me_half_a_year_ago_that_a/) &bull; [GitHub Demo](https://mikeveerman.github.io/qwen38-27b-mario) |

---

## 🖼️ Active Gallery Previews

| [GPT-6 Astra High](games/gpt6_astra_high.html) | [Gemini 3.8 Flash Full CoT](games/gemini38_flash_full.html) | [Qwen 3070 Potato Run (cc8.pl)](games/qwen38_flash_3070_potato.html) |
| :---: | :---: | :---: |
| ![Astra High](previews/gpt6_astra_high.png) | ![Gemini Full](previews/gemini38_flash_full.png) | ![Qwen Potato](previews/qwen38_flash_3070_potato.png) |
| **Three Worlds Edition** | **2.6k Deluxe NES Physics** | **RTX 3070 8GB Potato** |

| [The Matrix Bros (Ornith 35B)](games/ornith35b_matrix_bros.html) | [Qwen 27B Tiiny (ChopSticks)](games/qwen38_27b_chopsticks.html) | [Operation Wolf3D (Gemini Pro)](games/gemini38_pro_wolf_raycaster.html) |
| :---: | :---: | :---: |
| ![Matrix Bros](previews/ornith35b_matrix_bros.png) | ![ChopSticks](previews/qwen38_27b_chopsticks.png) | ![Operation Wolf3D](previews/gemini38_pro_wolf_raycaster.png) |
| **Cyber Katakana Rain** | **ChopSticks NES Replica** | **3D DDA Raycaster FPS** |

---

## ⚔️ The Blind Vibe Arena

To guarantee objective evaluations without brand or parameter bias, the **`⚔️ Blind Vibe Arena`** hides all model identities and ELO ratings prior to voting:
1. **Blind Cabinets**: Challenger A and Challenger B are presented with zero metadata.
2. **Side-by-Side Play**: Play or inspect both platformers in sandboxed cabinets.
3. **Voting**: Vote `👈 Challenger A`, `🤝 Tie`, or `👉 Challenger B`.
4. **Post-Vote Reveal**: The true model identities, hardware specifications, updated ELO deltas, and verified source links are revealed!
5. **Dynamic ELO Updates**:
   $$\Delta R_A = 32 \times \left(S_A - \frac{1}{1 + 10^{(R_B - R_A)/400}}\right)$$
   Your votes dynamically reshape the local leaderboard standings in real time.

---

## 🗄️ Experimental / Archived Entries

The following implementations are preserved in the repository for historical and cross-ecosystem reference, but are hidden from the active browser leaderboard:

1. **[Gemini 2.5 Pro PyGame Edition](games/gemini25_pro_pygame_healthynebula.py)**:
   - **Origin:** Submitted by `u/Healthy-Nebula-3603` on [r/LocalLLaMA (312 upvotes)](https://www.reddit.com/r/LocalLLaMA/comments/1jjsiiw/mario_game_made_by_new_a_gemini_pro_25_in_couple/).
   - **Reason for Archive:** Written in Python/Pygame rather than single-file browser HTML. Can be executed locally via `pip install pygame && python3 games/gemini25_pro_pygame_healthynebula.py`.
2. **[Paul Allen's Card (Gemini 3.8 Flash Baseline)](games/gemini38_flash_baseline.html)**:
   - **Origin:** Zero-bug conversational sprint baseline.
   - **Reason for Archive:** Superseded by the Deluxe 2.6k Full CoT deliberation implementation.

---

## 🚀 Running PlumberBench

```bash
# Clone the repository
git clone https://github.com/kartikeychauhan/plumberbench.git
cd plumberbench

# Launch local server
python3 -m http.server 8000
```
Open **`http://localhost:8000`** in your browser.  
*(You can also double click [`index.html`](index.html) to open directly via `file:///` — offline data fallbacks are pre-baked).*

---

## 🤝 Submissions & Workflow
We provide three streamlined ways to submit new runs:
1. **In-Browser Submission Studio**: Click `➕ Submit Run` in the top header of [`index.html`](index.html) to run preflight validation, verify zero dependencies, compute metrics, and export schema entries.
2. **Automated CLI Submission**: Run `python3 scripts/submit.py --file path/to/mario.html ...` to auto-capture preview screenshots and append entries in one command.
3. **Automated CI Validation**: Every Pull Request is verified automatically via GitHub Actions CI (`scripts/validate.py`).

See **[`SUBMISSIONS.md`](SUBMISSIONS.md)** for full prompt standards, hardware disclosure guidelines, and schema specifications.

---

## 📜 License & Notice

MIT License. All trademarks, service marks, and brand names are the property of their respective owners and are referenced solely for nominative identification and comparative benchmark evaluation.
