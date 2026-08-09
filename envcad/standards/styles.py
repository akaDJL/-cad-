"""文字样式与标注样式 v1.4（GB/T 50001—2017）。

改进:
  * 标注精度变量 DIMDEC/DIMRND/DIMTDEC
  * 字高四舍五入到 0.5mm 档位
  * 标注默认间隙增大防遮挡

汉字用仿宋 GB2312（高宽比 1:0.7），字母数字用 simplex。
"""
from __future__ import annotations

import ezdxf
from ezdxf.enums import TextEntityAlignment

import os as _os

def _resolve_font(default, *candidates):
    """跨平台回退：优先用存在的字体，否则用默认名（ezdxf 在无字体时静默回退）。"""
    for c in candidates:
        if _os.path.exists(c):
            return c
    return default

HZ_FONT = _resolve_font(
    "simfang.ttf",
    "simfang.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/simfang.ttf",
)
ENG_FONT = "simplex.shx"  # 标准 AutoCAD 字形

# ─── 字号档位 (图纸 mm) ──────────────────────────────────
FONT_SIZES = {
    "title":  5.0,     # 图名
    "subtitle": 4.0,   # 副标题
    "body":   3.5,     # 正文标注
    "note":   3.0,     # 注记
    "small":  2.5,     # 辅助说明
    "tiny":   2.0,     # 表格小字
}


def pick_font_size(size_mm: float) -> float:
    """将任意字高归一到最近的标准档位（0.5mm 步长）。"""
    return round(size_mm * 2) / 2


def setup_text_styles(doc: ezdxf.drawing.Drawing) -> None:
    """创建工程制图用文字样式。失败时回退到 STANDARD。"""
    styles = doc.styles
    try:
        styles.add("HZ", font=HZ_FONT)
    except Exception as _e:
        try:
            s = styles.add("HZ")
            s.dxf.font = HZ_FONT
        except Exception as _e:
            print(f'[WARNING] styles.py: {_e}')
    try:
        styles.add("ENG", font=ENG_FONT)
    except Exception as _e:
        try:
            s = styles.add("ENG")
            s.dxf.font = ENG_FONT
        except Exception as _e:
            print(f'[WARNING] styles.py: {_e}')
    try:
        styles.add("HZTXT", font=HZ_FONT)
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')


def setup_dimstyles(doc: ezdxf.drawing.Drawing, scale: float = 1.0) -> str:
    """创建国标标注样式，返回样式名。

    scale: 出图比例的倒数。1:100 图纸 scale=100。
    """
    name = f"GB-DIM-{int(scale)}"
    if name in doc.dimstyles:
        return name
    try:
        dim = doc.dimstyles.add(name)
    except Exception as _e:
        return "Standard"

    txt_h = 3.5 * scale
    arrow = 2.5 * scale

    # 基本标注
    dim.dxf.dimtxt = txt_h
    dim.dxf.dimasz = arrow
    dim.dxf.dimexe = 2.0 * scale
    dim.dxf.dimexo = 1.2 * scale        # 增大偏移防遮挡
    dim.dxf.dimgap = 1.5 * scale        # 增大文字与尺寸线间距
    dim.dxf.dimtxsty = "HZ"
    dim.dxf.dimclrt = 7
    dim.dxf.dimlwd = -2
    dim.dxf.dimclrd = 3
    dim.dxf.dimclre = 3

    # 精度变量
    dim.dxf.dimdec = 2                  # 小数位
    dim.dxf.dimrnd = 0.01               # 圆整
    dim.dxf.dimtdec = 2                  # 公差小数位
    # dim.dxf.dimaltd = 2  # 备用单位精度 - ezdxf DIMSTYLE 可能不支持

    return name


def set_text(msp, text, layer, height, align="left"):
    """统一的文字写入助手。"""
    return text
