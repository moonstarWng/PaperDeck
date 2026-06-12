"""
gen_figs.py — 使用 matplotlib 生成仿真科学图表作为 Demo 图片。
生成 12 张与 AST-LLM 论文主题相关的图表：架构图、柱状图、折线图等。
所有图片保存到 figs/ 目录，用于 paper2ppt Demo 流水线。

完全不消耗 LLM Token —— 纯 Python 代码 + matplotlib 渲染。
"""
import matplotlib
matplotlib.use('Agg')  # 无头渲染模式，不需要 GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

d = 'figs'
os.makedirs(d, exist_ok=True)
for f in os.listdir(d): os.remove(os.path.join(d, f))  # 清理旧图

# 全局样式配置
plt.rcParams.update({'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10})


# ═══════════════════════════════════════════
# 1A: AST-LLM 框架架构图（使用 matplotlib patches 绘制框+箭头）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis('off')
boxes = [
    (0.5, 3.8, 3.5, 1.8, '#E8F0F5', 'Gradient-Aware Sparsity\nAllocation (GASA)', '#007191'),
    (4.5, 3.8, 3.5, 1.8, '#E8F5E9', 'Hysteresis Pruning\nSchedule (HPS)', '#2E7D32'),
    (8.5, 3.8, 3.5, 1.8, '#FDEDEC', 'Block-Sparse\nGPU Kernels', '#D94F4F'),
    (1.5, 0.5, 9.5, 2, '#F5F5F5', 'AST-LLM Training: Dense Init -> Warmup -> Ramp -> Adaptive -> Converged', '#333333'),
]
for x, y, w, h, fc, txt, tc in boxes:
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.15', facecolor=fc, edgecolor=tc, linewidth=2)
    ax.add_patch(rect)
    ax.text(x+w/2, y+h/2, txt, ha='center', va='center', fontsize=10, color=tc, weight='bold')
for x1, x2 in [(4, 4.5), (8, 8.5)]:
    ax.annotate('', xy=(x2, 4.7), xytext=(x1, 4.7), arrowprops=dict(arrowstyle='->', color='#007191', lw=2.5))
ax.annotate('', xy=(6, 3.8), xytext=(6, 2.5), arrowprops=dict(arrowstyle='->', color='#007191', lw=2.5))
ax.set_title('AST-LLM: Adaptive Sparse Training Framework', fontsize=14, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '1A.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('1A')

# ═══════════════════════════════════════════
# 1DEF: GASA 层间梯度幅值与稀疏分配（双栏柱状图）
# ═══════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
layers = np.arange(1, 33)
grad_mag = np.exp(-((layers-16)**2)/80) + 0.3*np.sin(layers/2) + 0.5
ax1.bar(layers, grad_mag, color='#007191', alpha=0.85, edgecolor='white', linewidth=0.3)
ax1.set_xlabel('Layer Index'); ax1.set_ylabel('Normalized |Gradient|'); ax1.set_title('Gradient Magnitudes', weight='bold')
sparsity = 0.90 - 0.08 * grad_mag / grad_mag.max()
ax2.bar(layers, sparsity*100, color='#D48B2C', alpha=0.85, edgecolor='white', linewidth=0.3)
ax2.axhline(y=90, color='red', linestyle='--', alpha=0.5, label='Uniform 90%')
ax2.set_xlabel('Layer Index'); ax2.set_ylabel('Sparsity (%)'); ax2.set_title('GASA Allocation', weight='bold'); ax2.legend(fontsize=8)
plt.suptitle('Gradient-Aware Sparsity Allocation (GASA)', fontsize=13, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '1DEF.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('1DEF')

# ═══════════════════════════════════════════
# 2A: 扩展性 —— 各方法在不同模型规模下的困惑度退化（分组柱状图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
models = ['1.3B', '6.7B', '7B', '13B']
methods = {'AST-LLM': [0.5, 0.6, 0.7, 0.8], 'RigL': [1.5, 1.9, 2.2, 2.5], 'SET': [2.8, 3.3, 3.6, 4.0], 'Static MP': [4.5, 5.2, 5.8, 6.5]}
colors_m = {'AST-LLM': '#007191', 'RigL': '#D48B2C', 'SET': '#D94F4F', 'Static MP': '#999999'}
x = np.arange(len(models)); w = 0.2
for i, (name, vals) in enumerate(methods.items()):
    ax.bar(x + i*w, vals, w, label=name, color=colors_m[name], alpha=0.9, edgecolor='white')
ax.set_xticks(x + 1.5*w); ax.set_xticklabels(models)
ax.set_ylabel('Perplexity Degradation (%)'); ax.set_xlabel('Model Scale')
ax.set_title('Scaling: AST-LLM Advantage Grows with Model Size', weight='bold', color='#1A2E4A')
ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(d, '2A.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2A')

# ═══════════════════════════════════════════
# 2BC: 消融实验 —— 各组件贡献（柱状图 + 折线双轴图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
components = ['SET\n(Baseline)', '+Gradient\nRegrowth', '+GASA\n(62%)', '+HPS\n(28%)', '+Block-Sparse\n(10%)']
ppl = [12.5, 11.2, 9.8, 9.2, 9.0]
flops = [3.0, 3.0, 3.5, 3.5, 4.7]
cb = ['#999999', '#D48B2C', '#007191', '#2E7D32', '#1A2E4A']
ax2_ = ax.twinx()  # 双 Y 轴
ax.bar(components, ppl, color=cb, alpha=0.9, edgecolor='white')
ax2_.plot(components, flops, 'D-', color='#D94F4F', linewidth=2, markersize=8, label='FLOPs Reduction (x)')
ax.set_ylabel('Perplexity', color='#333333'); ax2_.set_ylabel('FLOPs Reduction', color='#D94F4F')
ax.set_title('Ablation: Component Contributions (Llama-2 7B)', weight='bold', color='#1A2E4A')
ax2_.legend(fontsize=8, loc='upper left')
plt.tight_layout(); plt.savefig(os.path.join(d, '2BC.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2BC')

# ═══════════════════════════════════════════
# 2DE: GASA 学到的逐层稀疏分布（34 层柱状图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 5))
layers = np.arange(1, 35)
sp = np.concatenate([[0.30], 0.90 - 0.06*np.sin(np.linspace(0, 3*np.pi, 32)), [0.45]])
cl = ['#D94F4F'] + ['#007191']*32 + ['#D48B2C']  # 嵌入层=红, Transformer块=青, LM头=金
ax.bar(layers, sp*100, color=cl, alpha=0.85, edgecolor='white', linewidth=0.3)
ax.axhline(y=90, color='grey', linestyle='--', alpha=0.5)
ax.set_xlabel('Layer Index'); ax.set_ylabel('Sparsity (%)')
ax.set_title('GASA-Learned Layer-wise Sparsity Distribution', weight='bold', color='#1A2E4A')
ax.text(2, 35, 'Embed', ha='center', fontsize=8)
ax.text(17, 96, 'Transformer Blocks (32 layers)', ha='center', fontsize=8)
ax.text(33, 50, 'LM Head', ha='center', fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(d, '2DE.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2DE')

# ═══════════════════════════════════════════
# 2FG: 能耗对比 + 节能倍数（双栏图）
# ═══════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
models_e = ['1.3B', '6.7B', '7B', '13B']
ed = [850, 4200, 5800, 18500]; ea = [240, 1150, 1600, 4800]
x = np.arange(len(models_e))
ax1.bar(x-0.2, ed, 0.4, label='Dense', color='#999999', alpha=0.85, edgecolor='white')
ax1.bar(x+0.2, ea, 0.4, label='AST-LLM', color='#007191', alpha=0.85, edgecolor='white')
ax1.set_xticks(x); ax1.set_xticklabels(models_e)
ax1.set_ylabel('Energy (kWh)'); ax1.set_title('Training Energy', weight='bold'); ax1.legend(fontsize=8)
su = [3.5, 3.65, 3.6, 3.85]
ax2.bar(models_e, su, color='#2E7D32', alpha=0.85, edgecolor='white')
for i, v in enumerate(su): ax2.text(i, v+0.05, f'{v:.1f}x', ha='center', fontsize=10, weight='bold', color='#2E7D32')
ax2.set_ylabel('Energy Reduction'); ax2.set_title('Efficiency Gain', weight='bold')
plt.suptitle('Energy & Carbon Footprint (90% Sparsity)', fontsize=13, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '2FG.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2FG')

# ═══════════════════════════════════════════
# 2H: 训练动态 —— 三阶段收敛 + 掩码稳定性（双栏折线图）
# ═══════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
steps = np.arange(0, 30000, 100)
# 模拟 AST-LLM 的指数衰减 + 小幅度振荡收敛曲线
ppl_ast = 25 * np.exp(-steps/3000) + 8.5 + 0.5*np.sin(steps/800)*np.exp(-steps/15000)
ppl_rigl = 25 * np.exp(-steps/3000) + 9.5 + 1.2*np.sin(steps/600)*np.exp(-steps/12000)
ax1.plot(steps, ppl_ast, '#007191', linewidth=2, label='AST-LLM')
ax1.plot(steps, ppl_rigl, '#D48B2C', linewidth=2, label='RigL', alpha=0.8)
# 三阶段背景色
ax1.axvspan(0, 5000, alpha=0.08, color='blue'); ax1.axvspan(5000, 20000, alpha=0.08, color='orange'); ax1.axvspan(20000, 30000, alpha=0.08, color='green')
ax1.set_xlabel('Training Steps'); ax1.set_ylabel('Perplexity'); ax1.set_title('Three-Phase Convergence', weight='bold'); ax1.legend(fontsize=7)
mc = np.abs(np.exp(-steps/4000) * (30 + 15*np.random.randn(len(steps))))
mc_rigl = np.abs(np.exp(-steps/6000) * (40 + 25*np.random.randn(len(steps))))
ax2.plot(steps, mc, '#007191', linewidth=2, label='AST-LLM'); ax2.plot(steps, mc_rigl, '#D48B2C', linewidth=2, label='RigL', alpha=0.8)
ax2.set_xlabel('Training Steps'); ax2.set_ylabel('Mask Change Rate (%)'); ax2.set_title('Mask Stability', weight='bold'); ax2.legend(fontsize=8)
plt.suptitle('Training Dynamics Analysis', fontsize=13, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '2H.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2H')

# ═══════════════════════════════════════════
# 2I: 鲁棒性 —— 5 个随机种子的困惑度分布（柱状图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
seeds = ['Seed 1', 'Seed 2', 'Seed 3', 'Seed 4', 'Seed 5']
pv = [8.95, 9.05, 8.88, 9.12, 8.98]
ax.bar(seeds, pv, color=['#007191']*5, alpha=0.85, edgecolor='white')
ax.axhline(y=9.0, color='red', linestyle='--', alpha=0.5, label='Mean=9.0')
ax.set_ylabel('Perplexity'); ax.set_title('Robustness Across 5 Random Seeds', weight='bold', color='#1A2E4A')
ax.set_ylim(8.5, 9.5); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(d, '2I.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2I')

# ═══════════════════════════════════════════
# 3A: 长序列性能 —— 随序列长度变化（对数 X 轴折线图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
sl = [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
pa = [9.0, 9.1, 9.3, 9.6, 10.0, 10.5, 11.0, 12.0]; pd = [8.5, 8.6, 8.8, 9.0, 9.3, 9.8, 10.5, 11.5]
ax.plot(sl, pd, 's-', color='#999999', linewidth=2, markersize=6, label='Dense')
ax.plot(sl, pa, 'o-', color='#007191', linewidth=2.5, markersize=7, label='AST-LLM (90%)')
ax.set_xscale('log'); ax.set_xlabel('Sequence Length (log scale)'); ax.set_ylabel('Perplexity')
ax.set_title('Long Sequence Performance (PG-19)', weight='bold', color='#1A2E4A')
ax.fill_between(sl, pd, pa, alpha=0.1, color='#007191'); ax.legend(fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(d, '3A.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('3A')

# ═══════════════════════════════════════════
# 3B: 多语言评估 —— 9 种语言的 XNLI 准确率（分组柱状图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
langs = ['EN', 'ZH', 'ES', 'FR', 'DE', 'JA', 'AR', 'RU', 'Avg']
da = [82, 78, 80, 79, 77, 72, 70, 73, 76.4]; aa = [81, 77, 79, 78, 76, 70, 68, 71, 75.0]
x = np.arange(len(langs)); w = 0.35
ax.bar(x-w/2, da, w, label='Dense', color='#999999', alpha=0.85, edgecolor='white')
ax.bar(x+w/2, aa, w, label='AST-LLM (90%)', color='#007191', alpha=0.85, edgecolor='white')
ax.set_xticks(x); ax.set_xticklabels(langs)
ax.set_ylabel('XNLI Accuracy (%)'); ax.set_title('Multilingual Evaluation (15 Languages)', weight='bold', color='#1A2E4A'); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(d, '3B.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('3B')

# ═══════════════════════════════════════════
# 3C: 推理吞吐量 —— 不同稀疏方法的 Tokens/sec（柱状图）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
mi = ['Dense', 'Unstructured\nSparse', 'Block-Sparse\n(AST-LLM)', 'Structured\nPruning']
tps = [45, 58, 126, 185]; ci = ['#999999', '#D48B2C', '#007191', '#2E7D32']
bars = ax.bar(mi, tps, color=ci, alpha=0.9, edgecolor='white')
ax.set_ylabel('Tokens per Second'); ax.set_title('Inference Throughput (A100, Llama-2 7B)', weight='bold', color='#1A2E4A')
for bar, v in zip(bars, tps): ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, str(v), ha='center', fontsize=11, weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '3C.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('3C')

# ═══════════════════════════════════════════
# 3D: 下游任务 —— 5 个基准的性能对比（分组柱状图 + 差值标注）
# ═══════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
tasks = ['MMLU', 'HellaSwag', 'ARC-C', 'GSM8K', 'TriviaQA']
ds = [65.2, 78.5, 52.3, 28.7, 71.0]; as_ = [64.0, 78.0, 52.0, 28.2, 69.5]
x = np.arange(len(tasks)); w = 0.35
ax.bar(x-w/2, ds, w, label='Dense', color='#999999', alpha=0.85, edgecolor='white')
ax.bar(x+w/2, as_, w, label='AST-LLM (90%)', color='#007191', alpha=0.85, edgecolor='white')
ax.set_xticks(x); ax.set_xticklabels(tasks)
ax.set_ylabel('Accuracy (%)'); ax.set_title('Downstream Task Performance', weight='bold', color='#1A2E4A'); ax.legend(fontsize=9)
for i in range(len(tasks)): ax.text(i, max(ds[i], as_[i])+0.5, f"-{ds[i]-as_[i]:.1f}%", ha='center', fontsize=8, color='#666')
plt.tight_layout(); plt.savefig(os.path.join(d, '3D.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('3D')

print(f"\nDone: 12 figures in {d}/")
