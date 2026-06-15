"""
gui/persistence.py — 自动持久化：启动恢复上次状态，切换页面自动保存。
数据存于 %APPDATA%/PaperDeck/config.json
"""
import json, os, base64

CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'PaperDeck')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')

DEFAULTS = {
    'api_base_url': 'https://api.deepseek.com',
    'api_key': '',
    'api_model': 'deepseek-chat',
    'last_pdf': '',
    'last_template': '',
    'last_figs': '',
}


def _encode_key(key):
    """对 API Key 做简单 base64 编码（防窥屏，非加密）。"""
    if not key:
        return ''
    return base64.b64encode(key.encode('utf-8')).decode('ascii')


def _decode_key(encoded):
    """解码 base64 编码的 API Key。"""
    if not encoded:
        return ''
    try:
        return base64.b64decode(encoded.encode('ascii')).decode('utf-8')
    except Exception:
        return encoded  # 兼容旧版明文存储


def load():
    """加载持久化配置，与 DEFAULTS 合并。"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        data = {}
    # 合并默认值
    merged = dict(DEFAULTS)
    merged.update(data)
    # 解码 API Key
    if merged.get('api_key'):
        merged['api_key'] = _decode_key(merged['api_key'])
    return merged


def save(data):
    """保存配置到磁盘。API Key 自动编码。"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    to_save = dict(data)
    # 编码 API Key
    if to_save.get('api_key'):
        to_save['api_key'] = _encode_key(to_save['api_key'])
    # 保存
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)


def save_from_shared(shared):
    """从 GUI 共享数据字典中提取并保存可持久化字段。"""
    save({
        'api_base_url': shared.get('api_base_url', ''),
        'api_key': shared.get('api_key', ''),
        'api_model': shared.get('api_model', ''),
        'extract_mode': shared.get('extract_mode', 'rule'),
        'last_pdf': shared.get('pdf_path') or '',
        'last_template': shared.get('template_path') or '',
        'last_figs': shared.get('figs_dir') or '',
    })


def restore_to_shared(shared):
    """从持久化存储恢复数据到共享字典。"""
    config = load()
    shared['api_base_url'] = config.get('api_base_url', '')
    shared['api_key'] = config.get('api_key', '')
    shared['api_model'] = config.get('api_model', '')
    shared['extract_mode'] = config.get('extract_mode', 'rule')
    # 路径字段——仅当共享数据中尚未设置时才恢复上次路径
    if not shared.get('pdf_path') and config.get('last_pdf'):
        shared['pdf_path'] = config['last_pdf']
    if not shared.get('template_path') and config.get('last_template'):
        shared['template_path'] = config['last_template']
    if not shared.get('figs_dir') and config.get('last_figs'):
        shared['figs_dir'] = config['last_figs']
