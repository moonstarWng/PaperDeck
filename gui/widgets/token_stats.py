"""
gui/widgets/token_stats.py — Token 用量统计弹窗。
"""
import customtkinter as ctk
from gui import token_tracker


class TokenStatsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Token 用量统计")
        self.geometry("600x500")
        self.minsize(500, 400)
        self.after(50, lambda: (self.lift(), self.focus_force()))
        self.after(100, self._refresh)

        # 标题
        ctk.CTkLabel(self, text="Token 用量统计", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # 统计数字区
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="x", padx=15, pady=5)
        self.stat_labels = {}
        for row, (key, label) in enumerate([
            ('session', '本次会话'), ('today', '本日'),
            ('week', '本周'), ('month', '本月'),
            ('total', '总计'),
        ]):
            ctk.CTkLabel(self.stats_frame, text=label, font=ctk.CTkFont(size=13, weight="bold")).grid(
                row=row, column=0, padx=10, pady=3, sticky="w")
            val_label = ctk.CTkLabel(self.stats_frame, text="—", font=ctk.CTkFont(size=13))
            val_label.grid(row=row, column=1, padx=10, pady=3, sticky="e")
            self.stat_labels[key] = val_label
        self.stats_frame.grid_columnconfigure(1, weight=1)

        # 流量图（简单文本柱状图）
        ctk.CTkLabel(self, text="近 7 天用量趋势", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 0))
        self.chart_canvas = ctk.CTkCanvas(self, height=180, bg='#2b2b2b', highlightthickness=0)
        self.chart_canvas.pack(fill="x", padx=15, pady=5)

        # 操作按钮
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(btn_frame, text="刷新", width=80, command=self._refresh).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="清除记录", width=80, fg_color="#D94F4F",
                       command=self._clear).pack(side="right", padx=5)

    def _refresh(self):
        stats = token_tracker.get_stats()
        for key, lbl in self.stat_labels.items():
            s = stats.get(key, {})
            total = s.get('total', 0)
            calls = s.get('calls', 0)
            lbl.configure(text=f"{total:,} tokens ({calls} 次调用)")

        # 画流量图
        self._draw_chart(stats.get('history', []))

    def _draw_chart(self, history):
        import time, math
        self.chart_canvas.delete("all")
        if not history:
            self.chart_canvas.create_text(280, 90, text="暂无数据", fill="#888888", font=("", 14))
            return

        w, h = 570, 180
        # 按天聚合
        days = {}
        for r in history:
            day = time.strftime('%m/%d', time.localtime(r['ts']))
            days[day] = days.get(day, 0) + r.get('total', 0)

        # 取最近 7 天
        import datetime
        result = {}
        for i in range(6, -1, -1):
            d = datetime.date.today() - datetime.timedelta(days=i)
            key = d.strftime('%m/%d')
            result[key] = days.get(key, 0)

        if not result:
            return

        max_v = max(result.values()) or 1
        bar_w = max(20, (w - 80) // len(result) - 10)
        x0 = 50

        # Y 轴
        self.chart_canvas.create_line(45, 15, 45, h - 25, fill='#555555')
        self.chart_canvas.create_line(45, h - 25, w - 10, h - 25, fill='#555555')
        # Y 轴标签
        if max_v > 0:
            for v in (max_v, max_v // 2):
                y = h - 25 - int((v / max_v) * (h - 50))
                self.chart_canvas.create_text(38, y, text=f'{v//1000}k' if v >= 1000 else str(v),
                                               fill='#888888', font=("", 8), anchor="e")

        for i, (day, val) in enumerate(result.items()):
            bar_h = int((val / max_v) * (h - 60)) if max_v > 0 else 0
            x = x0 + i * (bar_w + 10)
            y = h - 25 - bar_h
            # 柱子
            color = '#E63946' if i == len(result) - 1 else '#007191'
            self.chart_canvas.create_rectangle(x, y, x + bar_w, h - 25, fill=color, outline='')
            # 数值
            if val > 0:
                self.chart_canvas.create_text(x + bar_w / 2, y - 5,
                                               text=f'{val//1000}k' if val >= 1000 else str(val),
                                               fill='#CCCCCC', font=("", 8))
            # 日期
            self.chart_canvas.create_text(x + bar_w / 2, h - 10, text=day, fill='#888888', font=("", 8))

    def _clear(self):
        token_tracker.clear()
        self._refresh()
