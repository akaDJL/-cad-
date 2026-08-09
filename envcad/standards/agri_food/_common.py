"""农业食品机械模块公共基座 —— 100% 复用 envcad 已验证的国标代码。

本文件不复制 envcad 的任何绘图逻辑，只做三件事：
  1. 引导 sys.path，使 ``import envcad`` 可用（非破坏性，不修改原包）；
  2. 把 envcad 的 frame / layers / styles 封装成 ``add_a3_frame`` 一步调用；
  3. 提供符号比例换算助手 ``sym_scale_for``，让 envcad 中"图纸 mm × scale"
     约定的符号函数（hydraulic / mechanical / plumbing）能按实物 mm 尺寸复用。

绘图约定（沿用 envcad）：
  * modelspace 一律按 **实物 mm 1:1** 绘制；
  * 图框按出图比例 scale 放大（A3 = 420×297 × scale），出图 1:1 即为正确比例；
  * 图线按 GB/T 17450—1998：粗实线 0.5 / 中实线 0.35 / 细实线 0.18；
  * 汉字文字样式 "HZ" = 仿宋 GB2312（simfang.ttf），GB/T 14691—1993。
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Optional, Sequence, Tuple

# ── envcad 引导（只读引用，不修改原包） ─────────────────────
ENVCAD_ROOT = os.environ.get(
    "ENVCAD_ROOT",
    r"C:\Users\lenovo\Desktop\凹凸cad小助手（二集）v1.5",
)
if ENVCAD_ROOT not in sys.path:
    sys.path.insert(0, ENVCAD_ROOT)

from ezdxf.enums import TextEntityAlignment  # noqa: E402

from envcad.engine.dxf_base import new_drawing, save_dxf  # noqa: E402,F401
from envcad.standards.annotate import _t, draw_leader  # noqa: E402
from envcad.standards.dim import draw_dimension  # noqa: E402
from envcad.standards.frame import FrameInfo, draw_frame  # noqa: E402
from envcad.standards.notes import draw_notes_block  # noqa: E402

# ── 图层 ────────────────────────────────────────────────
# 主用图层全部取自 envcad.standards.layers.LAYER_DEFS（GB/T 17450）
L_THICK = "粗实线"       # 0.50mm 主可见轮廓
L_MED = "中实线"         # 0.35mm 次可见轮廓
L_THIN = "细实线"        # 0.18mm 辅助线、剖面、纹理
L_DIM = "细实线-尺寸"    # 0.18mm 尺寸线
L_CENTER = "点画线"      # 中心线 / 轴线
L_HIDDEN = "虚线"        # 不可见轮廓
L_TEXT = "文字"
L_TITLE = "文字-标题"

#: envcad 部分符号函数内部硬编码的图层名（plumbing / hydraulic），
#: 这些图层不在 LAYER_DEFS 中，需在新图里补建，否则 DXF 引用未定义图层。
EXTRA_LAYER_DEFS = [
    # (图层名, ACI 颜色, 线型, 线宽 1/100mm)
    ("给水管", 5, "CONTINUOUS", 50),      # plumbing.draw_plumbing_pipe
    ("中水管", 4, "CONTINUOUS", 35),      # plumbing.draw_plumbing_pipe
    ("管件", 1, "CONTINUOUS", 35),        # plumbing.draw_valve_plumbing
    ("消防", 1, "CONTINUOUS", 35),        # plumbing.draw_sprinkler
    ("元件", 2, "CONTINUOUS", 35),        # hydraulic.draw_* 默认图层
    ("中心线", 1, "CENTER", 18),          # mechanical._center_line
    ("三角标高", 3, "CONTINUOUS", 18),    # utils._tri
    ("尺寸标注", 3, "CONTINUOUS", 18),    # dim / dimensions 默认图层
]


def ensure_ext_layers(doc) -> None:
    """补建 envcad 符号函数所引用、但不在 LAYER_DEFS 中的图层。

    envcad 的 plumbing / hydraulic / mechanical 部分函数把图层名硬编码在
    函数体内（如 "给水管" "中心线"），若不预建会导致 DXF 引用未定义图层。
    本函数仅作用于当前 doc，不修改 envcad 包本身。
    """
    for name, color, ltype, lw in EXTRA_LAYER_DEFS:
        if name in doc.layers:
            continue
        try:
            layer = doc.layers.add(name)
            layer.dxf.color = color
            try:
                layer.dxf.linetype = (
                    ltype if doc.linetypes.has_entry(ltype) else "CONTINUOUS")
            except Exception as _e:
                layer.dxf.linetype = "CONTINUOUS"
            layer.dxf.lineweight = lw
        except Exception as _e:
            print(f'[WARNING] _common.py: {_e}')


# ── A3 图框（GB/T 14689—2008 幅面 + GB/T 50001—2017 标题栏） ──

def add_a3_frame(doc, scale: float, title: str,
                 drawing_no: str = "AGRI-00",
                 project: str = "农业食品机械",
                 unit: str = "envcad",
                 designer: str = "envcad",
                 date: str = "2026.07",
                 tracker=None) -> Tuple[float, float, float, float]:
    """绘制 A3 横式图框 + 标题栏，返回内框范围 (x0, y0, x1, y1)。

    直接委托 ``envcad.standards.frame.draw_frame``，不重写任何几何。

    Args:
        doc: ezdxf Drawing
        scale: 出图比例倒数（1:50 → 50）
        title: 图名
        drawing_no: 图号
    """
    info = FrameInfo(
        title=title, drawing_no=drawing_no,
        scale_str=f"1:{int(scale)}", project=project,
        unit=unit, designer=designer, date=date,
    )
    return draw_frame(doc, scale, info, tracker=tracker)


def new_agri_drawing(scale: float, title: str, drawing_no: str,
                     project: str = "农业食品机械"):
    """新建一张带 A3 图框的农机图纸。

    Returns:
        (doc, msp, dim_style, tracker, frame_box)
    """
    doc, dim_style, tracker = new_drawing(scale, return_tracker=True)
    ensure_ext_layers(doc)
    msp = doc.modelspace()
    box = add_a3_frame(doc, scale, title, drawing_no, project, tracker=tracker)
    return doc, msp, dim_style, tracker, box


# ── 符号比例换算 ────────────────────────────────────────

def sym_scale_for(target_mm: float, unit_paper_mm: float) -> float:
    """把"实物 mm 目标尺寸"换算成 envcad 符号函数所需的 scale。

    envcad 的 hydraulic / mechanical / plumbing 符号函数按
    ``图纸 mm × scale`` 出图，例如 ``hydraulic.draw_cylinder`` 缸筒长
    恒为 ``24 * scale``。若希望缸筒实物长 600mm，则应传
    ``scale = sym_scale_for(600, 24)``。

    Args:
        target_mm: 期望的实物尺寸（mm）
        unit_paper_mm: 该符号在源函数中的图纸 mm 系数
    """
    return float(target_mm) / float(unit_paper_mm)


# ── 常用绘图助手（薄封装，统一图层与文字样式） ──────────────

def rect(msp, x0: float, y0: float, x1: float, y1: float,
         layer: str = L_THICK, closed: bool = True):
    """按对角点画矩形（LWPOLYLINE）。"""
    return msp.add_lwpolyline(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        close=closed, dxfattribs={"layer": layer})


def poly(msp, pts: Sequence[Tuple[float, float]],
         layer: str = L_THICK, closed: bool = False):
    """画多段线。"""
    return msp.add_lwpolyline(list(pts), close=closed,
                              dxfattribs={"layer": layer})


def centerline(msp, p1, p2, scale: float, ext: float = 3.0,
               layer: str = L_CENTER):
    """画中心线，两端各外伸 ``ext`` 图纸 mm（GB/T 4457.4）。"""
    (x1, y1), (x2, y2) = p1, p2
    dx, dy = x2 - x1, y2 - y1
    lg = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / lg, dy / lg
    e = ext * scale
    return msp.add_line((x1 - ux * e, y1 - uy * e),
                        (x2 + ux * e, y2 + uy * e),
                        dxfattribs={"layer": layer})


def cross_center(msp, cx: float, cy: float, r: float, scale: float,
                 layer: str = L_CENTER):
    """圆的十字中心线（GB/T 4457.4）。"""
    e = 2.0 * scale
    msp.add_line((cx - r - e, cy), (cx + r + e, cy), dxfattribs={"layer": layer})
    msp.add_line((cx, cy - r - e), (cx, cy + r + e), dxfattribs={"layer": layer})


def dim_h(msp, p1, p2, scale: float, offset: float = 12.0, text: str = "",
          tracker=None):
    """水平线性标注（尺寸线在下方）——复用 envcad.standards.dim。"""
    return draw_dimension(msp, p1, p2, offset=offset, scale=scale,
                          text=text, layer=L_DIM, tracker=tracker)


def dim_v(msp, p1, p2, scale: float, offset: float = 12.0, text: str = "",
          tracker=None):
    """竖直线性标注（尺寸线在左侧）——复用 envcad.standards.dim。"""
    return draw_dimension(msp, p1, p2, offset=offset, scale=scale,
                          text=text, layer=L_DIM, tracker=tracker)


def label(msp, text: str, point, scale: float, height: float = 3.0,
          align=TextEntityAlignment.MIDDLE_CENTER, layer: str = L_TEXT,
          tracker=None):
    """写一行仿宋 GB2312 文字（图纸字高 ``height`` mm）。"""
    return _t(msp, text, point, height * scale, align=align, layer=layer,
              tracker=tracker)


def view_title(msp, text: str, point, scale: float, tracker=None):
    """视图名（3.5mm 加粗层）。"""
    return _t(msp, text, point, 3.5 * scale,
              align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TITLE,
              tracker=tracker)


def leader(msp, target, text: str, scale: float, bend=(8, 8),
           text_dir: str = "right", tracker=None):
    """零部件指引线标注——复用 envcad.standards.annotate.draw_leader。"""
    return draw_leader(msp, target, text, scale, bend=bend,
                       text_dir=text_dir, tracker=tracker)


def tech_notes(msp, origin, scale: float, notes: Iterable[str],
               title: str = "技术要求", width: float = 92.0, tracker=None):
    """技术要求文字块——复用 envcad.standards.notes.draw_notes_block。

    Args:
        origin: 文字块左上角（实物坐标）
        width: 块宽度（图纸 mm）
    """
    return draw_notes_block(msp, origin, list(notes), scale=scale,
                            title=title, width=width, tracker=tracker)


def hatch_solid(msp, pts: Sequence[Tuple[float, float]],
                layer: str = L_THIN, pattern: str = "ANSI31",
                pattern_scale: float = 1.0):
    """闭合区域填充（剖面线，GB/T 17453）。失败时静默跳过。"""
    try:
        h = msp.add_hatch(color=7, dxfattribs={"layer": layer})
        h.paths.add_polyline_path(list(pts), is_closed=True)
        h.set_pattern_fill(pattern, scale=pattern_scale)
        return h
    except Exception as _e:
        return None


def ground_line(msp, x0: float, x1: float, y: float, scale: float,
                n_ticks: int = 24, layer: str = L_THIN):
    """地平线 + 45° 短斜线（机械/农机侧视图惯用画法）。"""
    msp.add_line((x0, y), (x1, y), dxfattribs={"layer": L_MED})
    if n_ticks <= 0:
        return
    step = (x1 - x0) / n_ticks
    t = 2.0 * scale
    for i in range(n_ticks):
        px = x0 + i * step
        msp.add_line((px, y), (px - t, y - t), dxfattribs={"layer": layer})


def wheel(msp, cx: float, cy: float, d: float, scale: float,
          n_lugs: int = 14, rim_ratio: float = 0.58,
          hub_ratio: float = 0.16, layer: str = L_THICK):
    """轮胎侧视图：胎面圆 + 轮辋 + 轮毂 + 花纹 + 中心线。

    Args:
        d: 轮胎外径（实物 mm）
        n_lugs: 胎面花纹（人字胎爪）数量，0 = 不画
    """
    import math
    r = d / 2.0
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    r_rim = r * rim_ratio
    msp.add_circle((cx, cy), r_rim, dxfattribs={"layer": L_MED})
    msp.add_circle((cx, cy), r * hub_ratio, dxfattribs={"layer": L_MED})
    for i in range(max(0, n_lugs)):
        a = 2 * math.pi * i / n_lugs
        msp.add_line((cx + r_rim * math.cos(a), cy + r_rim * math.sin(a)),
                     (cx + r * math.cos(a), cy + r * math.sin(a)),
                     dxfattribs={"layer": L_THIN})
    cross_center(msp, cx, cy, r, scale)
    return (cx, cy, r)
