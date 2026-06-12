"""
ppt_layout.py — paper2ppt 可复用布局工具库。
支持从 template_design.json 加载设计令牌，替代硬编码样式。
"""
import os, json
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ═══════════════════════════════════════════
# 默认颜色调色板（被设计令牌覆盖）
# ═══════════════════════════════════════════

TEAL = RGBColor(0x00, 0x71, 0x91)
DARK = RGBColor(0x33, 0x33, 0x33)
GRAY = RGBColor(0xA5, 0xA5, 0xA5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x1A, 0x2E, 0x4A)
LIGHT_TEAL = RGBColor(0xE0, 0xF0, 0xF5)
LIGHT_GREEN = RGBColor(0xE8, 0xF5, 0xE9)
RED_ACCENT = RGBColor(0xD9, 0x4F, 0x4F)
GREEN_ACCENT = RGBColor(0x2E, 0x7D, 0x32)
LIGHT_RED = RGBColor(0xFD, 0xED, 0xEC)
GOLD = RGBColor(0xD4, 0x8B, 0x2C)
ORANGE = RGBColor(0xE0, 0x7B, 0x3A)
BLUE_SLATE = RGBColor(0x2E, 0x86, 0xAB)
BLUE_DEEP = RGBColor(0x1B, 0x5E, 0x7A)

COLOR_MAP = {
    'teal': TEAL, 'dark': DARK, 'gray': GRAY, 'white': WHITE, 'navy': NAVY,
    'light_teal': LIGHT_TEAL, 'light_green': LIGHT_GREEN,
    'red_accent': RED_ACCENT, 'green_accent': GREEN_ACCENT, 'light_red': LIGHT_RED,
    'gold': GOLD, 'orange': ORANGE, 'blue_slate': BLUE_SLATE, 'blue_deep': BLUE_DEEP,
}

# ═══════════════════════════════════════════
# 设计令牌（默认值 → 被 init_design() 覆盖）
# ═══════════════════════════════════════════

FONT_EN = 'Times New Roman'
FONT_CN = '微软雅黑'
BODY_SIZE = Pt(16)
IMG_W = 5.5
ACCENT_COLOR = TEAL        # 主色：圆点、标题装饰
TITLE_COLOR = TEAL         # 内容页标题色
TITLE_SIZE = Pt(24)        # 内容页标题字号
BODY_COLOR = DARK          # 正文色
FOOTER_BARS = [(7.2, GRAY, 0.095), (7.3, TEAL, 0.2)]  # [(y, color, height)]
HEADER_DECOS = []          # 标题装饰 [(x, y, w, h, color)]


def _hex_to_rgb(h):
    """'#RRGGBB' 或 'RRGGBB' → RGBColor。"""
    h = h.lstrip('#')
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def init_design(json_path):
    """
    从 template_design.json 加载设计令牌，覆盖模块级默认值。
    如果文件不存在或解析失败，保持默认值不变。
    """
    global FONT_EN, BODY_SIZE, ACCENT_COLOR, TITLE_COLOR, TITLE_SIZE, BODY_COLOR, FOOTER_BARS, HEADER_DECOS

    if not json_path or not os.path.exists(json_path):
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    # ── 字体 ──
    body = d.get('content_body', {})
    if body.get('font_name'):
        FONT_EN = body['font_name']
    if body.get('font_size_pt'):
        BODY_SIZE = Pt(body['font_size_pt'])
    if body.get('color'):
        BODY_COLOR = _hex_to_rgb(body['color'])

    # ── 内容标题 ──
    title = d.get('content_title', {})
    if title.get('font_size_pt'):
        TITLE_SIZE = Pt(title['font_size_pt'])
    if title.get('color'):
        TITLE_COLOR = _hex_to_rgb(title['color'])
        ACCENT_COLOR = TITLE_COLOR

    # ── 页脚 ──
    bars = d.get('footer_bars', [])
    if bars:
        FOOTER_BARS = []
        for b in bars:
            c = b.get('color', 'A5A5A5')
            FOOTER_BARS.append((b.get('y_in', 7.2), _hex_to_rgb(c), b.get('h_in', 0.1)))

    # ── 标题装饰 ──
    decos = d.get('header_decorations', [])
    if decos:
        HEADER_DECOS = []
        for dec in decos:
            HEADER_DECOS.append((
                dec.get('x_in', 0.3), dec.get('y_in', 0.25),
                dec.get('w_in', 0.15), dec.get('h_in', 0.45),
                _hex_to_rgb(dec.get('color', '007191'))
            ))


def parse_color(val):
    """解析颜色值：RGBColor / 命名键 / '#RRGGBB'。失败返回 DARK。"""
    if isinstance(val, RGBColor):
        return val
    if val in COLOR_MAP:
        return COLOR_MAP[val]
    if val.startswith('#'):
        return _hex_to_rgb(val)
    return DARK


