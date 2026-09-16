# 🍄 PlumberBench

> **The One-Shot Super Mario Platformer Benchmark for Large Language Models**  
> *"Criteria: Strict One-Shot. Scoring: Vibes."*

[![Leaderboard](https://img.shields.io/badge/PlumberBench-Leaderboard-e52521?style=for-the-badge&logo=nintendo)](https://github.com/kartikeychauhan/plumberbench)
[![One Shot](https://img.shields.io/badge/Format-Strict_One--Shot-f8c300?style=for-the-badge)](SUBMISSIONS.md)
[![Submissions](https://img.shields.io/badge/Entries-9_Contenders-2ea043?style=for-the-badge)](games/)

---

## 🎯 The PlumberBench Manifesto

Standard LLM benchmarks (HumanEval, SWE-bench, GSM8K) measure narrow syntax verification, unit test satisfaction, or multi-step tool calls. None of them measure **experiential coherence**: can a model produce something that actually *feels good to play*?

Building an authentic 2D platformer from a single prompt is the ultimate gauntlet for frontier and local models:
1. **Multimodal Spatial Reasoning**: Constructing coherent level topography, tile collision masks, bounding-box penetration resolution, and gravity curves.
2. **Hard Real-Time Game Loops**: 60 FPS deterministic execution loops, fixed-timestep physics accumulators, and zero-allocation frame routines.
3. **Chiptune Audio DSP**: Authentic NES (2A03) audio had no MP3s or WAV files. The model must synthesize square waves, triangle basslines, and pseudo-random shift-register white noise drums directly in Web Audio API code.
4. **Procedural Sprite Synthesis**: Zero external images or CDN downloads. Every Mario mustache, Goomba eye, Koopa shell, and mystery question block must be drawn pixel-by-pixel with Canvas 2D or SVG math.
5. **"Game Feel" (Juice)**: Variable jump height tied to button hold duration, acceleration curves, skid turn inertia, coyote jump buffer time, stomp bounce recoil, and turtle shell ricochet physics.

---

## 🕹️ The Leaderboard

All entries are strict **single-prompt, single-file artifacts** with zero external dependencies.

| Rank | Contender | Model | Origin / Hardware | Format | Vibe Score | NES Crunch | Physics Feel | Ambition | Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 | [Super Mario: Three Worlds](games/gpt6_astra_high.html) | **GPT-6 Astra** *(High CoT)* | Frontier Cloud API | HTML (204 lns) | **9.4** | 7.5 | 9.5 | 9.8 | 🟢 Active |
| 🥈 | [Super Mario Bros: 2.6k Deluxe](games/gemini38_flash_full.html) | **Gemini 3.8 Flash** *(Full CoT)* | Antigravity Pro Engine | HTML (2,628 lns) | **9.1** | 9.5 | 9.6 | 9.2 | 🟢 Active |
| 🥉 | [Super Pixel Bros (Course 1-1)](games/qwen38_flash_3070_potato.html) | **Qwen3.8-Flash-Next** *(UD-Q3_K_XL)* | RTX 3070 8GB Potato (cc8.pl) | HTML (1,277 lns) | **8.9** | 9.2 | 8.9 | 8.8 | 🟢 Active |
| 4 | [Qwen 27B Tiiny NES Replica](games/qwen38_27b_chopsticks.html) | **Qwen3.8-27B** *(UD-Q4_K_XL)* | RTX 3090 (u/ChopSticksPlease) | HTML (1,008 lns) | **8.7** | 9.0 | 8.6 | 8.5 | 🟢 Active |
| 5 | [Super Meadow: A Little Adventure](games/gpt6_astra_light.html) | **GPT-6 Astra** *(Light CoT)* | Frontier Cloud API | HTML (102 lns) | **8.6** | 6.0 | 9.2 | 8.8 | 🟢 Active |
| 6 | [The 60,000-Token Monolith](games/qwen38_gold_60k.html) | **Qwen3.8-Flash-Next** *(Gold Master)* | RTX 4070 12GB (Local Homelab) | HTML (1,248 lns) | **8.5** | 9.2 | 8.0 | 9.4 | 🟢 Active |
| 7 | [Circus Jumper](games/qwen38_27b_circus_mikenonect.html) | **Qwen3.8-27B** *(Q8 GGUF)* | Framework Desktop (u/MikeNonect) | HTML (1,637 lns) | **8.4** | 5.5 | 8.8 | 9.0 | 🟢 Active |
| 8 | [Gemini 2.5 Pro PyGame](games/gemini25_pro_pygame_healthynebula.py) | **Gemini 2.5 Pro** | Cloud API (u/Healthy-Nebula-3603) | Python (537 lns) | **8.1** | 8.0 | 8.5 | 7.8 | 🟢 Active |
| 9 | [Paul Allen's Card (Base)](games/gemini38_flash_baseline.html) | **Gemini 3.8 Flash** *(Interactive)* | Antigravity Fast Pass | HTML (992 lns) | **7.8** | 8.4 | 8.9 | 7.0 | 🟢 Active |

---

## 🔍 Contender Deep Dives

### 1. Super Mario: Three Worlds Edition (GPT-6 Astra High)
- **Model:** GPT-6 Astra in High Reasoning Mode.
- **Artifact:** [`games/gpt6_astra_high.html`](games/gpt6_astra_high.html) (37.5 KB, 204 lines).
- **Vibe Breakdown:** 3 distinct biome levels (*Mushroom Meadow*, *Sunset Steppes*, *Starlight Summit*), harmonic sinusoidal moving platforms that Mario physically rides, kickable turtle shells with ricochet bouncing, ceiling clearance checks during mushroom expansion, and multi-channel synth audio. Plays like a high-end modern indie platformer.

### 2. Super Mario Bros: 2.6k Deluxe (Gemini 3.8 Flash Full CoT)
- **Model:** Gemini 3.8 Flash with deep Chain-of-Thought deliberation.
- **Artifact:** [`games/gemini38_flash_full.html`](games/gemini38_flash_full.html) (74.8 KB, 2,628 lines).
- **Vibe Breakdown:** The king of raw physical momentum and audio crunch. Features an 800 Hz bandpass noise filter for authentic NES snare drum simulation, directional skidding with procedural dust puffs, 14-frame variable jump curves, and kickable Koopa shells that wipe out enemy chains.

### 3. Super Pixel Bros Course 1-1 (Qwen3.8-Flash-Next Potato Run)
- **Model:** Qwen3.8-Flash-Next-UD-Q3_K_XL (40k context, 10k reasoning limit).
- **Origin:** Submitted by `cc8.pl` on [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1wbchyj/qwen38_27b_made_mario_with_a_single_prompt_o/).
- **Hardware:** Local desktop with RTX 3070 8GB + 80GB DDR4 RAM + NVMe SSD running at 11–12 t/s.
- **Artifact:** [`games/qwen38_flash_3070_potato.html`](games/qwen38_flash_3070_potato.html) (67.5 KB, 1,277 lines).
- **Vibe Breakdown:** Proof that consumer hardware can one-shot complete games. Delivers an authentic 1985 NES clone with live HUD statistics, custom sound effects synthesized via Web Audio, Goombas, breakable blocks, and responsive platforming.

### 4. Qwen 27B Tiiny NES Replica (u/ChopSticksPlease)
- **Model:** Qwen3.8-27B-UD-Q4_K_XL.
- **Origin:** Viral [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1wbchyj/qwen38_27b_made_mario_with_a_single_prompt_o/) post hosted on Tiiny Host.
- **Hardware:** Local RTX 3090 with llama.cpp MTP speculative draft head.
- **Artifact:** [`games/qwen38_27b_chopsticks.html`](games/qwen38_27b_chopsticks.html) (30.8 KB, 1,008 lines).
- **Vibe Breakdown:** Precise 256×240 integer-scaled NES viewport, multi-channel sound sweeps, question block coin bounces, Goombas, and retro physics.

### 5. The 60,000-Token Monolith (Qwen3.8-Flash-Next Gold)
- **Model:** Qwen3.8-Flash-Next Gold Master on RTX 4070 12GB.
- **Inference:** Single contiguous 60,221-token generation (29,455 thinking tokens, 59 minutes CoT).
- **Artifact:** [`games/qwen38_gold_60k.html`](games/qwen38_gold_60k.html) (70.8 KB, 1,248 lines).
- **Vibe Breakdown:** Unmatched retro atmosphere. Features a custom post-processing CRT scanline shader pass with pulsing marquee lights, World 1-1 overworld AND World 1-2 underground pipe warps, bouncing fireballs, Koopas, and Piranha plants.

### 6. Circus Jumper (u/MikeNonect)
- **Model:** Qwen3.8-27B Q8 GGUF on Framework Desktop.
- **Origin:** Viral [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1vp438p/if_you_would_have_told_me_half_a_year_ago_that_a/) thread (629 upvotes).
- **Artifact:** [`games/qwen38_27b_circus_mikenonect.html`](games/qwen38_27b_circus_mikenonect.html) (52.4 KB, 1,637 lines).
- **Vibe Breakdown:** Creative reskin into an acrobatic circus platformer with trapeze ropes, tents, and juggling pins.

### 7. Gemini 2.5 Pro PyGame Edition (u/Healthy-Nebula-3603)
- **Model:** Gemini 2.5 Pro.
- **Origin:** Viral [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/comments/1jjsiiw/mario_game_made_by_new_a_gemini_pro_25_in_couple/) thread (312 upvotes).
- **Artifact:** [`games/gemini25_pro_pygame_healthynebula.py`](games/gemini25_pro_pygame_healthynebula.py) (25.3 KB, 537 lines).
- **Vibe Breakdown:** Standalone Python/Pygame script with procedurally generated bushes, clouds, momentum acceleration curves, and title screen.

---

## 🚀 Running PlumberBench

### 1. Interactive Web Arcade (Wall of Mario)
Launch the built-in retro arcade UI to play all games inside sandboxed arcade cabinets, compare prompt texts, upvote with local anti-cheat, and submit community reviews:

```bash
# Clone the repository
git clone https://github.com/kartikeychauhan/plumberbench.git
cd plumberbench

# Start local server
python3 -m http.server 8000
```
Open **`http://localhost:8000`** in your browser.

*(Note: `index.html` also works directly when opened with `file:///` protocol via double-click, thanks to embedded offline dataset fallbacks!)*

### 2. Playing Individual Games Directly
Every HTML entry in `games/` is 100% self-contained:
```bash
# Open any game in your default browser
xdg-open games/gpt6_astra_high.html
xdg-open games/qwen38_flash_3070_potato.html
xdg-open games/qwen38_gold_60k.html

# Run the PyGame entry (requires pygame)
pip install pygame
python3 games/gemini25_pro_pygame_healthynebula.py
```

---

## 📐 Evaluation Dimensions (The Plumber Radar)

| Dimension | Weight | Description |
| :--- | :---: | :--- |
| **NES Crunch** | 35% | Authenticity to the 1985 Famicom/NES aesthetic. Integer scaling, scanlines, chiptune sound synthesis (pulse sweeps, noise drums), 8-bit palette fidelity. |
| **Physics & Momentum** | 35% | Running acceleration, top speed, friction curves, skid turn dust, variable jump height on hold, coyote frame buffer, stomp squash physics. |
| **Ambition & Scope** | 30% | Multiple worlds, moving platforms, pipe warps, underground sub-levels, shell ricochet chaining, power-up states, boss encounters, and artistic innovation. |

---

## 🤝 Submissions & Contributions

Got a model that one-shotted Mario? We want to see it!
Please read **[`SUBMISSIONS.md`](SUBMISSIONS.md)** for submission rules, JSON schema, and pull request guidelines.

---

## 📜 License

MIT License. Super Mario Bros is a registered trademark of Nintendo. All implementations here are procedural, non-commercial fair-use benchmark evaluations created autonomously by artificial intelligence models.
