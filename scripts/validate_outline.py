#!/usr/bin/env python3
"""
validate_outline.py — 验证 slide-content.json 的结构完整性。
在生成 PPT 之前运行，确保所有必需字段存在且类型正确。

用法: python validate_outline.py <slide-content.json>
退出码: 0 = 有效, 1 = 存在错误

验证内容:
  - meta 必需字段（template_path, figs_dir, template_slide_indices）
  - slides 数组中每个元素的 type 是否合法
  - 各类型幻灯片的必需字段是否完整
  - toc_replacements 和 section_divider_edits 的格式
"""
import json, sys, os

# Schema 文件相对路径
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'slide-content-schema.json')


def validate(json_path):
    """
    验证 slide-content.json 的结构。

    验证逻辑分两层：
      1. meta 部分：检查模板路径、图片目录、幻灯片索引是否完整
      2. slides 数组：逐元素检查 type 合法性和必需字段

    参数:
      json_path: slide-content.json 文件路径
    返回:
      bool: 验证是否通过
    """
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errors = []

    # ═══ 验证 meta 部分 ═══
    if 'meta' not in data:
        errors.append("Missing 'meta' section")
    else:
        meta = data['meta']
        for key in ['template_path', 'figs_dir', 'template_slide_indices']:
            if key not in meta:
                errors.append(f"meta.{key} is required")
        indices = meta.get('template_slide_indices', {})
        for key in ['cover', 'toc', 'sections', 'thanks']:
            if key not in indices:
                errors.append(f"meta.template_slide_indices.{key} is required")

    # ═══ 验证 slides 数组 ═══
    if 'slides' not in data:
        errors.append("Missing 'slides' array")
    else:
        slides = data['slides']
        valid_types = {'keep', 'author', 'background', 'result', 'summary', 'discussion1', 'discussion2'}
        for i, slide in enumerate(slides):
            t = slide.get('type')
            if t not in valid_types:
                errors.append(f"slides[{i}]: unknown type '{t}'")
            elif t == 'keep':
                if 'ref' not in slide:
                    errors.append(f"slides[{i}] keep: missing 'ref'")
            elif t == 'result':
                # 结果页必须有标题、正文（数组）、图片（数组）
                for key in ['title', 'body', 'images']:
                    if key not in slide:
                        errors.append(f"slides[{i}] result: missing '{key}'")
                if 'body' in slide and not isinstance(slide['body'], list):
                    errors.append(f"slides[{i}] result: 'body' must be a list")
                if 'images' in slide:
                    for j, img in enumerate(slide['images']):
                        if 'file' not in img:
                            errors.append(f"slides[{i}] images[{j}]: missing 'file'")
            elif t == 'author':
                if 'journal' not in slide:
                    errors.append(f"slides[{i}] author: missing 'journal'")
            elif t == 'background':
                if 'cards' not in slide:
                    errors.append(f"slides[{i}] background: missing 'cards'")
            elif t == 'summary':
                if 'title' not in slide or 'flow_steps' not in slide:
                    errors.append(f"slides[{i}] summary: missing required fields")
            elif t == 'discussion1':
                if 'items' not in slide:
                    errors.append(f"slides[{i}] discussion1: missing 'items'")
            elif t == 'discussion2':
                for key in ['left_title', 'left_items', 'right_title', 'right_items']:
                    if key not in slide:
                        errors.append(f"slides[{i}] discussion2: missing '{key}'")

    # ═══ 验证可选部分格式 ═══
    if data.get('toc_replacements'):
        if not isinstance(data['toc_replacements'], dict):
            errors.append("toc_replacements must be a dict")
    if data.get('section_divider_edits'):
        for i, sde in enumerate(data['section_divider_edits']):
            if 'number' not in sde or 'title' not in sde:
                errors.append(f"section_divider_edits[{i}]: missing number/title")

    # ═══ 报告结果 ═══
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False

    print(f"VALID: {len(data['slides'])} slides defined")
    return True


