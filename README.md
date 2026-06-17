# PaperDeck — 论文文献汇报 PPT 自动生成

> 论文 PDF → 双击启动 → 一键生成 PPT。**不需要写代码。**

## 快速上手（3 分钟）

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
| 📊 模板 PPTX | 实验室/课题组的汇报模板 |

> 图片目录为可选。若提供，LLM 会自动分配图片到结果页。

### 3. 双击 `启动.bat` → 一键生成

1. 选择论文 PDF + 模板 PPTX
2. 配置 AI API（右下角「AI配置」）
3. 点击绿色按钮「**一键生成 PPT**」
4. 等待 30-90 秒（LLM 生成大纲 + 构建）
5. 点击「点击保存 PPT」→ 选择保存位置 → 自动打开

### 4. 精细控制（可选）

勾选「☑ 精细控制」后，可逐页调整：

- **第 2 页（大纲生成）**：读取论文 → 编辑章节配置 → 生成大纲 → 检查修改内容 → 手动分配图片
- **第 3 页（构建）**：验证 JSON → 开始构建 → 打开输出文件

### 5. 模板提取

支持三种模式（默认 PPT Master）：

| 模式 | 速度 | 说明 |
|------|------|------|
| PPT Master（推荐） | 10-30s | OOXML 直接分析，主题色/字体准确，无需 API |
| 规则 | 瞬间 | 纯规则匹配，适合标准模板 |
| LLM | 10-30s | 需 API，自适应不同模板 |

### 截图命名规则（可选）

```
figs/
├── 1A.jpg          ← 图1的A子图
├── 1DEF.jpg        ← 图1的D+E+F合并
├── 2BC.jpg         ← 图2的B+C合并
└── 5ABCD.jpg       ← 图5的A+B+C+D合并
```

---

## 需要 LLM API

PaperDeck 本身不包含大模型。你需要一个 OpenAI 兼容的 API：

| 服务 | 价格 | 获取方式 |
|------|------|---------|
| DeepSeek | ¥1/百万token | https://platform.deepseek.com |
| SiliconFlow | 有免费额度 | https://siliconflow.cn |
| 火山方舟 | 有免费模型 | https://console.volcengine.com/ark |

---

## 更新版本号

修改项目根目录 `VERSION` 文件即可。构建便携包时会自动读取。

## 构建便携包
```bash
python build_portable.py
# → dist/PaperDeck_vX.X_portable.zip
```

## 运行自测
```bash
python -m pytest test/ -q
```

## 排故

点击顶部「工具」→「保存排故包」，自动打包日志和 process/ 中的 JSON 文件。

## 项目结构
```
scripts/         核心逻辑（模板提取、PPT构建、元数据提取）
  vendor/         内置 ppt-master（OOXML 分析）
gui/              GUI 代码（customtkinter）
demo/
  demo1/          AST-LLM 示例
  demo2/          Attention Is All You Need 示例
test/             测试用例
```

## 开发规范
见 [DEVELOPMENT.md](DEVELOPMENT.md)

## License
MIT