def T(slide, l, t, w, h, text, sz=None, bold=False, color=None, align=PP_ALIGN.LEFT):
    """单行文本框。sz/color 默认使用设计令牌。"""
    if sz is None:
        sz = BODY_SIZE
    if color is None:
        color = BODY_COLOR
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; r = p.add_run()
    r.text = text; r.font.name = FONT_EN; r.font.size = sz; r.font.bold = bold
    if color:
        r.font.color.rgb = parse_color(color) if isinstance(color, str) else color
    p.alignment = align
    return tb


def M(slide, l, t, w, h, lines, sz=None, color=None):
    """多行文本框。"""
    if sz is None: sz = BODY_SIZE
    if color is None: color = BODY_COLOR
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = line
        r.font.name = FONT_EN; r.font.size = sz
        r.font.color.rgb = parse_color(color) if isinstance(color, str) else color
        p.space_after = Pt(2)
    return tb


def R(slide, l, t, w, h, fill_color, rounded=False, line_color=None):
    """填充矩形。"""
    st = 5 if rounded else 1
    rect = slide.shapes.add_shape(st, Inches(l), Inches(t), Inches(w), Inches(h))
    rect.fill.solid()
    rect.fill.fore_color.rgb = parse_color(fill_color) if isinstance(fill_color, str) else fill_color
    if line_color:
        rect.line.color.rgb = parse_color(line_color) if isinstance(line_color, str) else line_color
    else:
        rect.line.fill.background()
    return rect


def P(slide, path, l, t, w=None, max_h=None):
    """添加图片，保持宽高比。可指定 max_h 限制高度不超过。"""
    if w is None: w = IMG_W
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found"); return None
    try:
        pic = slide.shapes.add_picture(path, Inches(l), Inches(t))
        ratio = pic.height / pic.width
        pic.width = Inches(w)
        pic.height = int(Inches(w) * ratio)
        if max_h and pic.height > Inches(max_h):
            pic.height = Inches(max_h)
            pic.width = int(Inches(max_h) / ratio)
        return pic
    except Exception as e:
        print(f"  ERROR adding {path}: {e}"); return None


def title_bar(slide, text):
    """
    内容页标题栏。使用设计令牌中的颜色和装饰。
    绘制顺序：背景条 → 装饰元素 → 标题文字（确保文字不被遮挡）。
    """
    # 1. 先画页眉装饰（背景条、色块、分隔线）
    if HEADER_DECOS:
        for x, y, w, h, c in HEADER_DECOS:
            r = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
            r.fill.solid(); r.fill.fore_color.rgb = c; r.line.fill.background()
    else:
        r = slide.shapes.add_shape(1, Inches(0.3), Inches(0.25), Inches(0.15), Inches(0.45))
        r.fill.solid(); r.fill.fore_color.rgb = ACCENT_COLOR; r.line.fill.background()
        l = slide.shapes.add_shape(1, Inches(0.6), Inches(0.68), Inches(12.1), Pt(1.5))
        l.fill.solid(); l.fill.fore_color.rgb = RGBColor(0xCC, 0xCC, 0xCC); l.line.fill.background()

    # 2. 再画标题文字（在最上层）
    T(slide, 0.5, 0.15, 12.3, 0.55, text, sz=TITLE_SIZE, bold=True, color=TITLE_COLOR)

    # 3. 页脚装饰条
    for y, c, h in FOOTER_BARS:
        b = slide.shapes.add_shape(1, Inches(0), Inches(y), Inches(13.33), Inches(h))
        b.fill.solid(); b.fill.fore_color.rgb = c; b.line.fill.background()


def white_bg(slide):
    """全幅白色背景。"""
    bg = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(7.5))
    bg.fill.solid(); bg.fill.fore_color.rgb = WHITE; bg.line.fill.background()


def blank_layout(prs):
    """查找空白布局。"""
    for ly in prs.slide_layouts:
        if '空白' in ly.name:
            return ly
    return prs.slide_layouts[0]


def make_result_slide(prs, title, body_lines, img_specs, figs_dir='.'):
    """标准结果内容页：左图 + 右文（带圆点）。"""
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, title)

    lines = [l for l in body_lines if l.strip()]
    n = len(lines)
    spacing = 0.9 if n <= 3 else (0.7 if n <= 5 else 5.4 / (n + 1))
    start_y = 1.4

    for i, line in enumerate(lines):
        y = start_y + i * spacing
        dot = slide.shapes.add_shape(9, Inches(6.8), Inches(y + 0.15), Inches(0.18), Inches(0.18))
        dot.fill.solid(); dot.fill.fore_color.rgb = ACCENT_COLOR; dot.line.fill.background()
        T(slide, 7.15, y, 5.6, 0.45, line)

    for spec in img_specs:
        filename = spec['file']
        top_in = spec.get('top_in', 1.05)
        path = os.path.join(figs_dir, filename)
        P(slide, path, 0.3, top_in)

    return slide
