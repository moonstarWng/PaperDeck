"""
gui/pages/outline_page.py — 大纲生成页：读论文、LLM生成大纲、树形编辑、构建。
"""
import customtkinter as ctk
import json, sys, os, threading
from tkinter import messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from gui.workers.llm_worker import call_llm
from gui.widgets.outline_editor import OutlineEditor


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

    # ── 读取论文 ──
    def _read_paper(self):
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
                        self.status.configure(text=f"读取中... {i+1}/{total}", text_color="gray")
            full_text = "\n\n".join(text_parts)
            self.shared['paper_text'] = full_text
            self.status.configure(text=f"✓ 已读取 {total} 页，共 {len(full_text)} 字符。正在提取元数据...", text_color="gray")
            self._extract_metadata(full_text)
        except Exception as e:
            self.status.configure(text=f"读取失败: {e}", text_color="red")

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
            self.title_entry.delete(0, 'end'); self.title_entry.insert(0, meta.get('title_en', ''))
            self.journal_entry.delete(0, 'end'); self.journal_entry.insert(0, meta.get('journal', ''))
            self.author_entry.delete(0, 'end'); self.author_entry.insert(0, meta.get('authors', ''))
            self.shared['paper_meta'] = meta
            self.status.configure(text="✓ 元数据已提取，可点击「生成大纲」", text_color="green")
        except Exception as e:
            self.status.configure(text=f"元数据提取失败: {e}（可手动填写）", text_color="orange")

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

        figs = self._get_figs_list()
        prompt = (
            f"## 论文元数据{meta_block}\n\n"
            f"## 论文全文\n{paper_text[:40000]}\n\n"
            f"## 图片文件列表\n{figs}\n\n"
            f"请根据上述内容生成 slide-content.json。"
            f"重要：cover.presenter='xxx', cover.date='202X年X月'。"
        )
        threading.Thread(target=self._do_llm_call, args=(prompt,), daemon=True).start()

    def _do_llm_call(self, prompt):
        try:
            result = call_llm(self.shared['api_base_url'], self.shared['api_key'],
                              self.shared['api_model'], prompt,
                              on_progress=lambda msg: self.status.configure(text=msg, text_color="gray"))
            self.shared['slide_content_json'] = result
            # 加载到树形编辑器
            self.editor.set_figs_dir(self.shared.get('figs_dir', ''))
            ok = self.editor.load_from_json(result)
            if ok:
                self.status.configure(text="✓ 大纲已生成，可展开编辑后点击「构建 PPT」", text_color="green")
            else:
                self.status.configure(text="大纲生成完成但解析失败，请检查 JSON 格式", text_color="orange")
        except Exception as e:
            self.status.configure(text=f"生成失败: {e}", text_color="red")

    # ── 构建 ──
    def _go_build(self):
        """从树形编辑器导出 JSON 并跳转到构建页。"""
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

        # 自动注入论文信息页（在第一个 keep section 之后）
        pdf_path = self.shared.get('pdf_path', '')
        if pdf_path and os.path.exists(pdf_path):
            has_paper_info = any(s.get('type') == 'paper_info' for s in slides)
            if not has_paper_info:
                paper_title = self.title_entry.get().strip()
                pi = {'type': 'paper_info', 'pdf_path': pdf_path,
                       'paper_title': paper_title, 'extra_text': ''}
                # 找到 author slide 后的位置插入
                insert_at = 0
                for j, s in enumerate(slides):
                    if s.get('type') == 'author':
                        insert_at = j + 1; break
                slides.insert(insert_at, pi)

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
            "section_divider_edits": [
                {"number": "01", "title": "作者团队"},
                {"number": "02", "title": "课题背景"},
                {"number": "03", "title": "结果分析"},
                {"number": "04", "title": "讨论"}
            ],
            "slides": slides
        }
        self.shared['slide_content_json'] = json.dumps(full_config, indent=2, ensure_ascii=False)
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
