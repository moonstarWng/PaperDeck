"""
test/conftest.py — 共享 fixtures。
"""
import os, sys, pytest

# 确保 scripts/ 在 sys.path 中
_scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, _scripts_dir)


@pytest.fixture(scope='session')
def demo_dir():
    d = os.path.join(os.path.dirname(__file__), '..', 'demo', 'demo2')
    assert os.path.isdir(d), f"demo2 dir not found: {d}"
    return d


@pytest.fixture(scope='session')
def template_path(demo_dir):
    p = os.path.join(demo_dir, 'template.pptx')
    assert os.path.exists(p), f"template not found: {p}"
    return p


@pytest.fixture(scope='session')
def demo_pptx_path(demo_dir):
    p = os.path.join(demo_dir, 'demo_paper_汇报.pptx')
    if os.path.exists(p):
        return p
    # fallback to demo_paper.pdf level
    return None
