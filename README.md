# Scene-Code-as-Topology: Overcoming 1D Token-Stride & Diagonal Blindness in LLMs via Three.js 3D/4D Procedural Scene Graphs

[![Zenodo DOI](https://img.shields.io/badge/CERN_Zenodo_DOI-10.5281%2Fzenodo.23691649-0969da?style=for-the-badge&logo=zenodo)](https://doi.org/10.5281/zenodo.23691649)
[![Figshare DOI](https://img.shields.io/badge/Figshare_DOI-10.6084%2Fm9.figshare.34829706-6f42c1?style=for-the-badge&logo=figshare)](https://doi.org/10.6084/m9.figshare.34829706)
[![Preprint PDF](https://img.shields.io/badge/Preprint_Paper-PDF_(English)-d93f0b?style=for-the-badge)](./Scene_Code_as_Topology_Preprint_EN.pdf)
[![Self-Play Benchmark](https://img.shields.io/badge/Benchmark-30_Games_%2F_719_Moves-0969da?style=for-the-badge)](#2-empirical-results-n--30-games-719-moves)
[![3D/4D Code Win Rate](https://img.shields.io/badge/3D%2F4D_Scene_Code_Win_Rate-85.2%25_(23W--3D--4L)-2da44e?style=for-the-badge)](#2-empirical-results-n--30-games-719-moves)
[![Diagonal Monopoly](https://img.shields.io/badge/Diagonal_5--in--a--Row_Wins-9_%3A_0_Sweep-fb8500?style=for-the-badge)](#3-key-scientific-findings)
[![Statistical Significance](https://img.shields.io/badge/Binomial_p--value-0.00031_(p_%3C_0.001)-cf222e?style=for-the-badge)](#2-empirical-results-n--30-games-719-moves)

> **Repository Overview**: This repository contains the complete **experimental programs (`.py` & `.html`)**, **raw move-by-move empirical datasets (`.json`)**, **1080p split-screen match replay videos (`.mp4`)**, and **technical reports (`.md`)** for our 30-game ($719$-ply) controlled self-play study comparing **2D ASCII Matrix Serialization (Agent A)** against **Three.js 3D/4D Procedural Scene Graph Code (Agent B)** on a $15 \times 15$ Gomoku grid.

---

## 1. Theoretical Motivation: From First Principles

Why do frontier Large Language Models (LLMs) and Vision-Language Models (VLMs) struggle with spatial reasoning on discrete 2D grids, and why does **3D/4D Procedural Scene Code** resolve this bottleneck? Our framework is derived from a three-step First-Principles causal chain:

### Step 1: Why Vision (ViT) Fails on Exact Grids — Lossy Patch Compression
Vision Transformers (ViTs) encode images by dividing them into coarse patches (e.g., $14 \times 14$ or $16 \times 16$ pixels), acting as a **lossy spatial compression**. In natural images, semantic identity is invariant to resolution loss (*a blurry cat remains a cat, not a dog*). However, on a $15 \times 15$ discrete board, lossy visual patchification blurs grid intersections and misaligns stone coordinates (Rahmanzadehgervi et al., *arXiv:2407.06581*; Wang et al., *arXiv:2503.02358*).

### Step 2: Why 2D ASCII Text Still Fails — 1D Serialization & Diagonal Stride Blindness
Replacing pixel images with a **2D ASCII text matrix** (`Agent A`) provides **lossless token input**, which prior studies showed improves over raw vision (*Stuck in the Matrix*, *arXiv:2510.20198*). Yet a fundamental topological flaw remains:
* A 2D matrix of size $N \times N$ must be serialized row-by-row into a **1D token sequence** for Transformer self-attention.
* While **horizontal** neighbors (`-`) remain adjacent in 1D token space ($\text{stride} = 1$), **vertical** neighbors (`|`) are separated by $\text{stride} \approx N$ tokens, and **diagonal** neighbors (`/` and `\`) are separated by $\text{stride} \approx N \pm 1$ tokens across multiple newline boundaries.
* Consequently, 1D self-attention suffers from severe **cross-row and diagonal blindness**, forcing the LLM to perform error-prone mental coordinate arithmetic inside its Chain-of-Thought (CoT) and frequently hallucinating occupied intersections as empty.

### Step 3: Our Solution — `Scene-Code-as-Topology` (Three.js 3D/4D Procedural Scene Graph)
Instead of feeding a flattened 2D character table, **Agent B (Ours)** dynamically compiles the live board state before every move into executable **Three.js 3D/4D procedural scene graph code**:
1. **Explicit 3D Spatial Entity Instantiation**: Only occupied intersections are instantiated as discrete scene objects `createStone3D(col, row, color, x, z, u_diag1, v_diag2)`, eliminating empty-dot (`.`) counting errors.
2. **4D Collinear Diagonal Invariants**: Every stone explicitly carries its projected coordinates on four orthogonal/diagonal topological axes:
   $$x = c - 7, \quad z = r - 7, \quad u_{\text{diag1}} = x - z \text{ (main diagonal } \backslash\text{)}, \quad v_{\text{diag2}} = x + z \text{ (anti-diagonal } /\text{)}$$
   Stones that are diagonally collinear share an identical $u_{\text{diag1}}$ or $v_{\text{diag2}}$ invariant, transforming a hard 2D stride-counting problem into a trivial 1D invariant match for self-attention.
3. **3D Connected Ray Vectors (`create3DRayLine`)**: Contiguous aligned stones ($\ge 2$) along any of the 4 axes are compiled into explicit `THREE.Line` 3D ray vectors in the scene graph, directly exposing open-three and four-in-a-row threats in the input representation.

---

## 2. Empirical Results ($N = 30$ Games, 719 Moves)

### Strict Experimental Protocol
* **Zero Human Interference (Pure Empty Board)**: Every single game starts from an **empty $15 \times 15$ board at Move 1**, with zero human-crafted openings or midgame puzzles.
* **Identical Base LLM per Match**: In every game, both `Agent A (2D Matrix)` and `Agent B (Three.js 3D/4D Code)` call the **exact same model checkpoint** with identical decoding hyperparameters (`temperature = 0.2`) and identical system instructions—differing **solely** in input spatial representation.
* **Strict Black/White Alternation**: To eliminate first-mover (Black) bias, odd-numbered games (`G1, G3, G5, G7, G9`) assign **Black = Agent A (2D), White = Agent B (3D)**; even-numbered games (`G2, G4, G6, G8, G10`) assign **Black = Agent B (3D), White = Agent A (2D)**.

### Master Benchmark Table ($N = 30$ Games Across 3 Experimental Regimes)

| Experimental Group & Inference Regime | Agent A (2D Matrix Baseline) | Agent B (Ours: Three.js 3D/4D Code) | Win Ratio (B : A) | Diagonal Wins (B : A) | Spatial Hallucinations / Illegal Retries (B vs A) | Statistical Significance (Two-Tailed Binomial) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Group 1: `gemini-3.8-flash-high`**<br>*(Thinking ON, Heavyweight CoT, 10 Games / 278 Moves)* | 3W – 3D – 4L<br>*(0% White Win, 22.4s/move)* | **4W – 3D – 3L**<br>*(100% Black Unbeaten, 40% White Win, 15.2s/move)* | **4 : 3 (3D)**<br>*(-32.1% Latency)* | **1 : 0** | 0 vs 0 | White break-win rate $40\%$ vs. $0\%$ |
| **Group 2: `DeepSeek-V4.1-Flash-1017`**<br>*(Thinking OFF, Direct 1-Pass Attention, 10 Games / 199 Moves)* | 0W – 0D – 10L<br>*(0% Black, 0% White)* | **10W – 0D – 0L**<br>*(100% Black, 100% White)* | **10 : 0**<br>*(100% Win Rate)* | **1 : 0** | 2 vs 3 | **$p = 0.00195 < 0.01$**<br>*(99.8% Confidence)* |
| **Group 3: `DeepSeek-V4.1-Flash-1017`**<br>*(Thinking ON `thinking: enabled`, 10 Games / 242 Moves)* | 1W – 0D – 9L<br>*(355,743 CoT tokens)* | **9W – 0D – 1L**<br>*(100% White Win! 308,778 CoT tokens)* | **9 : 1**<br>*(90% Win Rate)* | **7 : 0**<br>*(7/9 wins on diagonals!)* | **42 vs 96**<br>*(-56.3% Hallucinations)* | **$p = 0.0215 < 0.05$**<br>*(One-tailed $p = 0.0107$)* |
| **DeepSeek Combined ($N = 20$ Games)**<br>*(Thinking OFF + Thinking ON, 441 Moves)* | 1W – 0D – 19L (5.0% Win) | **19W – 0D – 1L (95.0% Win)** | **19 : 1** | **8 : 0** | **44 vs 99** | **$p = 0.00004 < 0.0001$**<br>*(99.996% Confidence)* |
| **All 30 Games Total ($N = 30$ Games)**<br>*(719 Real API Moves)* | **4W – 3D – 23L (13.3% Win)** | **23W – 3D – 4L (85.2% of decisive)** | **23 : 4 (3D)** | **9 : 0**<br>*(100% of all diagonal wins!)* | **-55.6% Hallucinations** | **$p = 0.00031 < 0.001$**<br>*(99.97% Confidence)* |

---

## 3. Key Scientific Findings

### Finding 1: `9 : 0` Complete Monopoly on Diagonal Five-in-a-Row Victories
Across all 30 games ($719$ moves), a total of **9 games were won along a diagonal axis (`/` or `\`)**:
* **100% of all diagonal victories (`9 : 0`) were achieved by Agent B (Three.js 3D/4D Scene Code)** (`G1` in Group 1; `DS-G1` in Group 2; `DST-G2, G3, G4, G6, G7, G8, G9` in Group 3).
* **Agent A (2D Text Matrix) won 0 diagonal games across all 30 matches.**
* Most strikingly, comparing **Group 2 (DeepSeek Thinking OFF, `10:0`)** with **Group 3 (DeepSeek Thinking ON, `9:1`)** reveals how representation interacts with CoT reasoning: when CoT was disabled, the 2D baseline could not even track vertical columns; when CoT was enabled, the 2D baseline managed to defend basic vertical lines (salvaging 1 vertical win in `DST-G10`), **whereupon Agent B (3D/4D Code) immediately shifted its CoT tactics to the 4D diagonal axes (`u_diag1`, `v_diag2`) and executed 7 diagonal kills out of 9 wins (`7 : 0`)!**

### Finding 2: CoT Reasoning Cannot Cure 2D Spatial Hallucinations (`96` vs. `42` Illegal Move Retries)
In Group 3 (`DeepSeek-V4.1-Flash-1017` with `thinking: {"type": "enabled"}` and up to 4,096 CoT tokens per move), we tracked every instance where an agent hallucinated an already-occupied intersection as empty or exhausted its CoT budget attempting coordinate arithmetic:
* **Agent A (2D Matrix)** suffered **96 spatial occupancy hallucinations** (consuming `355,743` reasoning tokens), repeatedly miscounting `.` characters across rows in its CoT scratchpad.
* **Agent B (Three.js 3D/4D Code)** reduced spatial hallucinations by **56.3% (`42` vs. `96`)** while consuming **13.2% fewer reasoning tokens (`308,778` vs. `355,743`)** and winning **5 out of 5 games as second-mover White (`100%` White break-win rate)**.

### Finding 3: Compute–Representation Equivalence
Comparing lightweight CoT (`DeepSeek-V4.1-Flash`, `9:1`) with heavyweight CoT (`gemini-3.8-flash-high`, `4:3:3` where Agent A required **$22.4\text{s/move}$ vs. $15.2\text{s/move}$ for Agent B**, a $+47\%$ compute time penalty) demonstrates a fundamental law: **an impoverished 2D text representation forces LLMs to burn massive test-time CoT compute merely to reconstruct basic spatial topology that Three.js 3D/4D Scene Code provides directly in the input representation.**

---

## 4. Game-by-Game Breakdown ($N = 30$ Games)

### Group 3: `DeepSeek-V4.1-Flash-1017` — Thinking ENABLED (`9W – 0D – 1L`, 242 Moves)
*Dataset*: [`deepseek_thinking_10games_results.json`](./deepseek_thinking_10games_results.json) | *1080p Video Replay*: [`deepseek_thinking_10games_video_EN.mp4`](./deepseek_thinking_10games_video_EN.mp4)

| Game | Black (First) | White (Second) | Winner | Win Axis | Diagonal Win? | Moves | Winning 5-in-a-Row Coordinates |
| :---: | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| **DST-G1** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Vertical `\|` | No | 22 | `I10 - I9 - I8 - I7 - I6` |
| **DST-G2** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Anti-Diag `/` (`diag_slash`) | **Yes (#1)** | 31 | `J5 - I4 - H3 - G2 - F1` |
| **DST-G3** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Main-Diag `\` (`diag_backslash`) | **Yes (#2)** | 38 | `G12 - H11 - I10 - J9 - K8` |
| **DST-G4** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Anti-Diag `/` (`diag_slash`) | **Yes (#3)** | 19 | `L11 - K10 - J9 - I8 - H7` |
| **DST-G5** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Vertical `\|` | No | 18 | `I10 - I9 - I8 - I7 - I6` |
| **DST-G6** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Anti-Diag `/` (`diag_slash`) | **Yes (#4)** | 35 | `K8 - J7 - I6 - H5 - G4` |
| **DST-G7** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Anti-Diag `/` (`diag_slash`) | **Yes (#5)** | 12 | `J9 - I8 - H7 - G6 - F5` |
| **DST-G8** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Anti-Diag `/` (`diag_slash`) | **Yes (#6)** | 35 | `K10 - J9 - I8 - H7 - G6` |
| **DST-G9** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Anti-Diag `/` (`diag_slash`) | **Yes (#7)** | 10 | `L11 - K10 - J9 - I8 - H7` |
| **DST-G10** | **Agent B (3D)** | Agent A (2D) | Agent A (White) | Vertical `\|` | No | 22 | `E11 - E10 - E9 - E8 - E7` |

### Group 2: `DeepSeek-V4.1-Flash-1017` — Thinking DISABLED (`10W – 0D – 0L`, 199 Moves)
*Dataset*: [`deepseek_10games_results.json`](./deepseek_10games_results.json) | *1080p Video Replay*: [`deepseek_10games_video_EN.mp4`](./deepseek_10games_video_EN.mp4)

| Game | Black (First) | White (Second) | Winner | Win Axis | Diagonal Win? | Moves | Winning 5-in-a-Row Coordinates |
| :---: | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| **DS-G1** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Main-Diag `\` (`diag_backslash`) | **Yes (#8)** | 26 | `G4 - H5 - I6 - J7 - K8` |
| **DS-G2** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Vertical `\|` | No | 15 | `H4 - H5 - H6 - H7 - H8` |
| **DS-G3** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Vertical `\|` | No | 14 | `H3 - H4 - H5 - H6 - H7` |
| **DS-G4** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Horizontal `-` | No | 27 | `F7 - G7 - H7 - I7 - J7` |
| **DS-G5** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Horizontal `-` | No | 28 | `E9 - F9 - G9 - H9 - I9` |
| **DS-G6** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Vertical `\|` | No | 11 | `H4 - H5 - H6 - H7 - H8` |
| **DS-G7** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Horizontal `-` | No | 30 | `G9 - H9 - I9 - J9 - K9` |
| **DS-G8** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Vertical `\|` | No | 13 | `H4 - H5 - H6 - H7 - H8` |
| **DS-G9** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Horizontal `-` | No | 22 | `F11 - G11 - H11 - I11 - J11` |
| **DS-G10** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Vertical `\|` | No | 13 | `H4 - H5 - H6 - H7 - H8` |

### Group 1: `gemini-3.8-flash-high` — Thinking ENABLED (`4W – 3D – 3L`, 278 Moves)
*Dataset*: [`gomoku_10games_results.json`](./gomoku_10games_results.json) | *1080p Video Replay*: [`gomoku_10games_arena_video_EN.mp4`](./gomoku_10games_arena_video_EN.mp4)

| Game | Black (First) | White (Second) | Winner | Win Axis | Diagonal Win? | Moves | Winning 5-in-a-Row Coordinates |
| :---: | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| **GM-G1** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Anti-Diag `/` (`diag_slash`) | **Yes (#9)** | 10 | `J9 - I8 - H7 - G6 - F5` |
| **GM-G2** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Horizontal `-` | No | 31 | `D10 - E10 - F10 - G10 - H10` |
| **GM-G3** | Agent A (2D) | **Agent B (3D)** | Agent A (Black) | Horizontal `-` | No | 37 | `E9 - F9 - G9 - H9 - I9` |
| **GM-G4** | **Agent B (3D)** | Agent A (2D) | **Agent B (Black)** | Horizontal `-` | No | 29 | `C5 - D5 - E5 - F5 - G5` |
| **GM-G5** | Agent A (2D) | **Agent B (3D)** | Agent A (Black) | Vertical `\|` | No | 29 | `I12 - I11 - I10 - I9 - I8` |
| **GM-G6** | **Agent B (3D)** | Agent A (2D) | Draw (Agreed) | Late-Game Draw | No | 34 | Balanced defensive equilibrium |
| **GM-G7** | Agent A (2D) | **Agent B (3D)** | **Agent B (White!)** | Vertical `\|` | No | 24 | `F10 - F9 - F8 - F7 - F6` |
| **GM-G8** | **Agent B (3D)** | Agent A (2D) | Draw (Agreed) | Late-Game Draw | No | 28 | Balanced defensive equilibrium |
| **GM-G9** | Agent A (2D) | **Agent B (3D)** | Agent A (Black) | Horizontal `-` | No | 27 | `I9 - J9 - K9 - L9 - M9` |
| **GM-G10** | **Agent B (3D)** | Agent A (2D) | Draw (Agreed) | Late-Game Draw | No | 29 | Balanced defensive equilibrium |

---

## 5. Complete Repository Structure & Reproducibility

### A. Interactive 3D Self-Play Arena Workbench
* **[`gomoku_3d_arena_workbench.html`](./gomoku_3d_arena_workbench.html)**: Standalone browser-based Three.js WebGL split-screen workbench. Open directly in any modern browser to:
  1. Inspect live 3D board rendering vs. real-time compiled Three.js 3D/4D scene code;
  2. Replay preloaded self-play matches move-by-move (`gomoku_10games_preload.js`);
  3. Run new live self-play games against any OpenAI-compatible API endpoint.

### B. 1080p Match Replay Videos (`.mp4`)
* [`deepseek_thinking_10games_video_EN.mp4`](./deepseek_thinking_10games_video_EN.mp4) — Group 3 (`DeepSeek-V4.1-Flash` Thinking ON — `9 : 1` & `7` Diagonal Kills)
* [`deepseek_10games_video_EN.mp4`](./deepseek_10games_video_EN.mp4) — Group 2 (`DeepSeek-V4.1-Flash` Thinking OFF — `10 : 0` Sweep)
* [`gomoku_10games_arena_video_EN.mp4`](./gomoku_10games_arena_video_EN.mp4) — Group 1 (`gemini-3.8-flash-high` Thinking ON — `4 : 3 : 3` & `-32.1%` Latency)

### C. Raw Empirical Datasets (30 Games / 719 Moves)
* [`deepseek_thinking_10games_results.json`](./deepseek_thinking_10games_results.json) — Group 3 move-by-move coordinates, latency (`ms`), `reasoningTokens`, `illegalRetries`, and winning line vectors.
* [`deepseek_10games_results.json`](./deepseek_10games_results.json) — Group 2 move-by-move coordinates, latency (`ms`), and winning line vectors.
* [`gomoku_10games_results.json`](./gomoku_10games_results.json) & [`gomoku_10games_preload.js`](./gomoku_10games_preload.js) — Group 1 move-by-move dataset and HTML workbench preload bundle.

### D. Experimental & Video Rendering Programs
* [`run_deepseek_thinking_10games.py`](./run_deepseek_thinking_10games.py) — Group 3 automated 10-game self-play runner (`thinking: {"type": "enabled"}`).
* [`run_deepseek_10games.py`](./run_deepseek_10games.py) — Group 2 automated 10-game self-play runner (`thinking: {"type": "disabled"}`).
* [`run_10games_experiment.py`](./run_10games_experiment.py) — Group 1 automated 10-game self-play runner (`gemini-3.8-flash-high`).
* [`render_10games_video_en.py`](./render_10games_video_en.py) — 1080p (`1920x1080`) split-screen frame renderer and MP4 video synthesizer.

### E. Full Technical Report & Grant Proposal
* [`GRANT_PROPOSAL_AND_REPORT_EN.md`](./GRANT_PROPOSAL_AND_REPORT_EN.md) — Full English technical report and research credit grant proposal.


---

## 6. Study Limitations, Budget Constraints & Future Research Plan

Because this study was conducted independently under personal out-of-pocket API budget constraints (~3.5M total tokens), we explicitly note the following limitations:
1. **Limited Sample Size ($N = 10$ Games per Group, $N = 30$ Total)**: While the combined $23\text{W}-3\text{D}-4\text{L}$ margin achieves statistical significance ($p = 0.00031$) driven by the strong effect size on `DeepSeek-V4.1-Flash-1017` ($19 : 1$), a 10-game sample on `gemini-3.8-flash-high` ($4\text{W}-3\text{D}-3\text{L}$) has limited statistical power for narrow win-rate differentials.
2. **Limited Model Coverage (2 Models Evaluated)**: Thus far, we have only tested two models from Google and DeepSeek (`gemini-3.8-flash-high` and `DeepSeek-V4.1-Flash-1017`). How other untested models perform under this representation has not yet been evaluated.
3. **Preliminary Results & Compute Grant Plan**: Consequently, the findings reported here represent **preliminary empirical results**. To strengthen the scientific rigor of this study, we plan to apply for **Research API Compute Grants** from major AI research laboratories (such as Google and other research institutions) to continue completing these experiments across more models and larger game sample sizes.


---

## 7. Citation & Official Archival DOIs

- **Formal Preprint PDF**: [Scene_Code_as_Topology_Preprint_EN.pdf](./Scene_Code_as_Topology_Preprint_EN.pdf)
- **CERN Zenodo Official DOI**: [https://doi.org/10.5281/zenodo.23691649](https://doi.org/10.5281/zenodo.23691649)
- **Figshare Preprint DOI**: [https://doi.org/10.6084/m9.figshare.34829706](https://doi.org/10.6084/m9.figshare.34829706)

`ibtex
@misc{pathetic777_2026_scenecode,
  author       = {Pathetic777},
  title        = {{Scene-Code-as-Topology: Bypassing the 2D Tokenizer Bottleneck in Large Language Models via Procedural 3D/4D Scene Graph Representations}},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.23691649},
  url          = {https://doi.org/10.5281/zenodo.23691649}
}
`
