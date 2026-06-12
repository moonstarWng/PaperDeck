# PaperDeck — 论文文献汇报 PPT 自动生成

从论文 PDF 一键生成学术文献汇报 PPT。支持 Claude Code Agent 调用和命令行独立使用。

## 5 步流水线

```
论文 PDF ──→  提取图片  ──→  手动截图  ──→  生成大纲  ──→  生成 PPT
   │        (Python)     (你来做)     (AI 辅助)     (Python)
   │
   └──→  参考 PPTX  ──→  提取模板 (make-template)
```

| Step | 谁做 | 输入 | 输出 |
|------|------|------|------|
| 0. 生成模板 | Python | 参考汇报 PPTX | 设计骨架模板 (7-10 页) |
| 1. 提取图片 | Python | 论文 PDF | `outputs/extracted/` 图片 |
| 2. 分割子图 | **你** | 提取的整图 | `figs/` 按子图命名 |
| 3. 生成大纲 | AI | 论文全文 | 结构化大纲 (待审批) |
| 4. 生成 PPT | Python | 模板 + JSON + 图片 | 最终 PPTX |

## 快速开始

### 安装依赖

```bash
pip install python-pptx pypdf lxml Pillow
```

### 作为 Claude Code Agent

```bash
# 复制 Skill 到 Claude Code 技能目录
cp -r . ~/.claude/skills/paper2ppt/
```

然后在 Claude Code 中输入 `/paper2ppt`，按 Agent 引导操作。

### 命令行独立使用

```bash
# Step 0: 从参考 PPTX 提取设计模板
python scripts/make_template.py 参考.pptx 模板.pptx

# Step 1: 从论文 PDF 提取图片
python scripts/extract_images.py 论文.pdf outputs/extracted/

# Step 2: 手动截图子图，保存到 figs/ 目录
#   命名规则: {图号}{子图字母}.jpg  如 1A.jpg, 1DEF.jpg, 5ABCD.jpg

# Step 3: 创建 slide-content.json（参考 templates/example-slide-content.json）

# Step 4: 验证并生成
python scripts/validate_outline.py slide-content.json
python scripts/ppt_builder.py slide-content.json
```

## 文件结构

```
paper2ppt/
├── SKILL.md                          # Claude Code Agent 定义
├── prompt-base.txt                   # PPT 格式规范（用户原始 prompt）
├── agent-prompt.txt                  # 补充规则（踩坑经验）
├── scripts/
│   ├── make_template.py              # 模板提取
│   ├── extract_images.py             # PDF 图片提取
│   ├── ppt_builder.py                # JSON → PPTX 构建器
│   ├── ppt_layout.py                 # 布局工具库
│   ├── ppt_slides.py                 # 特殊幻灯片构建器
│   └── validate_outline.py           # JSON 验证
└── templates/
    ├── slide-content-schema.json     # JSON Schema
    └── example-slide-content.json    # 完整示例
```

## slide-content.json 格式

```jsonc
{
  "meta": {
    "template_path": "./template/template.pptx",
    "output_path": "./output.pptx",
    "figs_dir": "./figs",
    "template_slide_indices": { "cover": 0, "toc": 1, "sections": [2,3,5,6], "thanks": 7 }
  },
  "cover": {
    "title_en": "Paper Title\nLine 2\nLine 3",
    "presenter": "xxx",
    "date": "202X年X月"
  },
  "slides": [
    { "type": "keep", "ref": "cover" },
    { "type": "keep", "ref": "toc" },
    { "type": "keep", "ref": "section", "index": 0 },
    { "type": "author", "journal": {...}, "institutions": [...], "authors": "..." },
    { "type": "keep", "ref": "section", "index": 1 },
    { "type": "background", "cards": [...], "hypothesis": "...", "experiment": "..." },
    { "type": "keep", "ref": "section", "index": 2 },
    { "type": "result", "title": "3.1 ...", "body": ["要点1", "要点2", "要点3"], "images": [...] },
    // ... more result slides ...
    { "type": "keep", "ref": "section", "index": 3 },
    { "type": "discussion1", "title": "...", "items": [...] },
    { "type": "discussion2", "title": "...", "left_items": [...], "right_items": [...] },
    { "type": "keep", "ref": "thanks" }
  ]
}
```

完整 Schema: `templates/slide-content-schema.json`
完整示例: `templates/example-slide-content.json`

## 幻灯片类型

| type | 说明 |
|------|------|
| `keep` | 保留模板幻灯片 (cover/toc/section/thanks) |
| `author` | 作者团队页 — 卡片布局 |
| `background` | 课题背景页 — 三色卡片 |
| `result` | 结果页 — 左图右文，每行独立文本框 |
| `summary` | 结果总结页 — 流程箭头图 |
| `discussion1` | 讨论页 — 编号圆形列表 |
| `discussion2` | 双栏页 — 局限性 vs 临床意义 |

## PPT 规范

- 正文 16pt Times New Roman，全中文
- 图片宽度统一 5.5 英寸，左侧放置，保持原始宽高比
- 每页 3 行要点，每行独立文本框带青色圆点
- 模板封面/目录/章节页/致谢页保留原样，仅修改文字
- 详见 `prompt-base.txt` 和 `agent-prompt.txt`

## License

MIT
