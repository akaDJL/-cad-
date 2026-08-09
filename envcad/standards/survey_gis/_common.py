"""测绘与 GIS 扩展模块公共基础设施（非侵入式复用 envcad v1.5）。

设计原则：
  * 不修改 envcad 包，只从 envcad.standards.* / envcad.engine.* 导入复用。
  * 复用 envcad 的图层体系（layers.LAYER_DEFS）与仿宋 GB2312 文字样式（"HZ"）。
  * 本模块只补充测绘/GIS 专业图层，其余一律沿用国标基础图层。

制图依据：
  GB/T 50001—2017 房屋建筑制图统一标准（线宽组 4:2:1、字高系列）
  GB/T 14689—2008 图纸幅面和格式（A3 横式 420×297）
  GB/T 20257.1—2017 国家基本比例尺地图图式 第1部分（1:500 1:1000 1:2000）
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Sequence, Tuple

# ── envcad 包引导（只读引用，不改动源包） ────────────────────
ENVCAD_ROOT = os.environ.get(
    "ENVCAD_ROOT",
    r"C:\Users\lenovo\Desktop\凹凸cad小助手（二集）v1.5",
)
if ENVCAD_ROOT not in sys.path:
    sys.path.insert(0, ENVCAD_ROOT)

from ezdxf.enums import TextEntityAlignment            # noqa: E402
from ezdxf.math import Matrix44                        # noqa: E402

from envcad.engine.dxf_base import new_drawing, save_dxf, BBoxTracker  # noqa: E402,F401
from envcad.standards import frame as _frame           # noqa: E402
from envcad.standards import annotate as _annotate     # noqa: E402
from envcad.standards import layers as _layers         # noqa: E402
from envcad.utils import _r                            # noqa: E402

FrameInfo = _frame.FrameInfo
draw_leader = _annotate.draw_leader
draw_text_block = _annotate.draw_text_block

# A3 幅面（复用 envcad.standards.frame 的常量，避免二次定义）
A3_W, A3_H = _frame.A3_W, _frame.A3_H

# 汉字文字样式：仿宋 GB2312（envcad.standards.styles.HZ_FONT = simfang.ttf）
HZ = "HZ"
ENG = "ENG"


# ══════════════════════════════════════════════════════════
#  测绘 / GIS 专业图层（在 envcad 国标图层之外补充）
# ══════════════════════════════════════════════════════════
# (图层名, ACI 颜色, 线型, 线宽 1/100mm)
# 线宽遵循 GB/T 50001—2017 4.0.1 线宽组 粗:中:细 = 4:2:1（b=0.5mm）
SURVEY_LAYER_DEFS = [
    # —— 定位基础（GB/T 20257.1 4.1）——
    ("测量控制点",     7, "CONTINUOUS", 35),
    ("控制点注记",     7, "CONTINUOUS", 18),
    # —— 地形要素（GB/T 20257.1 4.2~4.8）——
    ("地形-居民地",    7, "CONTINUOUS", 35),
    ("地形-交通",      7, "CONTINUOUS", 35),
    ("地形-水系",      5, "CONTINUOUS", 18),
    ("地形-植被",      3, "CONTINUOUS", 18),
    ("地形-等高线",   30, "CONTINUOUS", 18),   # 首曲线（棕）
    ("地形-计曲线",   30, "CONTINUOUS", 35),   # 计曲线加粗
    ("地形-注记",      7, "CONTINUOUS", 18),
    # —— 地下管线探测（CJJ 61-2017《城市地下管线探测技术规程》；CJJ/T 158 为城建档案标准，非探测主体）——
    ("管线-探测",      2, "DASHED",     35),
    ("管点",           7, "CONTINUOUS", 18),
    ("给水管",         5, "CONTINUOUS", 50),
    ("排水管",         4, "CONTINUOUS", 50),
    ("燃气管",         2, "CONTINUOUS", 50),
    ("电力管",         1, "CONTINUOUS", 50),
    ("通信管",         6, "CONTINUOUS", 50),
    ("热力管",         3, "CONTINUOUS", 50),
    ("工艺管道",       7, "CONTINUOUS", 50),
    ("仪表",           7, "CONTINUOUS", 18),
    # —— 用地与权属（GB/T 50103—2010 总图制图标准）——
    ("用地红线",       1, "CONTINUOUS", 50),
    ("界址点",         1, "CONTINUOUS", 35),
    ("道路红线",       2, "CONTINUOUS", 35),
    ("建筑控制线",     6, "DASHED",     35),
]


def ensure_survey_layers(doc) -> None:
    """补建测绘/GIS 专业图层（幂等）。先确保 envcad 国标图层与线型存在。"""
    _layers.setup_layers(doc)
    for lt in ("DASHED", "CENTER", "PHANTOM"):
        _layers._ensure_linetype(doc, lt)
    for name, color, ltype, lw in SURVEY_LAYER_DEFS:
        if name in doc.layers:
            continue
        try:
            lay = doc.layers.add(name)
            lay.dxf.color = color
            lay.dxf.linetype = (
                ltype if ltype == "CONTINUOUS" or doc.linetypes.has_entry(ltype)
                else "CONTINUOUS"
            )
            lay.dxf.lineweight = lw
        except Exception as _e:
            print(f'[WARNING] _common.py: {_e}')


def ensure_doc_ready(msp) -> None:
    """从 modelspace 反查 doc 并确保图层/样式齐备。"""
    doc = getattr(msp, "doc", None)
    if doc is not None:
        ensure_survey_layers(doc)


# ══════════════════════════════════════════════════════════
#  文字与图元助手（统一走 envcad 的 HZ 仿宋样式）
# ══════════════════════════════════════════════════════════

def text(msp, content, point, height: float,
         align=TextEntityAlignment.MIDDLE_LEFT,
         layer: str = "文字", style: str = HZ, rotation: float = 0.0):
    """写入单行文字（仿宋 GB2312）。height 为实物坐标字高（已含比例）。"""
    if content is None or content == "":
        return None
    t = msp.add_text(str(content), dxfattribs={
        "layer": layer, "height": height, "style": style})
    t.set_placement(_r(*point), align=align)
    if rotation:
        t.dxf.rotation = rotation
    return t


def polyline(msp, pts: Sequence[Tuple[float, float]], layer: str,
             close: bool = False, linetype: str | None = None):
    """多段线（坐标自动圆整到 0.01mm，与 envcad 精度约定一致）。"""
    attribs = {"layer": layer}
    if linetype:
        attribs["linetype"] = linetype
    return msp.add_lwpolyline([_r(*p) for p in pts], close=close,
                              dxfattribs=attribs)


def line(msp, p1, p2, layer: str, linetype: str | None = None):
    attribs = {"layer": layer}
    if linetype:
        attribs["linetype"] = linetype
    return msp.add_line(_r(*p1), _r(*p2), dxfattribs=attribs)


def circle(msp, center, radius: float, layer: str):
    return msp.add_circle(_r(*center), radius, dxfattribs={"layer": layer})


def solid_fill(msp, pts: Iterable[Tuple[float, float]], layer: str):
    """实心填充（控制点、界址点等实心符号）。失败时回退为闭合多段线。"""
    pts = [_r(*p) for p in pts]
    try:
        h = msp.add_hatch(color=256, dxfattribs={"layer": layer})
        h.paths.add_polyline_path(pts, is_closed=True)
        h.set_solid_fill()
        return h
    except Exception as _e:
        return msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def fraction_label(msp, point, numerator: str, denominator: str,
                   height: float, layer: str = "控制点注记"):
    """分数式注记：分子=点名/点号，分母=高程（GB/T 20257.1 4.1 注记规定）。

    返回 (分数线长度, 分数线中点)。
    """
    px, py = point
    w = max(len(str(numerator)), len(str(denominator))) * height * 0.75
    text(msp, numerator, (px, py + height * 0.75), height,
         align=TextEntityAlignment.MIDDLE_LEFT, layer=layer)
    line(msp, (px, py), (px + w, py), layer)
    text(msp, denominator, (px, py - height * 0.75), height,
         align=TextEntityAlignment.MIDDLE_LEFT, layer=layer)
    return w, (px + w / 2, py)


# ══════════════════════════════════════════════════════════
#  图框复用（envcad.standards.frame.draw_frame 原样复用 + 平移）
# ══════════════════════════════════════════════════════════

def draw_frame_at(msp, x: float, y: float, scale: float,
                  info: FrameInfo, tracker=None):
    """在 (x, y) 处放置 envcad 的 A3 国标图框（GB/T 14689 + GB/T 50001）。

    envcad 的 draw_frame 固定绘于原点，此处复用其已验证代码后整体平移，
    不改动源包实现。返回内框范围 (x0, y0, x1, y1)。
    """
    doc = msp.doc
    ensure_survey_layers(doc)
    n0 = len(msp)
    bbox = _frame.draw_frame(doc, scale, info, tracker=tracker)
    if x or y:
        m = Matrix44.translate(x, y, 0)
        for e in list(msp)[n0:]:
            try:
                e.transform(m)
            except Exception as _e:
                print(f'[WARNING] _common.py: {_e}')
    x0, y0, x1, y1 = bbox
    return (x0 + x, y0 + y, x1 + x, y1 + y)


def sheet_size(scale: float) -> Tuple[float, float]:
    """A3 横式图幅在实物坐标下的尺寸。"""
    return A3_W * scale, A3_H * scale


__all__ = [
    "ENVCAD_ROOT", "new_drawing", "save_dxf", "BBoxTracker", "FrameInfo",
    "TextEntityAlignment", "HZ", "ENG", "A3_W", "A3_H",
    "SURVEY_LAYER_DEFS", "ensure_survey_layers", "ensure_doc_ready",
    "text", "polyline", "line", "circle", "solid_fill", "fraction_label",
    "draw_frame_at", "sheet_size", "draw_leader", "draw_text_block",
]
