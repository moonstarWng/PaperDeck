"""
gui/logger.py — 持久化日志模块。
日志写入 %APPDATA%/PaperDeck/logs/，每次启动新建文件，保留最近 10 个。
"""
import os, logging, datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'PaperDeck', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

_logger = None


def _cleanup_old_logs(keep=10):
    """保留最近 `keep` 个日志文件。"""
    files = sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.log')], reverse=True)
    for f in files[keep:]:
        try:
            os.remove(os.path.join(LOG_DIR, f))
        except OSError:
            pass


def get_logger(name='paperdeck'):
    """获取（或创建）持久化 logger。"""
    global _logger
    if _logger is not None:
        return _logger

    _cleanup_old_logs()

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(LOG_DIR, f'session_{timestamp}.log')

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # 文件处理器
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    _logger.addHandler(fh)

    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    _logger.addHandler(ch)

    _logger.info(f'PaperDeck session started | log: {log_path}')
    return _logger


def log_step(step, detail='', level='info'):
    """记录流水线步骤。"""
    logger = get_logger()
    msg = f'[{step}] {detail}' if detail else f'[{step}]'
    getattr(logger, level)(msg)


def log_error(msg, exc_info=False):
    """记录错误（可选附带 traceback）。"""
    get_logger().error(msg, exc_info=exc_info)
