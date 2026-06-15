"""
test/test_ppt_layout.py — color functions (tint, shade, luminance, contrast_text) / palette
"""
import pytest
from pptx.dml.color import RGBColor


class TestColorFunctions:
    def test_tint_lightens(self):
        from ppt_layout import _tint
        red = RGBColor(0xE6, 0x39, 0x46)
        light = _tint(red, 0.12)
        # 浅变体应更接近白色（RGB 值更高）
        assert light[0] > red[0]
        assert light[1] > red[1]
        assert light[2] > red[2]

    def test_shade_darkens(self):
        from ppt_layout import _shade
        red = RGBColor(0xE6, 0x39, 0x46)
        dark = _shade(red, 0.7)
        assert dark[0] < red[0]
        assert dark[1] < red[1]
        assert dark[2] < red[2]

    def test_luminance_black_white(self):
        from ppt_layout import _luminance
        assert _luminance(RGBColor(0, 0, 0)) < 0.01
        assert _luminance(RGBColor(0xFF, 0xFF, 0xFF)) > 0.99

    def test_contrast_text_dark_bg_returns_white(self):
        from ppt_layout import contrast_text, WHITE
        dark = RGBColor(0x1A, 0x1A, 0x1A)
        result = contrast_text(dark)
        assert result == WHITE

    def test_contrast_text_light_bg_returns_dark(self):
        from ppt_layout import contrast_text, DARK
        light = RGBColor(0xFF, 0xFF, 0xFF)
        result = contrast_text(light)
        assert result == DARK


class TestPalette:
    def test_derive_palette_sets_colors(self):
        from ppt_layout import derive_palette, PALETTE_PRIMARY, PALETTE_LIGHT, PALETTE_DARK, PALETTE_WARM, PALETTE_ACCENT2
        import ppt_layout
        red = RGBColor(0xE6, 0x39, 0x46)
        dark = RGBColor(0x1A, 0x1A, 0x1A)
        derive_palette(red, dark)
        # 重新从模块读
        p = ppt_layout.PALETTE_PRIMARY
        l = ppt_layout.PALETTE_LIGHT
        d = ppt_layout.PALETTE_DARK
        assert p == red
        assert l[0] > red[0]  # 浅变体更亮
        assert d == dark
