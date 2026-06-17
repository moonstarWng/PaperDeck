"""
gui/widgets/llm_settings.py — LLM 参数设置弹窗（温度、max_tokens 等）。
"""
import customtkinter as ctk
from tkinter import messagebox

DEFAULTS = {
    'temperature': '1.0',
    'max_tokens': '4096',
    'top_p': '1.0',
}


class LLMSettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, settings_dict):
        super().__init__(master)
        self.title("LLM 参数设置")
        self.geometry("400x320")
        self.resizable(False, False)
        self.configure(fg_color="#3A3C42")
        self.after(50, lambda: (self.lift(), self.focus_force()))
        self.after(150, lambda: (self.lift(), self.focus_force()))

        self.settings = settings_dict
        self._ensure_defaults()

        ctk.CTkLabel(self, text="LLM 参数设置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        # 温度 (0.0~2.0, step 0.1)
        ctk.CTkLabel(self, text="温度 (Temperature)", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20)
        temp_row = ctk.CTkFrame(self)
        temp_row.pack(fill="x", padx=20, pady=2)
        self.temp_slider = ctk.CTkSlider(temp_row, from_=0.0, to=2.0, number_of_steps=20,
                                          command=self._on_temp_change)
        self.temp_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.temp_label = ctk.CTkLabel(temp_row, text="1.0", width=35)
        self.temp_label.pack(side="right")
        self.temp_slider.set(float(self.settings.get('temperature', '1.0')))

        # 最大输出 (256~16384)
        ctk.CTkLabel(self, text="最大输出 (max_tokens)", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20, pady=(10, 0))
        mt_row = ctk.CTkFrame(self)
        mt_row.pack(fill="x", padx=20, pady=2)
        self.mt_options = ["512", "1024", "2048", "4096", "8192", "16384"]
        self.mt_var = ctk.StringVar(value=self.settings.get('max_tokens', '4096'))
        ctk.CTkOptionMenu(mt_row, values=self.mt_options, variable=self.mt_var, width=80).pack(side="right")

        # 核采样 (0.0~1.0, step 0.05)
        ctk.CTkLabel(self, text="核采样 (top_p)", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=20, pady=(10, 0))
        tp_row = ctk.CTkFrame(self)
        tp_row.pack(fill="x", padx=20, pady=2)
        self.tp_slider = ctk.CTkSlider(tp_row, from_=0.0, to=1.0, number_of_steps=20,
                                        command=self._on_tp_change)
        self.tp_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.tp_label = ctk.CTkLabel(tp_row, text="1.0", width=35)
        self.tp_label.pack(side="right")
        self.tp_slider.set(float(self.settings.get('top_p', '1.0')))

        # 按钮
        btn_row = ctk.CTkFrame(self)
        btn_row.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkButton(btn_row, text="恢复默认", width=80, fg_color="#555555",
                       command=self._restore).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="取消", width=60, fg_color="#555555",
                       command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_row, text="保存", width=60, command=self._save).pack(side="right", padx=5)

    def _ensure_defaults(self):
        for k, v in DEFAULTS.items():
            if k not in self.settings:
                self.settings[k] = v

    def _on_temp_change(self, v):
        self.temp_label.configure(text=f"{float(v):.1f}")

    def _on_tp_change(self, v):
        self.tp_label.configure(text=f"{float(v):.2f}")

    def _restore(self):
        self.temp_slider.set(1.0)
        self.mt_var.set("4096")
        self.tp_slider.set(1.0)

    def _save(self):
        self.settings['temperature'] = f"{self.temp_slider.get():.1f}"
        self.settings['max_tokens'] = self.mt_var.get()
        self.settings['top_p'] = f"{self.tp_slider.get():.2f}"
        messagebox.showinfo("保存成功", "参数已保存，下次生成大纲生效")
        self.destroy()
