# PaperDeck — 论文文献汇报 PPT 自动生成

> 论文 PDF → 双击启动 → 编辑大纲 → 一键生成 PPT。**不需要写代码。**

## 快速上手（5 分钟）

### 1. 下载 & 解压

从 [Releases](https://github.com/moonstarWng/PaperDeck/releases) 下载 `PaperDeck_vX.X_portable.zip`，解压到任意目录。

```
PaperDeck/
├── 启动.bat          ← 双击启动
├── python/            ← 内置 Python（不需要你装）
└── ...
```

### 2. 准备材料

| 你需要准备 | 说明 |
|-----------|------|
| 📄 论文 PDF | 要汇报的论文 |
| 📊 模板 PPTX | 实验室/课题组的汇报模板（7-8 页骨架即可） |
| 🖼️ 截图文件夹 | 论文图片的截图，命名规则见下方 |

### 3. 双击 `启动.bat`

启动后看到三个标签页：

```
┌──────────────────────────────────────────┐
│  [配置]    [大纲生成]    [构建]          │
└──────────────────────────────────────────┘
```

### 4. 配置页 — 填入信息

1. **论文 PDF** → 点「浏览」选择论文文件
2. **模板 PPTX** → 点「浏览」选择模板 → 点「检测」
   - 显示"✓ 已是模板骨架"→ 直接使用
   - 显示"⚠ 检测到完整PPTX"→ 会自动提取模板骨架
3. **图片目录** → 选择你截图好的 `figs/` 文件夹
4. **LLM API** → 填入你的 API 地址、Key、模型名 → 点「测试连接」
5. 点「下一步: 生成大纲 →」

### 5. 大纲生成页 — AI 帮你写

1. 点「读取论文」→ 自动读取全文，提取标题/期刊/作者
2. 点「生成大纲」→ AI 生成完整大纲，自动填入树形编辑器
3. **展开每个结果页**，检查修改：
   - 标题对不对
   - 3 个要点是否准确（可直接编辑）
   - 配图是否匹配（点配图按钮选择 `figs/` 中的文件）
4. 确认无误 → 点「构建 PPT →」

### 6. 构建页 — 一键出稿

点「▶ 开始构建」→ 等待几秒 → 点「打开文件夹」→ 找到生成的 PPTX。

### 截图命名规则

```
figs/
├── 1A.jpg          ← 图1的A子图
├── 1DEF.jpg        ← 图1的D+E+F合并
├── 2BC.jpg         ← 图2的B+C合并
├── 3A.jpg          ← ...
└── 5ABCD.jpg       ← 图5的A+B+C+D合并
```

格式：`{图号}{子图字母}.jpg`，子图可单个可合并。

---

## 需要 LLM API

PaperDeck 本身不包含大模型。你需要一个 OpenAI 兼容的 API（任选其一）：

| 服务 | 价格 | 获取方式 |
|------|------|---------|
| DeepSeek | ¥1/百万token | https://platform.deepseek.com |
| SiliconFlow | 有免费额度 | https://siliconflow.cn |
| 火山方舟 | 有免费模型 | https://console.volcengine.com/ark |

---

## 开发相关

### 运行自测
```bash
python test_pipeline.py
# 预期: 7/7 通过
```

### 构建便携包
```bash
python build_portable.py
# → dist/PaperDeck_vX.X_portable.zip
```

### 项目结构
```
scripts/     CLI 脚本 (make_template, extract_images, ppt_builder, ...)
gui/         GUI 代码 (customtkinter)
demo/
  demo1/      AST-LLM 示例（神经网络稀疏训练）
  demo2/      Attention Is All You Need 示例（Swiss 模板）
templates/   JSON Schema + 参考示例
```

### 开发规范
见 [DEVELOPMENT.md](DEVELOPMENT.md)

## License
MIT
