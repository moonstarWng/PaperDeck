"""
gui/pages/outline_page.py — 大纲生成页：读论文、LLM生成大纲、树形编辑、构建。
"""
import customtkinter as ctk
import json, sys, os, threading
from tkinter import messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from gui.workers.llm_worker import call_llm, build_system_prompt
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
        self.optimize_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(btn_frame, text="多轮优选", variable=self.optimize_var,
                         width=80).pack(side="left", padx=5)
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
        """元数据提取: Semantic Scholar → LLM 回退。"""
        if not self._check_api():
            return
        self._safe_ui(lambda: self.status.configure(text="正在查询 Semantic Scholar...", text_color="gray"))
        threading.Thread(target=self._do_scholar_lookup, args=(paper_text,), daemon=True).start()

    def _do_scholar_lookup(self, paper_text):
        """通过 Semantic Scholar 搜索论文元数据。"""
        import urllib.request, urllib.parse
        try:
            # 用论文前 200 字作为搜索词
            query = paper_text[:200].split('\n')[0][:150]
            q = urllib.parse.quote(query)
            url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=1&fields=title,authors,journal,year'
            req = urllib.request.Request(url, headers={'User-Agent': 'PaperDeck/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            if data.get('data'):
                p = data['data'][0]
                meta = {
                    'title_en': p.get('title', ''),
                    'journal': (p.get('journal', {}) or {}).get('name', '') if p.get('journal') else '',
                    'authors': ', '.join(a['name'] for a in (p.get('authors', []) or [])[:5]),
                }
                if p.get('year'):
                    meta['journal'] = f"{meta['journal']} ({p['year']})".strip()
                self._apply_metadata(meta)
                self._safe_ui(lambda: self.status.configure(
                    text="✓ 元数据已获取 (Semantic Scholar)", text_color="green"))
                return
        except Exception:
            pass
        # 回退 LLM
        self._safe_ui(lambda: self.status.configure(text="Scholar 查询失败，改用 LLM 提取...", text_color="gray"))
        prompt = f"""从论文首页提取元数据，返回纯 JSON:
{{"title_en": "英文原标题", "journal": "期刊名称", "authors": "作者列表（逗号分隔，取前5位）"}}
论文首页:
{paper_text[:3000]}"""
        threading.Thread(target=self._do_metadata_call, args=(prompt,), daemon=True).start()

    def _apply_metadata(self, meta):
        self.title_entry.delete(0, 'end'); self.title_entry.insert(0, meta.get('title_en', ''))
        self.journal_entry.delete(0, 'end'); self.journal_entry.insert(0, meta.get('journal', ''))
        self.author_entry.delete(0, 'end'); self.author_entry.insert(0, meta.get('authors', ''))
        self.shared['paper_meta'] = meta

    def _do_metadata_call(self, prompt):
        try:
            result = call_llm(self.shared['api_base_url'], self.shared['api_key'],
                              self.shared['api_model'], prompt, on_progress=lambda m: None)
            meta = json.loads(result)
            self._safe_ui(lambda: self._apply_metadata_and_status(meta))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._safe_ui(lambda: self.status.configure(
                text=f"元数据提取失败: {e}（可手动填写）", text_color="orange"))

    def _apply_metadata_and_status(self, meta):
        self._apply_metadata(meta)
        self.status.configure(text="✓ 元数据已提取，可点击「生成大纲」", text_color="green")

    # ── 生成大纲（任务流水线）──
    def _generate_outline(self):
        if not self._check_api():
            return
        paper_text = self.shared.get('paper_text', '')
        if not paper_text:
            messagebox.showerror("错误", "请先读取论文")
            return
        self.status.configure(text="正在分析论文...", text_color="gray")

        title = self.title_entry.get().strip()
        journal = self.journal_entry.get().strip()
        authors = self.author_entry.get().strip()
        sections = self._get_section_config()
        if not sections:
            messagebox.showerror("错误", "请至少启用一个章节")
            return

        task_data = {
            'paper_text': paper_text[:40000],
            'title': title, 'journal': journal, 'authors': authors,
            'sections': sections,
            'figs': self._get_figs_list(),
            'has_paper_info': self.paper_info_var.get(),
            'optimize': self.optimize_var.get(),
        }
        threading.Thread(target=self._do_task_pipeline, args=(task_data,), daemon=True).start()

    def _do_task_pipeline(self, td):
        """Task 流水线: 分析→规划→内容→组装。"""
        import time
        t_start = time.time()
        n_sec = len(td['sections'])
        log_step('outline', f'任务流水线开始 ({n_sec} 章节)')
        api_url = self.shared['api_base_url']
        api_key = self.shared['api_key']
        model = self.shared['api_model']
        total_tokens = 0

        import requests, json as _json
        def _ask(system_prompt, user_prompt, label='', temp=0.3):
            nonlocal total_tokens
            t0 = time.time()
            headers = {'Content-Type': 'application/json'}
            if api_key: headers['Authorization'] = f'Bearer {api_key}'
            resp = requests.post(f'{api_url.rstrip("/")}/chat/completions', headers=headers,
                json={'model': model, 'temperature': temp,
                      'messages': [{'role': 'system', 'content': system_prompt},
                                   {'role': 'user', 'content': user_prompt}]}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            usage = data.get('usage', {})
            pt = usage.get('prompt_tokens', 0); ct = usage.get('completion_tokens', 0)
            total_tokens += pt + ct
            log_step('llm', f'  {label}: {time.time()-t0:.1f}s | {pt}in+{ct}out')
            return data['choices'][0]['message']['content']

        try:
            # ── Task 1: 论文分析 ──
            self._safe_ui(lambda: self.status.configure(text="Task 1/4: 分析论文结构...", text_color="gray"))
            analysis_prompt = f"""分析以下论文，提取关键信息。返回纯 JSON:
{{
  "core_contribution": "一句话核心贡献",
  "key_findings": ["发现1", "发现2", ...] (5-8条),
  "methods": ["方法1", "方法2", ...],
  "implications": ["意义1", ...],
  "limitations": ["局限1", ...]
}}
论文:
标题: {td['title']}
期刊: {td['journal']}
全文:
{td['paper_text']}"""
            analysis = _json.loads(_ask("你是论文学术分析专家，提取论文核心信息。只返回 JSON。", analysis_prompt))

            # ── Task 2: 章节内容生成 ──
            self._safe_ui(lambda: self.status.configure(text="Task 2/4: 生成章节内容...", text_color="gray"))
            all_results = []
            for sec_i, (sec_title, sec_pages) in enumerate(td['sections']):
                num = f"0{sec_i+1}"
                content_prompt = f"""为章节「{sec_title}」生成 {sec_pages} 页内容。返回纯 JSON 数组:
[{{
  "type": "result",  // 或 author/background/summary/discussion1/discussion2
  "title": "页标题",
  "body": ["要点1(15-20字)", "要点2", "要点3"],  // 恰好3行
  "images": []  // 先空着
}}, ...]

论文分析:
{_json.dumps(analysis, ensure_ascii=False)[:3000]}
图片:
{td['figs']}"""
                raw = _ask("你是 PPT 内容生成专家。只返回 JSON 数组。", content_prompt)
                pages = _json.loads(raw)
                if isinstance(pages, dict): pages = [pages]
                all_results.append({'section': num, 'title': sec_title, 'pages': pages})
                self._safe_ui(lambda i=sec_i: self.status.configure(
                    text=f"Task 2/4: 章节 {i+1}/{len(td['sections'])} ({sec_title})", text_color="gray"))

            # ── Task 3: 图片分配 ──
            self._safe_ui(lambda: self.status.configure(text="Task 3/4: 分配图片...", text_color="gray"))
            if td['figs'].strip():
                fig_list = td['figs']
                result_titles = []
                for sec in all_results:
                    for p in sec['pages']:
                        if p.get('type') == 'result':
                            result_titles.append(p.get('title', ''))
                img_prompt = f"""将图片分配到各结果页。返回纯 JSON:
{{"mapping": [{{"title": "页标题", "images": ["1A.jpg"]}}, ...]}}

图片: {fig_list}
结果页: {_json.dumps(result_titles, ensure_ascii=False)}"""
                img_map = _json.loads(_ask("你是图片分配专家。只返回 JSON。", img_prompt))
                for sec in all_results:
                    for p in sec['pages']:
                        for m in img_map.get('mapping', []):
                            if m.get('title') == p.get('title'):
                                p['images'] = m.get('images', [])
                                break

            # ── Task 4: 组装 ──
            self._safe_ui(lambda: self.status.configure(text="Task 4/4: 组装大纲...", text_color="gray"))
            slides = [
                {"type": "keep", "ref": "cover"},
                {"type": "keep", "ref": "toc"},
            ]
            section_divider_edits = []
            for sec_i, sec in enumerate(all_results):
                num = f"0{sec_i+1}"
                section_divider_edits.append({"number": num, "title": sec['title']})
                if sec_i == 0 and td['has_paper_info']:
                    slides.append({"type": "paper_info", "pdf_path": self.shared.get('pdf_path', ''),
                                   "paper_title": td['title'], "extra_text": ""})
                slides.append({"type": "keep", "ref": "section", "index": sec_i})
                for p in sec['pages']:
                    # 统一 images 格式: ["1A.jpg"] → [{"file": "1A.jpg"}]
                    if 'images' in p:
                        imgs = p['images']
                        if imgs and isinstance(imgs[0], str):
                            p['images'] = [{"file": f} for f in imgs]
                    slides.append(p)
            slides.append({"type": "keep", "ref": "thanks"})

            full_config = {
                "meta": {"template_path": self.shared.get('template_path', ''),
                         "figs_dir": self.shared.get('figs_dir', ''),
                         "output_path": "./output.pptx"},
                "cover": {"title_en": td['title'], "presenter": "xxx", "date": "202X年X月"},
                "toc_replacements": {},
                "section_divider_edits": section_divider_edits,
                "slides": slides,
            }
            result = _json.dumps(full_config, indent=2, ensure_ascii=False)
            self.shared['slide_content_json'] = result
            elapsed = time.time() - t_start
            log_step('outline', f'任务流水线完成: {elapsed:.1f}s | 总 tokens: {total_tokens}')
            self._safe_ui(lambda: self._load_llm_result(result))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._safe_ui(lambda: self.status.configure(text=f"生成失败: {e}", text_color="red"))

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

    def _do_multi_llm_call(self, prompt):
        """多轮生成 + 评分优选。"""
        api_url = self.shared['api_base_url']
        api_key = self.shared['api_key']
        model = self.shared['api_model']
        N = 3
        versions = []

        try:
            for i in range(N):
                self._safe_ui(lambda i=i: self.status.configure(
                    text=f"多轮优选: 生成版本 {i+1}/{N}...", text_color="gray"))
                # 每次温度微调，增加多样性
                temp = 0.3 + i * 0.2
                # 临时 patch call_llm 不支持 temperature → 用 requests 直调
                import requests, json as _json
                sys_prompt = build_system_prompt()
                headers = {'Content-Type': 'application/json'}
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
                resp = requests.post(
                    f'{api_url.rstrip("/")}/chat/completions',
                    headers=headers,
                    json={'model': model, 'temperature': temp,
                          'messages': [
                              {'role': 'system', 'content': sys_prompt},
                              {'role': 'user', 'content': prompt}]},
                    timeout=180)
                resp.raise_for_status()
                result = resp.json()['choices'][0]['message']['content']
                versions.append(result)

            # 评分
            self._safe_ui(lambda: self.status.configure(
                text=f"多轮优选: 评分 {N} 个版本...", text_color="gray"))
            best = self._score_versions(versions, api_url, api_key, model)

            self.shared['slide_content_json'] = best
            self._safe_ui(lambda: self._load_llm_result(best))
        except Exception as e:
            import traceback
            traceback.print_exc()
            # 回退：用第一个成功的版本
            if versions:
                self.shared['slide_content_json'] = versions[0]
                self._safe_ui(lambda: self._load_llm_result(versions[0]))
            else:
                self._safe_ui(lambda: self.status.configure(
                    text=f"多轮优选失败: {e}", text_color="red"))

    def _score_versions(self, versions, api_url, api_key, model):
        """评分专家：选出最优版本。"""
        import requests, json as _json
        scorer_prompt = """你是一个 PPT 大纲质量评审专家。请对以下 {N} 个 slide-content.json 版本进行评分。

评分标准（每项 1-10 分）：
1. 章节结构：章节数是否正确、section divider 是否按要求排列
2. 内容质量：要点是否准确、简洁、有价值
3. 格式规范：JSON 结构是否符合 schema、每个 result 页是否恰好 3 行
4. 图片分配：图片是否合理分配到各结果页

对每个版本输出：
{{
  "scores": [
    {{"version": 0, "structure": 8, "content": 7, "format": 9, "images": 6, "note": "简短评价"}},
    ...
  ],
  "best": 0
}}
只返回 JSON，不要解释。"""

        prompt_text = scorer_prompt.replace('{N}', str(len(versions)))
        for i, v in enumerate(versions):
            prompt_text += f"\n\n=== 版本 {i} ===\n{v[:3000]}"  # 截断以控制 token

        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        resp = requests.post(
            f'{api_url.rstrip("/")}/chat/completions',
            headers=headers,
            json={'model': model, 'temperature': 0.0,
                  'messages': [{'role': 'user', 'content': prompt_text}]},
            timeout=120)
        resp.raise_for_status()
        result = resp.json()['choices'][0]['message']['content']

        # 解析评分
        try:
            data = _json.loads(result)
            best_idx = data.get('best', 0)
            scores = data.get('scores', [])
            note = scores[best_idx].get('note', '') if best_idx < len(scores) else ''
            self._safe_ui(lambda: self.status.configure(
                text=f"✓ 多轮优选完成 (选版本{best_idx+1}: {note})", text_color="green"))
            return versions[best_idx]
        except Exception:
            return versions[0]  # 解析失败则用第一个

    def _load_llm_result(self, result):
        """在主线程加载 LLM 结果，解析失败则自动修复重试。"""
        self.editor.set_figs_dir(self.shared.get('figs_dir', ''))
        # 保存原始输出
        pdf_path = self.shared.get('pdf_path', '')
        if pdf_path:
            proc_dir = os.path.join(os.path.dirname(os.path.abspath(pdf_path)), 'process')
            os.makedirs(proc_dir, exist_ok=True)
            with open(os.path.join(proc_dir, 'slide-content-raw.json'), 'w', encoding='utf-8') as f:
                f.write(result)

        ok = self.editor.load_from_json(result)
        if ok:
            self.status.configure(text="✓ 大纲已生成，可展开编辑后点击「构建 PPT」", text_color="green")
        else:
            # 自动修复
            self.status.configure(text="JSON 解析失败，自动修复中...", text_color="orange")
            threading.Thread(target=self._repair_json_loop, args=(result, 0), daemon=True).start()

    def _repair_json_loop(self, broken_json, attempt):
        """LLM 修复 JSON 循环，最多 3 次。"""
        if attempt >= 3:
            self._safe_ui(lambda: self.status.configure(
                text="大纲生成失败：JSON 无法修复，请检查 LLM 输出", text_color="red"))
            return

        self._safe_ui(lambda: self.status.configure(
            text=f"JSON 修复中 ({attempt+1}/3)...", text_color="orange"))

        try:
            import requests, json as _json
            # 提取错误信息
            error_msg = ''
            try:
                _json.loads(broken_json)
                error_msg = 'unknown error'
            except _json.JSONDecodeError as e:
                error_msg = str(e)

            repair_prompt = f"""以下 JSON 解析失败，错误: {error_msg}

请修复 JSON 语法错误（如尾随逗号、未闭合括号、非法字符等），不要修改内容、结构和逻辑。
只返回修复后的合法 JSON，不要包裹在 ```json``` 中，不要有任何解释。

原始 JSON:
{broken_json[:8000]}"""

            api_url = self.shared['api_base_url']
            api_key = self.shared['api_key']
            model = self.shared['api_model']
            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            resp = requests.post(
                f'{api_url.rstrip("/")}/chat/completions',
                headers=headers,
                json={'model': model, 'temperature': 0.0,
                      'messages': [{'role': 'user', 'content': repair_prompt}]},
                timeout=60)
            resp.raise_for_status()
            repaired = resp.json()['choices'][0]['message']['content']

            # 用 repair_and_validate 再次校验
            from scripts.validate_outline import repair_and_validate
            rule_fixed, warnings = repair_and_validate(repaired)
            if rule_fixed is None:
                repaired = repaired  # keep LLM version
            else:
                repaired = rule_fixed

            # 保存修复后的版本
            pdf_path = self.shared.get('pdf_path', '')
            if pdf_path:
                proc_dir = os.path.join(os.path.dirname(os.path.abspath(pdf_path)), 'process')
                with open(os.path.join(proc_dir, f'slide-content-repair{attempt+1}.json'), 'w', encoding='utf-8') as f:
                    f.write(repaired)

            ok = self.editor.load_from_json(repaired)
            if ok:
                self._safe_ui(lambda: self.status.configure(
                    text=f"✓ 大纲已生成 (JSON 修复 {attempt+1} 次后通过)", text_color="green"))
            else:
                # 再次失败，递归重试
                threading.Thread(target=self._repair_json_loop, args=(repaired, attempt + 1), daemon=True).start()
        except Exception as e:
            import traceback
            traceback.print_exc()
            threading.Thread(target=self._repair_json_loop, args=(broken_json, attempt + 1), daemon=True).start()

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

        # 构建器自动按需克隆章节页

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

        # 保存中间大纲到 process 目录
        pdf_path = self.shared.get('pdf_path', '')
        if pdf_path:
            proc_dir = os.path.join(os.path.dirname(os.path.abspath(pdf_path)), 'process')
            os.makedirs(proc_dir, exist_ok=True)
            outline_path = os.path.join(proc_dir, 'slide-content.json')
            try:
                with open(outline_path, 'w', encoding='utf-8') as f:
                    f.write(self.shared['slide_content_json'])
            except Exception:
                pass

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
