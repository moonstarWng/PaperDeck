# PaperDeck 开发规范

## 分支策略

```
main          ← 稳定发布分支，只接受 PR 合入，不直接 push
├── dev        ← 日常开发集成分支
├── feat/*     ← 新功能分支
├── fix/*      ← Bug 修复分支
└── release/*  ← 发布准备分支
```

| 分支类型 | 命名示例 | 从哪分出 | 合入哪 |
|---------|---------|---------|--------|
| 新功能 | `feat/image-crop` | `main` | `main` |
| Bug 修复 | `fix/build-path-error` | `main` | `main` |
| 紧急热修 | `fix/hotfix-xxx` | `main` | `main` |

**规则**：
- **禁止**直接 push 到 `main`
- 一个分支只做一件事
- 分支名用英文小写 + 连字符

## Commit 规范

```
<type>: <简短描述>

<详细说明（可选）>
```

| type | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 代码重构（不改变功能） |
| `docs` | 文档修改 |
| `style` | 格式/注释（不影响逻辑） |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖 |

**示例**：
```
feat: 添加大纲树形编辑器

- OutlineEditor 组件支持展开折叠、内联编辑
- 每行独立文本框 + 青色圆点标记
- 图片选择器弹出 figs/ 目录
```

## 提交流程

```
1. git checkout -b feat/xxx  （从 main 拉分支）
2. 开发 + 本地测试
3. python test_pipeline.py   （自测必须全绿）
4. git add + git commit
5. git push origin feat/xxx
6. 通知我 review
7. review 通过 → 我让你合 → git checkout main && git merge feat/xxx && git push
```

## 测试要求

**每次提交前必须跑**：
```bash
python test_pipeline.py
# 预期输出: 7/7 通过, 0 失败
```

**以下情况需额外手动验证**：
- 修改 GUI 代码 → 启动 GUI 点一遍完整流程
- 修改 ppt_builder → 用 demo 数据生成 PPT 并打开检查
- 修改 classify() → 用 demo/template.pptx 验证分类正确

## 版本号

```
v<主版本>.<次版本>.<修订号>
```

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 重大架构改动/不兼容 | 主版本 +1 | v1.0 → v2.0 |
| 新功能/模块 | 次版本 +1 | v1.0 → v1.1 |
| Bug 修复/小优化 | 修订号 +1 | v1.0 → v1.0.1 |

当前版本: **v1.0**

## 发布检查清单

每次打 release 前确认：

- [ ] `test_pipeline.py` 全绿
- [ ] GUI 完整流程跑通（配置→读论文→生成大纲→编辑→构建→打开PPT）
- [ ] `build_portable.py` 构建成功，解压后 `启动.bat` 能启动
- [ ] `README.md` 版本号更新
- [ ] `git tag vX.X.X` 打标签
- [ ] CHANGELOG 记录变更
