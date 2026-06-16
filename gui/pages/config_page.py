"""
gui/pages/config_page.py — 输入文件页：PDF + 模板 + 图片目录 + 模板检测/提取。
"""
import customtkinter as ctk
import sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from gui.widgets.file_picker import FilePicker
from gui.logger import log_step


class ConfigPage(ctk.CTkFrame):
    """Tab 1: 论文 PDF、模板 PPTX、图片目录。"""

    def __init__(self, master, shared, app):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.shared = shared
        self.app = app

        # ═══ 论文 PDF ═══
        ctk.CTkLabel(self, text="论文 PDF", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(10, 5))
        self.pdf_picker = FilePicker(self, "论文PDF:", [("PDF", "*.pdf"), ("All", "*.*")],
                                     on_change=lambda p: self._validate_pdf(p))
        self.pdf_picker.pack(fill="x", padx=10, pady=5)
        self.pdf_status = ctk.CTkLabel(self, text="未选择", text_color="gray")
        self.pdf_status.pack(anchor="w", padx=20)

        # ═══ 模板 PPTX + 检测 ═══
        ctk.CTkLabel(self, text="模板 PPTX", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))
        tmpl_frame = ctk.CTkFrame(self)
        tmpl_frame.pack(fill="x", padx=10, pady=5)
        self.tmpl_picker = FilePicker(tmpl_frame, "模板:", [("PPTX", "*.pptx"), ("All", "*.*")],
                                      on_change=lambda p: self._validate_tmpl(p))
        self.tmpl_picker.pack(side="left", fill="x", expand=True)
        self.detect_btn = ctk.CTkButton(tmpl_frame, text="检测", width=60, command=self._detect_template)
        self.detect_btn.pack(side="right", padx=5)
        self.tmpl_status = ctk.CTkLabel(self, text="未选择", text_color="gray")
        self.tmpl_status.pack(anchor="w", padx=20)

        # ── 提取模板按钮（检测到完整 PPTX 后显示）──
        self.extract_frame = ctk.CTkFrame(self)
        self.extract_btn = ctk.CTkButton(
            self.extract_frame, text="提取模板骨架", width=130,
            command=self._run_extract_template)
        self.extract_btn.pack(side="left", padx=(10, 5))
        self.extract_progress = ctk.CTkLabel(
            self.extract_frame, text="", text_color="gray")
        self.extract_progress.pack(side="left", padx=5)
        self.preview_btn = ctk.CTkButton(
            self.extract_frame, text="预览生成文件", width=100, fg_color="#2E7D32",
            command=self._preview_template)
        # preview_btn 默认不显示，提取成功后 pack

        # ── 模板提取模式 ──
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(mode_frame, text="提取模式:", width=70).pack(side="left", padx=(5, 0))
        self.extract_mode = ctk.StringVar(value="llm")
        self.mode_rule_btn = ctk.CTkRadioButton(
            mode_frame, text="规则 (快速)", variable=self.extract_mode, value="rule",
            command=self._on_mode_change)
        self.mode_rule_btn.pack(side="left", padx=5)
        self.mode_llm_btn = ctk.CTkRadioButton(
            mode_frame, text="LLM (自适应)", variable=self.extract_mode, value="llm",
            command=self._on_mode_change)
        self.mode_llm_btn.pack(side="left", padx=5)
        self.mode_hint = ctk.CTkLabel(mode_frame, text="", text_color="gray")
        self.mode_hint.pack(side="left", padx=10)

        # ═══ 图片目录 ═══
        ctk.CTkLabel(self, text="论文图片目录 (figs/)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))
        self.figs_picker = FilePicker(self, "图片:", directory=True,
                                      on_change=lambda p: self._validate_figs(p))
        self.figs_picker.pack(fill="x", padx=10, pady=5)
        self.figs_status = ctk.CTkLabel(self, text="(可选)", text_color="gray")
        self.figs_status.pack(anchor="w", padx=20)

        # ═══ 下一步按钮 ═══
        self.next_btn = ctk.CTkButton(self, text="下一步: 生成大纲 →", height=36, command=self._go_next)
        self.next_btn.pack(pady=20)

    # ── 文件合法性实时检测 ──
    def _validate_pdf(self, path):
        if not path:
            self.pdf_status.configure(text="未选择", text_color="gray")
        elif os.path.exists(path):
            self.pdf_status.configure(text="✓ 文件有效", text_color="green")
        else:
            self.pdf_status.configure(text="✗ 文件不存在", text_color="red")

    def _validate_tmpl(self, path):
        if not path:
            self.tmpl_status.configure(text="未选择", text_color="gray")
        elif os.path.exists(path):
            self.tmpl_status.configure(text="✓ 文件有效（点击「检测」判断是否为模板骨架）", text_color="green")
        else:
            self.tmpl_status.configure(text="✗ 文件不存在", text_color="red")

    def _validate_figs(self, path):
        if not path:
            self.figs_status.configure(text="(可选)", text_color="gray")
        elif os.path.exists(path):
            self.figs_status.configure(text="✓ 目录有效", text_color="green")
        else:
            self.figs_status.configure(text="✗ 目录不存在", text_color="red")

    def _validate_files(self):
        self._validate_pdf(self.pdf_picker.get_path())
        self._validate_tmpl(self.tmpl_picker.get_path())
        self._validate_figs(self.figs_picker.get_path())

    # ── 模式切换 ──
    def _on_mode_change(self):
        mode = self.extract_mode.get()
        if mode == "llm":
            self.mode_hint.configure(text="需 API 连接，约 10-30s，自适应不同模板")
        else:
            self.mode_hint.configure(text="无需 API，瞬间完成，适合标准模板")
        self.extract_frame.pack_forget()
        self.preview_btn.pack_forget()
        self.shared['is_template'] = False
        self.tmpl_status.configure(text="模式已切换，请重新检测模板", text_color="gray")

    # ── 模板检测 ──
    def _detect_template(self):
        """检测 PPTX 是否为模板骨架。"""
        self._validate_files()
        log_step('config', f'模板检测开始 ({self.extract_mode.get()} 模式)')
        path = self.tmpl_picker.get_path()
        if not path:
            self.tmpl_status.configure(text="请先选择模板文件", text_color="red")
            return
        if not os.path.exists(path):
            self.tmpl_status.configure(text="✗ 模板文件不存在", text_color="red")
            return
        self.shared['template_path'] = path

        if self.extract_mode.get() == "llm":
            self._detect_template_llm(path)
        else:
            self._detect_template_rule(path)

    def _detect_template_rule(self, path):
        try:
            from pptx import Presentation
            prs = Presentation(path)
            from scripts.make_template import classify
            t_count, c_count, placeholder_count = 0, 0, 0
            for slide in prs.slides:
                cat = classify(slide)
                if cat.startswith('SECTION_') or cat in ('COVER', 'TOC', 'THANKS', 'SUMMARY'):
                    t_count += 1
                elif cat in ('CONTENT', 'CONTENT_FRAME', 'DATA', 'DISCUSSION'):
                    c_count += 1
                    all_text = ' '.join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
                    if '此处填充' in all_text or '章节标题' in all_text or '论文标题' in all_text:
                        placeholder_count += 1
            if c_count > 0 and placeholder_count / c_count > 0.5:
                is_tpl = True
                ratio = 0.0
            else:
                ratio = c_count / max(len(prs.slides), 1)
                is_tpl = ratio < 0.2
            self.shared['is_template'] = is_tpl
            self._update_extract_ui(is_tpl, ratio)
        except Exception as e:
            self.tmpl_status.configure(text=f"检测失败: {e}", text_color="red")
            self.extract_frame.pack_forget()

    def _update_extract_ui(self, is_tpl, ratio=None):
        self.preview_btn.pack_forget()
        if is_tpl:
            self.tmpl_status.configure(
                text=f"✓ 已是模板骨架，可直接下一步",
                text_color="green")
            self.extract_frame.pack_forget()
            # 检查是否需要显示预览按钮（模板路径是否在 process/ 下）
            self._maybe_show_preview()
        else:
            mode_label = "LLM 自适应" if self.extract_mode.get() == "llm" else "规则"
            self.tmpl_status.configure(
                text=f"⚠ 检测到完整PPTX (内容页{ratio:.0%})，请点击「提取模板骨架」",
                text_color="orange")
            self.extract_frame.pack(fill="x", padx=10, pady=(5, 0), before=self.mode_rule_btn.master)
            self.extract_btn.configure(text=f"提取模板骨架 ({mode_label})", state="normal")
            self.extract_progress.configure(text="")

    def _maybe_show_preview(self):
        """如果模板路径在 process/ 目录下（说明是生成的文件），显示预览按钮。"""
        tmpl = self.shared.get('template_path', '')
        if tmpl and os.path.exists(tmpl) and 'process' in tmpl.replace('\\', '/'):
            self.extract_frame.pack(fill="x", padx=10, pady=(5, 0), before=self.mode_rule_btn.master)
            self.preview_btn.pack(side="left", padx=5)

    def _detect_template_llm(self, path):
        try:
            from scripts.llm_template_extract import load_template_cache
            cache = load_template_cache(path)
            if cache:
                cats = {s['index']: s['classification'] for s in cache['slides']}
                c_count = sum(1 for v in cats.values() if v == 'CONTENT')
                ratio = c_count / max(len(cats), 1)
                is_tpl = ratio < 0.2
                self.shared['is_template'] = is_tpl
                self._update_extract_ui(is_tpl, ratio)
                self.tmpl_status.configure(text=f"✓ 从缓存识别", text_color="green")
                return
        except Exception:
            pass

        try:
            from pptx import Presentation
            prs = Presentation(path)
            from scripts.make_template import classify
            c_count, ph_count = 0, 0
            for slide in prs.slides:
                cat = classify(slide)
                if cat in ('CONTENT', 'CONTENT_FRAME', 'DATA', 'DISCUSSION'):
                    c_count += 1
                    all_text = ' '.join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
                    if '此处填充' in all_text or '章节标题' in all_text or '论文标题' in all_text:
                        ph_count += 1
            if c_count > 0 and ph_count / c_count > 0.5:
                self.shared['is_template'] = True
                self._update_extract_ui(True, 0.0)
                self.tmpl_status.configure(text="✓ 已是模板骨架（检测到占位符），无需处理", text_color="green")
                from scripts.llm_template_extract import analyze_and_cache
                threading.Thread(target=lambda: analyze_and_cache(path), daemon=True).start()
                return
        except Exception:
            pass

        url = self.shared.get('api_base_url', '').strip()
        key = self.shared.get('api_key', '').strip()
        model = self.shared.get('api_model', '').strip()
        if not url or not key:
            self.tmpl_status.configure(text="LLM 模式需要填写 API 配置（点击右下角「AI配置」）", text_color="red")
            return
        self.tmpl_status.configure(text="LLM 分类中...", text_color="gray")
        threading.Thread(target=self._do_llm_detect, args=(path, url, key, model), daemon=True).start()

    def _do_llm_detect(self, path, url, key, model):
        try:
            from pptx import Presentation
            from scripts.llm_template_extract import (
                dump_all_slides, build_classification_prompt,
                parse_classification_response, CLASSIFICATION_SYSTEM,
            )
            import requests
            prs = Presentation(path)
            slides_data = dump_all_slides(prs)
            prompt = build_classification_prompt(slides_data)
            headers = {'Content-Type': 'application/json'}
            if key:
                headers['Authorization'] = f'Bearer {key}'
            resp = requests.post(
                f'{url.rstrip("/")}/chat/completions',
                headers=headers,
                json={'model': model, 'messages': [
                    {'role': 'system', 'content': CLASSIFICATION_SYSTEM},
                    {'role': 'user', 'content': prompt},
                ], 'temperature': 0.0},
                timeout=120,
            )
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            classifications = parse_classification_response(content)
            t_count = sum(1 for v in classifications.values() if v != 'CONTENT')
            c_count = sum(1 for v in classifications.values() if v == 'CONTENT')
            total = len(classifications)
            ratio = c_count / max(total, 1)
            is_tpl = ratio < 0.2
            self.shared['is_template'] = is_tpl
            self.shared['llm_classifications'] = classifications
            cats = []
            for i in sorted(classifications.keys()):
                cats.append(f"p{i}={classifications[i]}")
            detail = ", ".join(cats)
            self.after(0, lambda: self._update_extract_ui_llm(is_tpl, ratio, detail))
        except Exception as e:
            self.after(0, lambda: self.tmpl_status.configure(
                text=f"LLM 检测失败: {str(e)[:120]}", text_color="red"))

    def _update_extract_ui_llm(self, is_tpl, ratio, detail):
        self._update_extract_ui(is_tpl, ratio)
        current = self.tmpl_status.cget("text")
        self.tmpl_status.configure(text=f"{current}  [{detail}]")

    # ── 预览生成模板 ──
    def _preview_template(self):
        """用系统默认程序打开生成的模板 PPTX。"""
        path = self.shared.get('template_path', '')
        if path and os.path.exists(path):
            log_step('config', f'预览模板: {path}')
            try:
                os.startfile(path)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("无法打开", str(e))

    # ── 恢复共享数据 ──
    def restore_from_shared(self):
        if self.shared.get('pdf_path'):
            self.pdf_picker.set_path(self.shared['pdf_path'])
        if self.shared.get('template_path'):
            self.tmpl_picker.set_path(self.shared['template_path'])
        if self.shared.get('figs_dir'):
            self.figs_picker.set_path(self.shared['figs_dir'])
        if self.shared.get('extract_mode'):
            self.extract_mode.set(self.shared['extract_mode'])
            self._on_mode_change()
        self._validate_files()

    # ── 下一步 ──
    def _go_next(self):
        # 先校验文件（刷新状态标签）
        self._validate_files()

        errors = []
        if not self.pdf_picker.get_path():
            errors.append("论文 PDF 未选择")
        elif not self.pdf_picker.is_valid():
            errors.append("论文 PDF 文件不存在")
        if not self.tmpl_picker.get_path():
            errors.append("模板 PPTX 未选择")
        elif not self.tmpl_picker.is_valid():
            errors.append("模板 PPTX 文件不存在")
        figs = self.figs_picker.get_path()
        if figs and not self.figs_picker.is_valid():
            errors.append("图片目录不存在")
        key = self.shared.get('api_key', '').strip()
        if not key:
            errors.append("API Key 未填写（点击右下角「AI配置」）")

        if errors:
            from tkinter import messagebox
            messagebox.showerror("配置不完整", "\n".join(errors))
            return

        self.shared['pdf_path'] = self.pdf_picker.get_path()
        self.shared['template_path'] = self.tmpl_picker.get_path()
        self.shared['figs_dir'] = figs
        self.shared['extract_mode'] = self.extract_mode.get()

        # 模板未提取为骨架：宽松处理，允许继续
        if not self.shared.get('is_template', False):
            from tkinter import messagebox
            ok = messagebox.askyesno(
                "模板未处理",
                "当前模板可能尚未提取为骨架，\n"
                "直接使用完整 PPTX 可能导致样式不一致。\n\n"
                "是否仍然继续？\n"
                "（建议: 点「否」返回，先点击「提取模板骨架」）")
            if not ok:
                return

        self.app.switch_to_tab("大纲生成")

    # ── 提取模板 ──
    def _run_extract_template(self):
        log_step('config', f'开始提取模板 ({self.extract_mode.get()} 模式)')
        self.extract_btn.configure(state="disabled", text="提取中...")
        self.extract_progress.configure(text="准备中...", text_color="gray")
        self.preview_btn.pack_forget()
        self.next_btn.configure(state="disabled")
        mode = self.extract_mode.get()
        if mode == "llm":
            threading.Thread(target=self._do_extract_llm, daemon=True).start()
        else:
            threading.Thread(target=self._do_extract_rule, daemon=True).start()

    def _on_extract_done(self, dst):
        """提取成功后的 UI 更新（显示预览按钮）。"""
        self.extract_btn.configure(text="提取模板骨架", state="disabled")
        self.next_btn.configure(state="normal")
        if os.path.exists(dst):
            self.preview_btn.pack(side="left", padx=5)

    def _do_extract_rule(self):
        try:
            self.extract_progress.configure(text="提取中...")
            import sys, os as _os
            src = self.shared['template_path']
            proc_dir = _os.path.join(_os.path.dirname(_os.path.abspath(src)), 'process')
            _os.makedirs(proc_dir, exist_ok=True)
            dst = _os.path.join(proc_dir, 'template.pptx')
            sys.argv = ['make_template.py', src, dst]
            from scripts.make_template import main as make_tmpl_main
            make_tmpl_main()
            try:
                from scripts.template_extractor import extract as extract_design
                design = extract_design(dst)
                import json as _json
                design_path = dst.replace('.pptx', '_design.json')
                with open(design_path, 'w', encoding='utf-8') as f:
                    _json.dump(design, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            self.shared['template_path'] = dst
            self.shared['is_template'] = True
            self.tmpl_status.configure(
                text=f"✓ 模板骨架已提取 → {os.path.basename(dst)}", text_color="green")
            self.extract_progress.configure(text="完成", text_color="green")
            self._on_extract_done(dst)
        except Exception as e:
            self.extract_progress.configure(text=f"失败: {str(e)[:80]}", text_color="red")
            self.extract_btn.configure(state="normal")
            self.next_btn.configure(state="normal")

    def _do_extract_llm(self):
        def progress(msg):
            self.extract_progress.configure(text=msg, text_color="gray")

        try:
            import os as _os
            src = self.shared['template_path']
            proc_dir = _os.path.join(_os.path.dirname(_os.path.abspath(src)), 'process')
            _os.makedirs(proc_dir, exist_ok=True)
            dst = _os.path.join(proc_dir, 'template.pptx')
            url = self.shared.get('api_base_url', '').strip()
            key = self.shared.get('api_key', '').strip()
            model = self.shared.get('api_model', '').strip()

            from scripts.llm_template_extract import extract_template_llm
            result = extract_template_llm(src, dst, url, key, model, on_progress=progress)

            try:
                from scripts.template_extractor import extract as extract_design
                design = extract_design(dst)
                import json as _json
                design_path = dst.replace('.pptx', '_design.json')
                with open(design_path, 'w', encoding='utf-8') as f:
                    _json.dump(design, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

            self.shared['template_path'] = dst
            self.shared['is_template'] = True
            self.shared['llm_classifications'] = result['classifications']
            self.tmpl_status.configure(
                text=f"✓ LLM 模板已提取 → {os.path.basename(dst)}", text_color="green")
            self.extract_progress.configure(text="完成", text_color="green")
            self.extract_frame.pack_forget()
            self._on_extract_done(dst)
        except Exception as e:
            self.extract_progress.configure(text=f"失败: {str(e)[:80]}", text_color="red")
            self.extract_btn.configure(state="normal")
            self.next_btn.configure(state="normal")
