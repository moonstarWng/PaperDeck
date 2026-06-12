"""
gui/widgets/outline_editor.py — 大纲树形编辑器。
可展开/折叠的树形结构，内联编辑标题和要点，拖拽配图。
"""
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import json, os


class OutlineEditor(ctk.CTkScrollableFrame):
    """可滚动的大纲树形编辑器。"""

    def __init__(self, master, figs_dir='', **kwargs):
        super().__init__(master, **kwargs)
        self.figs_dir = figs_dir
        self.sections = []  # [{type, title, expanded, rows}]
        self.widgets = {}    # section_index -> frame
        self._build_placeholder()

    def set_figs_dir(self, path):
        """更新图片目录并刷新。"""
        self.figs_dir = path

    # ═══════════════════════════════════════════
    # 从 JSON 加载 / 导出 JSON
    # ═══════════════════════════════════════════

    def load_from_json(self, json_str):
        """从 slide-content.json 字符串解析并构建树。"""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON 解析错误", str(e))
            return False
        self.sections = self._parse_slides(data.get('slides', []))
        self._rebuild()
        return True

    def to_json(self, meta_overrides=None):
        """从树形编辑器导出 slide-content.json 字符串。"""
        slides = []
        for sec in self.sections:
            if sec['type'] == 'keep':
                slides.append({"type": "keep", "ref": sec['ref']})
            elif sec['type'] == 'author':
                slides.append(self._build_author_slide(sec))
            elif sec['type'] == 'background':
                slides.append(self._build_background_slide(sec))
            elif sec['type'] == 'result':
                slides.append(self._build_result_slide(sec))
            elif sec['type'] == 'summary':
                slides.append(self._build_summary_slide(sec))
            elif sec['type'] == 'discussion1':
                slides.append(self._build_discussion1_slide(sec))
            elif sec['type'] == 'discussion2':
                slides.append(self._build_discussion2_slide(sec))
        return json.dumps({"slides": slides}, indent=2, ensure_ascii=False)

    # ═══════════════════════════════════════════
    # JSON → 内部树结构
    # ═══════════════════════════════════════════

    def _parse_slides(self, slides):
        result = []
        for slide in slides:
            st = slide.get('type', '')
            if st == 'keep':
                result.append({'type': 'keep', 'ref': slide.get('ref', ''), 'expanded': False, 'rows': []})
            elif st == 'author':
                result.append({'type': 'author', 'expanded': True,
                    'rows': [
                        ('期刊', slide.get('journal', {}).get('name', '')),
                        ('IF', slide.get('journal', {}).get('if', '')),
                        ('作者', slide.get('authors', '')),
                        ('机构', '\n'.join(slide.get('institutions', []))),
                    ]})
            elif st == 'background':
                cards = slide.get('cards', [])
                rows = [('假说', slide.get('hypothesis', ''))]
                for i, c in enumerate(cards):
                    rows.append((f'卡片{i+1}: {c.get("title", "")}', c.get('body', '')))
                result.append({'type': 'background', 'expanded': True, 'rows': rows})
            elif st == 'result':
                rows = [(f'要点{i+1}', line) for i, line in enumerate(slide.get('body', []))]
                imgs = [img.get('file', '') for img in slide.get('images', [])]
                result.append({'type': 'result', 'title': slide.get('title', ''),
                    'expanded': True, 'rows': rows, 'images': imgs})
            elif st == 'summary':
                steps = [s.get('text', '') for s in slide.get('flow_steps', [])]
                cards = [c.get('title', '') + ': ' + c.get('detail', '') for c in slide.get('evidence_cards', [])]
                result.append({'type': 'summary', 'title': slide.get('title', ''),
                    'expanded': True, 'rows': [('步骤', '\n'.join(steps)), ('证据', '\n'.join(cards))]})
            elif st == 'discussion1':
                items = slide.get('items', [])
                rows = [(it.get('title', ''), it.get('detail', '')) for it in items]
                result.append({'type': 'discussion1', 'title': slide.get('title', ''),
                    'expanded': True, 'rows': rows})
            elif st == 'discussion2':
                result.append({'type': 'discussion2', 'title': slide.get('title', ''),
                    'expanded': True,
                    'rows': [('左栏', '\n'.join(slide.get('left_items', []))),
                             ('右栏', '\n'.join(slide.get('right_items', [])))]})
        return result

    # ═══════════════════════════════════════════
    # 树 → JSON 构建器
    # ═══════════════════════════════════════════

    def _build_result_slide(self, sec):
        body = [v for _, v in sec.get('rows', [])]
        images = [{'file': f, 'top_in': 1.05 + i * 2.8} for i, f in enumerate(sec.get('images', []))]
        return {'type': 'result', 'title': sec.get('title', ''), 'body': body, 'images': images}

    def _build_author_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        return {'type': 'author', 'journal': {'name': d.get('期刊', ''), 'if': d.get('IF', '')},
                'authors': d.get('作者', ''), 'institutions': d.get('机构', '').split('\n'),
                'prior_work': []}

    def _build_background_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        cards = []
        for k, v in sec.get('rows', []):
            if k.startswith('卡片'):
                title = k.split(': ', 1)[1] if ': ' in k else k
                cards.append({'title': title, 'body': v, 'color': 'teal'})
        return {'type': 'background', 'cards': cards, 'hypothesis': d.get('假说', '')}

    def _build_summary_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        steps = [{'text': s.strip(), 'color': 'teal'} for s in d.get('步骤', '').split('\n') if s.strip()]
        cards = []
        for line in d.get('证据', '').split('\n'):
            if ': ' in line:
                t, de = line.split(': ', 1)
                cards.append({'title': t, 'detail': de})
        return {'type': 'summary', 'title': sec.get('title', ''), 'flow_steps': steps, 'evidence_cards': cards}

    def _build_discussion1_slide(self, sec):
        items = [{'number': str(i+1), 'title': t, 'detail': d} for i, (t, d) in enumerate(sec.get('rows', []))]
        return {'type': 'discussion1', 'title': sec.get('title', ''), 'items': items}

    def _build_discussion2_slide(self, sec):
        d = {k: v for k, v in sec.get('rows', [])}
        return {'type': 'discussion2', 'title': sec.get('title', ''),
                'left_title': '局限性', 'left_items': d.get('左栏', '').split('\n'),
                'right_title': '临床意义', 'right_items': d.get('右栏', '').split('\n')}

    # ═══════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════

    def _build_placeholder(self):
        """显示空状态占位符。"""
        for w in self.winfo_children():
            w.destroy()
        ctk.CTkLabel(self, text="请先生成或粘贴大纲", text_color="gray").pack(pady=30)

    def _gather_edits(self):
        """在重建前收集所有输入框中的修改，写回 self.sections。"""
        for i, sec in enumerate(self.sections):
            if i not in self.widgets:
                continue
            content = self.widgets[i]
            children = [c for c in content.winfo_children() if isinstance(c, ctk.CTkFrame)]
            entry_idx = 0
            for row_frame in children:
                entries = [c for c in row_frame.winfo_children() if isinstance(c, ctk.CTkEntry)]
                for entry in entries:
                    val = entry.get().strip()
                    if sec['type'] == 'result':
                        if entry_idx == 0:
                            sec['title'] = val
                        else:
                            rows = sec.get('rows', [])
                            ri = entry_idx - 1
                            if ri < len(rows):
                                rows[ri] = (rows[ri][0], val)
                    else:
                        rows = sec.get('rows', [])
                        if entry_idx < len(rows):
                            rows[entry_idx] = (rows[entry_idx][0], val)
                    entry_idx += 1

    def _rebuild(self):
        """完全重建树形 UI。先收集编辑中的修改。"""
        self._gather_edits()
        for w in self.winfo_children():
            w.destroy()
        if not self.sections:
            self._build_placeholder()
            return

        type_names = {
            'keep': '📄', 'author': '作者团队', 'background': '课题背景',
            'result': '', 'summary': '总结', 'discussion1': '讨论',
            'discussion2': '讨论(双栏)',
        }

        for i, sec in enumerate(self.sections):
            st = sec['type']
            if st == 'keep':
                # 简洁显示
                row = ctk.CTkFrame(self, height=30)
                row.pack(fill="x", padx=5, pady=2)
                ctk.CTkLabel(row, text=f"{type_names.get(st,'')} {sec['ref']}", text_color="gray", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
                continue

            # 可展开的区块
            expanded = sec.get('expanded', True)
            section_frame = ctk.CTkFrame(self)
            section_frame.pack(fill="x", padx=5, pady=4)

            # 标题栏
            header = ctk.CTkFrame(section_frame, fg_color="#1A2E4A" if st != 'result' else "#007191")
            header.pack(fill="x")
            if st == 'result':
                header_text = sec.get('title', f'幻灯片 {i+1}')
            else:
                header_text = type_names.get(st, st)
            toggle = "▼" if expanded else "▶"
            title_btn = ctk.CTkButton(header, text=f"{toggle} {header_text}",
                                       fg_color="transparent", anchor="w",
                                       command=lambda idx=i: self._toggle_section(idx))
            title_btn.pack(side="left", fill="x", expand=True)

            if st == 'result':
                ctk.CTkButton(header, text="✕", width=25, fg_color="transparent",
                              command=lambda idx=i: self._delete_section(idx)).pack(side="right", padx=3)

            # 内容区
            if expanded:
                content = ctk.CTkFrame(section_frame)
                content.pack(fill="x", padx=15, pady=5)
                self.widgets[i] = content

                if st == 'result':
                    # 标题可编辑
                    title_row = ctk.CTkFrame(content)
                    title_row.pack(fill="x", pady=2)
                    ctk.CTkLabel(title_row, text="标题:", width=40).pack(side="left")
                    title_entry = ctk.CTkEntry(title_row, width=400)
                    title_entry.insert(0, sec.get('title', ''))
                    title_entry.pack(side="left", padx=5)
                    # 绑定修改
                    title_entry.configure(state="normal")

                    # 要点行
                    for j, (label, value) in enumerate(sec.get('rows', [])):
                        row = ctk.CTkFrame(content)
                        row.pack(fill="x", pady=1)
                        dot = ctk.CTkLabel(row, text="●", text_color="#007191", width=15, font=ctk.CTkFont(size=10))
                        dot.pack(side="left")
                        entry = ctk.CTkEntry(row, width=420)
                        entry.insert(0, value)
                        entry.pack(side="left", padx=5)

                    # 图片分配
                    img_row = ctk.CTkFrame(content)
                    img_row.pack(fill="x", pady=3)
                    ctk.CTkLabel(img_row, text="配图:", text_color="gray", width=40, font=ctk.CTkFont(size=10)).pack(side="left")
                    imgs = sec.get('images', [])
                    imgs_str = ', '.join(imgs) if imgs else '(点击添加)'
                    img_btn = ctk.CTkButton(img_row, text=imgs_str, fg_color="transparent",
                                             text_color="#007191", font=ctk.CTkFont(size=10),
                                             command=lambda idx=i: self._pick_images(idx))
                    img_btn.pack(side="left")

                else:
                    # 通用行编辑器
                    for j, (label, value) in enumerate(sec.get('rows', [])):
                        row = ctk.CTkFrame(content)
                        row.pack(fill="x", pady=1)
                        ctk.CTkLabel(row, text=label + ":", width=50, text_color="gray", font=ctk.CTkFont(size=10)).pack(side="left")
                        entry = ctk.CTkEntry(row, width=400)
                        entry.insert(0, value)
                        entry.pack(side="left", padx=5)

        # 底部操作栏
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(bottom, text="+ 添加结果页", fg_color="#007191", command=self._add_result_slide).pack(side="left", padx=5)
        ctk.CTkButton(bottom, text="刷新显示", fg_color="gray", command=self._rebuild).pack(side="right", padx=5)

    def _toggle_section(self, idx):
        if idx < len(self.sections):
            self.sections[idx]['expanded'] = not self.sections[idx].get('expanded', True)
            self._rebuild()

    def _delete_section(self, idx):
        if idx < len(self.sections) and messagebox.askyesno("确认", "删除此结果页？"):
            del self.sections[idx]
            self._rebuild()

    def _add_result_slide(self):
        self.sections.append({
            'type': 'result', 'title': '新结果页',
            'expanded': True,
            'rows': [('要点1', ''), ('要点2', ''), ('要点3', '')],
            'images': [],
        })
        self._rebuild()

    def _pick_images(self, idx):
        """从 figs/ 目录选择图片分配给结果页。"""
        if not self.figs_dir or not os.path.isdir(self.figs_dir):
            messagebox.showinfo("提示", "请先在配置页选择图片目录")
            return
        files = sorted([f for f in os.listdir(self.figs_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        if not files:
            messagebox.showinfo("提示", "图片目录为空")
            return

        # 简单弹窗：让用户输入逗号分隔的文件名
        current = ', '.join(self.sections[idx].get('images', []))
        result = simpledialog.askstring("选择图片",
            f"可用图片: {', '.join(files[:20])}{'...' if len(files)>20 else ''}\n\n请输入图片文件名(逗号分隔):",
            initialvalue=current)
        if result is not None:
            selected = [f.strip() for f in result.split(',') if f.strip() in files]
            self.sections[idx]['images'] = selected
            self._rebuild()
