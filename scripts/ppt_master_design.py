#!/usr/bin/env python3
"""
ppt_master_design.py — 从 ppt-master 主题数据构建 template_design.json。

将 pptx_to_svg 的 theme_colors/fonts 和 analyze_pptx 的 slide_library
映射为 PaperDeck 兼容的 template_design.json 格式。

用法:
    from scripts.ppt_master_design import build_design_json_from_theme
    design = build_design_json_from_theme(theme_colors, theme_fonts, slide_library)
"""

from __future__ import annotations
import re


def _hex_to_rgb_str(hex_color: str) -> str:
    """'#1F497D' → '1F497D'"""
    return hex_color.lstrip('#').upper()


def _px_to_pt(px: float | None) -> int | None:
    """像素 → pt (96dpi → 72dpi)"""
    if px is None:
        return None
    return round(px * 0.75)


def _parse_px(value) -> float | None:
    """安全解析像素值。"""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════
# 从 slide_library 提取字体/位置信息
# ═══════════════════════════════════════════


def _get_slide_by_type(slides: list[dict], page_type: str) -> dict | None:
    """获取第一个匹配 page_type 的 slide。"""
    for s in slides:
        if s.get('page_type') == page_type:
            return s
    return None


def _get_largest_text_slot(slide: dict) -> dict | None:
    """获取 slide 中文本最多的 slot（通常是最重要的标题/正文）。"""
    best = None
    best_len = 0
    for slot in slide.get('slots', []):
        text = slot.get('text', '').strip()
        if len(text) > best_len:
            best_len = len(text)
            best = slot
    return best


def _get_slot_font_info(slot: dict | None) -> dict:
    """从 slot 提取字体信息，转换为 template_design.json 格式。"""
    if slot is None:
        return {}
    metrics = slot.get('text_metrics', {})
    info = {}
    font_size_px = metrics.get('font_size_px')
    if font_size_px:
        info['font_size_pt'] = _px_to_pt(font_size_px)
    return info


def _extract_slide_fonts(slides: list[dict], page_type: str, role_filter: str = None) -> dict:
    """
    从指定类型的 slide 中提取字体信息。

    参数:
        slides: slide_library['slides'] 列表
        page_type: 要匹配的 page_type
        role_filter: 可选，只匹配特定 role 的 slot (如 'title_candidate')
    """
    result = {}
    for slide in slides:
        if slide.get('page_type') != page_type:
            continue
        for slot in slide.get('slots', []):
            if role_filter and slot.get('role') != role_filter:
                continue
            metrics = slot.get('text_metrics', {})
            if metrics.get('font_size_px'):
                result['font_size_pt'] = _px_to_pt(metrics['font_size_px'])
                break
        if result:
            break
    return result


# ═══════════════════════════════════════════
# 主题色 → PaperDeck 调色板 映射
# ═══════════════════════════════════════════


def _derive_content_colors(theme_colors: dict) -> dict:
    """
    从主题色推导内容页颜色。

    PPT 主题色语义:
      - dk1: 深色1 (通常是黑色, 正文色)
      - lt1: 浅色1 (通常是白色, 背景色)
      - dk2: 深色2 (深色强调, 常用于章节页背景)
      - lt2: 浅色2
      - accent1-6: 强调色 (accent1 是主题色)

    PaperDeck 需要的颜色:
      - content_body.color ← dk1 (正文用深色)
      - content_title.color ← accent1 (标题用强调色)
      - PALETTE_PRIMARY ← accent1
      - PALETTE_DARK ← dk2 (章节页深色背景)
      - section_bg_color ← dk2
      - cover_bg_color ← lt1
    """
    dk1 = theme_colors.get('dk1', '#000000')
    accent1 = theme_colors.get('accent1', '#4F81BD')
    dk2 = theme_colors.get('dk2', '#1F497D')
    lt1 = theme_colors.get('lt1', '#FFFFFF')

    return {
        'body_color': _hex_to_rgb_str(dk1),
        'title_color': _hex_to_rgb_str(accent1),
        'accent_color': _hex_to_rgb_str(accent1),
        'primary_color': _hex_to_rgb_str(accent1),
        'dark_bg_color': _hex_to_rgb_str(dk2),
        'light_bg_color': _hex_to_rgb_str(lt1),
    }


def _derive_palette_from_theme(theme_colors: dict) -> dict:
    """
    从主题色构建 PaperDeck compatible 调色板信息。
    返回的内容会被 ppt_layout.py 的 derive_palette() 使用。
    """
    accent1 = theme_colors.get('accent1', '#4F81BD')
    dk2 = theme_colors.get('dk2', '#1F497D')

    return {
        'primary': _hex_to_rgb_str(accent1),
        'dark': _hex_to_rgb_str(dk2),
    }


