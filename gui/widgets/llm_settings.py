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
        self.geometry("380x280")
        self.resizable(False, False)
        self.after(50, lambda: (self.lift(), self.focus_force()))

        self.settings = settings_dict
        self._ensure_defaults()

        ctk.CTkLabel(self, text="LLM 参数设置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # 温度
        row1 = ctk.CTkFrame(self)
        row1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row1, text="温度 (Temperature)", width=140).pack(side="left")
        self.temp_var = ctk.StringVar(value=self.settings.get('temperature', '1.0'))
        ctk.CTkEntry(row1, textvariable=self.temp_var, width=80).pack(side="right")
        ctk.CTkLabel(self, text="越高越随机 (0.0~2.0)，推荐 1.0",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=25)

        # max_tokens
        row2 = ctk.CTkFrame(self)
        row2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row2, text="最大输出 (max_tokens)", width=140).pack(side="left")
        self.mt_var = ctk.StringVar(value=self.settings.get('max_tokens', '4096'))
        ctk.CTkEntry(row2, textvariable=self.mt_var, width=80).pack(side="right")

        # top_p
        row3 = ctk.CTkFrame(self)
        row3.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row3, text="核采样 (top_p)", width=140).pack(side="left")
        self.tp_var = ctk.StringVar(value=self.settings.get('top_p', '1.0'))
        ctk.CTkEntry(row3, textvariable=self.tp_var, width=80).pack(side="right")
        ctk.CTkLabel(self, text="0.0~1.0，1.0 为不限制",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=25)

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

    def _restore(self):
        self.temp_var.set(DEFAULTS['temperature'])
        self.mt_var.set(DEFAULTS['max_tokens'])
        self.tp_var.set(DEFAULTS['top_p'])

    def _save(self):
        try:
            t = float(self.temp_var.get())
            m = int(self.mt_var.get())
            p = float(self.tp_var.get())
            if t < 0 or t > 2:
                raise ValueError
            self.settings['temperature'] = str(t)
            self.settings['max_tokens'] = str(m)
            self.settings['top_p'] = str(p)
            messagebox.showinfo("保存成功", "参数已保存，下次生成大纲生效")
            self.destroy()
        except ValueError:
            messagebox.showerror("格式错误", "温度/核采样应为 0.0~2.0 数字，max_tokens 应为整数")
