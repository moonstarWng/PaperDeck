# paper2ppt — 文献汇报PPT自动生成 Agent

## 触发条件

当用户提到以下任一关键词时调用本 Skill：
- `/paper2ppt`
- "文献汇报PPT"、"文献汇报"、"组会PPT"
- "从论文生成PPT"、"paper to ppt"
- "帮我做文献汇报"

## 快速开始

```bash
# 使用内置 Demo 体验完整流水线
bash quickstart.sh --demo

# 使用自己的论文
bash quickstart.sh 论文.pdf 模板.pptx
```

## 整体流程

本 Agent 执行 5 步流水线，在关键步骤暂停等待用户确认：

```
Step 0 ──→ Step 1 ──→ Step 2 ──→ Step 3 ──→ Step 4
生成模板    提取图片    分割子图    生成大纲    生成PPT
(Python)    (Python)   (你来做)   (Claude)   (Python)
```

| Step | 谁做 | 输入 | 输出 |
|------|------|------|------|
| 0. 生成模板 | Python | 参考PPTX | 设计骨架模板 (7-10页) |
| 1. 提取图片 | Python | 论文PDF | `outputs/extracted/` |
| 2. 分割子图 | **你** | 提取的整图 | `figs/` 子图截图 |
| 3. 生成大纲 | Claude | 论文全文 | 结构化大纲 (待审批) |
| 4. 生成PPT | Python | 模板+JSON+图片 | 最终PPTX |

**在开始前**，确认依赖已安装：`pip install python-pptx pypdf lxml Pillow`

## 规则文件

Agent 每次运行时必须读取并遵守以下规则文件（相对于本 Skill 目录）：
1. **`prompt-base.txt`**：原始PPT格式化规范（最高优先级）
2. **`agent-prompt.txt`**：32条从迭代中积累的补充规则和技术陷阱
3. **`lessons-learned.md`**：历史运行记录和质量改进（Agent 运行后自动追加）

## 可联合调用的第三方 Skills

本 Agent 可与以下 Skills 协同工作，增强论文分析和PPT生成能力。

### 内置 Skills（Claude Code 自带，直接可用）

| Skill | 用途 | 在本流程中的应用 |
|-------|------|-----------------|
| `pdf` | PDF 全文提取、表格解析、OCR | Step 3 提取论文全文时优先使用，比 pdfplumber 更稳定 |
| `pptx` | PPTX 读取、模板分析、视觉QA | Step 0 模板分析、Step 4 输出后视觉检查 |
| `fact-check` | 验证论文中的关键声明 | Step 3 生成大纲时交叉验证关键数据点 |
| `deep-research` | 深度研究主题背景 | Step 3 补充课题背景时检索相关文献 |
| `literature-review` | 系统性文献综述 | 可选：为汇报添加领域背景和对比文献 |

### 社区 Skills（需手动安装）

| Skill | 安装命令 | 与本 Agent 的协同 |
|-------|---------|-------------------|
| [paper-analyst](https://github.com/flyer-Li/paper-analyst) | `npx skills add flyer-Li/paper-analyst` | 反幻觉来源标注 → 提高大纲准确性；多模式论文分析 → 补充背景信息 |
| [literature-report-ppt-builder](https://github.com/fangyuanopus/literature-report-ppt-builder) | `npx skills add fangyuanopus/literature-report-ppt-builder` | 证据链驱动 → 与模板驱动互补；真实图源优先 → 提醒不生成假图 |

### 推荐协同模式

```
/paper2ppt 论文.pdf
  ├── Step 1: 提取图片
  ├── Step 2: (暂停) 手动截图
  ├── Step 3: 生成大纲
  │     ├── 调用 @pdf 提取全文
  │     ├── 调用 @fact-check 验证关键声明
  │     └── 可选: @deep-research 补充背景
  └── Step 4: 生成PPT
        └── 调用 @pptx 视觉QA检查
```

## Step 0: 生成模板 (make-template)

**输入**: 用户的完整文献汇报PPTX（参考样例）
**输出**: 仅保留设计骨架的模板PPTX (7-10页)

```bash
python scripts/make_template.py <参考PPTX路径> <输出模板路径>
```

如果用户未提供参考PPTX，询问用户是否已有现成模板。若有现成模板，跳过此步。
此脚本自动完成：删除内容图片、替换隐私信息、删除内容页、按类型去重。

## Step 1: 提取论文图片

```bash
python scripts/extract_images.py <论文PDF路径> outputs/extracted
```

完成后向用户报告提取统计。

## Step 2: 分割子图 (用户手动)

**暂停并等待用户。** 创建 `figs/README.txt`，列出所需图号。命名规则：`{图号}{子图字母}.jpg`

## Step 3: 生成大纲 (Claude)

1. 使用 `pdf` skill 提取论文全文
2. 分析结构：作者、期刊、背景、结果、讨论
3. 生成大纲（每结果页3行15-20字中文要点，勿标注图号，勿复制原文）
4. **显示大纲等待用户审批**

## Step 4: 生成PPT

1. 根据审批通过的大纲生成 `slide-content.json`
2. 验证：`python scripts/validate_outline.py slide-content.json`
3. 构建：`python scripts/ppt_builder.py slide-content.json`
4. 报告生成结果

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| PermissionError on save | 文件在 PowerPoint 中打开 | 换文件名保存 |
| 模板索引不匹配 | 不同PPTX布局不同 | 重新运行 make_template |
| 图片缺失 | figs/ 不完整 | 返回 Step 2 |
| 文本替换失败 | 模板实际文本与预期不符 | dump `<a:t>` 文本修正映射 |
| 中文乱码 | GBK编码 | 统一 UTF-8 |

## 依赖

```
python-pptx, pypdf, lxml, Pillow
```

## Demo

```bash
# 一键运行内置Demo
bash quickstart.sh --demo
```

Demo 包含：合成论文PDF + 占位图片 + 完整 slide-content.json。
