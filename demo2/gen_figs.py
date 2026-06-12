"""
生成 Attention Is All You Need 论文的仿真图表。
包括：Transformer 架构图、注意力机制、BLEU 分数等。
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np, os

d = 'figs'
os.makedirs(d, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.titlesize': 12})

# ── 1A: Transformer 架构 ──
fig, ax = plt.subplots(figsize=(7, 8))
ax.set_xlim(0, 8); ax.set_ylim(0, 11); ax.axis('off')
# Encoder stack (left)
ax.text(1.5, 10.5, 'Encoder', ha='center', fontsize=12, weight='bold', color='#007191')
for i in range(6):
    y = 8.5 - i * 1.1
    rect = mpatches.FancyBboxPatch((0.5, y), 2, 0.9, boxstyle='round', facecolor='#E0F0F5', edgecolor='#007191')
    ax.add_patch(rect)
    ax.text(1.5, y+0.45, f'Encoder {i+1}', ha='center', fontsize=8, color='#007191')
    ax.text(1.5, y+0.2, 'Self-Attn + FFN', ha='center', fontsize=7, color='gray')
# Output (top)
rect = mpatches.FancyBboxPatch((0.5, 8.8), 2, 0.7, boxstyle='round', facecolor='#FDEDEC', edgecolor='#D94F4F')
ax.add_patch(rect); ax.text(1.5, 9.15, 'Input Embedding', ha='center', fontsize=8, color='#D94F4F')
# Decoder stack (right)
ax.text(5.5, 10.5, 'Decoder', ha='center', fontsize=12, weight='bold', color='#2E7D32')
for i in range(6):
    y = 8.5 - i * 1.1
    rect = mpatches.FancyBboxPatch((4.5, y), 2, 0.9, boxstyle='round', facecolor='#E8F5E9', edgecolor='#2E7D32')
    ax.add_patch(rect)
    ax.text(5.5, y+0.45, f'Decoder {i+1}', ha='center', fontsize=8, color='#2E7D32')
    ax.text(5.5, y+0.2, 'Self+Cross+FFN', ha='center', fontsize=7, color='gray')
rect = mpatches.FancyBboxPatch((4.5, 8.8), 2, 0.7, boxstyle='round', facecolor='#FDEDEC', edgecolor='#D94F4F')
ax.add_patch(rect); ax.text(5.5, 9.15, 'Output Embedding', ha='center', fontsize=8, color='#D94F4F')
# Arrow from encoder to decoder
ax.annotate('', xy=(4.5, 7.5), xytext=(2.5, 7.5), arrowprops=dict(arrowstyle='->', color='#D48B2C', lw=3))
ax.text(3.5, 7.3, 'K, V', ha='center', fontsize=9, weight='bold', color='#D48B2C')
# Labels
ax.text(1.5, 9.5, '+ Positional\n  Encoding', ha='center', fontsize=7, color='gray')
ax.text(5.5, 9.5, '+ Positional\n  Encoding', ha='center', fontsize=7, color='gray')
ax.set_title('The Transformer - Model Architecture', fontsize=14, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '1A.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('1A')

# ── 1DEF: Scaled Dot-Product Attention ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
# Left: formula
ax1.axis('off'); ax1.set_xlim(0, 10); ax1.set_ylim(0, 6)
ax1.text(5, 4, 'Scaled Dot-Product Attention', ha='center', fontsize=13, weight='bold', color='#1A2E4A')
ax1.text(5, 3, 'Attention(Q, K, V) = softmax( QK^T / sqrt(d_k) ) V', ha='center', fontsize=11, color='#007191')
ax1.text(5, 2.2, 'Q: Query  K: Key  V: Value  d_k: key dimension', ha='center', fontsize=9, color='gray')
ax1.text(5, 1.5, 'Scaling factor 1/sqrt(d_k) prevents\nsoftmax from entering tiny gradient regions', ha='center', fontsize=8, color='#666')
# Right: Multi-Head
ax2.axis('off'); ax2.set_xlim(0, 10); ax2.set_ylim(0, 6)
ax2.text(5, 5, 'Multi-Head Attention', ha='center', fontsize=13, weight='bold', color='#1A2E4A')
ax2.text(5, 4, 'Concat( head_1, ..., head_h ) W^O', ha='center', fontsize=11, color='#007191')
ax2.text(5, 3.3, 'head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)', ha='center', fontsize=11, color='#007191')
ax2.text(5, 2.5, 'h = 8 parallel attention layers', ha='center', fontsize=9, color='gray')
ax2.text(5, 1.8, 'd_k = d_v = d_model / h = 64', ha='center', fontsize=9, color='gray')
ax2.text(5, 1.1, 'Each head attends to different\nrepresentation subspaces', ha='center', fontsize=8, color='#666')
plt.suptitle('Attention Mechanism', fontsize=14, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '1DEF.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('1DEF')

# ── 2A: BLEU scores ──
fig, ax = plt.subplots(figsize=(8, 5))
models = ['Transformer\n(Base)', 'Transformer\n(Big)', 'ByteNet', 'ConvS2S', 'MoE', 'GNMT+RL', 'Deep-Att\n+PosUnk']
bleu_en_de = [27.3, 28.4, 23.75, 25.16, 26.03, 24.6, None]
bleu_en_fr = [38.1, 41.8, None, 39.56, 40.56, 39.92, 39.2]
x = np.arange(len(models)); w = 0.35
bars1 = ax.bar(x - w/2, [v if v else 0 for v in bleu_en_de], w, label='WMT 2014 EN-DE', color='#007191', alpha=0.9, edgecolor='white')
bars2 = ax.bar(x + w/2, [v if v else 0 for v in bleu_en_fr], w, label='WMT 2014 EN-FR', color='#D48B2C', alpha=0.9, edgecolor='white')
for bar, val in zip(bars1, bleu_en_de):
    if val: ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val), ha='center', fontsize=8, weight='bold')
for bar, val in zip(bars2, bleu_en_fr):
    if val: ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, str(val), ha='center', fontsize=8, weight='bold')
ax.set_xticks(x); ax.set_xticklabels(models, fontsize=8)
ax.set_ylabel('BLEU Score'); ax.set_title('Machine Translation Performance (WMT 2014)', weight='bold', color='#1A2E4A')
ax.legend(fontsize=9, loc='upper left')
plt.tight_layout(); plt.savefig(os.path.join(d, '2A.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2A')

# ── 2BC: Training cost / efficiency ──
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
costs = {'Transformer Big': 2.0e19, 'Transformer Base': 3.3e18, 'ConvS2S': 9.6e18, 'ByteNet': 7.0e18, 'GNMT+RL': 4.5e18}
names = list(costs.keys()); vals = list(costs.values())
colors = ['#007191', '#007191', '#999999', '#999999', '#999999']
ax1.barh(names, vals, color=colors, alpha=0.85, edgecolor='white')
ax1.set_xlabel('Training Cost (FLOPs)'); ax1.set_xscale('log')
ax1.set_title('Training Efficiency', weight='bold')
for i, v in enumerate(vals):
    ax1.text(v*1.1, i, f'{v:.1e}', fontsize=8, va='center')
# Right: PPL vs steps
steps = np.arange(0, 100000, 1000)
ppl = 12 * np.exp(-steps/15000) + 4.0 + 0.5*np.sin(steps/5000)*np.exp(-steps/30000)
ax2.plot(steps, ppl, '#007191', linewidth=2)
ax2.set_xlabel('Training Steps'); ax2.set_ylabel('Perplexity')
ax2.set_title('Training Convergence', weight='bold')
plt.suptitle('Training Efficiency & Convergence', fontsize=13, color='#1A2E4A', weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '2BC.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2BC')

# ── 2DE: Ablation ──
fig, ax = plt.subplots(figsize=(8, 5))
ablations = ['Base Model', '- Multi-Head\n(h=1)', '- Attention\n(1 head)', '+ h=16', '+ h=32', '- Positional\nEncoding', '-Dropout', 'Big Model']
ppl_abl = [4.5, 5.2, 5.8, 4.4, 4.6, 6.0, 5.5, 3.5]
colors_abl = ['#007191'] + ['#D94F4F']*3 + ['#D48B2C']*2 + ['#999999']*2
ax.bar(ablations, ppl_abl, color=colors_abl, alpha=0.85, edgecolor='white')
ax.set_ylabel('Perplexity (EN-DE)'); ax.set_title('Ablation Study: Component Contributions', weight='bold', color='#1A2E4A')
for i, v in enumerate(ppl_abl):
    ax.text(i, v+0.05, str(v), ha='center', fontsize=9, weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(d, '2DE.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2DE')

# ── 2FG: Attention head visualization ──
fig, ax = plt.subplots(figsize=(8, 5))
data = np.random.rand(6, 6) * 0.8
data[0,0] = 0.95; data[1,0] = 0.7; data[2,2] = 0.85; data[3,1] = 0.75
# make it look more realistic
for i in range(6):
    data[i, max(0,i-1):min(6,i+2)] += 0.1
im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
ax.set_xticks(range(6)); ax.set_xticklabels(['The', 'animal', "didn't", 'cross', 'the', 'street'])
ax.set_yticks(range(6)); ax.set_yticklabels(['The', 'animal', "didn't", 'cross', 'the', 'street'])
plt.xticks(rotation=45)
ax.set_title('Attention Visualization: Anaphora Resolution', weight='bold', color='#1A2E4A')
plt.colorbar(im, ax=ax, label='Attention Weight')
plt.tight_layout(); plt.savefig(os.path.join(d, '2FG.jpg'), dpi=120, bbox_inches='tight'); plt.close()
print('2FG')

print(f"\nDone: 6 figures in {d}/")
