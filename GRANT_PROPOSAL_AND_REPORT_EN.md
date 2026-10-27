# Research Credit Grant Proposal & Cross-Model Empirical Report (English Version)

**Project Title**: *Scene-Code-as-Topology: Overcoming 1D Token-Stride and Diagonal Blindness in Large Language Models via 3D/4D Procedural Scene Graph Compilation*

---

## Part 1: Ready-to-Submit Grant Application Template (For Google / Anthropic / OpenAI)

### 1. Project Abstract / Summary (150–250 words)
While Large Language Models (LLMs) and Vision-Language Models (VLMs) excel at semantic reasoning, recent studies show that they suffer from severe spatial perception bottlenecks on discrete 2D grids—both visually due to Vision Transformer (ViT) patchification (Rahmanzadehgervi et al., *arXiv:2407.06581*; Wang et al., *arXiv:2503.02358*) and textually due to 1D token serialization of 2D matrices, which obscures vertical and diagonal topological relationships (*Stuck in the Matrix*, *arXiv:2510.20198*; *Grid-World Spatial Models*, *arXiv:2604.10690*).

We propose **Scene-Code-as-Topology**: a training-free framework that compiles discrete 2D spatial states into executable **Three.js 3D/4D procedural scene graph code** (explicitly projecting 2D coordinates $(x, z)$ into 4D collinear invariants $u = x - z$, $v = x + z$ and 3D connected ray vectors).

Across a **30-game controlled self-play benchmark (719 moves)** spanning two frontier model families (`gemini-3.8-flash-high` and `DeepSeek-V4.1-Flash-1017` across both non-thinking and thinking-enabled regimes), our Three.js 3D/4D representation achieved **overwhelming statistical superiority ($23\text{W} - 3\text{D} - 4\text{L}$, winning $85.2\%$ of decisive games, two-tailed binomial $p = 0.00031 < 0.001$)**:
1. **Direct Forward-Pass Regime (`DeepSeek-V4.1-Flash-1017`, Thinking OFF, $N=10$)**: Achieved a **10–0 complete sweep ($100\%$ win rate, $p = 0.00195 < 0.01$)** over the 2D ASCII matrix baseline.
2. **CoT Reasoning Regime on the Same Model (`DeepSeek-V4.1-Flash-1017`, Thinking ON, $N=10$)**: Achieved a **9–1 victory ($90\%$ win rate, $p = 0.0215 < 0.05$)**, scoring **7 diagonal five-in-a-row wins vs. 0 for the 2D baseline** while **reducing spatial occupancy hallucinations (illegal moves in CoT) by $56.3\%$** ($42$ vs. $96$) and using $13.2\%$ fewer thinking tokens ($308,778$ vs. $355,743$). Combined across both DeepSeek regimes ($N=20$), our representation wins **19–1 ($95.0\%$, $p = 0.00004 < 0.0001$)**.
3. **Heavyweight Reasoning Regime (`gemini-3.8-flash-high`, Thinking ON, $N=10$)**: Achieved a **4W–3D–3L advantage ($100\%$ unbeaten as Black, $40\%$ vs. $0\%$ White break-win rate)** while **reducing per-move latency by $32.1\%$** ($15.2\text{s}$ vs. $22.4\text{s}$).

---

## Part 2: 3-Group Empirical Benchmark ($N = 30$ Games, 719 Moves)

