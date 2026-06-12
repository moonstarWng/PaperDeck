"""
paper2ppt GUI — 桌面应用程序入口。
启动 customtkinter 主窗口，加载三页标签式界面。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui.app import main

if __name__ == '__main__':
    main()
