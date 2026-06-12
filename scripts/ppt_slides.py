"""
ppt_slides.py — 参数化的特殊幻灯片构建器。
每个函数接收一个从 slide-content.json 解析出的 data 字典，
构建特定类型的幻灯片（作者团队、课题背景、结果总结、讨论等）。
所有函数遵循相同的签名: (prs, data) -> slide
"""
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ppt_layout import (
    T, M, R, P, title_bar, white_bg, blank_layout,
    TEAL, DARK, WHITE, NAVY, LIGHT_TEAL, LIGHT_GREEN,
    RED_ACCENT, GREEN_ACCENT, GOLD, ORANGE, BLUE_SLATE, BLUE_DEEP,
    COLOR_MAP, parse_color, BODY_SIZE, FONT_EN, FONT_CN
)


def build_author_slide(prs, data):
    """
    构建"作者团队与研究背景"页。
    布局：上方左右两张卡片（期刊信息 + 研究机构），下方通栏横幅（通讯作者 + 前期基础）。

    data 结构:
      journal: {name, if, doi, date}
      institutions: [字符串列表]
      authors: 通讯作者字符串（用 | 分隔）
      prior_work: [前期研究工作列表]
    """
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, '1 作者团队与研究背景')

    journal = data.get('journal', {})
    institutions = data.get('institutions', [])
    authors = data.get('authors', '')
    prior_work = data.get('prior_work', [])

    # ── 左上卡片：期刊信息 ──
    R(slide, 0.4, 1.1, 5.8, 2.5, LIGHT_TEAL, rounded=True)  # 卡片背景
    R(slide, 0.4, 1.1, 5.8, 0.5, TEAL)                      # 卡片顶部色条
    T(slide, 0.6, 1.15, 5.4, 0.4, '  期刊信息', sz=Pt(18), bold=True, color=WHITE)
    # 动态拼接期刊信息：名称、IF、日期、DOI
    M(slide, 0.7, 1.8, 5.2, 1.5, [
        f"{journal.get('name', '')} (IF ~{journal.get('if', '')})" if journal.get('if') else journal.get('name', ''),
        f"{'Nature 子刊' if 'Nature' in journal.get('name', '') else ''} | {journal.get('date', '')}",
        f"DOI: {journal.get('doi', '')}" if journal.get('doi') else '',
    ], sz=BODY_SIZE, color=DARK)

    # ── 右上卡片：研究机构 ──
    R(slide, 6.6, 1.1, 6.3, 2.5, LIGHT_GREEN, rounded=True)
    R(slide, 6.6, 1.1, 6.3, 0.5, GREEN_ACCENT)              # 绿色顶部色条（与左侧区分）
    T(slide, 6.8, 1.15, 5.9, 0.4, '  研究机构', sz=Pt(18), bold=True, color=WHITE)
    M(slide, 6.9, 1.8, 5.8, 1.5, institutions, sz=BODY_SIZE, color=DARK)

    # ── 底部通栏：通讯作者 + 前期基础 ──
    R(slide, 0.4, 3.9, 12.5, 3.0, LIGHT_TEAL, rounded=True)
    T(slide, 0.7, 4.0, 5.0, 0.4, '  通讯作者', sz=Pt(18), bold=True, color=TEAL)
    T(slide, 0.7, 4.5, 11.8, 0.4, authors, sz=BODY_SIZE, bold=True, color=TEAL)
    T(slide, 0.7, 5.1, 5.0, 0.4, '  课题组前期研究基础', sz=BODY_SIZE, bold=True, color=TEAL)
    if prior_work:
        M(slide, 0.7, 5.5, 11.8, 1.2, prior_work, sz=BODY_SIZE, color=DARK)

    return slide


def build_background_slide(prs, data):
    """
    构建"课题背景"页。
    布局：3 张横向排列的卡片（每张含彩色标题条） + 底部假说/实验横幅。

    data 结构:
      cards: [{title, body, color}, ...]  — 2-4 张卡片
      hypothesis: 核心假说文本
      experiment: 实验设计文本
    """
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, '2 课题背景：从临床问题到科学机制')

    cards = data.get('cards', [])
    # 卡片等宽排列：每张 3.95in 宽，间距 0.27in
    for i, card in enumerate(cards):
        cx = 0.45 + i * 4.22                     # 水平起始位置
        color = parse_color(card.get('color', 'teal'))
        R(slide, cx, 1.15, 3.95, 3.6, LIGHT_TEAL, rounded=True)  # 卡片背景
        R(slide, cx, 1.15, 3.95, 0.55, color)                    # 彩色标题条
        T(slide, cx + 0.2, 1.2, 3.5, 0.45, card['title'], sz=Pt(20), bold=True, color=WHITE)
        # body 中的 \n 换行符需要显式 split 后传入 M()
        M(slide, cx + 0.25, 1.85, 3.4, 2.7,
           card['body'].strip().split('\n'), sz=BODY_SIZE, color=DARK)

    # 底部假说/实验横幅
    hypothesis = data.get('hypothesis', '')
    experiment = data.get('experiment', '')
    if hypothesis or experiment:
        R(slide, 0.45, 5.05, 12.4, 1.8, LIGHT_TEAL, rounded=True)
        T(slide, 0.7, 5.15, 11.9, 0.4, '核心假说与实验设计', sz=Pt(18), bold=True, color=TEAL)
        lines = []
        if hypothesis:
            lines.append('假说: ' + hypothesis)
        if experiment:
            lines.append('实验: ' + experiment)
        M(slide, 0.7, 5.6, 11.9, 1.1, lines, sz=BODY_SIZE, color=DARK)

    return slide


