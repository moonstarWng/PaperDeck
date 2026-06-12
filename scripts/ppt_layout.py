"""
ppt_layout.py — paper2ppt 可复用布局工具库。
从 generate_ppt.py v5 提取，不含任何论文特定内容。
提供颜色常量、基础绘制函数、标题栏、结果页构建器。
"""
import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ═══════════════════════════════════════════
# 颜色调色板
# ═══════════════════════════════════════════

TEAL = RGBColor(0x00, 0x71, 0x91)          # 主色：标题、强调、标记
DARK = RGBColor(0x33, 0x33, 0x33)           # 正文色
GRAY = RGBColor(0xA5, 0xA5, 0xA5)           # 装饰灰线
WHITE = RGBColor(0xFF, 0xFF, 0xFF)           # 白色背景
NAVY = RGBColor(0x1A, 0x2E, 0x4A)           # 深海军蓝（封面/章节页背景）
LIGHT_TEAL = RGBColor(0xE0, 0xF0, 0xF5)     # 浅青色卡片背景
LIGHT_GREEN = RGBColor(0xE8, 0xF5, 0xE9)    # 浅绿色卡片背景
RED_ACCENT = RGBColor(0xD9, 0x4F, 0x4F)     # 红色强调
GREEN_ACCENT = RGBColor(0x2E, 0x7D, 0x32)   # 绿色强调
LIGHT_RED = RGBColor(0xFD, 0xED, 0xEC)      # 浅红色卡片背景
GOLD = RGBColor(0xD4, 0x8B, 0x2C)           # 金色
ORANGE = RGBColor(0xE0, 0x7B, 0x3A)         # 橙色（流程图第二步）
BLUE_SLATE = RGBColor(0x2E, 0x86, 0xAB)     # 石板蓝（流程图第四步）
BLUE_DEEP = RGBColor(0x1B, 0x5E, 0x7A)      # 深蓝（流程图第六步）

# 颜色名称 → RGBColor 映射表，供 JSON 中按名称引用颜色
COLOR_MAP = {
    'teal': TEAL, 'dark': DARK, 'gray': GRAY, 'white': WHITE, 'navy': NAVY,
    'light_teal': LIGHT_TEAL, 'light_green': LIGHT_GREEN,
    'red_accent': RED_ACCENT, 'green_accent': GREEN_ACCENT, 'light_red': LIGHT_RED,
    'gold': GOLD, 'orange': ORANGE, 'blue_slate': BLUE_SLATE, 'blue_deep': BLUE_DEEP,
}

# ═══════════════════════════════════════════
# 样式默认值
# ═══════════════════════════════════════════

FONT_EN = 'Times New Roman'    # 英文字体
FONT_CN = '微软雅黑'            # 中文字体
BODY_SIZE = Pt(16)             # 正文统一字号
IMG_W = 5.5                    # 图片统一宽度（英寸）


def parse_color(val):
    """
    解析颜色值，支持三种输入格式：
      1. 已经是 RGBColor 对象 → 直接返回
      2. COLOR_MAP 中的键名（如 'teal'）→ 查表返回
      3. 十六进制字符串（如 '#007191'）→ 解析为 RGBColor
    解析失败时返回默认深色 DARK。
    """
    if isinstance(val, RGBColor):
        return val
    if val in COLOR_MAP:
        return COLOR_MAP[val]
    if val.startswith('#'):
        h = val.lstrip('#')
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return DARK


def T(slide, l, t, w, h, text, sz=BODY_SIZE, bold=False, color=DARK, align=PP_ALIGN.LEFT):
    """
    【核心函数】在幻灯片上添加单行文本框。
    参数：
      slide: 幻灯片对象
      l, t, w, h: 位置和尺寸（英寸）
      text: 文本内容
      sz: 字号，默认 BODY_SIZE (16pt)
      bold: 是否加粗
      color: 文字颜色，支持字符串名称或 RGBColor
      align: 对齐方式
    返回: 文本框对象
    """
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True                     # 自动换行，防止文字溢出
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.name = FONT_EN
    r.font.size = sz
    r.font.bold = bold
    if color:
        r.font.color.rgb = parse_color(color) if isinstance(color, str) else color
    p.alignment = align
    return tb


def M(slide, l, t, w, h, lines, sz=BODY_SIZE, color=DARK):
    """
    【核心函数】在幻灯片上添加多行文本框。
    每行作为独立的段落（paragraph），行间距 2pt。
    参数：
      lines: 字符串列表，每个元素为一行
      color: 同时应用于所有行
    """
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        # 第一行复用默认段落，后续行通过 add_paragraph() 添加
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = line
        r.font.name = FONT_EN
        r.font.size = sz
        r.font.color.rgb = parse_color(color) if isinstance(color, str) else color
        p.space_after = Pt(2)
    return tb


def R(slide, l, t, w, h, fill_color, rounded=False, line_color=None):
    """
    【核心函数】添加填充矩形（或圆角矩形）。
    参数：
      fill_color: 填充色
      rounded: True=圆角矩形(PPT形状类型5), False=直角矩形(类型1)
      line_color: 边框色，None 表示无边框
    """
    st = 5 if rounded else 1              # PPT 形状类型：5=圆角矩形, 1=直角矩形
    rect = slide.shapes.add_shape(st, Inches(l), Inches(t), Inches(w), Inches(h))
    rect.fill.solid()
    rect.fill.fore_color.rgb = parse_color(fill_color) if isinstance(fill_color, str) else fill_color
    if line_color:
        rect.line.color.rgb = parse_color(line_color) if isinstance(line_color, str) else line_color
    else:
        rect.line.fill.background()       # 无边框
    return rect


