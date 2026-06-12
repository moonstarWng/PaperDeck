"""
build_portable.py — 一键构建 paper2ppt Embeddable 便携包。
用户端无需 Python、无需 pip、无需联网。解压即用。

用法: python build_portable.py
输出: dist/PaperDeck_vX.X.zip
"""
import os, sys, shutil, zipfile, subprocess, urllib.request

PYTHON_VERSION = "3.11.9"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PORTABLE_DIR = "portable"
DIST_DIR = "dist"
VERSION = "1.0"

# ═══════════════════════════════════════════
# Step 1: 下载 + 解压 Python embeddable
# ═══════════════════════════════════════════

def download_python():
    """下载 Python embeddable 包 (约 12MB)。"""
    python_dir = os.path.join(PORTABLE_DIR, "python")
    zip_path = os.path.join(PORTABLE_DIR, "python_embed.zip")

    if os.path.exists(python_dir) and os.path.exists(os.path.join(python_dir, "python.exe")):
        print("[1/6] Python embeddable 已存在，跳过下载")
        return python_dir

    print(f"[1/6] 下载 Python {PYTHON_VERSION} embeddable (~12MB)...")
    os.makedirs(PORTABLE_DIR, exist_ok=True)

    def _report(count, block, total):
        if count % 20 == 0:
            pct = min(100, int(count * block * 100 / total))
            print(f"  {pct}%", end="\r")
    urllib.request.urlretrieve(PYTHON_EMBED_URL, zip_path, reporthook=_report)
    print("\n  下载完成")

    print("  解压...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(python_dir)
    os.remove(zip_path)

    # 启用 pip + 添加便携 Lib 路径：编辑 python3xx._pth
    pth_files = [f for f in os.listdir(python_dir) if f.endswith('._pth')]
    for pth in pth_files:
        pth_path = os.path.join(python_dir, pth)
        with open(pth_path, 'r') as f:
            content = f.read()
        # 1. 取消 import site 的注释（启用 pip 安装的包）
        if '#import site' in content:
            content = content.replace('#import site', 'import site')
        # 2. 添加便携 Lib 和 DLLs 目录到搜索路径
        for line in ['../Lib', './DLLs']:
            if line not in content:
                content = line + '\n' + content
        with open(pth_path, 'w') as f:
            f.write(content)
        print(f"  已配置路径: {pth} (+../Lib)")

    print(f"  Python → {python_dir}")
    return python_dir


# ═══════════════════════════════════════════
# Step 2: 安装 pip
# ═══════════════════════════════════════════

def install_pip(python_dir):
    """通过 get-pip.py 安装 pip 到 embeddable Python。"""
    python_dir = os.path.abspath(python_dir)
    pip_exe = os.path.join(python_dir, "Scripts", "pip.exe")
    if os.path.exists(pip_exe):
        print("[2/6] pip 已安装，跳过")
        return pip_exe

    print("[2/6] 安装 pip...")
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = os.path.abspath(os.path.join(PORTABLE_DIR, "get-pip.py"))
    urllib.request.urlretrieve(get_pip_url, get_pip_path)

    python_exe = os.path.join(python_dir, "python.exe")
    subprocess.run([python_exe, get_pip_path, "--no-warn-script-location"], check=True)
    os.remove(get_pip_path)

    print(f"  pip → {pip_exe}")
    return pip_exe


# ═══════════════════════════════════════════
# Step 3: 安装依赖到便携包
# ═══════════════════════════════════════════

def install_deps(pip_exe):
    """pip install 所有依赖到便携包的 Lib 目录。"""
    print("[3/6] 安装依赖 (仅首次需编译)...")
    deps = [
        "python-pptx",
        "pypdf",
        "pdfplumber",
        "lxml",
        "Pillow",
        "requests",
        "customtkinter",
    ]
    target = os.path.abspath(os.path.join(PORTABLE_DIR, "Lib"))
    for dep in deps:
        print(f"  pip install {dep}...")
        subprocess.run([
            os.path.abspath(pip_exe), "install", dep,
            "--target", target,
            "--no-warn-script-location",
            "--quiet",
        ], check=True)
    print("  依赖安装完成")


# ═══════════════════════════════════════════
# Step 4: 复制项目文件
# ═══════════════════════════════════════════

def copy_tkinter(python_dir):
    """将宿主 Python 的 tcl/tk 复制到 embeddable Python（embed 包不含 tkinter）。
    关键：tcl/ 和 DLLs/ 放到 python/ 目录（与 python.exe 同级），
    tkinter/ Python 模块放到便携 Lib/ 目录（._pth 已配置搜索此路径）。"""
    host_prefix = sys.prefix
    portable_lib = os.path.abspath(os.path.join(PORTABLE_DIR, 'Lib'))

    # 1. 复制 tcl/tk 运行时 (tcl/ 目录 → python/tcl/)
    tcl_src = os.path.join(host_prefix, 'tcl')
    tcl_dst = os.path.join(python_dir, 'tcl')
    if os.path.exists(tcl_src):
        if os.path.exists(tcl_dst):
            shutil.rmtree(tcl_dst)
        shutil.copytree(tcl_src, tcl_dst)
        print(f"  tcl/ -> python/tcl/")

    # 2. 复制 tcl/tk DLLs 和 _tkinter.pyd (DLLs/ → python/DLLs/)
    dlls_src = os.path.join(host_prefix, 'DLLs')
    dlls_dst = os.path.join(python_dir, 'DLLs')
    os.makedirs(dlls_dst, exist_ok=True)
    for f in os.listdir(dlls_src):
        if f.startswith('_tkinter') or f.startswith('tcl') or f.startswith('tk'):
            shutil.copy2(os.path.join(dlls_src, f), os.path.join(dlls_dst, f))
            print(f"  DLLs/{f}")

    # 3. 复制 tkinter Python 包 → portable/Lib/ (._pth 已配置 ../Lib)
    tk_lib_src = os.path.join(host_prefix, 'Lib', 'tkinter')
    tk_lib_dst = os.path.join(portable_lib, 'tkinter')
    if os.path.exists(tk_lib_src):
        if os.path.exists(tk_lib_dst):
            shutil.rmtree(tk_lib_dst)
        shutil.copytree(tk_lib_src, tk_lib_dst)
        print(f"  tkinter/ -> Lib/tkinter/")


def copy_project():
    """复制 paper2ppt 项目文件到便携包。"""
    base = os.path.abspath(os.path.dirname(__file__))
    print("[4/6] 复制项目文件...")
    items = [
        "gui_app.py", "gui", "scripts", "templates",
        "prompt-base.txt", "agent-prompt.txt",
    ]
    for item in items:
        src = os.path.join(base, item)
        dst = os.path.join(PORTABLE_DIR, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  {item}")
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  {item}/")
    # demo（可选，不含 pptx 文件）
    demo_src = os.path.join(base, "demo")
    if os.path.exists(demo_src):
        dst = os.path.join(PORTABLE_DIR, "demo")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(demo_src, dst, ignore=shutil.ignore_patterns("*.pptx", "__pycache__"))
        print(f"  demo/")


# ═══════════════════════════════════════════
# Step 5: 创建 启动.bat
# ═══════════════════════════════════════════

def create_launcher():
    """创建 启动.bat 启动脚本（._pth 已处理路径，此处仅设置编码并启动）。"""
    print("[5/6] 创建启动脚本...")
    bat_content = """@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
"%~dp0python\\python.exe" gui_app.py
if errorlevel 1 pause
"""
    bat_path = os.path.join(PORTABLE_DIR, "启动.bat")
    with open(bat_path, 'w', encoding='gbk') as f:
        f.write(bat_content)
    print(f"  启动.bat -> {bat_path}")


# ═══════════════════════════════════════════
# Step 6: 打包 → ZIP
# ═══════════════════════════════════════════

def package_zip():
    """将便携包压缩为单个 zip 文件。"""
    print("[6/6] 打包为 ZIP...")
    os.makedirs(DIST_DIR, exist_ok=True)
    zip_name = f"PaperDeck_v{VERSION}_portable.zip"
    zip_path = os.path.join(DIST_DIR, zip_name)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PORTABLE_DIR):
            # 跳过 .pyc 缓存
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                full = os.path.join(root, file)
                arcname = os.path.relpath(full, PORTABLE_DIR)
                zf.write(full, arcname)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"\n{'='*50}")
    print(f"  输出: {zip_path}")
    print(f"  大小: {size_mb:.1f} MB")
    print(f"  用户只需: 1. 解压  2. 双击 启动.bat")
    print(f"{'='*50}")

    # 自动解压到 dist/ 同名目录，便于本地测试
    extract_dir = os.path.join(DIST_DIR, f"PaperDeck_v{VERSION}_portable")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    print(f"\n[7/6] 自动解压 → {extract_dir}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
    print(f"  解压完成，双击 {extract_dir}\\启动.bat 即可测试")


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("=" * 50)
    print(f"PaperDeck v{VERSION} — 便携包构建")
    print("=" * 50)

    # 清理旧的 portable 目录
    if os.path.exists(PORTABLE_DIR):
        print(f"\n清理旧构建...")
        shutil.rmtree(PORTABLE_DIR)

    python_dir = os.path.abspath(download_python())
    pip_exe = install_pip(python_dir)
    install_deps(pip_exe)
    copy_tkinter(python_dir)
    copy_project()
    create_launcher()
    package_zip()


if __name__ == '__main__':
    main()
