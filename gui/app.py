"""
gui/app.py — 主窗口：customtkinter 三标签页布局。
"""
import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.pages.config_page import ConfigPage
from gui.pages.outline_page import OutlinePage
from gui.pages.build_page import BuildPage
from gui import persistence
from gui import logger as log

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_TITLE = "PaperDeck — 论文文献汇报PPT生成器"
WINDOW_SIZE = "1100x750"


class App(ctk.CTk):
    """主应用程序窗口，包含配置、大纲、构建三个标签页。"""

    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 600)

        # 共享数据存储：各页面通过此字典传递数据
        self.shared = {
            'pdf_path': None,
            'template_path': None,
            'is_template': False,
            'figs_dir': None,
            'api_base_url': 'https://api.deepseek.com',
            'api_key': '',
            'api_model': 'deepseek-chat',
            'paper_text': '',
            'paper_title': '',
            'outline': None,
            'slide_content_json': None,
        }

        # 顶部栏：AI配置 + 工具按钮
        top_bar = ctk.CTkFrame(self, height=36)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        self.ai_btn = ctk.CTkButton(top_bar, text="AI配置", width=80, height=28,
                                     fg_color="#333333", command=self._open_ai_config)
        self.ai_btn.pack(side="left")
        self.tools_btn = ctk.CTkButton(top_bar, text="工具", width=50, height=28,
                                        fg_color="#333333", command=self._open_tools_menu)
        self.tools_btn.pack(side="left", padx=5)

        # 标签页容器
        self.tabview = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.tabview.add("输入文件")
        self.tabview.add("大纲生成")
        self.tabview.add("构建")

        log.get_logger()  # 初始化日志
        # 恢复上次会话数据
        persistence.restore_to_shared(self.shared)

        # 初始化三个页面
        self.config_page = ConfigPage(self.tabview.tab("输入文件"), self.shared, self)
        self.outline_page = OutlinePage(self.tabview.tab("大纲生成"), self.shared, self)
        self.build_page = BuildPage(self.tabview.tab("构建"), self.shared, self)

        # 默认锁定 2、3 页（一键模式），勾选"精细控制"后解锁
        self._expert_mode = False

        # 启动后刷新配置页（加载恢复的路径）
        self.config_page.restore_from_shared()

        # 隐藏 2、3 页标签
        self.toggle_expert_mode(False)

        # 启动时检查 API 是否配置，未配置则自动弹出
        if not self.shared.get('api_key', '').strip():
            self.after(500, self._open_ai_config)

    def _open_ai_config(self):
        from gui.widgets.ai_config_popup import AIConfigPopup
        AIConfigPopup(self, self.shared)

    def _open_tools_menu(self):
        """工具菜单：关于 + 保存排故包。"""
        import tkinter.messagebox as mb
        import zipfile
        from datetime import datetime

        menu = ctk.CTkToplevel(self)
        menu.title("工具")
        menu.geometry("350x260")
        menu.resizable(False, False)
        menu.transient(self)
        menu.configure(fg_color="#3A3C42")

        # 居中
        menu.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 350) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 260) // 2
        menu.geometry(f"+{x}+{y}")

        # ── 版本信息 ──
        import os as _os
        repo = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        version = "v1.0"
        commit = ""
        # 优先读 VERSION 文件
        ver_file = _os.path.join(repo, 'VERSION')
        if _os.path.exists(ver_file):
            try:
                with open(ver_file) as vf:
                    version = f"v{vf.read().strip()}"
            except Exception:
                pass
        # 补充 git 信息
        try:
            import subprocess
            r = subprocess.run(["git", "describe", "--tags", "--always"],
                               cwd=repo, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                version = r.stdout.strip()
            r2 = subprocess.run(["git", "log", "-1", "--format=%h %s"],
                                cwd=repo, capture_output=True, text=True, timeout=5)
            if r2.returncode == 0:
                commit = r2.stdout.strip()
        except Exception:
            pass

        info = f"PaperDeck — 论文文献汇报PPT生成器\n\n版本: {version}"
        if commit:
            info += f"\n提交: {commit}"
        # 构建日期：取 VERSION 文件修改时间
        build_date = ""
        try:
            if _os.path.exists(ver_file):
                mtime = _os.path.getmtime(ver_file)
                build_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
        except Exception:
            pass
        if not build_date:
            build_date = datetime.now().strftime('%Y-%m-%d')
        info += f"\n构建日期: {build_date}"
        info += "\n\n技术栈: Python + customtkinter + python-pptx\n集成: ppt-master (OOXML分析)"

        ctk.CTkLabel(menu, text=info, justify="left", font=ctk.CTkFont(size=12)).pack(padx=15, pady=(15, 5))

        # ── 保存排故包按钮（靠下）──
        def _save_debug():
            try:
                from tkinter import filedialog
                default_name = f"PaperDeck_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = filedialog.asksaveasfilename(
                    title="保存排故包", defaultextension=".zip",
                    filetypes=[("ZIP", "*.zip")], initialfile=default_name)
                if not zip_path:
                    return

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    log_dir = _os.path.join(_os.environ.get('APPDATA', _os.path.expanduser('~')),
                                            'PaperDeck', 'logs')
                    if _os.path.isdir(log_dir):
                        for f in sorted(_os.listdir(log_dir)):
                            if f.endswith('.log'):
                                zf.write(_os.path.join(log_dir, f), f'logs/{f}')

                    pdf_path = self.shared.get('pdf_path', '')
                    if pdf_path and _os.path.exists(pdf_path):
                        proc_dir = _os.path.join(_os.path.dirname(_os.path.abspath(pdf_path)), 'process')
                        if _os.path.isdir(proc_dir):
                            for f in _os.listdir(proc_dir):
                                fp = _os.path.join(proc_dir, f)
                                if _os.path.isfile(fp) and f.endswith('.json'):
                                    zf.write(fp, f'process/{f}')

                    zf.writestr('version.txt', info)

                mb.showinfo("完成", f"排故包已保存:\n{zip_path}")
            except Exception as e:
                mb.showerror("失败", f"保存排故包失败: {e}")

        ctk.CTkButton(menu, text="保存排故包", width=120, height=32,
                       command=_save_debug).pack(side="bottom", pady=(0, 15))

    def _on_tab_change(self):
        """切换标签页时自动保存。"""
        persistence.save_from_shared(self.shared)

    def toggle_expert_mode(self, show: bool):
        """切换专家模式：显示/隐藏大纲页和构建页标签。"""
        self._expert_mode = show
        sb = self.tabview._segmented_button
        for name in ("大纲生成", "构建"):
            btn = sb._buttons_dict.get(name)
            if btn is not None:
                if show:
                    btn.grid()
                else:
                    btn.grid_remove()
        if not show:
            self.tabview.set("输入文件")

    def switch_to_tab(self, name):
        """切换到指定标签页并保存状态。"""
        persistence.save_from_shared(self.shared)
        self.tabview.set(name)


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
