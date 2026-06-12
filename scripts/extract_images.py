#!/usr/bin/env python3
"""
extract_images.py — 从论文 PDF 中提取嵌入的图片。
使用 pypdf 逐页扫描 PDF 的 XObject 资源，提取光栅图像。

用法: python extract_images.py <paper.pdf> [output_dir]

输出:
  - 图片文件: page_03_img_01.jpg, page_05_img_01.png ...
  - manifest.json: 记录每张图片的页码、尺寸、文件大小等元数据

依赖: pypdf
"""
import json, os, sys
from pypdf import PdfReader


def extract_images(pdf_path, output_dir='outputs/extracted'):
    """
    从 PDF 文件中提取所有嵌入的光栅图像。

    工作原理：
      遍历 PDF 的每一页 → 访问 /Resources → /XObject 字典 →
      筛选 /Subtype 为 /Image 的对象 → 根据 /Filter 确定文件扩展名 →
      调用 get_data() 获取原始字节 → 写入文件。

    参数:
      pdf_path: PDF 文件路径
      output_dir: 输出目录
    返回:
      成功提取的图片数量
    """
    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    manifest = []       # 图片元数据列表
    extracted = 0        # 计数器

    print(f"Scanning {total_pages} pages...")

    for page_num, page in enumerate(reader.pages, 1):
        # ── 获取页面的资源字典 ──
        resources = None
        try:
            resources = page.get('/Resources')
        except Exception:
            continue
        if resources is None:
            continue

        # ── 获取资源中的 XObject（外部对象，如图片）──
        xobjects = None
        try:
            xobjects = resources.get('/XObject')
        except Exception:
            continue
        if xobjects is None:
            continue

        img_idx = 0
        for obj_name in xobjects:
            xobj = xobjects[obj_name]
            if xobj is None:
                continue

            # 仅处理图像类型（非 Form 或其他 XObject 子类型）
            subtype = xobj.get('/Subtype', '')
            if subtype != '/Image':
                continue

            img_idx += 1
            width = xobj.get('/Width', '?')
            height = xobj.get('/Height', '?')
            filt = xobj.get('/Filter', '?')
            bpc = xobj.get('/BitsPerComponent', '?')

            # ── 根据压缩过滤器确定文件扩展名 ──
            # DCTDecode = JPEG 压缩（最常见）
            if isinstance(filt, list) and '/DCTDecode' in [str(f) for f in filt]:
                ext = 'jpg'
            elif '/DCTDecode' in str(filt):
                ext = 'jpg'
            elif '/JPXDecode' in str(filt):
                ext = 'jp2'                              # JPEG 2000
            else:
                ext = 'png'                              # 未压缩或其他压缩 → PNG

            filename = f'page_{page_num:02d}_img_{img_idx:02d}.{ext}'
            filepath = os.path.join(output_dir, filename)

            try:
                data = xobj.get_data()                   # 获取原始图像字节
                with open(filepath, 'wb') as f:
                    f.write(data)
                size_kb = len(data) / 1024
                print(f"  [page {page_num}] {filename}  {width}x{height}  {size_kb:.0f} KB")
                manifest.append({
                    'page': page_num,
                    'file': filename,
                    'width': width,
                    'height': height,
                    'size_kb': round(size_kb, 1),
                    'filter': str(filt),
                    'bpc': bpc,
                })
                extracted += 1
            except Exception as e:
                print(f"  [page {page_num}] {filename} ERROR: {e}")

    # ── 写入元数据清单 ──
    manifest_path = os.path.join(output_dir, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nExtracted {extracted} images -> {output_dir}")
    print(f"Manifest -> {manifest_path}")

    # 按页汇总
    from collections import Counter
    page_counts = Counter(m['page'] for m in manifest)
    print("\nImages per page:")
    for pg in sorted(page_counts):
        print(f"  Page {pg}: {page_counts[pg]} image(s)")

    return extracted


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <paper.pdf> [output_dir]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else 'outputs/extracted'
    extract_images(pdf_path, out_dir)