def P(slide, path, l, t, w=None):
    """
    【核心函数】添加图片，保持原始宽高比。
    参数：
      path: 图片文件路径
      l, t: 左上角位置
      w: 目标宽度（英寸），默认使用 IMG_W (5.5in)；高度自动计算
    如果文件不存在，打印警告并返回 None。
    """
    if w is None:
        w = IMG_W
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found")
        return None
    try:
        pic = slide.shapes.add_picture(path, Inches(l), Inches(t))
        # 利用 PIL 内建的高/宽比计算目标高度，保持原比例
        ratio = pic.height / pic.width
        pic.width = Inches(w)
        pic.height = int(Inches(w) * ratio)
        return pic
    except Exception as e:
        print(f"  ERROR adding {path}: {e}")
        return None


def title_bar(slide, text):
    """
    【核心函数】绘制标准内容页标题栏。
    包含：青色加粗标题文字 + 左侧青色小矩形标记 + 标题下方灰色分隔线
          + 页面底部灰色和青色装饰条。
    所有位置和尺寸严格匹配模板第5页的样式。
    """
    # 标题文字：左侧 0.5in，上方 0.15in，24pt 加粗青色
    T(slide, 0.5, 0.15, 12.3, 0.55, text, sz=Pt(24), bold=True, color=TEAL)
    # 左侧小矩形标记（0.15×0.45 英寸青色块）
    r = slide.shapes.add_shape(1, Inches(0.3), Inches(0.25), Inches(0.15), Inches(0.45))
    r.fill.solid(); r.fill.fore_color.rgb = TEAL; r.line.fill.background()
    # 标题下方分隔线（浅灰色细线）
    l = slide.shapes.add_shape(1, Inches(0.6), Inches(0.68), Inches(12.1), Pt(1.5))
    l.fill.solid(); l.fill.fore_color.rgb = RGBColor(0xCC, 0xCC, 0xCC); l.line.fill.background()
    # 底部装饰条：上方灰色细条 + 下方青色粗条
    for y, c in [(7.2, GRAY), (7.3, TEAL)]:
        b = slide.shapes.add_shape(1, Inches(0), Inches(y), Inches(13.33), Inches(0.095 if y < 7.3 else 0.2))
        b.fill.solid(); b.fill.fore_color.rgb = c; b.line.fill.background()


def white_bg(slide):
    """
    为幻灯片添加全幅白色背景矩形。
    因为 python-pptx 新建幻灯片时可能继承模板的透明背景，
    需要显式覆盖为白色以确保内容页的一致性。
    """
    bg = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(7.5))
    bg.fill.solid(); bg.fill.fore_color.rgb = WHITE; bg.line.fill.background()


def blank_layout(prs):
    """
    查找演示文稿中的"空白"布局。
    "空白"布局不包含任何占位符，适合完全自定义的幻灯片。
    如果找不到，回退到第一个可用布局。
    """
    for ly in prs.slide_layouts:
        if '空白' in ly.name:
            return ly
    return prs.slide_layouts[0]


def make_result_slide(prs, title, body_lines, img_specs, figs_dir='.'):
    """
    【核心函数】构建标准结果内容页：左侧图片 + 右侧带圆点标记的文字行。

    布局逻辑：
      - 图片固定在左侧（x=0.3in），宽度统一 5.5in
      - 每行正文为独立文本框，前面有青色圆点标记
      - 行距根据行数动态调整：3行以内 0.9in，5行以内 0.7in
      - 空行自动过滤

    参数：
      prs: Presentation 对象
      title: 幻灯片标题
      body_lines: 正文列表（每元素一行，空行自动跳过）
      img_specs: [{'file': '1A.jpg', 'top_in': 1.05}, ...] 图片文件及垂直位置
      figs_dir: 图片所在目录
    返回: 幻灯片对象
    """
    slide = prs.slides.add_slide(blank_layout(prs))
    white_bg(slide)
    title_bar(slide, title)

    # 过滤空行并计算行距
    lines = [l for l in body_lines if l.strip()]
    n = len(lines)
    spacing = 0.9 if n <= 3 else (0.7 if n <= 5 else 5.4 / (n + 1))
    start_y = 1.4

    for i, line in enumerate(lines):
        y = start_y + i * spacing
        # 青色小圆点标记（椭圆形，填充青色，无边框）
        dot = slide.shapes.add_shape(9, Inches(6.8), Inches(y + 0.15), Inches(0.18), Inches(0.18))
        dot.fill.solid(); dot.fill.fore_color.rgb = TEAL; dot.line.fill.background()
        # 正文文本框
        T(slide, 7.15, y, 5.6, 0.45, line, sz=BODY_SIZE, color=DARK)

    # 添加图片
    for spec in img_specs:
        filename = spec['file']
        top_in = spec.get('top_in', 1.05)
        path = os.path.join(figs_dir, filename)
        P(slide, path, 0.3, top_in)

    return slide
