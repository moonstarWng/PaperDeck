"""
gui/pages/build_page.py — 构建页：验证 JSON + 生成 PPT + 进度日志。
"""
import customtkinter as ctk
import json, sys, os, threading, subprocess, tempfile
from tkinter import messagebox, filedialog

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class BuildPage(ctk.CTkFrame):
    """Tab 3: 构建触发 + 实时日志 + 输出管理。"""

    def __init__(self, master, shared, app):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.shared = shared
        self.app = app
        self.output_path = ""

        # ── 顶部按钮栏 ──
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="← 返回大纲", width=100, command=lambda: app.switch_to_tab("大纲生成")).pack(side="left", padx=5)
        self.build_btn = ctk.CTkButton(btn_frame, text="▶ 开始构建", width=120, height=36,
                                        fg_color="#007191", command=self._build)
        self.build_btn.pack(side="left", padx=20)
        self.open_btn = ctk.CTkButton(btn_frame, text="打开文件夹", width=100, command=self._open_folder)
        self.open_btn.pack(side="right", padx=5)

        # ── 日志输出区 ──
        ctk.CTkLabel(self, text="构建日志", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(5, 0))
        self.log_text = ctk.CTkTextbox(self, height=400, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        # ── 状态 ──
        self.status = ctk.CTkLabel(self, text="就绪", text_color="gray")
        self.status.pack(anchor="w", padx=15, pady=5)

    def _log(self, msg):
        """追加日志到文本区。"""
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _build(self):
        """开始构建流程：验证 → 构建。"""
        # 获取 JSON
        json_str = self.shared.get('slide_content_json', '')
        if not json_str:
            # 尝试从大纲页编辑区获取
            messagebox.showerror("错误", "请先在大纲页生成或编辑 slide-content.json")
            return

        # 保存 JSON 到临时文件
        try:
            config = json.loads(json_str)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON 格式错误", str(e))
            return

        # 确保路径正确 + 输出目录存在
        config.setdefault('meta', {})
        config['meta']['template_path'] = self.shared.get('template_path', '')
        config['meta']['figs_dir'] = self.shared.get('figs_dir', '')
        out = config['meta'].get('output_path', '')
        # 如果 LLM 生成的输出路径不合法（含特殊字符或目录不存在），使用安全的默认路径
        pdf_dir = os.path.dirname(self.shared.get('pdf_path', '')) or os.path.expanduser('~/Desktop')
        safe_out = os.path.join(pdf_dir, 'output.pptx')
        if not out or out == './output.pptx':
            config['meta']['output_path'] = safe_out
        else:
            # 确保输出目录存在
            out_dir = os.path.dirname(out)
            if out_dir and not os.path.exists(out_dir):
                config['meta']['output_path'] = safe_out
            elif not out_dir:
                config['meta']['output_path'] = os.path.join(pdf_dir, os.path.basename(out))
        # 最终确保目录存在
        final_dir = os.path.dirname(config['meta']['output_path'])
        os.makedirs(final_dir, exist_ok=True)

        # 写入临时 JSON 文件
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(config, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
        tmp.close()

        self._log(f"[开始] slide-content.json → {tmp_path}")
        self.build_btn.configure(state="disabled")
        self.status.configure(text="构建中...", text_color="gray")
        threading.Thread(target=self._do_build, args=(tmp_path,), daemon=True).start()

    def _do_build(self, json_path):
        """在后台线程中执行构建。"""
        try:
            self._log("[验证] 检查 JSON 结构...")
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
            from validate_outline import validate
            if not validate(json_path):
                raise RuntimeError("JSON 验证失败")

            self._log("[构建] 开始生成 PPT...")
            from ppt_builder import load_json, build
            config = load_json(json_path)
            output = build(config, json_path)
            self.output_path = output
            self._log(f"[完成] ✓ 输出: {output}")
            self.status.configure(text=f"✓ 构建完成 → {output}", text_color="green")
        except Exception as e:
            self._log(f"[错误] {e}")
            self.status.configure(text=f"✗ 构建失败: {e}", text_color="red")
        finally:
            self.build_btn.configure(state="normal")
            try:
                os.unlink(json_path)
            except:
                pass

    def _open_folder(self):
        """在资源管理器中打开输出文件夹。"""
        if self.output_path and os.path.exists(self.output_path):
            os.startfile(os.path.dirname(self.output_path))
        elif self.output_path:
            messagebox.showinfo("提示", f"文件尚未生成，路径: {self.output_path}")
        else:
            messagebox.showinfo("提示", "尚未构建，无输出文件")
