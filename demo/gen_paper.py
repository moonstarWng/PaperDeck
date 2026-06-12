"""Generate a ~30-page synthetic neural network paper PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
import random, os

OUTPUT = 'demo_paper.pdf'
doc = SimpleDocTemplate(OUTPUT, pagesize=A4, leftMargin=2.5*cm, rightMargin=2.5*cm, topMargin=2*cm, bottomMargin=2*cm)
styles = getSampleStyleSheet()
body = ParagraphStyle('B', parent=styles['Normal'], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceBefore=16, spaceAfter=8)
h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12, spaceBefore=12, spaceAfter=6)
code_s = ParagraphStyle('Code', parent=styles['Normal'], fontSize=8, fontName='Courier', leading=10, leftIndent=20, spaceAfter=6)
fig_cap = ParagraphStyle('FC', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#555555'), spaceBefore=4, spaceAfter=10)

def T(t): return Paragraph(t, body)
def H(t): return Paragraph(t, h2)
def H3(t): return Paragraph(t, h3)
def S(h=12): return Spacer(1, h)
def PB(): return PageBreak()
def CAP(t): return Paragraph(t, fig_cap)

def fig(fid, cap):
    return [S(8), CAP(f'<b>{fid}.</b> {cap}'), S(4)]

def tbl(cap, rows, cols, labels):
    data = [[labels[c] if c>0 and r==0 else (labels[0] if c==0 and r>0 else '') for c in range(cols)] for r in range(rows)]
    for r in range(1, rows):
        data[r][0] = f'Model {chr(64+r)}'
        for c in range(1, cols):
            data[r][c] = f'{random.uniform(65,95):.1f}' if random.random() > 0.3 else f'{random.uniform(1.5,8.5):.1f}'
    tb = Table(data, colWidths=[100]+[75]*(cols-1))
    tb.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#007191')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('BACKGROUND',(0,1),(0,-1),colors.HexColor('#f0f0f5')),
        ('FONTSIZE',(0,0),(-1,-1),9),
    ]))
    return [S(8), tb, S(4), CAP(cap), S(4)]

A = []

# ═══ TITLE PAGE ═══
A.append(S(60))
A.append(Paragraph('<b>AST-LLM: Adaptive Sparse Training for Energy-Efficient Large Language Models</b>',
    ParagraphStyle('TT', parent=styles['Title'], fontSize=22, leading=28)))
A.append(S(20))
A.append(Paragraph('<i>Wei Chen<super>1</super>, Ming Zhang<super>1,2</super>, Jing Liu<super>1</super>, Hao Wang<super>2</super></i>', styles['Normal']))
A.append(Paragraph('<i><super>1</super>School of Computer Science, Beijing University  <super>2</super>AI Research Lab, Tsinghua University</i>', styles['Normal']))
A.append(S(16))
A.append(Paragraph('Submitted to NeurIPS 2026', ParagraphStyle('V', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#007191'))))
A.append(PB())

# ═══ ABSTRACT ═══
A.append(H('Abstract'))
A.append(T('The rapid scaling of Large Language Models (LLMs) has driven unprecedented gains in natural language understanding, but at the cost of enormous computational and energy requirements. Sparse training offers a promising avenue for reducing these costs by updating only a subset of parameters. However, existing methods rely on static sparsity patterns that fail to adapt to the evolving loss landscape. We propose AST-LLM (Adaptive Sparse Training for LLMs), a framework that dynamically adjusts sparsity patterns based on gradient signal importance. AST-LLM introduces three key innovations: (1) a gradient-aware sparsity allocation mechanism (GASA) that redistributes non-zero parameters across layers according to their contribution to loss reduction; (2) a hysteresis pruning schedule (HPS) that prevents premature removal of potentially important connections; and (3) a hardware-aware block-sparse format achieving 3.2× wall-clock speedup on NVIDIA A100 GPUs. Evaluated on Llama-2 (7B, 13B) and GPT-3-style (1.3B, 6.7B) architectures trained on the Pile and RefinedWeb, AST-LLM achieves 90% sparsity with only 0.8% perplexity degradation, reduces training FLOPs by 4.7×, and lowers energy consumption by 3.9×. Ablation studies reveal GASA contributes 62% of the total improvement.'))
A.append(PB())

# ═══ 1. INTRODUCTION (3 pages) ═══
A.append(H('1. Introduction'))
A.append(T('Large Language Models have transformed AI, achieving remarkable performance across text generation, translation, summarization, and code synthesis [1-4]. The dominant paradigm has been to scale model size, data, and compute [5,6]. GPT-4 contains over 1.7 trillion parameters; PaLM-2 and Llama-3 push boundaries further. However, this scaling comes at staggering cost: training GPT-4 reportedly consumed over 50 GWh of electricity, equivalent to the annual consumption of 5,000 US households [7].'))
A.append(T('The environmental and economic implications have sparked intense interest in efficient training. Among the most promising approaches is sparse training, where only a fraction of parameters are updated per iteration [8-10]. By maintaining dynamic sparse connectivity, sparse training can reduce both memory footprint and computational cost proportionally to sparsity ratio. Early work focused on vision tasks with CNNs [11,12], demonstrating 80-90% of weights could be pruned without significant accuracy loss. Recent efforts extend these techniques to transformers [13,14], but face fundamental challenges unique to LLMs.'))
A.append(T('The key challenge: the LLM loss landscape is highly non-stationary. Optimal sparsity at initialization differs dramatically from the pattern needed during convergence. Static masks—whether set at initialization (SNIP [15], GraSP [16]) or periodically recomputed (RigL [17], SET [18])—cannot capture nuanced gradient dynamics across billions of parameters. Furthermore, load imbalance from unstructured sparsity leads to poor hardware utilization, often negating theoretical FLOPs reduction [19,20].'))
A.append(T('We propose AST-LLM, jointly optimizing sparsity pattern, training dynamics, and hardware efficiency. Key contributions: (1) gradient-aware sparsity allocation (GASA) continuously redistributing the sparsity budget across layers; (2) hysteresis pruning schedule (HPS) using dual-threshold to prevent oscillatory pruning; (3) block-sparse implementation achieving 3.2× speedup. AST-LLM achieves 90% sparsity with negligible quality loss on models up to 13B parameters.'))
A.append(PB())

# ═══ 2. RELATED WORK (3 pages) ═══
A.append(H('2. Related Work'))
A.append(H3('2.1 Sparse Neural Network Training'))
A.append(T('Sparse training methods divide into static and dynamic approaches. Static methods fix the sparsity pattern before training, using criteria such as weight magnitude [21], gradient signal [15,16], or random initialization [22]. While efficient, they cannot adapt to changing gradient landscapes. Dynamic methods periodically update the pattern. SET [18] randomly regrows pruned connections every ΔT steps. RigL [17] improves SET by regrowing based on gradient magnitude. DSR [23] introduced learnable pruning thresholds via straight-through estimation. However, these methods were designed for moderate-scale vision models and struggle with LLM-scale training due to mask update overhead and lack of layer-wise adaptation.'))
A.append(H3('2.2 Efficient Transformer Training'))
A.append(T('Several lines of work target efficient transformer training: mixed-precision [24] reduces memory bandwidth; gradient checkpointing [25] trades compute for memory; FlashAttention [26,27] restructures attention to minimize HBM accesses; ZeRO [28] and FSDP [29] partition states across workers. While complementary, these methods do not reduce fundamental parameter count. Combining AST-LLM with these yields multiplicative gains.'))
A.append(H3('2.3 Lottery Ticket Hypothesis at Scale'))
A.append(T('The Lottery Ticket Hypothesis (LTH) [30] showed dense networks contain sparse subnetworks trainable in isolation to match full accuracy. Subsequent work extended LTH to larger models [31] and transformers [32,33]. Super Tickets [34] and Prune Once for All [35] simplified the pipeline. However, LTH methods require multiple rounds of training, impractical for LLMs. We draw inspiration from LTH while enabling single-pass training for billion-parameter models.'))
A.append(PB())

# ═══ 3. METHOD (5 pages) ═══
A.append(H('3. AST-LLM Framework'))
A.append(T('AST-LLM consists of three integrated components enabling efficient adaptive sparse training. Figure 1 provides an architectural overview.'))
A.extend(fig('Figure 1', 'Architecture of AST-LLM. (A) GASA module computes per-layer importance from gradient statistics and redistributes the global sparsity budget. (B) HPS uses dual thresholds for pruning/regrowth decisions. (C) Block-sparse format for efficient GPU execution.'))

A.append(H3('3.1 Gradient-Aware Sparsity Allocation (GASA)'))
A.append(T('Traditional methods apply uniform sparsity across layers, but transformer layers exhibit vastly different pruning sensitivity. Early embedding layers and final LM heads are particularly sensitive, while intermediate FFN layers in deeper blocks tolerate much higher sparsity. GASA dynamically allocates the sparsity budget.'))
A.append(T('Formally, for L layers, global target sparsity S, and mean gradient magnitude g_l(t) at step t, the allocation for layer l is:'))
A.append(S(4))
A.append(Paragraph('  s_l(t) = S * (g_l(t)^α) / (Σ_i g_i(t)^α)', code_s))
A.append(S(4))
A.append(T('where α is a temperature hyperparameter. α=0 gives uniform allocation; larger α concentrates non-zero parameters in high-gradient layers. We found α=0.5 optimal across model scales. EMA smoothing with β=0.99 prevents oscillation from mini-batch gradient noise.'))
A.append(PB())

A.append(H3('3.2 Hysteresis Pruning Schedule (HPS)'))
A.append(T('Dynamic sparse training suffers from "flip-flopping": weights near the pruning threshold oscillate between pruned and regrown states, wasting resources. HPS uses dual thresholds inspired by physical hysteresis.'))
A.append(T('HPS maintains pruning threshold θ_p and regrowth threshold θ_r (θ_r > θ_p). A weight is removed only when |w| < θ_p for k consecutive cycles. A missing connection regrows only when gradient magnitude |∇_w| > θ_r for m consecutive cycles. The hysteresis gap Δ = θ_r - θ_p adapts based on layer-wise gradient variance: Δ_l = Δ_0 * σ_l / σ̄, where σ_l is gradient std of layer l, σ̄ is mean across layers. Δ_0 = 0.15 provides robust performance.'))

A.append(H3('3.3 Hardware-Aware Block-Sparse Implementation'))
A.append(T('Unstructured sparsity leads to irregular memory access that modern GPUs handle poorly. We enforce sparsity at 32×32 contiguous blocks, enabling coalesced memory access and efficient Tensor Core utilization. Our kernel achieves 3.2× speedup over dense GEMM at 90% sparsity (vs 1.3× for unstructured). The two-level index structure (block-level CSR mapping to dense sub-matrices) enables direct Tensor Core loading without explicit gather/scatter.'))

A.append(H3('3.4 Training Pipeline'))
A.append(T('AST-LLM integrates into standard training with minimal overhead. The sparsity mask updates every T_update = 500 steps (<0.3% of total training time). Algorithm 1 summarizes the procedure.'))
A.extend(fig('Algorithm 1', 'AST-LLM Training: (1) Initialize dense model; (2) Per step: forward/backward with current mask; (3) Every T_update steps: update gradient EMA, recompute layer-wise allocation via GASA, update masks via HPS; (4) Continue to convergence.'))
A.append(PB())

# ═══ 4. EXPERIMENTAL SETUP ═══
A.append(H('4. Experimental Setup'))
A.append(H3('4.1 Models and Datasets'))
A.append(T('We evaluate on four configurations: GPT-3-style (1.3B, 6.7B) and Llama-2 (7B, 13B) with standard transformer architecture (pre-normalization, RoPE, SwiGLU). Training data: the Pile (825 GB, 22 subdomains) and RefinedWeb (5T tokens). We also test on CodeParrot and PubMed subsets for domain-specific evaluation.'))
A.append(H3('4.2 Baselines'))
A.append(T('We compare against: Dense training, Static magnitude pruning (MP), SNIP [15], SET [18], RigL [17], and DSR [23]. All sparse methods target 90% global sparsity unless specified.'))
A.append(H3('4.3 Hyperparameters'))
A.append(T('AdamW optimizer (β1=0.9, β2=0.95), weight decay 0.1, gradient clipping 1.0. Cosine LR schedule, 2000 warmup steps, peak LR 3e-4 (1.3B/6.7B) or 2e-4 (7B/13B). Batch size 512-2048 tokens. 64-256 A100-80GB GPUs, FSDP with bfloat16.'))
A.append(PB())

# ═══ 5. RESULTS (multiple pages) ═══
A.append(H('5. Results'))
A.append(H3('5.1 Main Results'))
A.append(T('Table 1 summarizes results across all scales. AST-LLM achieves 90% sparsity with only 0.8% average perplexity degradation, significantly outperforming RigL (2.3%), SET (3.7%), and MP (6.1%). Training FLOPs reduction of 4.7× approaches the theoretical maximum (10× at 90% sparsity), demonstrating excellent hardware utilization.'))
A.extend(tbl('Table 1: Main results. Metrics: Perplexity (WikiText-103, C4), training FLOPs (relative), wall-clock time (relative).', 6, 5, ['Method','PPL-Wiki↓','PPL-C4↓','FLOPs↓','Time↓']))
A.append(PB())

A.append(H3('5.2 Scaling Behavior'))
A.append(T('Figure 2 shows perplexity degradation vs model size. The relative benefit of AST-LLM increases with scale: for 1.3B, AST-LLM outperforms RigL by 0.9 PPL; for 13B, the gap widens to 2.4 PPL. This suggests adaptive sparsity becomes increasingly important at larger scales where loss landscapes are more heterogeneous.'))
A.extend(fig('Figure 2', 'Scaling behavior. (A) WikiText-103 PPL vs model size. (B) C4 PPL vs model size. (C) Training FLOPs reduction ratio. (D) Memory usage comparison across methods.'))
A.append(T('We hypothesize this scaling advantage stems from: (1) larger models exhibit greater heterogeneity in gradient statistics, providing more opportunity for GASA; (2) HPS is more effective in deeper networks where gradient noise accumulates.'))
A.append(PB())

A.append(H3('5.3 Ablation Study'))
A.append(T('Figure 3 presents ablation isolating each component on Llama-2 7B at 90% sparsity. Starting from SET baseline, we incrementally add gradient-based regrowth (→RigL), GASA, HPS, and block-sparse implementation.'))
A.extend(fig('Figure 3', 'Ablation on Llama-2 7B. (A) WikiText-103 PPL. (B) C4 PPL. (C) Training FLOPs. (D) GASA α sweep. (E) HPS Δ₀ sweep. (F) T_update sweep.'))
A.append(T('GASA contributes 62% of total perplexity improvement—confirming adaptive allocation is the most impactful innovation. HPS contributes 28% by reducing late-stage training instability. Block-sparse implementation contributes 10% to practical speedup with negligible quality impact. Hyperparameter sweeps confirm α=0.5, Δ₀=0.15, T_update=500 are robust across scales.'))
A.append(PB())

A.append(H3('5.4 Layer-wise Sparsity Distribution'))
A.append(T('Figure 4 visualizes the GASA-learned sparsity distribution for Llama-2 7B. The pattern is highly non-uniform: embedding layers at 65-75% sparsity, early transformer blocks at 88-92%, middle blocks at 92-95%, late blocks at 85-90%, and LM head at only 55% sparsity, confirming its critical role. This validates GASA\'s core premise.'))
A.extend(fig('Figure 4', 'Learned layer-wise sparsity for Llama-2 7B. (A) Sparsity ratio per layer. (B) Gradient magnitude vs assigned sparsity. (C) Evolution of sparsity distribution over training. (D) Attention head importance heatmap.'))

A.append(H3('5.5 Energy Efficiency'))
A.append(T('Table 2 reports actual energy consumption using NVIDIA-smi monitoring. AST-LLM reduces energy by 3.9× for 13B training, saving ~42 MWh—equivalent to 4 households annual electricity. Carbon footprint uses US average grid intensity (0.385 kg CO₂/kWh).'))
A.extend(tbl('Table 2: Energy consumption and carbon footprint at 90% sparsity.', 5, 4, ['Model','Energy(kWh)↓','CO₂(kg)↓','Speedup×']))
A.append(PB())

A.append(H3('5.6 Structured Pruning Comparison'))
A.append(T('AST-LLM significantly outperforms structured pruning methods. Head pruning (removing 90% of attention heads) degrades PPL by 5.8%, FFN dimension pruning by 4.2%, layer dropping by 7.3%, while AST-LLM degrades by only 0.8%. Structured methods impose rigid constraints, discarding useful partial information.'))
A.extend(tbl('Table 3: Comparison with structured pruning on Llama-2 7B.', 7, 4, ['Method','PPL↓','MMLU','Speedup','Sparsity']))

A.append(H3('5.7 Downstream Tasks'))
A.append(T('Beyond perplexity, we evaluate on MMLU (57-subject accuracy), HellaSwag (commonsense), ARC-Challenge (science reasoning), GSM8K (math). AST-LLM at 90% sparsity matches or exceeds dense baseline on 3/4 benchmarks, with only 1.2% MMLU drop. Sparse training preserves both language modeling and reasoning capabilities.'))
A.extend(tbl('Table 4: Downstream performance on Llama-2 7B at 90% sparsity.', 6, 5, ['Method','MMLU↑','HellaSwag↑','ARC-C↑','GSM8K↑']))

A.append(H3('5.8 Training Dynamics'))
A.append(T('Figure 5 analyzes training dynamics. AST-LLM exhibits three-phase convergence: (1) rapid pruning (0-5k steps) where the mask stabilizes; (2) exploration (5k-20k) where GASA reallocates budget; (3) convergence (>20k) where both weights and mask converge. RigL and SET show persistent mask fluctuations throughout, indicating instability.'))
A.extend(fig('Figure 5', 'Training dynamics. (A) PPL vs steps. (B) Mask change rate (Jaccard). (C) Gradient norm across layers. (D) PCA projection of loss landscape. (E) Effective rank of weight matrices.'))

A.append(H3('5.9 Few-shot Evaluation'))
A.append(T('We evaluate few-shot performance on Llama-2 7B with 0-shot, 1-shot, and 5-shot settings across 10 diverse tasks. AST-LLM retains 97% of dense few-shot accuracy at 90% sparsity, compared to 89% for RigL. The gap is largest for knowledge-intensive tasks (MMLU, TriviaQA) where preserving dense connections in critical layers matters most.'))
A.extend(tbl('Table 5: Few-shot evaluation (Llama-2 7B, 5-shot).', 6, 4, ['Method','MMLU','TriviaQA','ARC-C','Avg']))
A.append(PB())

# ═══ 6. ANALYSIS ═══
A.append(H('6. Analysis and Discussion'))
A.append(H3('6.1 Why Adaptive Sparsity Helps More at Scale'))
A.append(T('The benefit of adaptive sparsity increases with model size due to growing heterogeneity of layer-wise loss landscapes. In 1.3B models, gradient magnitude variance across layers is ~2.3×; in 13B, it grows to 6.8×. GASA exploits this by concentrating parameters where gradients are strongest. This has important implications: as models scale, adaptive approaches become necessities rather than luxuries.'))
A.append(H3('6.2 Gradient Flow Analysis'))
A.append(T('We analyze gradient flow through sparse masks using the effective gradient norm ratio—the ratio of gradient norm reaching early layers relative to the final layer. Dense training maintains 0.72 ratio; AST-LLM maintains 0.68; RigL drops to 0.41; SET to 0.28. This indicates AST-LLM better preserves gradient signal propagation, crucial for training deep transformers.'))
A.append(H3('6.3 Compute-Memory Tradeoffs'))
A.append(T('AST-LLM introduces a modest memory overhead (12% for storing dual thresholds and gradient statistics) but achieves significant compute savings (4.7× FLOPs reduction). For GPU-hour-constrained researchers, this represents a favorable tradeoff. The block-sparse format adds 5% memory overhead for index structures but enables 3.2× practical speedup.'))

A.append(H3('6.4 Robustness to Hyperparameter Variation'))
A.append(T('We conducted extensive sensitivity analysis across key hyperparameters. AST-LLM is robust to α in [0.3, 0.7], Δ₀ in [0.10, 0.20], and T_update in [200, 1000]. Performance degrades gracefully outside these ranges: setting α too high (>1.0) concentrates parameters excessively in few layers, while α too low (<0.1) approximates uniform allocation and loses adaptive benefit.'))
A.append(H3('6.5 Comparison with Knowledge Distillation'))
A.append(T('We compare AST-LLM with knowledge distillation (KD), where a sparse student learns from a dense teacher. At 90% sparsity, KD achieves 1.5% PPL degradation (vs 0.8% for AST-LLM) but requires the additional cost of training the teacher model. AST-LLM provides a self-contained solution without teacher overhead, making it more practical for scenarios where a pre-trained dense model is unavailable.'))
A.append(H3('6.6 Convergence Guarantees'))
A.append(T('We provide theoretical analysis of convergence for AST-LLM under standard assumptions (L-smooth loss, bounded gradient variance). With the hysteresis schedule, the effective learning rate for each parameter is modulated by the mask state, creating an implicit annealing effect. Under mild conditions, AST-LLM converges to a stationary point at rate O(1/√T), matching dense training convergence rate.'))
A.append(PB())

# ═══ ADDITIONAL RESULTS ═══
A.append(H('5. Additional Experimental Results'))
A.append(H3('5.10 Multilingual Evaluation'))
A.append(T('We evaluate on multilingual benchmarks: XNLI (15 languages), Flores-200 (translation quality), and MMLU-multilingual. AST-LLM maintains 96% of dense multilingual accuracy, with no language disproportionately affected. This suggests adaptive sparsity preserves the multilingual representations learned during pre-training.'))
A.extend(tbl('Table 6: Multilingual evaluation on Llama-2 7B. XNLI accuracy averaged across 15 languages.', 6, 4, ['Method','XNLI↑','Flores↑','MMLU-M↑','Avg']))

A.append(H3('5.11 Long Sequence Performance'))
A.append(T('We test on long-range tasks: PG-19 (books, avg 70K tokens), SCROLLS (summarization), and LongBench. AST-LLM maintains 95% of dense performance at 32K context length. At 64K+ tokens, performance gap narrows as attention computation dominates over FFN computation.'))
A.extend(fig('Figure 6', 'Long sequence evaluation. (A) PPL vs sequence length on PG-19. (B) ROUGE-L on SCROLLS. (C) LongBench composite score. (D) Attention vs FFN compute ratio at different lengths.'))

A.append(H3('5.12 Robustness to Initialization'))
A.append(T('We test AST-LLM across 5 different random initializations. The variance in final perplexity is 0.12 (vs 0.08 for dense), indicating good reproducibility. The learned sparsity patterns across different seeds show 78% Jaccard similarity in layer-wise allocation, suggesting GASA converges to a stable, non-random allocation.'))
A.extend(tbl('Table 7: Robustness across 5 random seeds on Llama-2 7B. Mean ± std reported.', 4, 4, ['Method','PPL(μ±σ)','FLOPs↓','MaskSim↑']))

A.append(H3('5.13 Inference Efficiency'))
A.append(T('While AST-LLM primarily targets training efficiency, we also evaluate inference. The AST-LLM-trained sparse model achieves 2.8× inference speedup with block-sparse kernels, and can be further compressed via structured pruning for 4.1× speedup with 2.3% additional PPL degradation. This dual-use capability—efficient training producing efficient models—is a practical advantage.'))
A.extend(tbl('Table 8: Inference efficiency on A100. Throughput (tokens/sec), latency (ms/token).', 5, 5, ['Method','Tokens/s↑','Latency↓','PPL','Speedup×']))
A.append(PB())

# ═══ 2.5 PRELIMINARIES ═══
A.append(H('2.5 Preliminaries: Sparse Training Formalism'))
A.append(T('We establish formal notation. Let f(x; θ) be a neural network with parameters θ ∈ R^d. In sparse training, we maintain a binary mask m ∈ {0,1}^d where m_i=1 indicates an active parameter. The effective parameters are θ̃ = θ ⊙ m. The training objective is min_θ L(f(x; θ⊙m), y) subject to ||m||₀ ≤ (1-S)·d, where S is the target sparsity. Dynamic sparse training updates both θ and m: θ^(t+1) = θ^(t) - η·∇_θL ⊙ m^(t), and m^(t+1) = UpdateMask(θ^(t), ∇_θL^(t)). The mask update function is the key differentiator across methods.'))
A.append(T('AST-LLM extends this formalism with two key generalizations: (1) layer-wise sparsity budgets S_l replace the global constraint; (2) the mask update uses a stateful hysteresis mechanism rather than a stateless threshold. The combination enables both spatial adaptation (which layers get parameters) and temporal stability (preventing oscillatory mask changes).'))
A.append(PB())

# ═══ 3.5 MORE METHOD DETAILS ═══
A.append(H3('3.5 Initialization and Warmup Strategy'))
A.append(T('Proper initialization is critical for sparse training. We initialize AST-LLM with a warmup phase (first 2000 steps) at 50% sparsity using uniform allocation. After warmup, GASA activates and the sparsity linearly increases to the target 90% over the next 3000 steps. This graduated approach prevents catastrophic pruning of essential early-stage connections. The warmup phase adds negligible overhead (<1% of total training) while significantly improving final model quality (0.4 PPL improvement vs cold start).'))
A.append(H3('3.6 Gradient Accumulation and Micro-Batching'))
A.append(T('LLM training typically uses gradient accumulation across micro-batches. AST-LLM computes gradient statistics on accumulated gradients rather than per-micro-batch, reducing noise in the GASA allocation. For a global batch of 2048 tokens split across 16 micro-batches of 128, gradient statistics are aggregated before computing layer-wise sparsity allocation. This adds negligible overhead since statistics are only computed every T_update steps.'))
A.append(H3('3.7 Distributed Training Considerations'))
A.append(T('In the FSDP setting, each GPU holds a shard of parameters. AST-LLM computes layer-wise gradient statistics using local all-reduce operations. The communication overhead is O(L) per mask update (L layers), which is negligible compared to gradient synchronization. For the block-sparse format, we ensure block boundaries align with FSDP shard boundaries to minimize cross-device communication during sparse GEMM.'))
A.append(PB())

# ═══ APPENDIX ═══
A.append(H('Appendix A: Extended Hyperparameter Analysis'))
A.append(T('Table A1 provides the complete hyperparameter sweep for GASA α across all model scales. The optimal α shifts slightly with model size: 0.45 for 1.3B, 0.50 for 6.7B/7B, 0.55 for 13B. This suggests larger models benefit from slightly more concentrated allocation, consistent with their greater layer-wise heterogeneity.'))
A.extend(tbl('Table A1: GASA α sweep across model scales. WikiText-103 PPL reported.', 6, 5, ['α','1.3B','6.7B','7B','13B']))
A.append(T('Table A2 shows the HPS Δ₀ sweep. Performance is stable across Δ₀ ∈ [0.10, 0.20] with degradation outside this range. Too small Δ₀ (<0.05) causes excessive flip-flopping; too large (>0.30) makes the mask too rigid to adapt.'))
A.extend(tbl('Table A2: HPS Δ₀ sweep on Llama-2 7B. PPL and mask flip rate reported.', 5, 4, ['Δ₀','PPL↓','FlipRate↓','Stable?']))

A.append(H('Appendix B: Detailed Per-Layer Analysis'))
A.append(T('We provide the complete per-layer sparsity distribution for all 32 transformer blocks, embedding layer, and LM head. Table B1 reports the final sparsity ratio, gradient magnitude, and effective parameter count for each layer. The attention output projection layers consistently show the highest sensitivity, likely due to their role in aggregating multi-head information.'))
A.extend(tbl('Table B1: Per-layer sparsity for Llama-2 7B (32 layers).', 34, 4, ['Layer','Sparsity%','|∇|','ActiveParams']))
A.append(PB())

A.append(H('Appendix C: Compute Infrastructure Details'))
A.append(T('All experiments were conducted on an internal cluster with 256 NVIDIA A100-80GB GPUs interconnected via InfiniBand HDR (200 Gbps). Training the 13B model with AST-LLM required 128 GPUs for 48 hours. Dense training baseline required 256 GPUs for 96 hours. Carbon footprint estimated using CodeCarbon with real-time grid intensity monitoring. All experiments used PyTorch 2.1 with CUDA 12.1. We will release code, trained masks, and experiment configurations upon publication.'))
A.append(T('Table C1 details the hardware configuration and training time for each experiment.'))
A.extend(tbl('Table C1: Compute infrastructure and training duration for each experiment.', 5, 5, ['Model','GPUs','Hours','kWh','CO₂(kg)']))

A.append(H('Appendix D: Additional Qualitative Examples'))
A.append(T('We provide qualitative examples comparing AST-LLM and dense model outputs on standard prompts. Table D1 shows generation samples across diverse tasks. AST-LLM generations are nearly indistinguishable from dense baselines, consistent with the quantitative metrics.'))
A.extend(tbl('Table D1: Generation quality comparison on Llama-2 7B. Human preference win rate (vs dense).', 5, 4, ['Task','AST-LLM Win%','Dense Win%','Tie%']))
A.append(PB())
A.append(H('7. Limitations and Future Work'))
A.append(T('AST-LLM has several limitations. First, optimization is A100-specific; other hardware (TPUs, AMD GPUs) may not achieve the same speedup. Second, GASA assumes gradient magnitude reliably proxies parameter importance—this may not hold universally. Third, we only validated decoder-only architectures; encoder-decoder (T5) and MoE models remain untested. Fourth, block-sparse format limits maximum sparsity to ~95% before block-level artifacts appear.'))
A.append(T('Future work: (1) extending to mixture-of-experts architectures where dynamic expert selection synergizes with dynamic sparsity; (2) developing hardware-agnostic block-sparse kernels via Triton/OpenAI compiler; (3) exploring AST-LLM for continual pre-training and domain adaptation; (4) integrating with quantization for further efficiency gains; (5) applying GASA principles to structured sparsity for inference optimization.'))
A.append(PB())

# ═══ 8. BROADER IMPACT ═══
A.append(H('8. Broader Impact'))
A.append(T('The environmental impact of LLM training is pressing. By reducing training energy 3.9×, AST-LLM represents a concrete step toward sustainable AI. If adopted for next-generation frontier models, it could prevent tens of thousands of tons of CO₂ emissions. However, efficiency improvements risk Jevons paradox—by making training cheaper, it may incentivize even larger models. Responsible deployment should couple with institutional compute budgeting and carbon accounting policies.'))
A.append(T('On accessibility: reducing LLM training cost by 4.7× could democratize LLM research, enabling academic labs and institutions in developing countries to participate in foundation model development. This aligns with broader goals of equitable AI research.'))
A.append(PB())

# ═══ 9. CONCLUSION ═══
A.append(H('9. Conclusion'))
A.append(T('We presented AST-LLM, an adaptive sparse training framework enabling efficient LLM training at 90% sparsity with negligible quality loss. Three components—GASA, HPS, and block-sparse implementation—collectively achieve 4.7× FLOPs reduction and 3.9× energy savings. Comprehensive evaluation across four model scales demonstrates consistent improvement over existing methods with increasing advantage at larger scales. AST-LLM represents a step toward economically and environmentally sustainable AI, and we hope it inspires further research at the intersection of efficient ML and large-scale systems.'))
A.append(PB())

# ═══ REFERENCES ═══
A.append(H('References'))
refs = [
    '[1] Brown et al. "Language Models are Few-Shot Learners." NeurIPS 2020.',
    '[2] Touvron et al. "Llama 2: Open Foundation and Fine-Tuned Chat Models." arXiv 2023.',
    '[3] OpenAI. "GPT-4 Technical Report." arXiv 2023.',
    '[4] Anil et al. "PaLM 2 Technical Report." arXiv 2023.',
    '[5] Kaplan et al. "Scaling Laws for Neural Language Models." arXiv 2020.',
    '[6] Hoffmann et al. "Training Compute-Optimal Large Language Models." NeurIPS 2022.',
    '[7] Patterson et al. "Carbon Emissions and Large Neural Network Training." arXiv 2021.',
    '[8] Hoefler et al. "Sparsity in Deep Learning." JMLR 2021.',
    '[9] Gale et al. "The State of Sparsity in Deep Neural Networks." arXiv 2019.',
    '[10] Blalock et al. "What is the State of Neural Network Pruning?" MLSys 2020.',
    '[11] Han et al. "Learning both Weights and Connections." NeurIPS 2015.',
    '[12] Frankle & Carbin. "The Lottery Ticket Hypothesis." ICLR 2019.',
    '[13] Chen et al. "The Lottery Ticket Hypothesis for Pre-trained BERT." NeurIPS 2020.',
    '[14] Kurtic et al. "The Optimal BERT Surgeon." ICML 2022.',
    '[15] Lee et al. "SNIP: Single-shot Network Pruning." ICLR 2019.',
    '[16] Wang et al. "GraSP: Gradient Signal Preservation." ICLR 2020.',
    '[17] Evci et al. "Rigging the Lottery: Making All Tickets Winners." ICML 2020.',
    '[18] Mocanu et al. "Scalable Training with Adaptive Sparse Connectivity." Nature Comm 2018.',
    '[19] Yao et al. "Efficient Deep Learning: A Survey." ACM CSUR 2023.',
    '[20] Liu et al. "Sparse Training: A Comprehensive Survey." arXiv 2024.',
    '[21] Janowsky. "Pruning versus Clipping." Physical Review E 1989.',
    '[22] Liu et al. "Rethinking the Value of Network Pruning." ICLR 2019.',
    '[23] Kusupati et al. "DSR: Differentiable Sparsity." ICML 2021.',
    '[24] Micikevicius et al. "Mixed Precision Training." ICLR 2018.',
    '[25] Chen et al. "Training Deep Nets with Sublinear Memory Cost." arXiv 2016.',
    '[26] Dao et al. "FlashAttention." NeurIPS 2022.',
    '[27] Dao. "FlashAttention-2." arXiv 2023.',
    '[28] Rajbhandari et al. "ZeRO: Memory Optimizations." SC 2020.',
    '[29] Zhao et al. "PyTorch FSDP." VLDB 2023.',
    '[30] Frankle & Carbin. "The Lottery Ticket Hypothesis." ICLR 2019.',
    '[31] Renda et al. "Comparing Rewinding and Fine-tuning." ICLR 2020.',
    '[32] Chen et al. "Lottery Ticket for Pre-trained BERT." NeurIPS 2020.',
    '[33] Prasanna et al. "When BERT Plays the Lottery." EMNLP 2020.',
    '[34] Zhou et al. "Deconstructing Lottery Tickets." NeurIPS 2019.',
    '[35] Michel et al. "Prune Once for All." arXiv 2021.',
]
for ref in refs:
    A.append(Paragraph(ref, ParagraphStyle('R', parent=styles['Normal'], fontSize=8, leading=11, leftIndent=16, firstLineIndent=-16, spaceAfter=2)))

print(f'Building PDF ({len(A)} elements)...')
doc.build(A)
print(f'Done: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f} KB)')
