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

        # 标签页容器
        self.tabview = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.add("配置")
        self.tabview.add("大纲生成")
        self.tabview.add("构建")

        log.get_logger()  # 初始化日志
        # 恢复上次会话数据
        persistence.restore_to_shared(self.shared)

        # 初始化三个页面
        self.config_page = ConfigPage(self.tabview.tab("配置"), self.shared, self)
        self.outline_page = OutlinePage(self.tabview.tab("大纲生成"), self.shared, self)
        self.build_page = BuildPage(self.tabview.tab("构建"), self.shared, self)

        # 启动后刷新配置页（加载恢复的路径和API设置）
        self.config_page.restore_from_shared()

        # Token 统计按钮（右下角）
        self.stats_btn = ctk.CTkButton(self, text="📊 Token 用量", width=100, height=28,
                                        fg_color="#333333", command=self._open_token_stats)
        self.stats_btn.place(relx=1.0, rely=1.0, x=-120, y=-35)

    def _open_token_stats(self):
        from gui.widgets.token_stats import TokenStatsWindow
        TokenStatsWindow(self)

    def _on_tab_change(self):
        """切换标签页时自动保存。"""
        persistence.save_from_shared(self.shared)

    def switch_to_tab(self, name):
        """切换到指定标签页并保存状态。"""
        persistence.save_from_shared(self.shared)
        self.tabview.set(name)


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