def build_summary_slide(prs, data):
    """
    构建"结果总结"页。
    布局：顶部横向流程箭头图 + 中部证据卡片 + 底部结论横幅。

    data 结构:
      title: 幻灯片标题
      flow_steps: [{text, color}, ...]  — 流程步骤
      evidence_cards: [{title, detail}, ...]  — 证据卡片
      conclusions: [字符串列表]  — 结论要点
    """
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, data.get('title', '研究总结'))

    # ── 顶部流程箭头图 ──
    flow_steps = data.get('flow_steps', [])
    n = len(flow_steps)
    if n > 0:
        # 自适应宽度：总可用宽度 12.5in，减去箭头间距
        bw = max(1.0, (12.5 - (n - 1) * 0.08) / n)  # 每步宽度不低于 1.0in
        bw = min(bw, 1.8)                              # 每步宽度不超过 1.8in
        x0 = (13.33 - (n * (bw + 0.08) - 0.08)) / 2   # 居中起始位置
        bh = 0.95
        for i, step in enumerate(flow_steps):
            x = x0 + i * (bw + 0.08)
            color = parse_color(step.get('color', 'teal'))
            R(slide, x, 1.2, bw, bh, color, rounded=True)
            T(slide, x + 0.06, 1.28, bw - 0.12, bh - 0.16, step['text'],
               sz=Pt(11), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
            # 步骤之间添加右箭头符号
            if i < n - 1:
                T(slide, x + bw + 0.005, 1.4, 0.1, 0.4, '→', sz=Pt(22), bold=True, color=TEAL, align=PP_ALIGN.CENTER)

    # ── 中部证据卡片 ──
    evidence_cards = data.get('evidence_cards', [])
    if evidence_cards:
        nc = len(evidence_cards)
        cw = min(3.95, (12.5 - (nc - 1) * 0.1) / nc)
        for i, card in enumerate(evidence_cards):
            cx = 0.45 + i * (cw + 0.1)
            R(slide, cx, 2.55, cw, 1.35, LIGHT_TEAL, rounded=True)
            T(slide, cx + 0.2, 2.65, cw - 0.4, 0.35, card['title'], sz=BODY_SIZE, bold=True, color=TEAL)
            T(slide, cx + 0.2, 3.05, cw - 0.4, 0.7, card['detail'], sz=BODY_SIZE, color=DARK)

    # ── 底部结论横幅 ──
    conclusions = data.get('conclusions', [])
    if conclusions:
        R(slide, 0.45, 4.2, 12.4, 2.7, LIGHT_TEAL, rounded=True)
        T(slide, 0.7, 4.3, 11.9, 0.35, '核心结论', sz=Pt(18), bold=True, color=TEAL)
        M(slide, 0.7, 4.7, 11.9, 2.0, conclusions, sz=BODY_SIZE, color=DARK)

    return slide


def build_discussion1_slide(prs, data):
    """
    构建"讨论1"页 —— 编号圆形列表布局。
    每个条目：左侧青色圆形编号 + 右侧标题 + 下方详细描述。
    条目之间用细灰色分隔线隔开。

    data 结构:
      title: 幻灯片标题
      items: [{number, title, detail}, ...]  — 讨论条目列表
    """
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, data.get('title', '4 讨论'))

    items = data.get('items', [])
    for i, item in enumerate(items):
        y = 1.15 + i * 1.48                           # 每条目的垂直位置
        # 青色圆形编号标记（形状类型 9 = 椭圆）
        c = slide.shapes.add_shape(9, Inches(0.55), Inches(y + 0.1), Inches(0.5), Inches(0.5))
        c.fill.solid(); c.fill.fore_color.rgb = TEAL; c.line.fill.background()
        T(slide, 0.55, y + 0.15, 0.5, 0.4, item.get('number', str(i + 1)),
           sz=Pt(14), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        # 标题
        T(slide, 1.25, y, 3.0, 0.4, item['title'], sz=BODY_SIZE, bold=True, color=TEAL)
        # 详细描述
        T(slide, 1.25, y + 0.4, 11.5, 0.85, item['detail'], sz=BODY_SIZE, color=DARK)
        # 分隔线（最后一项不加）
        if i < len(items) - 1:
            sep = slide.shapes.add_shape(1, Inches(1.25), Inches(y + 1.32), Inches(11.0), Pt(0.5))
            sep.fill.solid(); sep.fill.fore_color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
            sep.line.fill.background()

    return slide


def build_discussion2_slide(prs, data):
    """
    构建"讨论2"页 —— 左右双栏布局。
    左侧：局限性列表（浅青色背景）
    右侧：临床意义/未来方向（浅绿色背景）

    data 结构:
      title: 幻灯片标题
      left_title: 左栏标题
      left_items: 左栏条目列表
      right_title: 右栏标题
      right_items: 右栏条目列表
    """
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, data.get('title', '4 局限性与临床意义'))

    left_title = data.get('left_title', '局限性')
    left_items = data.get('left_items', [])
    right_title = data.get('right_title', '临床意义')
    right_items = data.get('right_items', [])

    # 左栏
    R(slide, 0.4, 1.1, 6.0, 5.5, LIGHT_TEAL, rounded=True)
    T(slide, 0.7, 1.25, 5.4, 0.4, left_title, sz=Pt(20), bold=True, color=TEAL)
    M(slide, 0.7, 1.8, 5.4, 4.5, left_items, sz=BODY_SIZE, color=DARK)

    # 右栏
    R(slide, 6.8, 1.1, 6.1, 5.5, LIGHT_GREEN, rounded=True)
    T(slide, 7.1, 1.25, 5.5, 0.4, right_title, sz=Pt(20), bold=True, color=GREEN_ACCENT)
    M(slide, 7.1, 1.8, 5.5, 4.5, right_items, sz=BODY_SIZE, color=DARK)

    return slide
