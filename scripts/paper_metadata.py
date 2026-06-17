#!/usr/bin/env python3
"""
paper_metadata.py — 从 PDF 提取 DOI 并通过 CrossRef 获取完整元数据。

用法:
    from scripts.paper_metadata import extract_doi_from_pdf, lookup_crossref

    doi = extract_doi_from_pdf("paper.pdf")
    meta = lookup_crossref(doi)  # → {title, authors, journal, year, volume, ...}
"""

import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

# DOI 正则: "10." + 4+ 数字 + "/" + 非空白字符
_DOI_PATTERN = re.compile(r'\b(10\.\d{4,}/[^\s]+)\b')


def extract_doi_from_pdf(pdf_path: str) -> str | None:
    """
    从 PDF 中提取 DOI。

    优先扫第一页（DOI 通常在页眉或摘要附近），
    找不到再扫最后一页（部分期刊放在页脚参考文献旁）。

    返回 DOI 字符串（如 "10.1145/3295222.3295265"），找不到返回 None。
    """
    # 方案 1: pdfplumber（文本提取最准）
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_check = []
            if len(pdf.pages) >= 1:
                pages_to_check.append(0)
            if len(pdf.pages) >= 2:
                pages_to_check.append(len(pdf.pages) - 1)

            for page_idx in pages_to_check:
                text = pdf.pages[page_idx].extract_text()
                if text:
                    m = _DOI_PATTERN.search(text)
                    if m:
                        doi = m.group(1).rstrip('.,;)]}')
                        return doi
    except ImportError:
        pass
    except Exception:
        pass

    # 方案 2: pypdfium2 兜底
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        pages_to_check = []
        if len(pdf) >= 1:
            pages_to_check.append(0)
        if len(pdf) >= 2:
            pages_to_check.append(len(pdf) - 1)

        for page_idx in pages_to_check:
            page = pdf[page_idx]
            text_page = page.get_textpage()
            text = text_page.get_text_range()
            if text:
                m = _DOI_PATTERN.search(text)
                if m:
                    return m.group(1).rstrip('.,;)]}')
    except ImportError:
        pass
    except Exception:
        pass

    # 方案 3: 原始二进制搜索（最后兜底）
    try:
        with open(pdf_path, 'rb') as f:
            raw = f.read()
        text = raw.decode('utf-8', errors='ignore')
        matches = _DOI_PATTERN.findall(text)
        if matches:
            return matches[0].rstrip('.,;)]}')
    except Exception:
        pass

    return None


# ═══════════════════════════════════════════
# CrossRef API
# ═══════════════════════════════════════════

CROSSREF_API = 'https://api.crossref.org/works'


def lookup_crossref(doi: str, timeout: int = 15) -> dict | None:
    """
    通过 CrossRef API 获取论文完整元数据。

    返回 dict 结构:
      {
        "title": "论文标题",
        "authors": "作者1, 作者2, ...",
        "journal": "期刊名称",
        "year": 2024,
        "volume": "12",
        "issue": "3",
        "pages": "123-145",
        "doi": "10.xxx/xxx",
        "abstract": "摘要全文...",
        "publisher": "出版社",
        "type": "journal-article",
        "citation": "Journal Name 12(3), 123-145 (2024)",
        "url": "https://doi.org/10.xxx/xxx",
        "raw": {...},  # CrossRef 原始 JSON
      }

    找不到或网络错误返回 None。
    """
    url = f'{CROSSREF_API}/{urllib.parse.quote(doi, safe="")}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'PaperDeck/1.0 (mailto:paperdeck@example.com)',
        'Accept': 'application/json',
    })

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f'  [CrossRef] API 请求失败: {e}')
        return None

    msg = data.get('message')
    if not msg:
        return None

    # ── 解析标题 ──
    title = ''
    titles = msg.get('title', [])
    if titles:
        title = titles[0]

    # ── 解析作者 ──
    authors = []
    for a in msg.get('author', []):
        family = a.get('family', '')
        given = a.get('given', '')
        name = f'{given} {family}'.strip()
        if name:
            authors.append(name)
    authors_str = ', '.join(authors[:8])

    # ── 解析期刊 ──
    container = (msg.get('container-title') or [''])[0]
    if not container:
        container = (msg.get('short-container-title') or [''])[0]

    # ── 发表日期 ──
    issued = msg.get('issued', {})
    date_parts = issued.get('date-parts', [[None]])[0]
    year = date_parts[0] if date_parts else None

    # ── 卷/期/页 ──
    volume = msg.get('volume', '')
    issue = msg.get('issue', '')
    pages = msg.get('page', '')

    # ── 摘要 ──
    abstract = msg.get('abstract', '')
    if abstract:
        abstract = re.sub(r'<[^>]+>', '', abstract)
        abstract = re.sub(r'\s+', ' ', abstract).strip()

    # ── 出版商 ──
    publisher = msg.get('publisher', '')

    # ── URL ──
    paper_url = f'https://doi.org/{doi}'

    # ── 组装引用字符串 ──
    citation_parts = []
    if container:
        citation_parts.append(container)
    vol_issue = ''
    if volume:
        vol_issue = volume
        if issue:
            vol_issue += f'({issue})'
    if vol_issue:
        citation_parts.append(vol_issue)
    if pages:
        citation_parts.append(pages)
    if year:
        citation_parts.append(f'({year})')
    citation = ', '.join(citation_parts)

    meta = {
        'title': title,
        'authors': authors_str,
        'journal': container,
        'year': year,
        'volume': volume,
        'issue': issue,
        'pages': pages,
        'doi': doi,
        'abstract': abstract,
        'publisher': publisher,
        'type': msg.get('type', ''),
        'citation': citation,
        'url': paper_url,
        'raw': msg,
    }

    return meta


