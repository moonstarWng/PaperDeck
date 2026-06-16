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
    TEAL, DARK, WHITE, NAVY,  # 保留旧常量供 fallback
    COLOR_MAP, parse_color, contrast_text,
    BODY_SIZE, FONT_EN, FONT_CN,
    PALETTE_PRIMARY, PALETTE_LIGHT, PALETTE_DARK, PALETTE_WARM, PALETTE_ACCENT2,
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
    R(slide, 0.4, 1.1, 5.8, 2.5, PALETTE_LIGHT, rounded=True)  # 卡片背景
    R(slide, 0.4, 1.1, 5.8, 0.5, PALETTE_PRIMARY)             # 卡片顶部色条
    T(slide, 0.6, 1.15, 5.4, 0.4, '  期刊信息', sz=Pt(18), bold=True, color=WHITE)
    # 动态拼接期刊信息：名称、IF、日期、DOI
    M(slide, 0.7, 1.8, 5.2, 1.5, [
        f"{journal.get('name', '')} (IF ~{journal.get('if', '')})" if journal.get('if') else journal.get('name', ''),
        f"{'Nature 子刊' if 'Nature' in journal.get('name', '') else ''} | {journal.get('date', '')}",
        f"DOI: {journal.get('doi', '')}" if journal.get('doi') else '',
    ], sz=BODY_SIZE, color=DARK)

    # ── 右上卡片：研究机构 ──
    R(slide, 6.6, 1.1, 6.3, 2.5, PALETTE_WARM, rounded=True)
    R(slide, 6.6, 1.1, 6.3, 0.5, PALETTE_ACCENT2)           # 第二强调色顶部色条
    T(slide, 6.8, 1.15, 5.9, 0.4, '  研究机构', sz=Pt(18), bold=True, color=WHITE)
    M(slide, 6.9, 1.8, 5.8, 1.5, institutions, sz=BODY_SIZE, color=DARK)

    # ── 底部通栏：通讯作者 + 前期基础 ──
    R(slide, 0.4, 3.9, 12.5, 3.0, PALETTE_LIGHT, rounded=True)
    T(slide, 0.7, 4.0, 5.0, 0.4, '  通讯作者', sz=Pt(18), bold=True, color=PALETTE_PRIMARY)
    T(slide, 0.7, 4.5, 11.8, 0.4, authors, sz=BODY_SIZE, bold=True, color=PALETTE_PRIMARY)
    T(slide, 0.7, 5.1, 5.0, 0.4, '  课题组前期研究基础', sz=BODY_SIZE, bold=True, color=PALETTE_PRIMARY)
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
        R(slide, cx, 1.15, 3.95, 3.6, PALETTE_LIGHT, rounded=True)  # 卡片背景
        R(slide, cx, 1.15, 3.95, 0.55, color)                    # 彩色标题条
        T(slide, cx + 0.2, 1.2, 3.5, 0.45, card['title'], sz=Pt(20), bold=True, color=WHITE)
        # body 中的 \n 换行符需要显式 split 后传入 M()
        M(slide, cx + 0.25, 1.85, 3.4, 2.7,
           card['body'].strip().split('\n'), sz=BODY_SIZE, color=DARK)

    # 底部假说/实验横幅
    hypothesis = data.get('hypothesis', '')
    experiment = data.get('experiment', '')
    if hypothesis or experiment:
        R(slide, 0.45, 5.05, 12.4, 1.8, PALETTE_LIGHT, rounded=True)
        T(slide, 0.7, 5.15, 11.9, 0.4, '核心假说与实验设计', sz=Pt(18), bold=True, color=PALETTE_PRIMARY)
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
                T(slide, x + bw + 0.005, 1.4, 0.1, 0.4, '→', sz=Pt(22), bold=True, color=PALETTE_PRIMARY, align=PP_ALIGN.CENTER)

    # ── 中部证据卡片 ──
    evidence_cards = data.get('evidence_cards', [])
    if evidence_cards:
        nc = len(evidence_cards)
        cw = min(3.95, (12.5 - (nc - 1) * 0.1) / nc)
        for i, card in enumerate(evidence_cards):
            cx = 0.45 + i * (cw + 0.1)
            R(slide, cx, 2.55, cw, 1.35, PALETTE_LIGHT, rounded=True)
            T(slide, cx + 0.2, 2.65, cw - 0.4, 0.35, card['title'], sz=BODY_SIZE, bold=True, color=PALETTE_PRIMARY)
            T(slide, cx + 0.2, 3.05, cw - 0.4, 0.7, card['detail'], sz=BODY_SIZE, color=DARK)

    # ── 底部结论横幅 ──
    conclusions = data.get('conclusions', [])
    if conclusions:
        R(slide, 0.45, 4.2, 12.4, 2.7, PALETTE_LIGHT, rounded=True)
        T(slide, 0.7, 4.3, 11.9, 0.35, '核心结论', sz=Pt(18), bold=True, color=PALETTE_PRIMARY)
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
    # 根据条目数动态调整间距，避免文字重叠
    n_items = max(len(items), 1)
    available_h = 5.8  # title_bar 下方可用高度
    row_h = min(1.48, available_h / n_items)  # 每行高度，最多 1.48in
    for i, item in enumerate(items):
        y = 1.15 + i * row_h
        detail_h = max(0.6, row_h - 0.55)  # 详细描述高度自适应
        # 圆形编号
        c = slide.shapes.add_shape(9, Inches(0.55), Inches(y + 0.05), Inches(0.45), Inches(0.45))
        c.fill.solid(); c.fill.fore_color.rgb = PALETTE_PRIMARY; c.line.fill.background()
        T(slide, 0.55, y + 0.08, 0.45, 0.4, item.get('number', str(i + 1)),
           sz=Pt(14), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        # 标题
        T(slide, 1.25, y, 3.0, 0.35, item['title'], sz=BODY_SIZE, bold=True, color=PALETTE_PRIMARY)
        # 详细描述
        T(slide, 1.25, y + 0.35, 11.5, detail_h, item['detail'], sz=BODY_SIZE, color=DARK)
        # 分隔线
        if i < len(items) - 1:
            sep_y = y + row_h - 0.08
            sep = slide.shapes.add_shape(1, Inches(1.25), Inches(sep_y), Inches(11.0), Pt(0.5))
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
    n_left = max(len(left_items), 1); n_right = max(len(right_items), 1)
    max_items = max(n_left, n_right)
    col_h = min(5.5, 0.6 * max_items + 0.5)  # 动态列高，每项约 0.6in
    R(slide, 0.4, 1.1, 6.0, col_h, PALETTE_LIGHT, rounded=True)
    T(slide, 0.7, 1.25, 5.4, 0.4, left_title, sz=Pt(20), bold=True, color=PALETTE_PRIMARY)
    M(slide, 0.7, 1.8, 5.4, col_h - 0.6, left_items, sz=BODY_SIZE, color=DARK)

    # 右栏
    R(slide, 6.8, 1.1, 6.1, col_h, PALETTE_WARM, rounded=True)
    T(slide, 7.1, 1.25, 5.5, 0.4, right_title, sz=Pt(20), bold=True, color=PALETTE_ACCENT2)
    M(slide, 7.1, 1.8, 5.5, col_h - 0.6, right_items, sz=BODY_SIZE, color=DARK)

    return slide


def build_paper_info_slide(prs, data):
    """
    论文信息页：左侧 PDF 首页截图 + 右侧原文链接（自动搜索）。
    data: {pdf_path, paper_title, extra_text}
    """
    import urllib.request, urllib.parse
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, '原文信息')

    pdf_path = data.get('pdf_path', '')
    paper_title = data.get('paper_title', '')
    extra = data.get('extra_text', '')

    # ── 左侧：PDF 首页渲染 ──
    first_page_img = None
    if pdf_path and os.path.exists(pdf_path):
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(pdf_path)
            bitmap = pdf[0].render(scale=1.5)
            img_path = pdf_path.replace('.pdf', '_page1.jpg')
            bitmap.to_pil().save(img_path, 'JPEG', quality=85)
            first_page_img = img_path
        except Exception as e:
            print(f"  WARNING: PDF render: {e}")

    if first_page_img:
        P(slide, first_page_img, 0.3, 1.1, 5.8, max_h=5.5)
    else:
        T(slide, 0.5, 2.5, 5.5, 1.0, '(PDF 首页渲染失败)', sz=Pt(12), color=RGBColor(0x99, 0x99, 0x99))

    # ── 右侧：原文链接（Semantic Scholar → Google Scholar fallback）──
    link_lines = []
    if paper_title:
        try:
            q = urllib.parse.quote(paper_title[:200])
            u = f'https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=1'
            req = urllib.request.Request(u, headers={'User-Agent': 'PaperDeck/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                import json as _json
                d = _json.loads(resp.read())
                if d.get('data'):
                    p = d['data'][0]
                    pid = p.get('paperId', '')
                    eid = p.get('externalIds', {})
                    link_lines.append(f'Semantic Scholar: https://api.semanticscholar.org/CorpusID:{pid}')
                    if eid.get('DOI'):
                        link_lines.append(f'DOI: https://doi.org/{eid["DOI"]}')
                    if eid.get('ArXiv'):
                        link_lines.append(f'arXiv: https://arxiv.org/abs/{eid["ArXiv"]}')
        except Exception:
            pass
        if not link_lines:
            q = urllib.parse.quote(paper_title[:200])
            link_lines.append(f'Google Scholar: https://scholar.google.com/scholar?q={q}')

    T(slide, 6.8, 1.2, 5.8, 0.4, '原文链接', sz=Pt(16), bold=True, color=PALETTE_PRIMARY)
    M(slide, 6.8, 1.7, 5.8, 3.5, link_lines, sz=Pt(13), color=DARK)
    if extra:
        T(slide, 6.8, 4.8, 5.8, 1.5, extra, sz=Pt(12), color=RGBColor(0x66, 0x66, 0x66))

    return slide
