"""
gui/pages/outline_page.py — 大纲生成页：读论文、LLM生成大纲、树形编辑、构建。
"""
import customtkinter as ctk
import json, sys, os, threading
from tkinter import messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from gui.workers.llm_worker import call_llm
from gui.widgets.outline_editor import OutlineEditor
from gui.logger import log_step


class OutlinePage(ctk.CTkFrame):
    """Tab 2: 论文元数据 + 大纲树形编辑器 + 生成 slide-content.json。"""

    def __init__(self, master, shared, app):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.shared = shared
        self.app = app

        # ── 顶部按钮栏 ──
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="← 返回配置", width=100, command=lambda: app.switch_to_tab("配置")).pack(side="left", padx=5)
        self.read_btn = ctk.CTkButton(btn_frame, text="读取论文", width=80, command=self._read_paper)
        self.read_btn.pack(side="left", padx=5)
        self.gen_btn = ctk.CTkButton(btn_frame, text="生成大纲", width=80, fg_color="#007191",
                                      command=self._generate_outline)
        self.gen_btn.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="构建 PPT →", width=100, fg_color="green",
                       command=self._go_build).pack(side="right", padx=5)

        self.status = ctk.CTkLabel(self, text="请先读取论文", text_color="gray")
        self.status.pack(anchor="w", padx=15)

        # ── 章节配置（可编辑）──
        ctk.CTkLabel(self, text="章节配置（可编辑标题和页数）",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(5, 0))
        self.section_rows = []  # [(enable_var, title_var, count_var, row_frame)]
        self.sections_frame = ctk.CTkFrame(self)
        self.sections_frame.pack(fill="x", padx=10, pady=(0, 5))

        # 表头
        hdr = ctk.CTkFrame(self.sections_frame)
        hdr.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(hdr, text="启用", width=40).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="章节标题", width=140).pack(side="left", padx=2)
        ctk.CTkLabel(hdr, text="页数", width=40).pack(side="left", padx=2)

        self._default_sections = [
            ('作者团队', '1'),
            ('课题背景', '1'),
            ('结果分析', '4'),
            ('结果总结', '1'),
            ('讨论分析', '2'),
        ]
        for title, pages in self._default_sections:
            self._add_section_row(title, pages, True)

        # 操作按钮
        btn_row = ctk.CTkFrame(self.sections_frame)
        btn_row.pack(fill="x", padx=5, pady=2)
        ctk.CTkButton(btn_row, text="+ 添加章节", width=80, height=24,
                       command=lambda: self._add_section_row('新章节', '1', True)).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="恢复默认", width=70, height=24,
                       command=self._reset_sections).pack(side="left", padx=5)

        # 论文信息页（独立开关）
        self.paper_info_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.sections_frame, text="附加论文信息页（PDF首页 + 原文链接）",
                         variable=self.paper_info_var).pack(anchor="w", padx=5, pady=(5, 0))

        # ── 论文信息区 ──
        ctk.CTkLabel(self, text="论文信息（读取论文后自动填充）", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(5, 0))
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(info_frame, text="标题:", width=50).grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.title_entry = ctk.CTkEntry(info_frame, width=500)
        self.title_entry.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        ctk.CTkLabel(info_frame, text="期刊:", width=50).grid(row=1, column=0, padx=5, pady=3, sticky="e")
        self.journal_entry = ctk.CTkEntry(info_frame, width=300)
        self.journal_entry.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ctk.CTkLabel(info_frame, text="作者:", width=50).grid(row=2, column=0, padx=5, pady=3, sticky="e")
        self.author_entry = ctk.CTkEntry(info_frame, width=500)
        self.author_entry.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        # ── 大纲树形编辑器 ──
        ctk.CTkLabel(self, text="大纲（可展开编辑）", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 0))
        self.editor = OutlineEditor(self, height=400)
        self.editor.pack(fill="both", expand=True, padx=10, pady=5)

    def _add_section_row(self, title, pages, enabled):
        """添加一行章节配置。"""
        row = ctk.CTkFrame(self.sections_frame)
        # 插入到按钮行之前
        for child in self.sections_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child != row:
                for sub in child.winfo_children():
                    if isinstance(sub, ctk.CTkButton) and '+ 添加' in (sub.cget('text') or ''):
                        row.pack(fill="x", padx=5, pady=1, before=child)
                        break
                else:
                    continue
                break
        else:
            row.pack(fill="x", padx=5, pady=1)

        enable_var = ctk.BooleanVar(value=enabled)
        ctk.CTkCheckBox(row, text="", variable=enable_var, width=30).pack(side="left", padx=2)

        title_var = ctk.StringVar(value=title)
        ctk.CTkEntry(row, textvariable=title_var, width=140).pack(side="left", padx=2)

        count_var = ctk.StringVar(value=pages)
        ctk.CTkOptionMenu(row, values=["1", "2", "3", "4", "5", "6"],
                          variable=count_var, width=45).pack(side="left", padx=2)

        # 上移/下移
        ctk.CTkButton(row, text="↑", width=25, height=24,
                       command=lambda r=row: self._move_section_row(r, -1)).pack(side="right", padx=1)
        ctk.CTkButton(row, text="↓", width=25, height=24,
                       command=lambda r=row: self._move_section_row(r, 1)).pack(side="right", padx=1)
        ctk.CTkButton(row, text="×", width=25, height=24, fg_color="#D94F4F",
                       command=lambda r=row: self._remove_section_row(r)).pack(side="right", padx=2)

        self.section_rows.append((enable_var, title_var, count_var, row))

    def _move_section_row(self, row, direction):
        """上移(-1)或下移(+1)一行。"""
        for i, (ev, tv, cv, r) in enumerate(self.section_rows):
            if r == row:
                new_i = i + direction
                if 0 <= new_i < len(self.section_rows):
                    self.section_rows[i], self.section_rows[new_i] = \
                        self.section_rows[new_i], self.section_rows[i]
                    # 重新 pack 到正确顺序
                    for _, _, _, rr in self.section_rows:
                        rr.pack_forget()
                    btn_row = None
                    for child in self.sections_frame.winfo_children():
                        if isinstance(child, ctk.CTkFrame):
                            for sub in child.winfo_children():
                                if isinstance(sub, ctk.CTkButton) and '+ 添加' in sub.cget('text'):
                                    btn_row = child
                                    break
                    for _, _, _, rr in self.section_rows:
                        if btn_row:
                            rr.pack(fill="x", padx=5, pady=1, before=btn_row)
                        else:
                            rr.pack(fill="x", padx=5, pady=1)
                break

    def _remove_section_row(self, row):
        """删除一行章节配置。"""
        for i, (ev, tv, cv, r) in enumerate(self.section_rows):
            if r == row:
                row.destroy()
                self.section_rows.pop(i)
                break

    def _get_section_config(self):
        """获取当前选中的章节配置列表 [(title, page_count), ...]"""
        config = []
        for enable_var, title_var, count_var, _ in self.section_rows:
            if enable_var.get():
                config.append((title_var.get().strip() or '章节', int(count_var.get() or '1')))
        return config

    def _reset_sections(self):
        """恢复默认章节配置。"""
        for _, _, _, row in self.section_rows:
            row.destroy()
        self.section_rows.clear()
        for title, pages in self._default_sections:
            self._add_section_row(title, pages, True)

    # ── 读取论文 ──
    def _read_paper(self):
        log_step('outline', '开始读取论文')
        pdf_path = self.shared.get('pdf_path')
        if not pdf_path:
            messagebox.showerror("错误", "请先在配置页选择论文 PDF")
            return
        self.status.configure(text="正在读取论文...", text_color="gray")
        threading.Thread(target=self._do_read_paper, args=(pdf_path,), daemon=True).start()

    def _do_read_paper(self, pdf_path):
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                total = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
                    if i % 5 == 0:
                        cur = i + 1
                        self._safe_ui(lambda c=cur: self.status.configure(
                            text=f"读取中... {c}/{total}", text_color="gray"))
            full_text = "\n\n".join(text_parts)
            self.shared['paper_text'] = full_text
            self._safe_ui(lambda: self.status.configure(
                text=f"✓ 已读取 {total} 页，共 {len(full_text)} 字符。正在提取元数据...", text_color="gray"))
            self._extract_metadata(full_text)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._safe_ui(lambda: self.status.configure(
                text=f"读取失败: {e}", text_color="red"))

    def _extract_metadata(self, paper_text):
        """使用 LLM 从论文首页提取标题、期刊、作者。"""
        if not self._check_api():
            return
        first_page = paper_text[:3000]
        prompt = f"""从以下论文首页文本中提取元数据，返回纯 JSON:
{{
  "title_en": "英文原标题",
  "journal": "期刊名称",
  "authors": "作者列表（逗号分隔，取前5位）"
}}
论文首页:
{first_page}"""
        threading.Thread(target=self._do_metadata_call, args=(prompt,), daemon=True).start()

    def _do_metadata_call(self, prompt):
        try:
            result = call_llm(self.shared['api_base_url'], self.shared['api_key'],
                              self.shared['api_model'], prompt, on_progress=lambda m: None)
            meta = json.loads(result)
            def _apply():
                self.title_entry.delete(0, 'end'); self.title_entry.insert(0, meta.get('title_en', ''))
                self.journal_entry.delete(0, 'end'); self.journal_entry.insert(0, meta.get('journal', ''))
                self.author_entry.delete(0, 'end'); self.author_entry.insert(0, meta.get('authors', ''))
                self.shared['paper_meta'] = meta
                self.status.configure(text="✓ 元数据已提取，可点击「生成大纲」", text_color="green")
            self._safe_ui(_apply)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._safe_ui(lambda: self.status.configure(
                text=f"元数据提取失败: {e}（可手动填写）", text_color="orange"))

    # ── 生成大纲 ──
    def _generate_outline(self):
        if not self._check_api():
            return
        paper_text = self.shared.get('paper_text', '')
        if not paper_text:
            messagebox.showerror("错误", "请先读取论文")
            return
        self.status.configure(text="正在调用 LLM 生成大纲...", text_color="gray")

        title = self.title_entry.get().strip()
        journal = self.journal_entry.get().strip()
        authors = self.author_entry.get().strip()
        meta_block = ""
        if title: meta_block += f'\n论文标题: {title}'
        if journal: meta_block += f'\n期刊: {journal}'
        if authors: meta_block += f'\n作者: {authors}'

        # ── 章节约束（从用户配置生成）──
        sections = self._get_section_config()
        if not sections:
            messagebox.showerror("错误", "请至少启用一个章节")
            return

        # ── 章节约束（强约束，LLM 必须遵守）──
        section_spec = []
        for i, (title, pages) in enumerate(sections):
            section_spec.append(f"  章节{i+1}(编号0{i+1}): {title} — 包含 {pages} 个内容页")
        has_paper_info = self.paper_info_var.get()

        constraint = (
            f"\n\n## ⚠️ 章节结构约束（不遵守将导致生成失败）\n"
            f"你必须严格按照以下结构生成 slides 数组，共 {len(sections)} 个章节:\n"
            + "\n".join(section_spec) + "\n"
            f"\nslides 数组必须包含:\n"
            f"  1. 先放 'keep' + 'cover'\n"
            f"  2. 再放 'keep' + 'toc'\n"
        )
        for i, (title, pages) in enumerate(sections):
            constraint += f"  3+{i}. 'keep' + 'section' (index={i})  → 章节分隔页「{title}」\n"
            constraint += f"       然后恰好 {pages} 个内容页 (type=result/author/background/summary/discussion)\n"
        constraint += (
            f"  N. 最后放 'keep' + 'thanks'\n"
            f"\n规则:\n"
            f"1. 总共恰好 {len(sections)} 个 section divider，不能多也不能少\n"
            f"2. 每个 section 下的内容页数等于上述指定值\n"
            f"3. 封面: presenter='xxx', date='202X年X月'\n"
            f"4. 每个 result 页恰好 3 行要点\n"
        )
        if has_paper_info:
            constraint += "5. 在第一个 section 后插入 paper_info 页\n"
        else:
            constraint += "5. 不要生成 paper_info 页\n"

        figs = self._get_figs_list()
        prompt = (
            f"## 论文元数据{meta_block}\n\n"
            f"## 论文全文\n{paper_text[:40000]}\n\n"
            f"## 图片文件列表\n{figs}\n"
            f"{constraint}\n\n"
            f"请根据上述内容生成 slide-content.json。"
        )
        threading.Thread(target=self._do_llm_call, args=(prompt,), daemon=True).start()

    def _safe_ui(self, fn):
        """在主线程安全调用 UI 更新，忽略已销毁的控件。"""
        try:
            self.after(0, fn)
        except Exception:
            pass  # widget 已销毁

    def _do_llm_call(self, prompt):
        try:
            result = call_llm(
                self.shared['api_base_url'], self.shared['api_key'],
                self.shared['api_model'], prompt,
                on_progress=lambda msg: self._safe_ui(
                    lambda: self.status.configure(text=msg, text_color="gray")))
            self.shared['slide_content_json'] = result
            self._safe_ui(lambda: self._load_llm_result(result))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._safe_ui(lambda: self.status.configure(
                text=f"生成失败: {e}", text_color="red"))

    def _load_llm_result(self, result):
        """在主线程加载 LLM 结果到编辑器。"""
        self.editor.set_figs_dir(self.shared.get('figs_dir', ''))
        # 保存原始输出以备排查
        pdf_path = self.shared.get('pdf_path', '')
        if pdf_path:
            raw_path = os.path.join(os.path.dirname(pdf_path), 'slide-content-raw.json')
            try:
                with open(raw_path, 'w', encoding='utf-8') as f:
                    f.write(result)
            except Exception:
                pass
        ok = self.editor.load_from_json(result)
        if ok:
            self.status.configure(text="✓ 大纲已生成，可展开编辑后点击「构建 PPT」", text_color="green")
        else:
            self.status.configure(text="大纲生成完成但解析失败，请检查 JSON 格式", text_color="orange")

    # ── 构建 ──
    def _go_build(self):
        """从树形编辑器导出 JSON 并跳转到构建页。"""
        log_step('outline', '开始构建大纲')
        figs_dir = self.shared.get('figs_dir', '')
        self.editor.set_figs_dir(figs_dir)

        # 导出 JSON
        json_str = self.editor.to_json()
        # 补全 meta 等顶层字段
        try:
            tree_data = json.loads(json_str)
        except json.JSONDecodeError:
            messagebox.showerror("错误", "大纲数据格式异常")
            return

        slides = tree_data.get("slides", [])

        # 自动注入论文信息页 —— 仅当用户勾选了该选项
        pdf_path = self.shared.get('pdf_path', '')
        if pdf_path and os.path.exists(pdf_path) and self.paper_info_var.get():
            has_paper_info = any(s.get('type') == 'paper_info' for s in slides)
            if not has_paper_info:
                paper_title = self.title_entry.get().strip()
                pi = {'type': 'paper_info', 'pdf_path': pdf_path,
                       'paper_title': paper_title, 'extra_text': ''}
                insert_at = 0
                for j, s in enumerate(slides):
                    if s.get('type') == 'author':
                        insert_at = j + 1; break
                slides.insert(insert_at, pi)

        # ── 根据用户配置的章节动态生成 ──
        sections = self._get_section_config()
        if not sections:
            messagebox.showerror("错误", "请至少配置一个章节")
            return

        # 检查模板章节页是否足够
        tmpl_path = self.shared.get('template_path', '')
        if tmpl_path and os.path.exists(tmpl_path):
            from pptx import Presentation
            from scripts.make_template import classify
            prs = Presentation(tmpl_path)
            tmpl_section_count = sum(1 for s in prs.slides if classify(s).startswith('SECTION_'))
            if len(sections) > tmpl_section_count:
                messagebox.showwarning("章节页不足",
                    f"你配置了 {len(sections)} 个章节，但模板只有 {tmpl_section_count} 个章节页。\n"
                    f"超出部分将复用最后一个章节页。")

        section_divider_edits = []
        for i, (title, _) in enumerate(sections):
            section_divider_edits.append({
                "number": f"0{i+1}",
                "title": title,
            })

        full_config = {
            "meta": {
                "template_path": self.shared.get('template_path', ''),
                "figs_dir": figs_dir,
                "output_path": "./output.pptx"
            },
            "cover": {
                "title_en": self.title_entry.get().strip(),
                "presenter": "xxx",
                "date": "202X年X月"
            },
            "toc_replacements": {},
            "section_divider_edits": section_divider_edits,
            "slides": slides
        }
        self.shared['slide_content_json'] = json.dumps(full_config, indent=2, ensure_ascii=False)

        # 保存中间大纲到文件（与输出同目录，方便排查）
        pdf_path = self.shared.get('pdf_path', '')
        if pdf_path:
            outline_path = os.path.join(os.path.dirname(pdf_path), 'slide-content.json')
            try:
                with open(outline_path, 'w', encoding='utf-8') as f:
                    f.write(self.shared['slide_content_json'])
            except Exception:
                pass  # 保存失败不影响主流程

        self.app.switch_to_tab("构建")

    def _get_figs_list(self):
        figs_dir = self.shared.get('figs_dir', '')
        if figs_dir and os.path.isdir(figs_dir):
            files = [f for f in os.listdir(figs_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            return "\n".join(sorted(files))
        return "(未指定图片目录)"

    def _check_api(self):
        if not self.shared.get('api_key'):
            messagebox.showerror("错误", "请先在配置页填写 API Key")
            return False
        return True
