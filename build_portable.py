"""
build_portable.py — 一键构建 paper2ppt Embeddable 便携包。
用户端无需 Python、无需 pip、无需联网。解压即用。

用法: python build_portable.py
输出: dist/PaperDeck_vX.X.zip
"""
import os, sys, re, shutil, zipfile, subprocess, urllib.request

PYTHON_VERSION = "3.13.9"
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
    """pip install 所有依赖到便携包的 Lib 目录。已有包则跳过。"""
    deps = [
        "python-pptx",
        "pypdf",
        "pdfplumber",
        "pypdfium2",
        "lxml",
        "Pillow",
        "requests",
        "customtkinter",
    ]
    target = os.path.abspath(os.path.join(PORTABLE_DIR, "Lib"))
    os.makedirs(target, exist_ok=True)

    # 检测已安装的包，跳过无需重新安装的
    existing = set()
    for entry in os.listdir(target):
        # 包目录名可能是 foo 或 foo-version.dist-info
        name = re.split(r'-\d', entry)[0].lower().replace('_', '-')
        existing.add(name)

    missing = []
    for dep in deps:
        if dep.lower().replace('_', '-') in existing:
            print(f"  pip install {dep}... 跳过 (已安装)")
        else:
            missing.append(dep)

    if not missing:
        print("[3/6] 依赖已完整，跳过")
        return

    print(f"[3/6] 安装依赖 ({len(missing)} 个缺失)...")
    for dep in missing:
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
    """将宿主 Python 的 tcl/tk 注入 embeddable Python（embed 包不含 tkinter）。

    策略（Python 版本匹配 3.13.9，避免版本混用导致 .pyd 不兼容）:
      - tcl/ 运行时 → python/tcl/
      - 宿主 DLLs/ 全部文件 → python/DLLs/
        （._pth 中 ./DLLs 使 Python 优先从这找 .pyd/.dll；
         Windows 搜索调用模块所在目录，依赖 DLL 都能找到）
      - tkinter/ Python 包 → portable/Lib/tkinter/
    """
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

    # 2. 复制宿主 DLLs/ 全部文件 → python/DLLs/
    # （tcl86t.dll 有额外的传递依赖，只复制个别文件不够）
    dlls_src = os.path.join(host_prefix, 'DLLs')
    dlls_dst = os.path.join(python_dir, 'DLLs')
    if os.path.exists(dlls_dst):
        shutil.rmtree(dlls_dst)
    shutil.copytree(dlls_src, dlls_dst)
    n_dlls = len(os.listdir(dlls_dst))
    print(f"  DLLs/ → python/DLLs/ ({n_dlls} files)")

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
    """创建 启动.bat 启动脚本（._pth 处理 Python 模块路径，PATH 处理 Windows DLL 搜索）。"""
    print("[5/6] 创建启动脚本...")
    bat_content = r"""@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set PATH=%~dp0python\DLLs;%~dp0python;%PATH%
"%~dp0python\python.exe" gui_app.py
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
    try:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        print(f"\n[7/6] 自动解压 → {extract_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        print(f"  解压完成，双击 {extract_dir}\\启动.bat 即可测试")
    except PermissionError:
        print(f"\n[7/6] 自动解压跳过（目录被占用，ZIP 已生成）")
        print(f"  手动解压 {zip_path} 即可")


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("=" * 50)
    print(f"PaperDeck v{VERSION} — 便携包构建")
    print("=" * 50)

    # ── 增量构建：已有 portable/python/ 则不清理，仅更新项目文件 ──
    force_clean = '--clean' in sys.argv or '--force' in sys.argv
    if force_clean and os.path.exists(PORTABLE_DIR):
        print(f"\n[0/6] 强制清理旧构建...")
        shutil.rmtree(PORTABLE_DIR)
    elif not os.path.exists(os.path.join(PORTABLE_DIR, 'python', 'python.exe')):
        # 首次构建，或 python embeddable 缺失时才清理
        if os.path.exists(PORTABLE_DIR):
            print(f"\n[0/6] Python 环境缺失，清理重建...")
            shutil.rmtree(PORTABLE_DIR)
    else:
        print(f"\n[0/6] 检测到已有 Python 环境，增量构建 (仅更新项目文件)")
        # 清理上次的项目文件，保留 python/ 和 Lib/ 依赖
        for item in os.listdir(PORTABLE_DIR):
            p = os.path.join(PORTABLE_DIR, item)
            if item not in ('python', 'Lib'):
                if os.path.isfile(p) or os.path.islink(p):
                    os.remove(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)

    python_dir = os.path.abspath(download_python())
    pip_exe = install_pip(python_dir)
    install_deps(pip_exe)
    copy_tkinter(python_dir)
    copy_project()
    create_launcher()
    package_zip()


if __name__ == '__main__':
    main()
