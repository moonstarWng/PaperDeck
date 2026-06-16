"""
gui/widgets/file_picker.py — 文件选择器组件（拖拽 + 浏览按钮）。
"""
import customtkinter as ctk
from tkinter import filedialog
import os


class FilePicker(ctk.CTkFrame):
    """带标签、路径显示、浏览按钮的文件选择器。支持文件或目录模式。"""

    def __init__(self, master, label_text, file_types=None, directory=False,
                 on_change=None, **kwargs):
        """
        参数:
          label_text: 左侧标签文字
          file_types: 文件类型过滤，如 [("PPTX", "*.pptx"), ("All", "*.*")]
          directory: True=选择目录, False=选择文件
          on_change: 路径变化回调 (path: str) -> None
        """
        super().__init__(master, **kwargs)
        self.file_types = file_types or [("All Files", "*.*")]
        self.directory = directory
        self._path = ""
        self._updating = False
        self._on_change_cb = on_change

        # 标签
        self.label = ctk.CTkLabel(self, text=label_text, width=80, anchor="w")
        self.label.pack(side="left", padx=(5, 5))

        # 路径显示
        self.path_var = ctk.StringVar(value="")
        self.path_entry = ctk.CTkEntry(self, textvariable=self.path_var, width=320)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)
        # 监听手动编辑路径
        self.path_var.trace_add("write", self._on_path_var_change)

        # 浏览按钮
        self.browse_btn = ctk.CTkButton(self, text="浏览", width=60,
                                         command=self._browse)
        self.browse_btn.pack(side="right", padx=5)

    def _on_path_var_change(self, *_):
        """用户手动编辑路径时触发。"""
        if self._updating:
            return
        display = self.path_var.get()
        if display:
            self._path = display
        if self._on_change_cb:
            self._on_change_cb(self._path)

    def _browse(self):
        """打开文件/目录选择对话框。"""
        if self.directory:
            path = filedialog.askdirectory(title="选择目录")
        else:
            path = filedialog.askopenfilename(title="选择文件", filetypes=self.file_types)
        if path:
            self.set_path(path)

    def set_path(self, path):
        """设置路径并更新显示。"""
        self._path = path
        self._updating = True  # 抑制 trace 回调
        self.path_var.set(path)
        self._updating = False
        if self._on_change_cb:
            self._on_change_cb(path)

    def get_path(self):
        """获取当前选择的路径。"""
        return self._path

    def is_valid(self):
        """检查路径是否存在。"""
        return bool(self._path and os.path.exists(self._path))
