#!/usr/bin/env bash
# quickstart.sh — paper2ppt 一键快速开始
#
# 用法:
#   bash quickstart.sh                          # 交互式引导
#   bash quickstart.sh --demo                   # 使用 demo 数据运行
#   bash quickstart.sh paper.pdf template.pptx  # 指定论文和模板

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  paper2ppt — 文献汇报PPT自动生成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ── Check dependencies ──
echo -e "${YELLOW}[check] 检查依赖...${NC}"
MISSING=""
for mod in pptx pypdf lxml PIL; do
    python -c "import $mod" 2>/dev/null || MISSING="$MISSING $mod"
done
# PIL is imported as 'PIL' but the package is 'Pillow'
python -c "from PIL import Image" 2>/dev/null || MISSING="$MISSING Pillow"

if [ -n "$MISSING" ]; then
    echo -e "${RED}[error] 缺少依赖: $MISSING${NC}"
    echo -e "${YELLOW}运行: pip install python-pptx pypdf lxml Pillow${NC}"
    exit 1
fi
echo -e "${GREEN}[ ok ] 所有依赖已安装${NC}"
echo ""

# ── Determine mode ──
MODE="${1:-interactive}"

if [ "$MODE" = "--demo" ]; then
    echo -e "${BLUE}[demo] 使用内置Demo运行完整流水线${NC}"
    PAPER="demo/demo_paper.pdf"
    TEMPLATE=""
    FIGS="demo/figs"
    JSON="demo/slide-content.json"
    OUTPUT="demo/demo_output.pptx"
    SKIP_STEP2=true
elif [ "$MODE" = "interactive" ] || [ $# -eq 0 ]; then
    echo -e "${YELLOW}[step] Step 0: 准备模板${NC}"
    echo "  如果你已有参考文献汇报PPTX，输入路径（自动提取模板骨架）："
    echo "  如果已有模板PPTX，直接输入模板路径："
    echo "  按回车跳过（稍后手动提供）："
    read -r REF_PPTX
    if [ -n "$REF_PPTX" ]; then
        python scripts/make_template.py "$REF_PPTX" template/template.pptx
        TEMPLATE="template/template.pptx"
        echo -e "${GREEN}[ ok ] 模板已生成: $TEMPLATE${NC}"
    fi

    echo ""
    echo -e "${YELLOW}[step] Step 1: 提取图片${NC}"
    echo "  输入论文PDF路径："
    read -r PAPER
    if [ -n "$PAPER" ] && [ -f "$PAPER" ]; then
        python scripts/extract_images.py "$PAPER" outputs/extracted/
        echo -e "${GREEN}[ ok ] 图片已提取到 outputs/extracted/${NC}"
    fi

    echo ""
    echo -e "${YELLOW}[step] Step 2: 手动截图子图${NC}"
    echo "  请将子图截图保存到 figs/ 目录"
    echo "  命名规则: {图号}{子图字母}.jpg  例如: 1A.jpg, 2BC.jpg"
    echo "  完成后按回车继续..."
    read -r _
    FIGS="./figs"

    echo ""
    echo -e "${YELLOW}[step] Step 3: 生成大纲${NC}"
    echo "  请在 AI 辅助下生成 slide-content.json"
    echo "  参考: templates/example-slide-content.json"
    echo "  输入 JSON 文件路径："
    read -r JSON

    echo ""
    echo -e "${YELLOW}[step] Step 4: 生成PPT${NC}"
    echo "  模板路径 (回车=template/template.pptx):"
    read -r TEMPLATE
    TEMPLATE="${TEMPLATE:-template/template.pptx}"
    OUTPUT="${OUTPUT:-output.pptx}"
else
    PAPER="$1"
    TEMPLATE="${2:-template/template.pptx}"
    echo -e "${BLUE}[run] 论文: $PAPER${NC}"
    echo -e "${BLUE}[run] 模板: $TEMPLATE${NC}"
fi

# ── Step 0: Make template ──
if [ -n "$REF_PPTX" ] && [ -f "$REF_PPTX" ]; then
    echo ""
    echo -e "${YELLOW}[0/4] 生成模板...${NC}"
    python scripts/make_template.py "$REF_PPTX" "$TEMPLATE"
    echo -e "${GREEN}[ ok ] 模板: $TEMPLATE${NC}"
fi

# ── Step 1: Extract images ──
if [ "$SKIP_STEP2" != "true" ] && [ -n "$PAPER" ] && [ -f "$PAPER" ]; then
    echo ""
    echo -e "${YELLOW}[1/4] 提取图片...${NC}"
    python scripts/extract_images.py "$PAPER" outputs/extracted/
    echo -e "${GREEN}[ ok ] 图片: outputs/extracted/${NC}"
fi

# ── Step 2: Check figures ──
if [ "$SKIP_STEP2" != "true" ]; then
    echo ""
    echo -e "${YELLOW}[2/4] 检查子图截图...${NC}"
    if [ -d "$FIGS" ] && [ "$(ls -A "$FIGS" 2>/dev/null)" ]; then
        COUNT=$(ls -1 "$FIGS"/*.{jpg,png} 2>/dev/null | wc -l)
        echo -e "${GREEN}[ ok ] figs/: ${COUNT} 张图片${NC}"
    else
        echo -e "${RED}[ !! ] figs/ 为空！${NC}"
        echo -e "${YELLOW}请手动截图子图，命名规则: {图号}{子图字母}.jpg${NC}"
        echo -e "${YELLOW}如: 1A.jpg, 1DEF.jpg, 2BC.jpg${NC}"
        echo "完成后重新运行此脚本"
        exit 1
    fi
fi

# ── Step 3: Validate JSON ──
if [ -n "$JSON" ] && [ -f "$JSON" ]; then
    echo ""
    echo -e "${YELLOW}[3/4] 验证 slide-content.json...${NC}"
    python scripts/validate_outline.py "$JSON"
else
    echo -e "${YELLOW}[3/4] 跳过 — 请手动创建 slide-content.json${NC}"
    echo "  参考: templates/example-slide-content.json"
    exit 0
fi

# ── Step 4: Build PPT ──
echo ""
echo -e "${YELLOW}[4/4] 生成PPT...${NC}"
python scripts/ppt_builder.py "$JSON"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  完成！输出: $OUTPUT${NC}"
echo -e "${GREEN}========================================${NC}"