# ═══════════════════════════════════════════
# Semantic Scholar DOI 精确查询（关键词/领域）
# ═══════════════════════════════════════════

def lookup_semantic_scholar_by_doi(doi: str, timeout: int = 10) -> dict | None:
    """
    通过 Semantic Scholar API 按 DOI 精确查询，获取 keywords/fieldsOfStudy。

    返回:
        {"fields_of_study": ["Computer Science", ...],
         "citation_count": 1234,
         "tldr": "一句话摘要"}

    失败返回 None。
    """
    url = f'https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(doi, safe="")}'
    url += '?fields=fieldsOfStudy,citationCount,tldr'
    req = urllib.request.Request(url, headers={'User-Agent': 'PaperDeck/1.0'})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None

    if not data or data.get('error'):
        return None

    result = {}
    fos = data.get('fieldsOfStudy')
    if fos:
        result['fields_of_study'] = fos
    cc = data.get('citationCount')
    if cc is not None:
        result['citation_count'] = cc
    tldr = data.get('tldr')
    if tldr:
        result['tldr'] = tldr.get('text', '') if isinstance(tldr, dict) else str(tldr)

    return result if result else None


# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════


def extract_metadata(pdf_path: str) -> dict | None:
    """
    一站式提取论文元数据：PDF → DOI → CrossRef + Semantic Scholar（关键词）。

    返回 dict (同 lookup_crossref 格式 + 可选 keywords)，失败返回 None。
    """
    doi = extract_doi_from_pdf(pdf_path)
    if not doi:
        print(f'  [paper_metadata] 未能从 PDF 提取 DOI')
        return None

    print(f'  [paper_metadata] DOI: {doi}')
    meta = lookup_crossref(doi)
    if not meta:
        return None

    print(f'  [paper_metadata] 标题: {meta["title"][:80]}...')
    print(f'  [paper_metadata] 引用: {meta["citation"]}')

    # 附加：Semantic Scholar 关键词/领域
    try:
        ss = lookup_semantic_scholar_by_doi(doi)
        if ss:
            if ss.get('fields_of_study'):
                meta['keywords'] = ', '.join(ss['fields_of_study'])
                print(f'  [paper_metadata] 关键词: {meta["keywords"]}')
            if ss.get('citation_count'):
                meta['citation_count'] = ss['citation_count']
    except Exception:
        pass

    return meta


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python paper_metadata.py <paper.pdf>")
        sys.exit(1)

    path = sys.argv[1]
    print(f"=== 提取 DOI: {path} ===")
    doi = extract_doi_from_pdf(path)
    if not doi:
        print("未找到 DOI")
        sys.exit(1)

    print(f"DOI: {doi}")
    print()
    print("=== CrossRef 元数据 ===")
    meta = lookup_crossref(doi)
    if meta:
        for k, v in meta.items():
            if k == 'raw':
                continue
            print(f"  {k}: {str(v)[:120]}")
    else:
        print("CrossRef 查询失败")
