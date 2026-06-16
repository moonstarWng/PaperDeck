"""
gui/workers/llm_worker.py — LLM API 调用工作线程。
使用 OpenAI 兼容的 Chat Completions API 生成大纲和 slide-content.json。
"""
import json, requests
from gui.logger import log_step


def _sanitize(text):
    """清除提示词中的个人信息（汇报人姓名等），替换为占位符。"""
    import re
    # 替换 "汇报人：xxx" 模式为 "汇报人：xxx"
    text = re.sub(r'汇报人[：:]\s*\S{1,4}', '汇报人：xxx', text)
    # 替换 "马淦" 等具体姓名
    for name in ['马淦']:
        text = text.replace(name, 'xxx')
    return text


def build_system_prompt():
    """从 prompt-base.txt 和 agent-prompt.txt 构建系统提示词（已脱敏）。"""
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prompt_parts = []

    for fname in ['prompt-base.txt', 'agent-prompt.txt']:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            content = None
            for enc in ['utf-8', 'gbk', 'gb2312']:
                try:
                    with open(fpath, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            if content:
                prompt_parts.append(_sanitize(content))

    # 读取 JSON Schema
    schema_path = os.path.join(base_dir, 'templates', 'slide-content-schema.json')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        prompt_parts.append(f"\n## 输出格式要求\n你必须返回一个合法的 JSON 对象，符合以下 Schema:\n{json.dumps(schema, indent=2, ensure_ascii=False)}")

    prompt_parts.append("""
## 任务
阅读用户提供的论文全文和图片列表，生成一个完整的 slide-content.json。
注意:
1. 所有内容使用中文
2. 每个结果页恰好3行要点，每行15-20字
3. 不标注图片编号(如"见图1A")
4. 英文学术术语首次出现时加括号中文翻译
5. 用自己的话总结，不复制原文
6. 返回纯 JSON，不要包裹在 ```json``` 中，不要有任何解释文字
""")
    return "\n\n".join(prompt_parts)


def call_llm(base_url, api_key, model, user_prompt, on_progress=None):
    """
    调用 OpenAI 兼容 API 生成内容。
    返回: str: LLM 返回的 JSON 字符串
    """
    import time
    t0 = time.time()
    if on_progress:
        on_progress("正在连接 LLM API...")
    log_step('llm', f'调用 {model} @ {base_url}')
    # 估算输入 token（中文约 1 char ≈ 1.5 token）
    input_chars = len(user_prompt)
    log_step('llm', f'  输入约 {input_chars} 字符')
    system_prompt = build_system_prompt()

    resp = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 16384,
        },
        timeout=300,
    )

    if resp.status_code != 200:
        raise requests.RequestException(f"HTTP {resp.status_code}: {resp.text[:200]}")

    if on_progress:
        on_progress("正在解析响应...")
    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    # 耗时和 token 统计
    elapsed = time.time() - t0
    usage = data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
    log_step('llm', f'  完成: {elapsed:.1f}s | tokens: {prompt_tokens}in + {completion_tokens}out = {total_tokens}')

    # 尝试从响应中提取 JSON（LLM 可能在前后加了说明文字）
    content = _extract_json(content)
    return content


def _extract_json(text):
    """从 LLM 响应中提取 JSON 对象。尝试多种策略。"""
    # 策略1: 直接解析
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 策略2: 提取第一个 { 到最后一个 } 之间的内容
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        extracted = text[start:end+1]
        try:
            json.loads(extracted)
            return extracted
        except json.JSONDecodeError:
            pass

    # 策略3: 移除 markdown 代码块标记
    if '```json' in text:
        text = text.split('```json', 1)[1]
        if '```' in text:
            text = text.split('```', 1)[0]
        try:
            json.loads(text.strip())
            return text.strip()
        except json.JSONDecodeError:
            pass

    # 所有策略都失败，返回原始文本
    return text
