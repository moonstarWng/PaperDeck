"""
gui/pages/config_page.py — 配置页：文件输入 + API 设置 + 模板检测。
"""
import customtkinter as ctk
import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from gui.widgets.file_picker import FilePicker


class ConfigPage(ctk.CTkFrame):
    """Tab 1: 论文 PDF、模板 PPTX、图片目录、LLM API 配置。"""

    def __init__(self, master, shared, app):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.shared = shared
        self.app = app

        # ═══ 论文 PDF ═══
        ctk.CTkLabel(self, text="论文 PDF", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(10, 5))
        self.pdf_picker = FilePicker(self, "论文PDF:", [("PDF", "*.pdf"), ("All", "*.*")])
        self.pdf_picker.pack(fill="x", padx=10, pady=5)

        # ═══ 模板 PPTX + 检测 ═══
        ctk.CTkLabel(self, text="模板 PPTX", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))
        tmpl_frame = ctk.CTkFrame(self)
        tmpl_frame.pack(fill="x", padx=10, pady=5)
        self.tmpl_picker = FilePicker(tmpl_frame, "模板:", [("PPTX", "*.pptx"), ("All", "*.*")])
        self.tmpl_picker.pack(side="left", fill="x", expand=True)
        self.detect_btn = ctk.CTkButton(tmpl_frame, text="检测", width=60, command=self._detect_template)
        self.detect_btn.pack(side="right", padx=5)
        self.tmpl_status = ctk.CTkLabel(self, text="", text_color="gray")
        self.tmpl_status.pack(anchor="w", padx=20)

        # ═══ 图片目录 ═══
        ctk.CTkLabel(self, text="论文图片目录 (figs/)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))
        self.figs_picker = FilePicker(self, "图片:", directory=True)
        self.figs_picker.pack(fill="x", padx=10, pady=5)
        self.figs_status = ctk.CTkLabel(self, text="", text_color="gray")
        self.figs_status.pack(anchor="w", padx=20)

        # ═══ LLM API 配置 ═══
        ctk.CTkLabel(self, text="LLM API 配置 (OpenAI 兼容)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))

        api_frame = ctk.CTkFrame(self)
        api_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(api_frame, text="Base URL:", width=70).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.url_entry = ctk.CTkEntry(api_frame, width=400, placeholder_text="https://api.deepseek.com")
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.url_entry.insert(0, self.shared.get('api_base_url', 'https://api.deepseek.com'))

        ctk.CTkLabel(api_frame, text="API Key:", width=70).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.key_entry = ctk.CTkEntry(api_frame, width=400, show="*", placeholder_text="sk-xxxxxxxx")
        self.key_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(api_frame, text="Model:", width=70).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.model_entry = ctk.CTkEntry(api_frame, width=200, placeholder_text="deepseek-chat")
        self.model_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.model_entry.insert(0, self.shared.get('api_model', 'deepseek-chat'))

        self.test_btn = ctk.CTkButton(api_frame, text="测试连接", width=80, command=self._test_api)
        self.test_btn.grid(row=2, column=2, padx=10, pady=5)
        self.api_status = ctk.CTkLabel(self, text="", text_color="gray")
        self.api_status.pack(anchor="w", padx=20)

        # ═══ 下一步按钮 ═══
        self.next_btn = ctk.CTkButton(self, text="下一步: 生成大纲 →", height=36, command=self._go_next)
        self.next_btn.pack(pady=20)

    # ── 模板检测 ──
    def _detect_template(self):
        """检测 PPTX 是否为模板骨架。"""
        path = self.tmpl_picker.get_path()
        if not path:
            self.tmpl_status.configure(text="请先选择模板文件", text_color="red")
            return
        try:
            from pptx import Presentation
            prs = Presentation(path)
            from scripts.make_template import classify
            t_count, c_count = 0, 0
            for slide in prs.slides:
                cat = classify(slide)
                if cat.startswith('SECTION_') or cat in ('COVER', 'TOC', 'THANKS', 'SUMMARY'):
                    t_count += 1
                elif cat in ('CONTENT', 'CONTENT_FRAME', 'DATA', 'DISCUSSION'):
                    c_count += 1
            ratio = c_count / max(len(prs.slides), 1)
            is_tpl = ratio < 0.2
            self.shared['is_template'] = is_tpl
            self.shared['template_path'] = path
            if is_tpl:
                self.tmpl_status.configure(text=f"✓ 已是模板骨架 (内容页{ratio:.0%})，无需处理", text_color="green")
            else:
                self.tmpl_status.configure(text=f"⚠ 检测到完整PPTX (内容页{ratio:.0%})，将自动提取模板", text_color="orange")
        except Exception as e:
            self.tmpl_status.configure(text=f"检测失败: {e}", text_color="red")

    # ── API 测试 ──
    def _test_api(self):
        """发送最小请求测试 API 连通性。"""
        url = self.url_entry.get().strip()
        key = self.key_entry.get().strip()
        model = self.model_entry.get().strip()
        if not url or not key:
            self.api_status.configure(text="请填写 Base URL 和 API Key", text_color="red")
            return
        self.api_status.configure(text="测试中...", text_color="gray")
        threading.Thread(target=self._do_test_api, args=(url, key, model), daemon=True).start()

    def _do_test_api(self, url, key, model):
        try:
            import requests
            resp = requests.post(f"{url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                timeout=15)
            if resp.status_code == 200:
                self.api_status.configure(text="✓ 连接成功", text_color="green")
            else:
                self.api_status.configure(text=f"✗ HTTP {resp.status_code}: {resp.text[:80]}", text_color="red")
        except Exception as e:
            self.api_status.configure(text=f"✗ 连接失败: {str(e)[:80]}", text_color="red")

    # ── 验证并跳转 ──
    def restore_from_shared(self):
        """从共享数据恢复输入框内容（启动时调用）。"""
        if self.shared.get('pdf_path'):
            self.pdf_picker.set_path(self.shared['pdf_path'])
        if self.shared.get('template_path'):
            self.tmpl_picker.set_path(self.shared['template_path'])
        if self.shared.get('figs_dir'):
            self.figs_picker.set_path(self.shared['figs_dir'])
        if self.shared.get('api_key'):
            self.key_entry.delete(0, 'end')
            self.key_entry.insert(0, self.shared['api_key'])

    def _go_next(self):
        """验证所有输入后切换到大纲页。"""
        errors = []
        if not self.pdf_picker.is_valid():
            errors.append("论文 PDF 未选择或不存在")
        if not self.tmpl_picker.is_valid():
            errors.append("模板 PPTX 未选择或不存在")
        figs = self.figs_picker.get_path()
        if figs and not self.figs_picker.is_valid():
            errors.append("图片目录不存在")
        key = self.key_entry.get().strip()
        if not key:
            errors.append("API Key 未填写")

        if errors:
            from tkinter import messagebox
            messagebox.showerror("配置不完整", "\n".join(errors))
            return

        # 保存到共享数据
        self.shared['pdf_path'] = self.pdf_picker.get_path()
        self.shared['template_path'] = self.tmpl_picker.get_path()
        self.shared['figs_dir'] = figs
        self.shared['api_base_url'] = self.url_entry.get().strip()
        self.shared['api_key'] = key
        self.shared['api_model'] = self.model_entry.get().strip()

        # 如果模板需要提取，先跑 make_template
        if not self.shared.get('is_template', False):
            from tkinter import messagebox
            if messagebox.askyesno("提取模板", "检测到完整PPTX，需要先提取模板骨架。是否继续？"):
                self._run_make_template()

        self.app.switch_to_tab("大纲生成")

    def _run_make_template(self):
        """在后台线程中运行模板提取。"""
        from scripts.make_template import main as make_tmpl_main
        threading.Thread(target=self._do_make_template, daemon=True).start()

    def _do_make_template(self):
        import sys
        src = self.shared['template_path']
        dst = src.replace('.pptx', '_模板.pptx')
        sys.argv = ['make_template.py', src, dst]
        try:
            from scripts.make_template import main as make_tmpl_main
            make_tmpl_main()
            self.shared['template_path'] = dst
            self.shared['is_template'] = True
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("模板提取失败", str(e))
