"""电子与半导体行业模块公共基座（envcad 扩展，非侵入）。

本文件不复制 envcad 的任何绘图逻辑，只做**薄封装**：
  * 图层名 —— 全部沿用 envcad.standards.layers.LAYER_DEFS 中已有图层
  * 文字样式 —— 沿用 envcad.standards.styles 的 "HZ"（仿宋 GB2312 simfang.ttf）
    与 "ENG"（simplex.shx）
  * 图框标题栏 —— 直接调用 envcad.standards.frame.draw_frame（GB/T 14689 A3）
  * 线性标注 —— 直接调用 envcad.standards.dim.draw_dimension（GB/T 1800.2—2020）
  * 技术要求块 —— 直接调用 envcad.standards.notes.draw_notes_block

依据标准:
  GB/T 14689—2008 技术制图 图纸幅面和格式
  GB/T 17450—1998 技术制图 图线
  GB/T 4457.4—2002 机械制图 图样画法 图线
  GB/T 10609.2—2009 技术制图 明细栏

比例约定（沿用 envcad）:
  modelspace 一律按 1:1 实物毫米绘制，图框按 ``scale`` 放大。
  ``scale`` = 出图比例的倒数：1:100→100，1:1→1.0，5:1（放大）→0.2。
  电子件尺寸小，故本包各模块默认 scale 取 0.2~2.0，而非环保工程的 50/100。
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Optional, Sequence, Tuple

# ── 让扩展包可以 import envcad（只读引用，不修改原包） ──────────
ENVCAD_ROOT = r"C:/Users/lenovo/Desktop/凹凸cad小助手（二集）v1.5"
if ENVCAD_ROOT not in sys.path:
    sys.path.insert(0, ENVCAD_ROOT)

from ezdxf.enums import TextEntityAlignment  # noqa: E402

from envcad.engine.dxf_base import new_drawing, save_dxf  # noqa: E402,F401
from envcad.standards.frame import FrameInfo, draw_frame  # noqa: E402
from envcad.standards.annotate import _t, draw_leader  # noqa: E402,F401
from envcad.standards.dim import draw_dimension  # noqa: E402
from envcad.standards.notes import draw_notes_block  # noqa: E402,F401
from envcad.standards.bom import draw_bom  # noqa: E402,F401
from envcad.standards.layers import LAYER_DEFS, layer_of  # noqa: E402,F401


# ── 语义图层 → envcad 既有图层名映射（不新建图层） ──────────────
L_OUTLINE = "粗实线"        # 主轮廓：板边、封装本体、壳体外壁
L_MID = "中实线"            # 次轮廓：引脚、翅片、连接器针
L_THIN = "细实线"           # 辅助线、剖面网格、图例
L_DIM = "细实线-尺寸"       # 尺寸线（GB/T 17450 细实线）
L_AUX = "细实线-辅助"
L_HIDDEN = "虚线"           # 不可见轮廓（内层、埋孔）
L_CENTER = "点画线"         # 中心线 / 对称线
L_PHANTOM = "双点画线"      # 假想线：禁布区、包络线
L_TEXT = "文字"
L_TITLE = "文字-标题"
L_HATCH = "剖面线"
L_DEV = "设备"              # 元器件本体填充色
L_LEGEND = "图例"

#: 各模块生成的 DXF 至少应包含的图层（供验证脚本断言）
EXPECTED_LAYERS = (L_OUTLINE, L_THIN, L_DIM, L_TEXT, L_TITLE, "图框")

HZ = "HZ"    # 仿宋 GB2312
ENG = "ENG"  # simplex.shx


# ══════════════════════════════════════════════════════════
#  图纸装配
# ══════════════════════════════════════════════════════════

def new_sheet(title: str, drawing_no: str, scale: float = 1.0,
              project: str = "电子与半导体",
              unit: str = "envcad",
              designer: str = "envcad",
              date: str = "2026.07"):
    """新建一张带 GB A3 图框的图纸。

    依据标准: GB/T 14689—2008（幅面）、GB/T 50001—2017（标题栏）。

    返回 (doc, msp, dim_style, tracker, (x0, y0, x1, y1))，
    其中 (x0,y0,x1,y1) 为内框范围（实物坐标 mm）。
    """
    doc, dim_style, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    info = FrameInfo(
        title=title,
        drawing_no=drawing_no,
        scale_str=_scale_str(scale),
        project=project,
        unit=unit,
        designer=designer,
        date=date,
    )
    bounds = draw_frame(doc, scale, info, tracker=tracker)
    return doc, msp, dim_style, tracker, bounds


def _scale_str(scale: float) -> str:
    """把 envcad 的 scale（出图比例倒数）转成 GB/T 14690 比例字符串。"""
    if abs(scale - 1.0) < 1e-9:
        return "1:1"
    if scale > 1.0:
        return f"1:{scale:g}"
    return f"{1.0 / scale:g}:1"


def sheet_center(bounds: Sequence[float],
                 fx: float = 0.5, fy: float = 0.55) -> Tuple[float, float]:
    """按内框比例取一个定位点，便于把图形摆在图幅中部。"""
    x0, y0, x1, y1 = bounds
    return (x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy)


# ══════════════════════════════════════════════════════════
#  绘图小工具（全部落在 envcad 既有图层上）
# ══════════════════════════════════════════════════════════

def rect(msp, x0: float, y0: float, w: float, h: float,
         layer: str = L_OUTLINE, close: bool = True):
    """左下角定位的矩形（LWPOLYLINE）。"""
    return msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=close, dxfattribs={"layer": layer})


def rounded_rect(msp, x0: float, y0: float, w: float, h: float, r: float,
                 layer: str = L_OUTLINE):
    """圆角矩形（直线 + 四段 90° 圆弧）。r<=0 时退化为矩形。"""
    if r <= 0:
        return rect(msp, x0, y0, w, h, layer)
    x1, y1 = x0 + w, y0 + h
    a = {"layer": layer}
    msp.add_line((x0 + r, y0), (x1 - r, y0), dxfattribs=a)
    msp.add_line((x1, y0 + r), (x1, y1 - r), dxfattribs=a)
    msp.add_line((x1 - r, y1), (x0 + r, y1), dxfattribs=a)
    msp.add_line((x0, y1 - r), (x0, y0 + r), dxfattribs=a)
    msp.add_arc((x0 + r, y0 + r), r, 180, 270, dxfattribs=a)
    msp.add_arc((x1 - r, y0 + r), r, 270, 360, dxfattribs=a)
    msp.add_arc((x1 - r, y1 - r), r, 0, 90, dxfattribs=a)
    msp.add_arc((x0 + r, y1 - r), r, 90, 180, dxfattribs=a)


def center_cross(msp, cx: float, cy: float, size: float,
                 layer: str = L_CENTER):
    """中心线十字（GB/T 4457.4 细点画线）。"""
    msp.add_line((cx - size, cy), (cx + size, cy), dxfattribs={"layer": layer})
    msp.add_line((cx, cy - size), (cx, cy + size), dxfattribs={"layer": layer})


def hole(msp, cx: float, cy: float, dia: float,
         layer: str = L_OUTLINE, cross: bool = True,
         cross_layer: str = L_CENTER):
    """圆孔 + 中心线（GB/T 4459.1 孔中心线画法）。"""
    msp.add_circle((cx, cy), dia / 2.0, dxfattribs={"layer": layer})
    if cross:
        center_cross(msp, cx, cy, dia * 0.8, cross_layer)


def text(msp, content: str, point, height: float,
         align=TextEntityAlignment.LEFT, layer: str = L_TEXT,
         style: str = HZ, rotation: float = 0.0):
    """写字（仿宋 GB2312 / simplex），高度为实物 mm。"""
    if not content:
        return None
    t = msp.add_text(str(content), dxfattribs={
        "layer": layer, "height": height, "style": style,
        "rotation": rotation,
    })
    t.set_placement(point, align=align)
    return t


def view_title(msp, content: str, cx: float, y: float, scale: float):
    """视图名称（GB/T 50001 视图标题，字高 3.5mm 出图）。"""
    return text(msp, content, (cx, y), 3.5 * scale,
                align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TITLE)


def dim_line(msp, p1, p2, offset: float, scale: float,
             text_str: str = "", tracker=None):
    """线性尺寸（复用 envcad.standards.dim.draw_dimension）。

    offset 为调用方已按出图放大的 mm（即 offset = N * scale），
    本函数换算回 envcad 的"图纸 mm"基准（除以 scale），由 draw_dimension
    再乘回 scale，得到正确的实物坐标偏移，避免双重乘 scale。
    """
    return draw_dimension(msp, p1, p2, offset=offset / scale, scale=scale,
                          text=text_str, layer=L_DIM, tracker=tracker)


def param_table(msp, origin, rows: Iterable[Tuple[str, str]],
                scale: float, title: str = "参数表",
                col1: float = 34.0, col2: float = 30.0,
                row_h: float = 6.0):
    """参数表（GB/T 10609.2 明细栏画法的简化两列版）。

    origin 为表格左上角，返回右下角坐标。
    """
    s = scale
    ox, oy = origin
    w1, w2, rh = col1 * s, col2 * s, row_h * s
    rows = list(rows)
    cur = oy
    if title:
        rect(msp, ox, cur - rh, w1 + w2, rh, L_OUTLINE)
        text(msp, title, (ox + (w1 + w2) / 2, cur - rh / 2), 3.0 * s,
             align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TITLE)
        cur -= rh
    for k, v in rows:
        rect(msp, ox, cur - rh, w1, rh, L_THIN)
        rect(msp, ox + w1, cur - rh, w2, rh, L_THIN)
        text(msp, k, (ox + 1.5 * s, cur - rh / 2), 2.5 * s,
             align=TextEntityAlignment.MIDDLE_LEFT)
        text(msp, v, (ox + w1 + 1.5 * s, cur - rh / 2), 2.5 * s,
             align=TextEntityAlignment.MIDDLE_LEFT, style=ENG)
        cur -= rh
    rect(msp, ox, cur, w1 + w2, oy - cur, L_OUTLINE)
    return (ox + w1 + w2, cur)


def notes(msp, origin, lines: Sequence[str], scale: float,
          title: str = "技术要求", width: float = 95.0, tracker=None):
    """技术要求块（复用 envcad.standards.notes.draw_notes_block）。"""
    return draw_notes_block(msp, origin, list(lines), title=title,
                            width=width, scale=scale, tracker=tracker)


# ══════════════════════════════════════════════════════════
#  GB/T 1804—2000 线性尺寸未注公差
# ══════════════════════════════════════════════════════════

#: 公差等级 → [(尺寸段上限 mm, 极限偏差 ±mm), ...]
#: 依据 GB/T 1804—2000 表1（线性尺寸的极限偏差数值）
GB1804_LINEAR = {
    "f": [(3, 0.05), (6, 0.05), (30, 0.1), (120, 0.15),
          (400, 0.2), (1000, 0.3), (2000, 0.5)],
    "m": [(3, 0.1), (6, 0.1), (30, 0.2), (120, 0.3),
          (400, 0.5), (1000, 0.8), (2000, 1.2)],
    "c": [(3, 0.2), (6, 0.3), (30, 0.5), (120, 0.8),
          (400, 1.2), (1000, 2.0), (2000, 3.0)],
    "v": [(3, None), (6, 0.5), (30, 1.0), (120, 1.5),
          (400, 2.5), (1000, 4.0), (2000, 6.0)],
}


def gb1804_tolerance(size_mm: float, grade: str = "m") -> Optional[float]:
    """查 GB/T 1804—2000 线性尺寸未注公差（返回 ±mm，None 表示不规定）。

    grade: f 精密 / m 中等 / c 粗糙 / v 最粗。
    """
    table = GB1804_LINEAR.get(grade, GB1804_LINEAR["m"])
    for upper, tol in table:
        if size_mm <= upper:
            return tol
    return table[-1][1]


__all__ = [
    "new_sheet", "sheet_center", "save_dxf", "rect", "rounded_rect",
    "center_cross", "hole", "text", "view_title", "dim_line", "param_table",
    "notes", "gb1804_tolerance", "GB1804_LINEAR", "EXPECTED_LAYERS",
    "TextEntityAlignment", "HZ", "ENG",
    "L_OUTLINE", "L_MID", "L_THIN", "L_DIM", "L_AUX", "L_HIDDEN",
    "L_CENTER", "L_PHANTOM", "L_TEXT", "L_TITLE", "L_HATCH", "L_DEV",
    "L_LEGEND",
]
