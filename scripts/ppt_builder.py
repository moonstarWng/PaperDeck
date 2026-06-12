#!/usr/bin/env python3
"""
ppt_builder.py — paper2ppt 的 JSON 驱动 PPT 组装器。
读取 slide-content.json，加载模板 PPTX，构建所有幻灯片，
编辑模板页（封面/目录/章节/致谢），按计划重排序，保存最终 PPTX。

用法: python ppt_builder.py <slide-content.json>
"""
import copy, json, os, sys
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 将 scripts 目录加入路径，支持同目录导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ppt_layout import (
    FONT_EN, FONT_CN, BODY_SIZE, TEAL, DARK, WHITE,
    blank_layout, make_result_slide, parse_color, init_design,
)
from ppt_slides import (
    build_author_slide, build_background_slide, build_summary_slide,
    build_discussion1_slide, build_discussion2_slide, build_paper_info_slide,
)

# PPTX 内部 XML 命名空间，用于直接操作幻灯片列表和文本元素
NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def load_json(path):
    """从文件加载 JSON 配置。"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_path(json_path, relative_path):
    """
    将 slide-content.json 中的相对路径解析为绝对路径。
    所有路径相对于 JSON 文件所在目录解析，避免工作目录依赖。
    """
    if os.path.isabs(relative_path):
        return relative_path
    json_dir = os.path.dirname(os.path.abspath(json_path))
    return os.path.normpath(os.path.join(json_dir, relative_path))


# ═══════════════════════════════════════════
# 模板幻灯片编辑器（仅修改文字，不修改任何图形元素）
# ═══════════════════════════════════════════

def edit_cover(slide, cover_data, tmpl_path=''):
    """
    修改封面幻灯片文字。
    通过位置特征识别标题区域和汇报人区域，替换文字内容。

    封面模板特征：
      - 标题区：垂直位置 2.0-3.0in，高度 > 1.0in（大号文字框）
      - 汇报人区：垂直位置 5.0-6.0in，水平位置 > 5.0in，宽度 < 4.0in（右下角小文字框）

    注意：汇报人区的原始宽度仅约 2.1in，需扩大至 4.5in 才能容纳完整信息。
    """
    title_en = cover_data.get('title_en', '')
    presenter = cover_data.get('presenter', 'xxx')
    date = cover_data.get('date', '')

    # 收集所有文本形状（用于智能识别标题和汇报人位置）
    text_shapes = []
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            t = shape.top / 914400
            l = shape.left / 914400
            w = shape.width / 914400
            h = shape.height / 914400
            text_shapes.append((shape, t, l, w, h, shape.text_frame.text.strip()))

    if not text_shapes:
        return

    # 标题 = 面积最大的文本框（宽度 > 3in 且高度 > 0.5in）
    candidates = [s for s in text_shapes if s[3] > 3 and s[4] > 0.5]
    title_shape = max(candidates, key=lambda s: s[3] * s[4]) if candidates else max(text_shapes, key=lambda s: len(s[5]))

    # 汇报人 = 含关键词 或 下半部分小文本框
    presenter_shape = None
    for s in text_shapes:
        txt = s[5].lower()
        if '汇报人' in txt or 'presenter' in txt:
            presenter_shape = s
            break
    if not presenter_shape:
        small = [s for s in text_shapes if s[1] > 3.5 and s[3] < 6 and s[4] < 1.0 and s != title_shape]
        if small:
            presenter_shape = min(small, key=lambda s: s[3] * s[4])

    # 标题字体：尝试从 design.json 读取 cover_title
    title_font = FONT_EN
    title_sz = Pt(32)
    try:
        import json as _json
        dj = tmpl_path.replace('.pptx', '_design.json')
        if os.path.exists(dj):
            with open(dj, 'r', encoding='utf-8') as f:
                ct = _json.load(f).get('cover_title', {})
                if ct.get('font_name'): title_font = ct['font_name']
                if ct.get('font_size_pt'): title_sz = Pt(ct['font_size_pt'])
    except: pass

    # 替换标题文字
    tf = title_shape[0].text_frame; tf.clear()
    for i, line in enumerate(title_en.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = line
        r.font.name = title_font; r.font.size = title_sz; r.font.bold = True

    # 替换汇报人文字
    if presenter_shape:
        ps = presenter_shape[0]
        if ps.width / 914400 < 4.0:
            ps.width = Inches(4.5)
        tf = ps.text_frame; tf.clear()
        p = tf.paragraphs[0]
        r1 = p.add_run(); r1.text = '汇报人：'
        r1.font.name = FONT_EN; r1.font.size = Pt(20); r1.font.bold = True
        r2 = p.add_run(); r2.text = f'{presenter}    '
        r2.font.name = FONT_CN; r2.font.size = Pt(20); r2.font.bold = True
        if date:
            r3 = p.add_run(); r3.text = date
            r3.font.name = FONT_EN; r3.font.size = Pt(16)


def edit_toc(slide, toc_map):
    """
    修改目录页文字。
    通过遍历幻灯片 XML 中的所有 <a:t> 文本元素进行查找替换。
    必须使用 XML 级别操作而非 python-pptx 的 shape 遍历，
    因为目录页的文本分散在深层 GROUP 嵌套中，shape.has_text_frame 无法穿透。
    """
    if not toc_map:
        return
    for t_elem in slide._element.iter(f'{{{NS_A}}}t'):
        if t_elem.text:
            for old, new in toc_map.items():
                if old in t_elem.text:
                    t_elem.text = t_elem.text.replace(old, new)


def edit_section_divider(slide, number, title):
    """
    修改章节分隔页的编号和标题文字。
    编号特征：恰好2位数字
    标题特征：包含中文字符
    """
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            # 匹配两位数字编号（如 '01', '02'）
            if text.isdigit() and len(text) == 2:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.text.strip().isdigit() and len(run.text.strip()) == 2:
                            run.text = number
            # 匹配章节标题：中文或英文（只要不是纯数字且长度≥2）
            elif len(text) >= 2 and not text.isdigit():
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if not run.text.strip().isdigit() and len(run.text.strip()) >= 2:
                            run.text = title


# ═══════════════════════════════════════════
# 主编排器
# ═══════════════════════════════════════════

def build(config, json_path='.'):
    """
    主编排函数：加载模板 → 构建所有幻灯片 → 编辑模板页 → 重排序 → 保存。

    工作流程：
      1. 从 meta 中读取模板路径、输出路径、图片目录、模板幻灯片索引
      2. 按 slides 数组顺序构建所有内容幻灯片（追加到模板幻灯片末尾）
      3. 编辑模板幻灯片（封面/目录/章节分隔页）的文字
      4. 通过操作 sldIdLst XML 重排序所有幻灯片
      5. 保存最终 PPTX
    """
    meta = config.get('meta', {})
    # 将 JSON 中的相对路径解析为绝对路径
    template_path = resolve_path(json_path, meta.get('template_path', 'template.pptx'))
    output_path = resolve_path(json_path, meta.get('output_path', 'output.pptx'))
    figs_dir = resolve_path(json_path, meta.get('figs_dir', './figs'))
    indices = meta.get('template_slide_indices', {})

    # 加载模板设计令牌
    design_json = template_path.replace('.pptx', '_design.json')
    init_design(design_json)

    prs = Presentation(template_path)
    print(f"Template: {len(prs.slides)} slides")

    # 自动检测模板幻灯片索引（如果 JSON 中未指定或指定了不完整的）
    from make_template import classify
    auto_indices = {'cover': 0, 'toc': 1, 'sections': [], 'thanks': len(prs.slides) - 1}
    for i, slide in enumerate(prs.slides):
        cat = classify(slide)
        if cat == 'COVER':
            auto_indices['cover'] = i
        elif cat == 'TOC':
            auto_indices['toc'] = i
        elif cat.startswith('SECTION_'):
            auto_indices['sections'].append(i)
        elif cat == 'THANKS':
            auto_indices['thanks'] = i
    auto_indices['sections'].sort()
    # JSON 中的值覆盖自动检测值（允许用户手动指定）
    for key in ['cover', 'toc', 'thanks']:
        if key in indices:
            auto_indices[key] = indices[key]
    if 'sections' in indices and indices['sections']:
        auto_indices['sections'] = indices['sections']
    indices = auto_indices

    slides_plan = config.get('slides', [])
    section_divider_map = config.get('section_divider_edits', [])
    section_indices = indices.get('sections', [])

    new_order = []          # 最终幻灯片排列顺序（模板原始索引 + 新幻灯片索引）
    section_used = 0        # 跟踪下一次使用哪个章节分隔页

    # 幻灯片类型 → 构建函数的映射表
    slide_builders = {
        'author': build_author_slide,
        'background': build_background_slide,
        'summary': build_summary_slide,
        'discussion1': build_discussion1_slide,
        'discussion2': build_discussion2_slide,
        'paper_info': build_paper_info_slide,
    }

    # ── 遍历构建计划，逐一创建幻灯片 ──
    for item in slides_plan:
        stype = item.get('type')

        if stype == 'keep':
            # 保留模板原始幻灯片：按 ref 引用名映射到实际索引
            ref = item.get('ref')
            if ref == 'cover':
                new_order.append(indices.get('cover', 0))
            elif ref == 'toc':
                new_order.append(indices.get('toc', 1))
            elif ref == 'thanks':
                new_order.append(indices.get('thanks', 7))
            elif ref == 'section':
                idx = item.get('index', section_used)
                section_used = idx + 1
                if idx < len(section_indices):
                    new_order.append(section_indices[idx])
                else:
                    print(f"  WARNING: section index {idx} out of range")

        elif stype == 'result':
            # 结果内容页：标题 + 正文 + 图片
            title = item.get('title', '')
            body = item.get('body', [])
            imgs = item.get('images', [])
            make_result_slide(prs, title, body, imgs, figs_dir)
            new_order.append(len(prs.slides) - 1)
            print(f"  Result: {title[:60]}")

        elif stype in slide_builders:
            # 解析 paper_info 的相对路径
            if stype == 'paper_info' and item.get('pdf_path'):
                item['pdf_path'] = resolve_path(json_path, item['pdf_path'])
            slide_builders[stype](prs, item)
            new_order.append(len(prs.slides) - 1)
            print(f"  {stype}: {item.get('title', '')[:60]}")

        else:
            print(f"  WARNING: unknown slide type '{stype}'")

    print(f"\nBuilt {len(new_order)} slides in plan")

    # ── 编辑模板幻灯片文字 ──
    print("Editing template slides...")
    if 'cover' in config:
        edit_cover(prs.slides[indices.get('cover', 0)], config['cover'], template_path)
    if 'toc_replacements' in config:
        edit_toc(prs.slides[indices.get('toc', 1)], config['toc_replacements'])
    for i, sde in enumerate(section_divider_map):
        if i < len(section_indices):
            edit_section_divider(prs.slides[section_indices[i]], sde['number'], sde['title'])
    # 致谢页保持模板原文，不做任何修改

    # ── 重排序幻灯片 ──
    # python-pptx 不支持原生重排序，需直接操作 sldIdLst XML
    print("Reordering slides...")
    pres_elem = prs.part._element
    sldIdLst = pres_elem.find(f'{{{NS_P}}}sldIdLst')
    if sldIdLst is not None:
        all_ids = list(sldIdLst)
        # 清空当前顺序
        for c in list(sldIdLst):
            sldIdLst.remove(c)
        # 按 new_order 重新插入（使用 deepcopy 避免引用冲突）
        for i in new_order:
            if i < len(all_ids):
                sldIdLst.append(copy.deepcopy(all_ids[i]))
    print(f"Final: {len(prs.slides)} slides")

    # ── 保存 ──
    print(f"\nSaving {output_path}...")
    prs.save(output_path)
    print(f"DONE: {output_path}")
    return output_path


def main():
    """命令行入口：接收 slide-content.json 路径，执行完整构建流程。"""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <slide-content.json>")
        sys.exit(1)
    config = load_json(sys.argv[1])
    build(config, sys.argv[1])


if __name__ == '__main__':
    main()
