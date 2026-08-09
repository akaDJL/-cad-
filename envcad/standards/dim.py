"""尺寸公差标注 v1.1（GB/T 1800.2—2020）。

【注意：dim ≠ dimensions】本模块只做"公差"（Tolerance），不管"标注"（Annotation）。
如需坐标标注/角度标注/链式基线标注/半径直径引出，请用 `standards.dimensions`。

基于 ezdxf DimStyle override 和 MText 堆叠，实现:
  * 对称公差（±偏差）
  * 极限偏差（上标/下标堆叠）
  * 配合公差（H7/g6、H8/f7 等），全直径段查表（≤3 ~ 500mm）
  * 显式偏差参数（Agent 搜索后传入，绕过查表）

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import Optional, Tuple, List, Union

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  GB/T 1800.2—2020 公差数据（全直径段）
# ══════════════════════════════════════════════════════════

# 基本尺寸分段 (mm): [low, high)
_DIAMETER_RANGES: List[Tuple[float, float]] = [
    (0,  3),  (3,  6),  (6,  10), (10, 18), (18, 30),
    (30, 50), (50, 80), (80, 120),(120,180),(180,250),
    (250,315),(315,400),(400,500),
]

# IT 标准公差数值 (μm)，索引对应上述直径段
_IT: dict = {
    5:  [4,    5,    6,    8,    9,    11,   13,   15,   18,   20,   23,   25,   27],
    6:  [6,    8,    9,    11,   13,   16,   19,   22,   25,   29,   32,   36,   40],
    7:  [10,   12,   15,   18,   21,   25,   30,   35,   40,   46,   52,   57,   63],
    8:  [14,   18,   22,   27,   33,   39,   46,   54,   63,   72,   81,   89,   97],
    9:  [25,   30,   36,   43,   52,   62,   74,   87,   100,  115,  130,  140,  155],
    10: [40,   48,   58,   70,   84,   100,  120,  140,  160,  185,  210,  230,  250],
}

# 轴基本偏差 (μm)；负值为上偏差(es)，正值为下偏差(ei)
# g/h 类：负 es；k~p 类：正 ei
_SHAFT_DEV: dict = {
    "g": [-2,  -4,  -5,  -6,  -7,  -9,  -10, -12, -14, -15, -17, -18, -20],
    "h": [ 0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
    "k": [ 0,   1,   1,   1,   2,   2,   2,   3,   3,   4,   4,   4,   5],
    "m": [ 2,   4,   6,   7,   8,   9,   11,  13,  15,  17,  20,  21,  23],
    "n": [ 4,   8,  10,  12,  15,  17,  20,  23,  27,  31,  34,  37,  40],
    "p": [ 6,  12,  15,  18,  22,  26,  32,  37,  43,  50,  56,  62,  68],
    "f": [-6, -10, -13, -16, -20, -25, -30, -36, -43, -50, -56, -62, -68],
    "e": [-14,-20, -25, -32, -40, -50, -60, -72, -85,-100,-110,-125,-135],
    "d": [-20,-30, -40, -50, -65, -80,-100,-120,-145,-170,-190,-210,-230],
}


def _find_range_idx(diameter: float) -> int:
    """根据基本直径找到尺寸段索引。"""
    for i, (lo, hi) in enumerate(_DIAMETER_RANGES):
        if lo < diameter <= hi:
            return i
    # fallback: 取最接近的段
    if diameter <= 3:
        return 0
    return len(_DIAMETER_RANGES) - 1


def _shaft_tolerance(letter: str, it_grade: int, idx: int) -> Tuple[float, float]:
    """计算轴的上下偏差 (es, ei)，单位 μm。"""
    it = _IT.get(it_grade, _IT[7])[idx]

    if letter == "j" and it_grade == 6:  # js6 对称
        half = it / 2
        return (+half, -half)
    if letter == "j" and it_grade == 7:
        half = it / 2
        return (+half, -half)

    dev = _SHAFT_DEV.get(letter)
    if dev is None:
        return (0.0, -float(it))

    d = dev[idx]

    if letter in ("g", "h", "f", "e", "d"):
        # 负向偏差：es = d，ei = d - IT
        es = float(d)
        ei = es - it
    else:
        # 正向偏差（k, m, n, p）：ei = d，es = d + IT
        ei = float(d)
        es = ei + it

    return (es, ei)


def lookup_fit(basic_diameter: float, fit_code: str
               ) -> Tuple[float, float, float, float]:
    """根据基本直径和配合代号查 GB/T 1800.2 公差。

    参数:
        basic_diameter: 基本尺寸 (mm)，如 20, 50
        fit_code: 配合代号，如 "H7/g6", "H8/f7"

    返回:
        (hole_es_μm, hole_ei_μm, shaft_es_μm, shaft_ei_μm)
        偏差单位均为 μm（微米）

    示例:
        lookup_fit(20, "H7/g6") → (21000, 0, -7000, -20000)
        即孔 +21μm/0，轴 -7μm/-20μm
    """
    parts = fit_code.split("/")
    hole_code = parts[0].strip()
    shaft_code = parts[1].strip() if len(parts) > 1 else ""

    idx = _find_range_idx(basic_diameter)

    # ── 孔 ──
    hole_letter = hole_code[0].upper()
    hole_it = int(hole_code[1:])

    if hole_letter == "H":
        hole_es = float(_IT.get(hole_it, _IT[7])[idx])
        hole_ei = 0.0
    else:
        hole_es = 0.0
        hole_ei = 0.0

    # ── 轴 ──
    shaft_letter = shaft_code[0].lower()
    shaft_it = int(shaft_code[1:])
    shaft_es, shaft_ei = _shaft_tolerance(shaft_letter, shaft_it, idx)

    return (hole_es, hole_ei, shaft_es, shaft_ei)


def _fmt_dev(um_value: float) -> str:
    """将 μm 偏差值格式化为 mm 字符串（带符号）。"""
    mm = um_value / 1000.0
    return f"{mm:+.3f}"


# ─── 内部辅助 ───────────────────────────────────────────

# ══════════════════════════════════════════════════════════
#  DIM 标注函数
# ══════════════════════════════════════════════════════════

def add_dim_style_tolerance(doc, dimstyle_name: str,
                             upper: str, lower: str,
                             height_factor: float = 0.7) -> str:
    """为已有 DimStyle 添加公差后缀（dimstyle override）。"""
    if dimstyle_name not in doc.dimstyles:
        return dimstyle_name

    dim = doc.dimstyles.get(dimstyle_name)
    dim.dxf.dimtol = 1
    dim.dxf.dimtp = abs(float(upper)) if upper else 0
    dim.dxf.dimtm = abs(float(lower)) if lower else 0
    dim.dxf.dimtfac = height_factor

    return dimstyle_name


def draw_dimension(msp, p1: Tuple[float, float], p2: Tuple[float, float],
                   offset: float = 10.0, scale: float = 100.0,
                   dimstyle: str = "Standard",
                   text: str = "", upper: str = "", lower: str = "",
                   sym: bool = False,
                   layer: str = "尺寸标注",
                   tracker=None):
    """绘制带公差的线性标注。

    参数:
        p1, p2: 标注起止点
        offset: 尺寸线偏移距离（图纸 mm）
        scale: 出图比例倒数
        text: 自定义标注文字（空则自动计算距离）
        upper: 上偏差（如 "+0.018"）
        lower: 下偏差（如 "0"）
        sym: True = 对称公差（用 ± 符号）
    """
    s = scale
    x1, y1 = _r(*p1)
    x2, y2 = _r(*p2)

    off = offset * s

    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > abs(dy):
        p3 = (x1, y1 - off)
        p4 = (x2, y2 - off)
    else:
        p3 = (x1 - off, y1)
        p4 = (x2 - off, y2)

    msp.add_line(p3, p4, dxfattribs={"layer": layer})
    msp.add_line(p1, p3, dxfattribs={"layer": layer})
    msp.add_line(p2, p4, dxfattribs={"layer": layer})

    mx = (p3[0] + p4[0]) / 2
    my = (p3[1] + p4[1]) / 2
    txt_h = 3.0 * s

    dist_mm = math.hypot(x2 - x1, y2 - y1)
    base_text = text if text else f"{dist_mm:.1f}"

    if sym and upper:
        tol_text = f"{base_text}±{upper.lstrip('+')}"
        t = msp.add_text(tol_text, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((mx, my + 1.5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    elif upper or lower:
        upper_clean = upper.lstrip("+") or "0"
        lower_clean = lower.lstrip("+") or "0"

        tol_str = f"{base_text}\\S{upper_clean}^{lower_clean};"
        t = msp.add_mtext(tol_str, dxfattribs={
            "layer": "文字", "style": "ENG", "char_height": txt_h,
        })
        t.set_location(insert=(mx, my + 1.5 * s),
                       attachment_point=5)
        t.dxf.width = 15 * s
    else:
        t = msp.add_text(base_text, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((mx, my + 1.5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker is not None:
        tracker.register(mx - 6 * s, my - 4 * s,
                         mx + 6 * s, my + 6 * s, margin=30)

    return (mx, my)


# ══════════════════════════════════════════════════════════
#  配合公差标注（支持查表 + 显式传入）
# ══════════════════════════════════════════════════════════

def draw_fit_annotation(msp, point, base_size: str, fit_code: str,
                         scale: float = 100.0,
                         leader_dir: Tuple[float, float] = (1, 1),
                         layer: str = "尺寸标注",
                         # 显式偏差 (mm)，Agent 搜索后传入，绕过查表
                         hole_es: Optional[float] = None,
                         hole_ei: Optional[float] = None,
                         shaft_es: Optional[float] = None,
                         shaft_ei: Optional[float] = None,
                         basic_diameter: Optional[float] = None,
                         tracker=None):
    """绘制配合公差引出标注。

    参数:
        point: 标注点
        base_size: 基本尺寸文本（如 "φ20"）
        fit_code: 配合代号（如 "H7/g6", "H8/f7"）

    ── 查表模式（默认）──
        自动从 base_size 解析直径，查 GB/T 1800.2 表。
        覆盖 ≤3 ~ 500mm 全直径段。

    ── 显式模式（Agent 搜索后使用）──
        传入 hole_es/hole_ei/shaft_es/shaft_ei（单位 mm），
        将完全绕过查表。
        示例: hole_es=0.021, hole_ei=0, shaft_es=-0.007, shaft_ei=-0.020

    basic_diameter: 基本直径 mm（查表用；默认从 base_size 解析）
    """
    s = scale
    tx, ty = _r(*point)

    parts = fit_code.split("/")
    hole = parts[0] if len(parts) > 0 else ""
    shaft = parts[1] if len(parts) > 1 else ""

    # ── 确定偏差值 ──
    if all(v is not None for v in [hole_es, hole_ei, shaft_es, shaft_ei]):
        # 显式模式：Agent 搜索后传入，直接使用
        hes, hei = hole_es, hole_ei       # type: ignore
        ses, sei = shaft_es, shaft_ei     # type: ignore
    else:
        # 查表模式
        if basic_diameter is None:
            # 尝试从 base_size 中提取直径
            import re
            nums = re.findall(r'\d+\.?\d*', base_size)
            basic_diameter = float(nums[0]) if nums else 10.0

        h_es_um, h_ei_um, s_es_um, s_ei_um = lookup_fit(
            basic_diameter, fit_code)
        hes = h_es_um / 1000.0
        hei = h_ei_um / 1000.0
        ses = s_es_um / 1000.0
        sei = s_ei_um / 1000.0

    # ── 指引线 ──
    dx, dy = leader_dir
    L = 12 * s
    bx = tx + dx * L
    by = ty + dy * L
    msp.add_line((tx, ty), (bx, by), dxfattribs={"layer": layer})

    h_len = 8 * s
    hx = bx + (h_len if dx >= 0 else -h_len)
    msp.add_line((bx, by), (hx, by), dxfattribs={"layer": layer})

    # ── 配合标注文字 ──
    txt_h = 2.8 * s
    fit_text = f"{base_size}{fit_code}"
    txt_dir = 1 if dx >= 0 else -1
    txt_x = hx + txt_dir * 2 * s
    txt_y = by + 1.5 * s

    t = msp.add_text(fit_text, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    align = TextEntityAlignment.LEFT if dx >= 0 else TextEntityAlignment.RIGHT
    t.set_placement((txt_x, txt_y), align=align)

    # ── 详细公差值 ──
    detail_y = by - 0.5 * s
    detail_text = (f"孔 ES{_fmt_dev(hes)} EI{_fmt_dev(hei)}  "
                   f"轴 es{_fmt_dev(ses)} ei{_fmt_dev(sei)}")
    t = msp.add_text(detail_text, dxfattribs={
        "layer": "文字", "height": 2.0 * s, "style": "ENG",
    })
    t.set_placement((txt_x, detail_y), align=align)

    if tracker is not None:
        tracker.register(tx - 2 * s, by - 6 * s,
                         txt_x + 15 * s, txt_y + 6 * s, margin=30)

    return (txt_x, txt_y)