# ═══════════════════════════════════════════
# 主导出函数
# ═══════════════════════════════════════════


def build_design_json_from_theme(
    theme_colors: dict[str, str],
    theme_fonts: dict[str, str],
    slide_library: dict,
) -> dict:
    """
    从 ppt-master 主题数据构建 template_design.json。

    参数:
        theme_colors:  pptx_to_svg 提取的 12 色主题色板
        theme_fonts:   pptx_to_svg 提取的字体方案
        slide_library: analyze_pptx 返回的 slide 结构分析

    返回:
        兼容 template_design.json 格式的 dict，额外包含:
          - "_source": "pptmaster" (标记来源)
          - "theme": {colors, fonts} (原始主题数据)
    """
    slides = slide_library.get('slides', [])
    colors = _derive_content_colors(theme_colors)
    palette = _derive_palette_from_theme(theme_colors)

    # ── 字体 ──
    major_font = theme_fonts.get('majorLatin', 'Calibri')
    minor_font = theme_fonts.get('minorLatin', 'Calibri')
    # 东亚字体优先
    ea_font = theme_fonts.get('majorEastAsia', '') or theme_fonts.get('minorEastAsia', '')

    body_font = ea_font or minor_font
    title_font = ea_font or major_font

    # ── 封面页 ──
    cover_slide = _get_slide_by_type(slides, 'cover_candidate')
    cover_title_slot = _get_largest_text_slot(cover_slide) if cover_slide else None
    cover_title_info = _get_slot_font_info(cover_title_slot)
    cover_title = {
        'font_name': title_font,
        'font_size_pt': cover_title_info.get('font_size_pt', 38),
        'bold': True,
        'color': colors.get('title_color', '000000'),
    }

    # ── 内容页标题 ──
    # 从 content_candidate slide 中找 title_candidate role 的 slot
    content_title_extra = _extract_slide_fonts(slides, 'content_candidate', 'title_candidate')
    # 如果没有 content_candidate，用 chapter_candidate
    if not content_title_extra:
        # 从 chapter slide 找 title（如 "2 Section Title"）
        chapter_slide = _get_slide_by_type(slides, 'chapter_candidate')
        ch_title = _get_largest_text_slot(chapter_slide) if chapter_slide else None
        content_title_extra = _get_slot_font_info(ch_title)

    content_title = {
        'font_name': title_font,
        'font_size_pt': content_title_extra.get('font_size_pt', 24),
        'bold': True,
        'color': colors.get('title_color', '000000'),
    }

    # ── 内容页正文 ──
    content_body = {
        'font_name': body_font,
        'font_size_pt': 18,  # 默认 18pt，ppt-master 通常不区分 body size
        'bold': False,
        'color': colors.get('body_color', '333333'),
    }

    # ── 章节页 ──
    chapter_slide = _get_slide_by_type(slides, 'chapter_candidate')
    chapter_num_slot = None
    chapter_title_slot = None
    if chapter_slide:
        for slot in chapter_slide.get('slots', []):
            text = slot.get('text', '').strip()
            if text.isdigit() and len(text) <= 2:
                chapter_num_slot = slot
            elif len(text) > 2 and not text.isdigit():
                if chapter_title_slot is None:
                    chapter_title_slot = slot

    section_number = {
        'font_name': title_font,
        'font_size_pt': _get_slot_font_info(chapter_num_slot).get('font_size_pt', 56),
        'bold': True,
        'color': colors.get('light_bg_color', 'FFFFFF'),  # 深色底上白字
    }
    section_title = {
        'font_name': title_font,
        'font_size_pt': _get_slot_font_info(chapter_title_slot).get('font_size_pt', 28),
        'bold': True,
        'color': colors.get('light_bg_color', 'FFFFFF'),
    }

    # ── 目录页 ──
    toc_slide = _get_slide_by_type(slides, 'toc_candidate')
    toc_num_slot = None
    toc_item_slot = None
    if toc_slide:
        for slot in toc_slide.get('slots', []):
            text = slot.get('text', '').strip()
            if text.isdigit() and len(text) <= 2:
                if toc_num_slot is None:
                    toc_num_slot = slot
            elif len(text) > 2:
                if toc_item_slot is None:
                    toc_item_slot = slot

    toc_number = {
        'font_name': title_font,
        'font_size_pt': _get_slot_font_info(toc_num_slot).get('font_size_pt', 24),
        'bold': True,
        'color': colors.get('accent_color', '000000'),
    }
    toc_item = {
        'font_name': body_font,
        'font_size_pt': _get_slot_font_info(toc_item_slot).get('font_size_pt', 18),
        'bold': False,
        'color': colors.get('body_color', '333333'),
    }

    # ── 致谢页 ──
    thanks_slide = _get_slide_by_type(slides, 'ending_candidate')
    thanks_slot = _get_largest_text_slot(thanks_slide) if thanks_slide else None
    thanks_title = {
        'font_name': title_font,
        'font_size_pt': _get_slot_font_info(thanks_slot).get('font_size_pt', 48),
        'bold': True,
        'color': colors.get('title_color', '000000'),
    }

    # ── 页脚栏 / 页眉装饰 ──
    # 从 slide_library 无法直接提取非文本形状。
    # 留空，下游 init_design() 会使用默认值或 template_extractor 的结果。
    footer_bars = []
    header_decorations = []

    # ── 组装最终 JSON ──
    design = {
        '_source': 'pptmaster',
        'meta': {
            'source': slide_library.get('source_pptx', ''),
            'total_slides': slide_library.get('slide_count', 0),
        },
        'content_title': content_title,
        'content_body': content_body,
        'footer_bars': footer_bars,
        'header_decorations': header_decorations,
        'cover_title': cover_title,
        'cover_presenter': {},
        'cover_bg_color': colors.get('light_bg_color', 'FFFFFF'),
        'section_number': section_number,
        'section_title': section_title,
        'section_bg_color': colors.get('dark_bg_color', '1F497D'),
        'toc_number': toc_number,
        'toc_item': toc_item,
        'thanks_title': thanks_title,
        'default_font': body_font,
        # 新增：原始主题数据，供下游增强使用
        'theme': {
            'colors': {k: _hex_to_rgb_str(v) for k, v in theme_colors.items()},
            'fonts': theme_fonts,
            'palette_primary': palette.get('primary', ''),
            'palette_dark': palette.get('dark', ''),
        },
    }

    return design


