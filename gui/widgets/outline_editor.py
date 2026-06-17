"""
gui/widgets/outline_editor.py — 大纲树形编辑器。
可展开/折叠的树形结构，内联编辑标题和要点，拖拽配图。
"""
import customtkinter as ctk
from tkinter import messagebox
import json, os


# 幻灯片类型 → 颜色映射（深色主题）
TYPE_COLORS = {
    'paper_info': '#2E7D32',
    'author': '#1A6B7A',
    'background': '#5C3D8F',
    'result': '#007191',
    'summary': '#D48B2C',
    'discussion1': '#B84C3D',
    'discussion2': '#9B4D8A',
}


def _is_long_text(value):
    """判断文本是否适合多行文本框（>40 字符或含换行）。"""
    return len(value) > 40 or '\n' in value


class OutlineEditor(ctk.CTkScrollableFrame):
    """可滚动的大纲树形编辑器。"""

    def __init__(self, master, figs_dir='', **kwargs):
        super().__init__(master, **kwargs)
        self.figs_dir = figs_dir
        self.sections = []          # [{type, title, expanded, rows, images?}]
        self.widgets = {}           # section_index -> content frame
        self._dirty = False         # 标记是否有未保存的修改
        self._build_placeholder()

    def set_figs_dir(self, path):
        self.figs_dir = path

    # ═══════════════════════════════════════════
    # JSON 加载 / 导出
    # ═══════════════════════════════════════════

    def load_from_json(self, json_str):
        import sys, os as _os
        sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', 'scripts'))
        from validate_outline import repair_and_validate
        repaired, warnings = repair_and_validate(json_str)
        if repaired is None:
            messagebox.showerror("JSON 解析错误", warnings[0] if warnings else "无法解析")
            return False
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON 解析错误", str(e))
            return False
        if warnings:
            print(f'[outline_editor] JSON 修复: {warnings}')
        self.sections = self._parse_slides(data.get('slides', []))
        self._dirty = False
        self._rebuild()
        return True

    def is_dirty(self):
        return self._dirty

    def to_json(self, meta_overrides=None):
        self._gather_edits()
        slides = []
        for sec in self.sections:
            st = sec['type']
            if st == 'keep':
                keep = {"type": "keep", "ref": sec['ref']}
                if sec.get('index') is not None:
                    keep['index'] = sec['index']
                slides.append(keep)
            elif st == 'paper_info':
                rows = {k: v for k, v in sec.get('rows', [])}
                slides.append({'type': 'paper_info',
                               'paper_title': rows.get('标题', ''),
                               'extra_text': rows.get('备注', '')})
            elif st == 'author':
                slides.append(self._build_author_slide(sec))
            elif st == 'background':
                slides.append(self._build_background_slide(sec))
            elif st == 'result':
                slides.append(self._build_result_slide(sec))
            elif st == 'summary':
                slides.append(self._build_summary_slide(sec))
            elif st == 'discussion1':
                slides.append(self._build_discussion1_slide(sec))
            elif st == 'discussion2':
                slides.append(self._build_discussion2_slide(sec))
        return json.dumps({"slides": slides}, indent=2, ensure_ascii=False)

    # ═══════════════════════════════════════════
    # JSON ↔ 内部树
    # ═══════════════════════════════════════════

    def _parse_slides(self, slides):
        result = []
        for slide in slides:
            st = slide.get('type', '')
            if st == 'keep':
                result.append({'type': 'keep', 'ref': slide.get('ref', ''),
                               'expanded': False, 'rows': [], 'index': slide.get('index')})
            elif st == 'paper_info':
                result.append({'type': 'paper_info', 'expanded': True, 'rows': [
                    ('标题', slide.get('paper_title', '')),
                    ('备注', slide.get('extra_text', '')),
                ], 'images': []})
            elif st == 'author':
                result.append({'type': 'author', 'expanded': True,
                    'rows': [
                        ('期刊', slide.get('journal', {}).get('name', '')),
                        ('IF', slide.get('journal', {}).get('if', '')),
                        ('作者', slide.get('authors', '')),
                        ('机构', '\n'.join(slide.get('institutions', []))),
                    ], 'images': []})
            elif st == 'background':
                cards = slide.get('cards', [])
                rows = [('假说', slide.get('hypothesis', ''))]
                for i, c in enumerate(cards):
                    rows.append((f'卡片{i+1}: {c.get("title", "")}', c.get('body', '')))
                result.append({'type': 'background', 'expanded': True, 'rows': rows, 'images': []})
            elif st == 'result':
                rows = [(f'要点{i+1}', line) for i, line in enumerate(slide.get('body', []))]
                imgs = [img.get('file', '') for img in slide.get('images', [])]
                result.append({'type': 'result', 'title': slide.get('title', ''),
                    'expanded': True, 'rows': rows, 'images': imgs})
            elif st == 'summary':
                steps = [s.get('text', '') for s in slide.get('flow_steps', [])]
                cards = [c.get('title', '') + ': ' + c.get('detail', '')
                         for c in slide.get('evidence_cards', [])]
                result.append({'type': 'summary', 'title': slide.get('title', ''),
                    'expanded': True, 'rows': [('步骤', '\n'.join(steps)),
                                               ('证据', '\n'.join(cards))], 'images': []})
            elif st == 'discussion1':
                items = slide.get('items', [])
                rows = [(it.get('title', ''), it.get('detail', '')) for it in items]
                result.append({'type': 'discussion1', 'title': slide.get('title', ''),
                    'expanded': True, 'rows': rows, 'images': []})
            elif st == 'discussion2':
                result.append({'type': 'discussion2', 'title': slide.get('title', ''),
                    'expanded': True,
                    'rows': [('左栏', '\n'.join(slide.get('left_items', []))),
                             ('右栏', '\n'.join(slide.get('right_items', [])))], 'images': []})
        return result

    # ═══════════════════════════════════════════
    # 树 → JSON 构建器
    # ═══════════════════════════════════════════

    def _build_result_slide(self, sec):
        body = [v for _, v in sec.get('rows', []) if v and not v.startswith('[图')]
        images = [{'file': f, 'top_in': 1.05 + i * 2.8}
                  for i, f in enumerate(sec.get('images', []))]
        return {'type': 'result', 'title': sec.get('title', ''), 'body': body, 'images': images}

    def _build_author_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        return {'type': 'author',
                'journal': {'name': d.get('期刊', ''), 'if': d.get('IF', '')},
                'authors': d.get('作者', ''),
                'institutions': d.get('机构', '').split('\n') if d.get('机构') else [],
                'prior_work': []}

    def _build_background_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        cards = []
        for k, v in sec.get('rows', []):
            if k.startswith('卡片'):
                title = k.split(': ', 1)[1] if ': ' in k else k
                cards.append({'title': title, 'body': v, 'color': 'teal'})
        return {'type': 'background', 'cards': cards,
                'hypothesis': d.get('假说', '')}

    def _build_summary_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        steps = [{'text': s.strip(), 'color': 'teal'}
                 for s in d.get('步骤', '').split('\n') if s.strip()]
        cards = []
        for line in d.get('证据', '').split('\n'):
            if ': ' in line:
                t, de = line.split(': ', 1)
                cards.append({'title': t, 'detail': de})
        return {'type': 'summary', 'title': sec.get('title', ''),
                'flow_steps': steps, 'evidence_cards': cards}

    def _build_discussion1_slide(self, sec):
        items = [{'number': str(i+1), 'title': t, 'detail': d}
                 for i, (t, d) in enumerate(sec.get('rows', []))]
        return {'type': 'discussion1', 'title': sec.get('title', ''), 'items': items}

    def _build_discussion2_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        return {'type': 'discussion2', 'title': sec.get('title', ''),
                'left_title': '局限性',
                'left_items': [l for l in d.get('左栏', '').split('\n') if l.strip()],
                'right_title': '临床意义',
                'right_items': [l for l in d.get('右栏', '').split('\n') if l.strip()]}

    # ═══════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════

    def _build_placeholder(self):
        for w in self.winfo_children():
            w.destroy()
        ctk.CTkLabel(self, text="请先生成或加载大纲", text_color="gray",
                     font=ctk.CTkFont(size=14)).pack(pady=40)

    def _gather_edits(self):
        """收集所有编辑框的修改写回 self.sections。"""
        for i, sec in enumerate(self.sections):
            if sec['type'] == 'keep' or i not in self.widgets:
                continue
            content = self.widgets[i]
            try:
                if not content.winfo_exists():
                    continue
            except Exception:
                continue

            # 收集标题（result 类型）
            for c in _iter_children(content):
                if isinstance(c, ctk.CTkEntry) and getattr(c, '_outline_role', '') == 'title':
                    sec['title'] = c.get().strip()
                    self._dirty = True

            # 收集所有行编辑框
            for c in _iter_children(content):
                if not isinstance(c, ctk.CTkFrame):
                    continue
                role = getattr(c, '_outline_role', '')
                if role not in ('row', 'row_textbox'):
                    continue
                idx = getattr(c, '_row_index', -1)
                if idx < 0:
                    continue
                rows = sec.get('rows', [])
                if idx >= len(rows):
                    continue
                label = rows[idx][0]
                if role == 'row_textbox':
                    val = getattr(c, '_textbox', None)
                    if val:
                        rows[idx] = (label, val.get("1.0", "end-1c"))
                        self._dirty = True
                else:
                    for child in c.winfo_children():
                        if isinstance(child, ctk.CTkEntry):
                            rows[idx] = (label, child.get().strip())
                            self._dirty = True

    def _rebuild(self):
        self._gather_edits()
        for w in self.winfo_children():
            w.destroy()
        self.widgets.clear()
        if not self.sections:
            self._build_placeholder()
            return

        type_names = {
            'keep': '', 'paper_info': '论文信息', 'author': '作者团队',
            'background': '课题背景', 'result': '结果页',
            'summary': '结果总结', 'discussion1': '讨论分析①',
            'discussion2': '讨论分析②',
        }

        for i, sec in enumerate(self.sections):
            st = sec['type']

            # ── keep 类型：简洁标签 ──
            if st == 'keep':
                ref = sec.get('ref', '')
                label_map = {'cover': '封面', 'toc': '目录', 'section': f'章节分隔 {sec.get("index", "")}',
                             'thanks': '致谢'}
                label = label_map.get(ref, ref)
                row = ctk.CTkFrame(self, height=28, fg_color="#2A2A2A")
                row.pack(fill="x", padx=8, pady=1)
                ctk.CTkLabel(row, text=f"   {label}",
                             text_color="#888888", font=ctk.CTkFont(size=11)).pack(side="left", padx=10)
                continue

            # ── 内容页：卡片式布局 ──
            color = TYPE_COLORS.get(st, '#555555')
            expanded = sec.get('expanded', True)
            card = ctk.CTkFrame(self, fg_color="#2B2B2B", border_width=1,
                                border_color="#444444")
            card.pack(fill="x", padx=8, pady=5)

            # ── 标题栏 ──
            header = ctk.CTkFrame(card, fg_color=color, height=32)
            header.pack(fill="x")
            header.pack_propagate(False)

            toggle = "▼" if expanded else "▶"
            if st == 'result':
                title_text = sec.get('title', '新结果页')[:40]
            else:
                title_text = type_names.get(st, st)
            hdr_btn = ctk.CTkButton(header, text=f" {toggle}  {title_text}",
                                     fg_color="transparent", anchor="w",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     command=lambda idx=i: self._toggle_section(idx))
            hdr_btn.pack(side="left", fill="x", expand=True)

            # 操作按钮
            btn_bar = ctk.CTkFrame(header, fg_color="transparent")
            btn_bar.pack(side="right", padx=4)
            ctk.CTkButton(btn_bar, text="↑", width=24, height=24, fg_color="transparent",
                          command=lambda idx=i: self._move_section(idx, -1)).pack(side="left", padx=1)
            ctk.CTkButton(btn_bar, text="↓", width=24, height=24, fg_color="transparent",
                          command=lambda idx=i: self._move_section(idx, 1)).pack(side="left", padx=1)
            ctk.CTkButton(btn_bar, text="✕", width=24, height=24, fg_color="transparent",
                          hover_color="#8B0000",
                          command=lambda idx=i: self._delete_section(idx)).pack(side="left", padx=1)

            if not expanded:
                continue

            # ── 内容区 ──
            content = ctk.CTkFrame(card, fg_color="#2F2F2F")
            content.pack(fill="x", padx=12, pady=(8, 8))
            self.widgets[i] = content

            # result 的特有标题行
            if st == 'result':
                trow = ctk.CTkFrame(content)
                trow.pack(fill="x", pady=(0, 6))
                ctk.CTkLabel(trow, text="标题:", width=40, font=ctk.CTkFont(size=11),
                             text_color="#AAAAAA").pack(side="left")
                te = ctk.CTkEntry(trow, width=360, font=ctk.CTkFont(size=12))
                te.insert(0, sec.get('title', ''))
                te._outline_role = 'title'
                te.pack(side="left", padx=5)

            # ── 行编辑器 ──
            rows = sec.get('rows', [])
            for j, (label, value) in enumerate(rows):
                if _is_long_text(value):
                    # 多行文本框
                    self._add_textbox_row(content, j, label, value)
                else:
                    # 单行输入框
                    self._add_entry_row(content, j, label, value)

            # ── 底部：配图 + 添加行 ──
            bot = ctk.CTkFrame(content)
            bot.pack(fill="x", pady=(6, 0))

            # 所有内容页都有配图按钮
            imgs = sec.get('images', [])
            imgs_str = ', '.join(imgs) if imgs else '(点击添加配图)'
            ctk.CTkButton(bot, text=f"🖼 {imgs_str[:50]}", fg_color="#3A3A3A",
                          font=ctk.CTkFont(size=11),
                          command=lambda idx=i: self._pick_images(idx)).pack(side="left", padx=2)

            # 添加行按钮（适用于有列表的类型）
            if st in ('result', 'background', 'discussion1'):
                ctk.CTkButton(bot, text="+ 添加行", width=70, height=24,
                              fg_color="#3A3A3A", font=ctk.CTkFont(size=11),
                              command=lambda idx=i: self._add_row(idx)).pack(side="left", padx=2)

        # ── 底部操作栏 ──
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(bottom, text="+ 添加结果页", fg_color="#007191",
                      font=ctk.CTkFont(size=12),
                      command=self._add_result_slide).pack(side="left", padx=5)
        ctk.CTkButton(bottom, text="刷新显示", fg_color="#444444",
                      font=ctk.CTkFont(size=12),
                      command=self._rebuild).pack(side="right", padx=5)

    def _add_entry_row(self, parent, row_idx, label, value):
        """单行编辑框：label + CTkEntry。"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        row._outline_role = 'row'
        row._row_index = row_idx
        ctk.CTkLabel(row, text=label + ":", width=55, anchor="e",
                     text_color="#AAAAAA", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 5))
        entry = ctk.CTkEntry(row, font=ctk.CTkFont(size=12))
        entry.insert(0, value)
        entry.pack(side="left", fill="x", expand=True)
        # 删除行按钮（仅列表项）
        ctk.CTkButton(row, text="✕", width=20, height=20, fg_color="transparent",
                      hover_color="#8B0000", font=ctk.CTkFont(size=9),
                      command=lambda r=row: self._remove_row(r)).pack(side="right", padx=2)

    def _add_textbox_row(self, parent, row_idx, label, value):
        """多行文本编辑框：label + CTkTextbox（3-5行高）。"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        row._outline_role = 'row_textbox'
        row._row_index = row_idx

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=label + ":", anchor="w",
                     text_color="#AAAAAA", font=ctk.CTkFont(size=11)).pack(side="left")
        ctk.CTkButton(top, text="✕", width=20, height=20, fg_color="transparent",
                      hover_color="#8B0000", font=ctk.CTkFont(size=9),
                      command=lambda r=row: self._remove_row(r)).pack(side="right", padx=2)

        # 按内容行数自适应高度（3-8行）
        n_lines = max(3, min(8, value.count('\n') + 1,
                             (len(value) // 35) + 1))
        tb = ctk.CTkTextbox(row, height=n_lines * 22, font=ctk.CTkFont(size=12),
                            wrap="word", fg_color="#3A3A3A")
        tb.insert("1.0", value)
        tb.pack(fill="x", pady=(2, 0))
        row._textbox = tb

    def _remove_row(self, row_frame):
        """删除指定行并重建 UI。"""
        idx = getattr(row_frame, '_row_index', -1)
        parent = row_frame.master
        # 找到 section 索引
        sec_idx = None
        for i, w in self.widgets.items():
            if w is parent:
                sec_idx = i
                break
        if sec_idx is None:
            return
        sec = self.sections[sec_idx]
        rows = sec.get('rows', [])
        if idx < 0 or idx >= len(rows):
            return
        label = rows[idx][0]
        if not messagebox.askyesno("确认", f"删除「{label}」？"):
            return
        del rows[idx]
        self._rebuild()

    def _add_row(self, sec_idx):
        """给指定 section 添加新行。"""
        if sec_idx >= len(self.sections):
            return
        sec = self.sections[sec_idx]
        st = sec['type']
        if st == 'result':
            n = len(sec.get('rows', [])) + 1
            sec.setdefault('rows', []).append((f'要点{n}', ''))
        elif st == 'background':
            n = len([r for r in sec.get('rows', []) if r[0].startswith('卡片')]) + 1
            sec.setdefault('rows', []).append((f'卡片{n}: 新卡片', ''))
        elif st == 'discussion1':
            n = len(sec.get('rows', [])) + 1
            sec.setdefault('rows', []).append((f'讨论点{n}', ''))
        self._dirty = True
        self._rebuild()

    # ═══════════════════════════════════════════
    # 操作：展开/折叠、删除、移动、添加
    # ═══════════════════════════════════════════

    def _toggle_section(self, idx):
        if idx < len(self.sections):
            self.sections[idx]['expanded'] = not self.sections[idx].get('expanded', True)
            self._rebuild()

    def _delete_section(self, idx):
        if idx >= len(self.sections):
            return
        sec = self.sections[idx]
        if sec['type'] == 'keep':
            messagebox.showinfo("提示", "封面/目录/章节/致谢不可删除")
            return
        type_names = {
            'paper_info': '论文信息', 'author': '作者团队', 'background': '课题背景',
            'result': '结果页', 'summary': '结果总结',
            'discussion1': '讨论分析①', 'discussion2': '讨论分析②',
        }
        name = type_names.get(sec['type'], sec['type'])
        if messagebox.askyesno("确认", f"删除「{name}」？"):
            del self.sections[idx]
            self._dirty = True
            self._rebuild()

    def _move_section(self, idx, direction):
        """上移 (-1) 或下移 (+1)。"""
        new_idx = idx + direction
        if 0 <= new_idx < len(self.sections):
            # 不能跨越 keep 类型的封面
            if self.sections[new_idx]['type'] == 'keep' and self.sections[new_idx]['ref'] == 'cover':
                return
            if self.sections[idx]['type'] == 'keep':
                return
            self.sections.insert(new_idx, self.sections.pop(idx))
            self._dirty = True
            self._rebuild()

    def _add_result_slide(self):
        self.sections.append({
            'type': 'result', 'title': '新结果页', 'expanded': True,
            'rows': [('要点1', ''), ('要点2', ''), ('要点3', '')],
            'images': [],
        })
        self._dirty = True
        self._rebuild()

    def _pick_images(self, idx):
        if not self.figs_dir or not os.path.isdir(self.figs_dir):
            messagebox.showinfo("提示", "请先在输入文件页选择图片目录")
            return
        files = sorted([f for f in os.listdir(self.figs_dir)
                        if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        if not files:
            messagebox.showinfo("提示", "图片目录为空")
            return
        current = set(self.sections[idx].get('images', []))
        dlg = _ImagePickerDialog(self, files, current)
        self.wait_window(dlg)
        if dlg.result is not None:
            self.sections[idx]['images'] = dlg.result
            self._dirty = True
            self._rebuild()


def _iter_children(widget):
    """递归遍历子控件。"""
    try:
        for c in widget.winfo_children():
            yield c
            yield from _iter_children(c)
    except Exception:
        pass


class _ImagePickerDialog(ctk.CTkToplevel):
    """多选图片对话框：滚动 checkbox 列表 + 确认/取消。"""

    def __init__(self, master, files, selected):
        super().__init__(master)
        self.title("选择配图")
        self.geometry("420x420")
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color="#3A3C42")
        self.after(50, lambda: (self.lift(), self.focus_force(), self.grab_set()))

        self.result = None
        self.files = files
        self.vars = {}  # filename -> BooleanVar

        ctk.CTkLabel(self, text="选择配图文件（可多选）",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 5))

        # 全选 / 清空
        sel_bar = ctk.CTkFrame(self)
        sel_bar.pack(fill="x", padx=15, pady=3)
        ctk.CTkButton(sel_bar, text="全选", width=60, height=24, fg_color="#555555",
                      command=self._select_all).pack(side="left", padx=3)
        ctk.CTkButton(sel_bar, text="清空", width=60, height=24, fg_color="#555555",
                      command=self._clear_all).pack(side="left", padx=3)
        ctk.CTkLabel(sel_bar, text=f"共 {len(files)} 个文件",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(side="right")

        # 滚动列表
        scroll = ctk.CTkScrollableFrame(self, height=260)
        scroll.pack(fill="both", expand=True, padx=15, pady=8)

        for f in files:
            var = ctk.BooleanVar(value=f in selected)
            self.vars[f] = var
            cb = ctk.CTkCheckBox(scroll, text=f, variable=var, font=ctk.CTkFont(size=12))
            cb.pack(anchor="w", pady=1)

        # 底部按钮
        btn_row = ctk.CTkFrame(self)
        btn_row.pack(fill="x", padx=15, pady=(5, 12))
        ctk.CTkButton(btn_row, text="取消", width=70, fg_color="#555555",
                      command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_row, text="确定", width=70,
                      command=self._confirm).pack(side="right", padx=5)

    def _select_all(self):
        for v in self.vars.values():
            v.set(True)

    def _clear_all(self):
        for v in self.vars.values():
            v.set(False)

    def _confirm(self):
        self.result = [f for f, v in self.vars.items() if v.get()]
        self.destroy()