def repair_and_validate(json_str):
    """
    尝试修复常见 LLM JSON 错误，返回 (repaired_json_str, warnings_list)。
    修复项：
      - 去除尾随逗号
      - 修复 Markdown 代码块包裹
      - 补全缺失的 meta 字段
      - 补全 slides 中缺失的必需字段
      - 修复 body 字段类型（字符串→列表）
    """
    warnings = []
    data = None

    # 1. 尝试解析 JSON
    for attempt_name, fixed_str in _try_parse_fixes(json_str):
        try:
            data = json.loads(fixed_str)
            if attempt_name != 'direct':
                warnings.append(f'JSON 语法修复: {attempt_name}')
            break
        except json.JSONDecodeError:
            continue

    if data is None:
        return None, ['JSON 无法解析，请检查语法']

    # 2. 补全结构
    if 'meta' not in data:
        data['meta'] = {}
        warnings.append('补全缺失字段: meta')
    meta = data['meta']
    for key, default in [('template_path', './template.pptx'), ('figs_dir', './figs'),
                          ('output_path', './output.pptx')]:
        if key not in meta:
            meta[key] = default
            warnings.append(f'补全缺失字段: meta.{key}')
    if 'template_slide_indices' not in meta:
        meta['template_slide_indices'] = {}
        warnings.append('补全缺失字段: meta.template_slide_indices (将由构建器自动检测)')

    if 'slides' not in data:
        data['slides'] = []
        warnings.append('补全缺失字段: slides (空数组)')

    # 3. 修复每个 slide
    for i, slide in enumerate(data['slides']):
        st = slide.get('type', '')
        if st == 'result':
            if 'title' not in slide:
                slide['title'] = f'结果 {i+1}'
                warnings.append(f'slides[{i}]: 补全缺失 title')
            if 'body' not in slide:
                slide['body'] = ['要点1', '要点2', '要点3']
                warnings.append(f'slides[{i}]: 补全缺失 body')
            elif isinstance(slide['body'], str):
                slide['body'] = [slide['body']]
                warnings.append(f'slides[{i}]: body 字符串→列表')
            if 'images' not in slide:
                slide['images'] = []
                warnings.append(f'slides[{i}]: 补全缺失 images')
        elif st == 'author':
            if 'journal' not in slide:
                slide['journal'] = {'name': ''}
        elif st == 'background':
            if 'cards' not in slide:
                slide['cards'] = []
        elif st == 'summary':
            if 'title' not in slide:
                slide['title'] = '研究总结'
            if 'flow_steps' not in slide:
                slide['flow_steps'] = []
        elif st == 'discussion1':
            if 'items' not in slide:
                slide['items'] = []
        elif st == 'discussion2':
            for key in ['left_title', 'left_items', 'right_title', 'right_items']:
                if key not in slide:
                    slide[key] = ''
                    warnings.append(f'slides[{i}]: 补全缺失 {key}')

    if 'cover' not in data:
        data['cover'] = {'title_en': '', 'presenter': 'xxx', 'date': '202X年X月'}
    if 'toc_replacements' not in data:
        data['toc_replacements'] = {}
    if 'section_divider_edits' not in data:
        data['section_divider_edits'] = [
            {'number': '01', 'title': '作者团队'},
            {'number': '02', 'title': '课题背景'},
            {'number': '03', 'title': '结果分析'},
            {'number': '04', 'title': '讨论'},
        ]

    repaired_str = json.dumps(data, indent=2, ensure_ascii=False)
    return repaired_str, warnings


def _try_parse_fixes(json_str):
    """尝试多种修复策略，生成器返回 (描述, 修复后字符串)。"""
    yield ('direct', json_str)

    # 去 Markdown 代码块
    s = json_str.strip()
    if s.startswith('```json'):
        s = s.split('```json', 1)[1]
        if '```' in s:
            s = s.split('```', 1)[0]
        yield ('去除```json标记', s.strip())
    elif s.startswith('```'):
        s = s[3:]
        if s.endswith('```'):
            s = s[:-3]
        yield ('去除```标记', s.strip())

    # 去除尾随逗号 (在 ] 或 } 之前的逗号)
    import re
    fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
    if fixed != json_str:
        yield ('去除尾随逗号', fixed)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <slide-content.json>")
        sys.exit(1)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