# ═══════════════════════════════════════════
# 增强现有的 template_design.json
# ═══════════════════════════════════════════


def enhance_existing_design(existing_design: dict, theme_colors: dict, theme_fonts: dict) -> dict:
    """
    用 ppt-master 主题数据增强已有的 template_design.json。

    只填充现有设计 JSON 中缺失的字段，不覆盖已有数据。

    参数:
        existing_design: 现有的 template_design.json 内容
        theme_colors:    pptx_to_svg 的主题色
        theme_fonts:     pptx_to_svg 的字体方案

    返回:
        增强后的 dict（修改原对象）
    """
    colors = _derive_content_colors(theme_colors)
    major_font = theme_fonts.get('majorLatin', '')
    minor_font = theme_fonts.get('minorLatin', '')
    ea_font = theme_fonts.get('majorEastAsia', '') or theme_fonts.get('minorEastAsia', '')
    body_font = ea_font or minor_font
    title_font = ea_font or major_font

    # 补充缺失的字体字段
    if body_font:
        for key in ('content_body', 'toc_item'):
            if key in existing_design and not existing_design[key].get('font_name'):
                existing_design[key]['font_name'] = body_font

        if not existing_design.get('default_font'):
            existing_design['default_font'] = body_font

    if title_font:
        for key in ('content_title', 'cover_title', 'section_number',
                     'section_title', 'toc_number', 'thanks_title'):
            if key in existing_design and not existing_design[key].get('font_name'):
                existing_design[key]['font_name'] = title_font

    # 补充缺失的颜色字段
    body_color = colors.get('body_color', '')
    title_color = colors.get('title_color', '')
    dark_bg = colors.get('dark_bg_color', '')

    if body_color:
        for key in ('content_body', 'toc_item'):
            if key in existing_design and not existing_design[key].get('color'):
                existing_design[key]['color'] = body_color

    if title_color:
        for key in ('content_title', 'cover_title', 'toc_number', 'thanks_title'):
            if key in existing_design and not existing_design[key].get('color'):
                existing_design[key]['color'] = title_color

    if dark_bg:
        if not existing_design.get('section_bg_color'):
            existing_design['section_bg_color'] = dark_bg

    # 追加主题数据
    existing_design['theme'] = {
        'colors': {k: _hex_to_rgb_str(v) for k, v in theme_colors.items()},
        'fonts': theme_fonts,
    }

    return existing_design
