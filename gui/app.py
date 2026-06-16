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

        # 顶部栏：AI配置按钮
        top_bar = ctk.CTkFrame(self, height=36)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))
        self.ai_btn = ctk.CTkButton(top_bar, text="AI配置", width=80, height=28,
                                     fg_color="#333333", command=self._open_ai_config)
        self.ai_btn.pack(side="left")

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

        # 启动后刷新配置页（加载恢复的路径）
        self.config_page.restore_from_shared()

        # 启动时检查 API 是否配置，未配置则自动弹出
        if not self.shared.get('api_key', '').strip():
            self.after(500, self._open_ai_config)

    def _open_ai_config(self):
        from gui.widgets.ai_config_popup import AIConfigPopup
        AIConfigPopup(self, self.shared)

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
