"""
gui/widgets/ai_config_popup.py — AI 配置弹窗：API 设置 + Token 用量。
通过主界面「AI配置」按钮打开。
"""
import customtkinter as ctk
import threading
from gui import token_tracker


class AIConfigPopup(ctk.CTkToplevel):
    """AI 配置弹窗，含「API 配置」和「Token 用量」两个子标签页。"""

    def __init__(self, master, shared):
        super().__init__(master)
        self.shared = shared
        self.title("AI 配置")
        self.geometry("620x540")
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color="#3A3C42")
        self.after(50, lambda: (self.lift(), self.focus_force(), self.grab_set()))

        # ── 子标签页 ──
        self.sub_tabs = ctk.CTkTabview(self, command=self._on_sub_tab_change)
        self.sub_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        self.sub_tabs.add("API 配置")
        self.sub_tabs.add("AI参数调整")
        self.sub_tabs.add("Token 用量")

        self._build_api_page(self.sub_tabs.tab("API 配置"))
        self._build_params_page(self.sub_tabs.tab("AI参数调整"))
        self._build_token_page(self.sub_tabs.tab("Token 用量"))

        # 启动时如果切到 Token，刷新一次
        self.after(100, self._refresh_on_show)

    def _refresh_on_show(self):
        if self.sub_tabs.get() == "Token 用量":
            self._refresh_stats()

    # ═══════════════════════════════════════════
    # API 配置子页
    # ═══════════════════════════════════════════

    def _build_api_page(self, parent):
        ctk.CTkLabel(parent, text="LLM API 配置 (OpenAI 兼容)",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 10))

        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame, text="Base URL:", width=75).grid(
            row=0, column=0, padx=5, pady=6, sticky="e")
        self.url_entry = ctk.CTkEntry(frame, width=400, placeholder_text="https://api.deepseek.com")
        self.url_entry.grid(row=0, column=1, padx=5, pady=6, sticky="w")
        self.url_entry.insert(0, self.shared.get('api_base_url', 'https://api.deepseek.com'))

        ctk.CTkLabel(frame, text="API Key:", width=75).grid(
            row=1, column=0, padx=5, pady=6, sticky="e")
        self.key_entry = ctk.CTkEntry(frame, width=400, show="*", placeholder_text="sk-xxxxxxxx")
        self.key_entry.grid(row=1, column=1, padx=5, pady=6, sticky="w")
        if self.shared.get('api_key'):
            self.key_entry.insert(0, self.shared['api_key'])

        ctk.CTkLabel(frame, text="Model:", width=75).grid(
            row=2, column=0, padx=5, pady=6, sticky="e")
        self.model_entry = ctk.CTkEntry(frame, width=240, placeholder_text="deepseek-chat")
        self.model_entry.grid(row=2, column=1, padx=5, pady=6, sticky="w")
        self.model_entry.insert(0, self.shared.get('api_model', 'deepseek-chat'))

        # 按钮行
        btn_row = ctk.CTkFrame(parent)
        btn_row.pack(fill="x", padx=15, pady=(10, 5))
        self.test_btn = ctk.CTkButton(btn_row, text="测试连接", width=90, command=self._test_api)
        self.test_btn.pack(side="left", padx=5)
        self.save_btn = ctk.CTkButton(btn_row, text="保存配置", width=90, command=self._save_config)
        self.save_btn.pack(side="left", padx=5)

        self.api_status = ctk.CTkLabel(parent, text="", text_color="gray")
        self.api_status.pack(anchor="w", padx=25)

    def _save_config(self):
        self._save_to_shared()
        self.api_status.configure(text="✓ 配置已保存", text_color="green")

    # ═══════════════════════════════════════════
    # AI参数调整子页
    # ═══════════════════════════════════════════

    def _build_params_page(self, parent):
        ctk.CTkLabel(parent, text="AI 参数调整",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))
        ctk.CTkLabel(parent, text="调整生成多样性、输出长度等参数",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)

        # 温度
        ctk.CTkLabel(parent, text="温度 (Temperature)", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(15, 0))
        temp_row = ctk.CTkFrame(parent)
        temp_row.pack(fill="x", padx=20, pady=2)
        self.temp_slider = ctk.CTkSlider(temp_row, from_=0.0, to=2.0, number_of_steps=20,
                                          command=self._on_temp_change)
        self.temp_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.temp_label = ctk.CTkLabel(temp_row, text="1.0", width=35)
        self.temp_label.pack(side="right")
        temp_val = float(self.shared.get('temperature', '1.0'))
        self.temp_slider.set(temp_val)
        self.temp_label.configure(text=f"{temp_val:.1f}")

        # 最大输出
        ctk.CTkLabel(parent, text="最大输出 (max_tokens)", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(10, 0))
        mt_row = ctk.CTkFrame(parent)
        mt_row.pack(fill="x", padx=20, pady=2)
        self.mt_options = ["512", "1024", "2048", "4096", "8192", "16384"]
        self.mt_var = ctk.StringVar(value=self.shared.get('max_tokens', '4096'))
        ctk.CTkOptionMenu(mt_row, values=self.mt_options, variable=self.mt_var, width=80).pack(side="right")

        # 核采样
        ctk.CTkLabel(parent, text="核采样 (top_p)", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(10, 0))
        tp_row = ctk.CTkFrame(parent)
        tp_row.pack(fill="x", padx=20, pady=2)
        self.tp_slider = ctk.CTkSlider(tp_row, from_=0.0, to=1.0, number_of_steps=20,
                                        command=self._on_tp_change)
        self.tp_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.tp_label = ctk.CTkLabel(tp_row, text="1.0", width=35)
        self.tp_label.pack(side="right")
        tp_val = float(self.shared.get('top_p', '1.0'))
        self.tp_slider.set(tp_val)
        self.tp_label.configure(text=f"{tp_val:.2f}")

        # 多轮优选版本数
        ctk.CTkLabel(parent, text="多轮优选版本数 (num_versions)", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(10, 0))
        nv_row = ctk.CTkFrame(parent)
        nv_row.pack(fill="x", padx=20, pady=2)
        self.nv_options = ["2", "3", "4", "5", "6"]
        self.nv_var = ctk.StringVar(value=self.shared.get('num_versions', '3'))
        ctk.CTkOptionMenu(nv_row, values=self.nv_options, variable=self.nv_var, width=80).pack(side="right")

        # 按钮
        btn_row = ctk.CTkFrame(parent)
        btn_row.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkButton(btn_row, text="恢复默认", width=80, fg_color="#555555",
                       command=self._restore_params).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="保存", width=60, command=self._save_params).pack(side="right", padx=5)
        self.params_status = ctk.CTkLabel(parent, text="", text_color="gray")
        self.params_status.pack(anchor="w", padx=25)

    def _on_temp_change(self, v):
        self.temp_label.configure(text=f"{float(v):.1f}")

    def _on_tp_change(self, v):
        self.tp_label.configure(text=f"{float(v):.2f}")

    def _restore_params(self):
        self.temp_slider.set(1.0); self.temp_label.configure(text="1.0")
        self.mt_var.set("4096")
        self.tp_slider.set(1.0); self.tp_label.configure(text="1.00")
        self.nv_var.set("3")

    def _save_params(self):
        self.shared['temperature'] = f"{self.temp_slider.get():.1f}"
        self.shared['max_tokens'] = self.mt_var.get()
        self.shared['top_p'] = f"{self.tp_slider.get():.2f}"
        self.shared['num_versions'] = self.nv_var.get()
        self._save_to_shared()
        self.params_status.configure(text="✓ 参数已保存，下次生成大纲生效", text_color="green")

    def _test_api(self):
        url = self.url_entry.get().strip()
        key = self.key_entry.get().strip()
        model = self.model_entry.get().strip()
        if not url or not key:
            self.api_status.configure(text="请填写 Base URL 和 API Key", text_color="red")
            return
        self.api_status.configure(text="测试中...", text_color="gray")
        self._save_to_shared()
        threading.Thread(target=self._do_test_api, args=(url, key, model), daemon=True).start()

    def _do_test_api(self, url, key, model):
        import time
        t0 = time.time()
        try:
            import requests
            resp = requests.post(f"{url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                timeout=15)
            if resp.status_code == 200:
                elapsed = time.time() - t0
                self.api_status.configure(text=f"✓ 连接成功 ({elapsed:.1f}s)", text_color="green")
            else:
                self.api_status.configure(
                    text=f"✗ HTTP {resp.status_code}: {resp.text[:80]}", text_color="red")
        except Exception as e:
            self.api_status.configure(text=f"✗ 连接失败: {str(e)[:80]}", text_color="red")

    def _save_to_shared(self):
        self.shared['api_base_url'] = self.url_entry.get().strip()
        self.shared['api_key'] = self.key_entry.get().strip()
        self.shared['api_model'] = self.model_entry.get().strip()

    def save_to_shared(self):
        self._save_to_shared()

    # ═══════════════════════════════════════════
    # Token 用量子页
    # ═══════════════════════════════════════════

    def _build_token_page(self, parent):
        ctk.CTkLabel(parent, text="Token 用量统计",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        self.stats_frame = ctk.CTkFrame(parent)
        self.stats_frame.pack(fill="x", padx=15, pady=5)
        self.stat_labels = {}
        for row, (key, label) in enumerate([
            ('session', '本次会话'), ('today', '本日'),
            ('week', '本周'), ('month', '本月'),
            ('total', '总计'),
        ]):
            ctk.CTkLabel(self.stats_frame, text=label,
                         font=ctk.CTkFont(size=13, weight="bold")).grid(
                row=row, column=0, padx=10, pady=3, sticky="w")
            val_label = ctk.CTkLabel(self.stats_frame, text="—", font=ctk.CTkFont(size=13))
            val_label.grid(row=row, column=1, padx=10, pady=3, sticky="e")
            self.stat_labels[key] = val_label
        self.stats_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="近 7 天用量趋势",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 0))
        self.chart_canvas = ctk.CTkCanvas(parent, height=150, bg='#2b2b2b', highlightthickness=0)
        self.chart_canvas.pack(fill="x", padx=15, pady=5)

        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(btn_frame, text="刷新", width=80, command=self._refresh_stats).pack(
            side="left", padx=5)
        ctk.CTkButton(btn_frame, text="清除记录", width=80, fg_color="#D94F4F",
                       command=self._clear_stats).pack(side="right", padx=5)

    def _refresh_stats(self):
        stats = token_tracker.get_stats()
        for key, lbl in self.stat_labels.items():
            s = stats.get(key, {})
            total = s.get('total', 0)
            calls = s.get('calls', 0)
            lbl.configure(text=f"{total:,} tokens ({calls} 次调用)")
        self._draw_chart(stats.get('history', []))

    def _draw_chart(self, history):
        import time, datetime
        self.chart_canvas.delete("all")
        if not history:
            self.chart_canvas.create_text(240, 75, text="暂无数据",
                                          fill="#888888", font=("", 14))
            return

        w, h = 520, 150
        days = {}
        for r in history:
            day = time.strftime('%m/%d', time.localtime(r['ts']))
            days[day] = days.get(day, 0) + r.get('total', 0)

        result = {}
        for i in range(6, -1, -1):
            d = datetime.date.today() - datetime.timedelta(days=i)
            key = d.strftime('%m/%d')
            result[key] = days.get(key, 0)

        max_v = max(result.values()) or 1
        bar_w = max(18, (w - 80) // len(result) - 10)
        x0 = 50

        self.chart_canvas.create_line(45, 10, 45, h - 20, fill='#555555')
        self.chart_canvas.create_line(45, h - 20, w - 10, h - 20, fill='#555555')
        if max_v > 0:
            for v in (max_v, max_v // 2):
                y = h - 20 - int((v / max_v) * (h - 40))
                self.chart_canvas.create_text(38, y,
                    text=f'{v//1000}k' if v >= 1000 else str(v),
                    fill='#888888', font=("", 8), anchor="e")

        for i, (day, val) in enumerate(result.items()):
            bar_h = int((val / max_v) * (h - 50)) if max_v > 0 else 0
            x = x0 + i * (bar_w + 10)
            y = h - 20 - bar_h
            color = '#E63946' if i == len(result) - 1 else '#007191'
            self.chart_canvas.create_rectangle(x, y, x + bar_w, h - 20, fill=color, outline='')
            if val > 0:
                self.chart_canvas.create_text(
                    x + bar_w / 2, y - 5,
                    text=f'{val//1000}k' if val >= 1000 else str(val),
                    fill='#CCCCCC', font=("", 8))
            self.chart_canvas.create_text(x + bar_w / 2, h - 8,
                                          text=day, fill='#888888', font=("", 8))

    def _clear_stats(self):
        token_tracker.clear()
        self._refresh_stats()

    def _on_sub_tab_change(self):
        if self.sub_tabs.get() == "Token 用量":
            self._refresh_stats()

    def is_configured(self):
        return bool(self.shared.get('api_key', '').strip())