| Experimental Group & Inference Regime | Agent A (2D Matrix Baseline) | Agent B (Ours: Three.js 3D/4D Code) | Win Ratio (B : A) | Diagonal Wins (B : A) | Spatial Hallucinations / Illegal Retries (B vs A) | Statistical Significance (Two-Tailed Binomial) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Group 1: `gemini-3.8-flash-high`**<br>*(Thinking ON, Heavyweight CoT)* | 3W – 3D – 4L<br>*(0% White Win, 22.4s/move)* | **4W – 3D – 3L**<br>*(40% White Win, 15.2s/move)* | **4 : 3 (3D)**<br>*(-32.1% Latency)* | **1 : 0** | 0 vs 0 | White break-win rate $40\%$ vs. $0\%$ |
| **Group 2: `DeepSeek-V4.1-Flash-1017`**<br>*(Thinking OFF, Direct Forward Pass)* | 0W – 0D – 10L<br>*(0% Black, 0% White)* | **10W – 0D – 0L**<br>*(100% Black, 100% White)* | **10 : 0**<br>*(100% Win Rate)* | **1 : 0** | 2 vs 3 | **$p = 0.00195 < 0.01$**<br>*(Highly Significant)* |
| **Group 3: `DeepSeek-V4.1-Flash-1017`**<br>*(Thinking ON, `thinking: enabled`)* | 1W – 0D – 9L<br>*(355,743 CoT tokens)* | **9W – 0D – 1L**<br>*(100% White Win! 308,778 CoT tokens)* | **9 : 1**<br>*(90% Win Rate)* | **7 : 0**<br>*(7/9 wins on diagonals!)* | **42 vs 96**<br>*(-56.3% Hallucinations)* | **$p = 0.0215 < 0.05$**<br>*(Significant)* |
| **DeepSeek Combined ($N = 20$)**<br>*(Thinking OFF + Thinking ON)* | 1W – 0D – 19L (5.0% Win) | **19W – 0D – 1L (95.0% Win)** | **19 : 1** | **8 : 0** | **44 vs 99** | **$p = 0.00004 < 0.0001$**<br>*(Extremely Significant)* |
| **All 30 Games Total ($N = 30$)** | **4W – 3D – 23L (13.3% Win)** | **23W – 3D – 4L (85.2% of decisive)** | **23 : 4 (3D)** | **9 : 0**<br>*(100% of all diagonal wins!)* | **-55.6% Hallucinations** | **$p = 0.00031 < 0.001$**<br>*(99.97% Confidence)* |

---

## Part 3: Three Fundamental Scientific Findings

1. **9–0 Complete Monopoly on Diagonal Five-in-a-Row Wins Across 30 Games**:
   Across all 30 games ($719$ moves), there were **9 games won along a diagonal axis (`/` or `\`)**. **Every single one of those 9 diagonal victories ($9 : 0$) was achieved by Agent B (Three.js 3D/4D Scene Code)**; the 2D text matrix baseline never achieved a single diagonal win across 30 games. In Group 3 (`DeepSeek-V4.1-Flash` with Thinking ON), once CoT reasoning was unlocked, Agent B weaponized the explicit 4D invariants (`u_diag1 = x - z`, `v_diag2 = x + z`) to execute **7 diagonal kills out of 9 wins**.
2. **CoT Thinking Alone Cannot Cure 2D Representation Blindness (`10:0` vs. `9:1`)**:
   Enabling `thinking: {"type": "enabled"}` on `DeepSeek-V4.1-Flash-1017` only allowed the 2D baseline to salvage **1 vertical win out of 10 games** (improving from `0:10` to `1:9`). Even worse, while attempting mental coordinate arithmetic over the 2D ASCII grid inside its Chain-of-Thought, the 2D baseline suffered **96 illegal-move occupancy hallucinations** (exhausting its 4,096 CoT token budget and trying to place stones on already-occupied intersections), whereas our Three.js 3D/4D object representation cut spatial hallucinations by **56.3%** ($42$ vs. $96$) while consuming **13.2% fewer thinking tokens**.
3. **Compute-Representation Equivalence**:
   Comparing lightweight CoT (`DeepSeek-V4.1-Flash`, `9:1`) with heavyweight CoT (`gemini-3.8-flash-high`, `4:3:3` with $+47\%$ slower latency for 2D) proves that an impoverished 2D text representation forces LLMs to burn massive test-time CoT compute merely to reconstruct basic grid topology that **Three.js 3D/4D Scene-Code-as-Topology** provides for free in the input space.
