"""
gui/token_tracker.py — 全局 token 用量统计 + 持久化。
所有 LLM 调用通过 record() 记录，支持按时间维度查询。
"""
import os, json, time, threading

_STORE_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'PaperDeck')
_STORE_PATH = os.path.join(_STORE_DIR, 'token_usage.json')
_lock = threading.Lock()

def _load():
    if os.path.exists(_STORE_PATH):
        try:
            with open(_STORE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save(records):
    os.makedirs(_STORE_DIR, exist_ok=True)
    with open(_STORE_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

def record(model, prompt_tokens, completion_tokens):
    """记录一次 LLM 调用的 token 消耗。"""
    entry = {
        'ts': time.time(),
        'model': model,
        'in': prompt_tokens,
        'out': completion_tokens,
        'total': prompt_tokens + completion_tokens,
    }
    with _lock:
        records = _load()
        records.append(entry)
        # 保留最近 90 天
        cutoff = time.time() - 90 * 86400
        records = [r for r in records if r['ts'] > cutoff]
        _save(records)

def get_stats():
    """返回 {this_session, today, this_week, this_month, history} 统计数据。"""
    records = _load()
    now = time.time()
    today_start = now - now % 86400  # 今天 00:00
    week_start = today_start - (time.localtime().tm_wday) * 86400
    month_start = today_start - (time.localtime().tm_mday - 1) * 86400

    def _sum(start_ts):
        recs = [r for r in records if r['ts'] >= start_ts]
        return {
            'calls': len(recs),
            'in': sum(r['in'] for r in recs),
            'out': sum(r['out'] for r in recs),
            'total': sum(r['total'] for r in recs),
        }
    return {
        'session': _sum(records[-1]['ts'] if records else now),
        'today': _sum(today_start),
        'week': _sum(week_start),
        'month': _sum(month_start),
        'total': _sum(0),
        'history': records,  # 原始记录供画图
    }

def clear():
    _save([])
