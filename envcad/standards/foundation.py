"""基础与结构详图 v1.0（GB 50007—2011、GB 50010—2010、GB 50011—2010）。

基于 ezdxf 实现桩位平面图、基础详图、楼板配筋、剪力墙布置、
楼梯详图、挡土墙、基坑支护等结构施工图。

所有设计参数（桩径、桩长、配筋率、混凝土强度等）由 Agent 搜索后显式传入。
纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  桩位平面图
# ══════════════════════════════════════════════════════════

def draw_pile_plan(msp, origin, width: float, length: float,
                    piles: List[dict],
                    scale: float = 100.0,
                    label: str = "",
                    layer: str = "桩基",
                    tracker=None):
    """桩位平面布置图。

    参数:
        width/length: 承台/筏板尺寸 mm
        piles: 桩列表 [{"x":1000,"y":500,"dia":600,"type":"PHC","length":25}, ...]
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    l = length * s

    # 承台轮廓（虚线）
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + l), (ox, oy + l)],
        close=True, dxfattribs={"layer": layer, "linetype": "DASHED"}
    )

    # 轴线标注
    _draw_axis(msp, ox, oy, ox + w, oy + l, s)

    # 桩位
    for pile in piles:
        px = ox + pile.get("x", 0) * s
        py = oy + pile.get("y", 0) * s
        dia = pile.get("dia", 600) * s
        ptype = pile.get("type", "")

        # 桩圆
        r = dia / 2
        msp.add_circle((px, py), r, dxfattribs={"layer": layer})

        # 桩类型标记
        if ptype:
            t = msp.add_text(ptype, dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG",
            })
            t.set_placement((px, py + r + 2 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

        # 十字中心
        msp.add_line((px - r * 0.5, py), (px + r * 0.5, py),
                     dxfattribs={"layer": "中心线"})
        msp.add_line((px, py - r * 0.5), (px, py + r * 0.5),
                     dxfattribs={"layer": "中心线"})

    # 尺寸标注
    _dim_arrows(msp, ox, oy - 5 * s, ox + w, oy - 5 * s,
                f"{width / 1000:.1f}m", s, layer)
    _dim_arrows(msp, ox - 5 * s, oy, ox - 5 * s, oy + l,
                f"{length / 1000:.1f}m", s, layer)

    if label:
        txt_h = 3.5 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + l + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + w, oy + l)


# ══════════════════════════════════════════════════════════
#  基础详图
# ══════════════════════════════════════════════════════════

def draw_foundation_detail(msp, origin, f_type: str = "isolated",
                            width: float = 2000, height: float = 500,
                            depth: float = 1500,
                            scale: float = 100.0,
                            label: str = "",
                            params: dict = None,
                            layer: str = "基础",
                            tracker=None):
    """基础详图（断面）。

    参数:
        f_type: "isolated"独立 / "strip"条形 / "raft"筏板 / "pile_cap"承台
        width/height: 基础尺寸 mm
        depth: 埋深 mm
        params: {"concrete":"C30","cover":"50mm","reinforcement":"Φ12@150",...}
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    h = height * s
    d = depth * s

    # 基础轮廓
    msp.add_lwpolyline(
        [(ox - w / 2, oy), (ox + w / 2, oy),
         (ox + w / 2, oy - h), (ox - w / 2, oy - h)],
        close=True, dxfattribs={"layer": layer}
    )

    # 柱/墙身轮廓
    col_w = w * 0.4
    msp.add_lwpolyline(
        [(ox - col_w / 2, oy), (ox + col_w / 2, oy),
         (ox + col_w / 2, oy + d * 0.3), (ox - col_w / 2, oy + d * 0.3)],
        close=True, dxfattribs={"layer": layer}
    )

    # 垫层
    pad = 3.0 * s
    msp.add_line((ox - w / 2 - pad, oy - h - pad),
                 (ox + w / 2 + pad, oy - h - pad),
                 dxfattribs={"layer": "细实线"})
    msp.add_line((ox - w / 2 - pad, oy - h),
                 (ox - w / 2 - pad, oy - h - pad),
                 dxfattribs={"layer": "细实线"})
    msp.add_line((ox + w / 2 + pad, oy - h),
                 (ox + w / 2 + pad, oy - h - pad),
                 dxfattribs={"layer": "细实线"})

    # 地面线
    gl = d * 0.6
    msp.add_line((ox - w, oy + gl), (ox + w, oy + gl),
                 dxfattribs={"layer": "细实线", "linetype": "DASHDOT"})
    t = msp.add_text("GL", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "ENG",
    })
    t.set_placement((ox + w + 2 * s, oy + gl),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    # 标高
    _elevation(msp, ox - w / 2 - 8 * s, oy, f"±0.000", s)
    _elevation(msp, ox - w / 2 - 8 * s, oy - h,
               f"-{height / 1000:.3f}", s)

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox, oy + gl + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + gl + 5 * s + 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((ox, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + w / 2, oy - h - pad)


# ══════════════════════════════════════════════════════════
#  楼板配筋图
# ══════════════════════════════════════════════════════════

def draw_slab_reinforcement(msp, origin, width: float, length: float,
                             top_bars: dict = None,
                             bottom_bars: dict = None,
                             thickness: float = 120,
                             scale: float = 100.0,
                             label: str = "",
                             layer: str = "结构",
                             tracker=None):
    """楼板配筋图。

    参数:
        top_bars: {"x":"Φ10@150","y":"Φ10@200","add":"Φ12@200(L=1500)"}
        bottom_bars: {"x":"Φ8@150","y":"Φ8@200"}
        thickness: 板厚 mm
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    l = length * s
    t = thickness * s

    # 板轮廓
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + l), (ox, oy + l)],
        close=True, dxfattribs={"layer": layer}
    )

    # 底部钢筋（长向）
    if bottom_bars:
        bx = bottom_bars.get("x", "")
        by = bottom_bars.get("y", "")
        if bx:
            _draw_slab_bars(msp, ox, oy, w, l, "x", bx, s, "细实线")
        if by:
            _draw_slab_bars(msp, ox, oy, w, l, "y", by, s, "细实线")

    # 顶部钢筋（短向 + 附加筋）
    if top_bars:
        tx = top_bars.get("x", "")
        ty = top_bars.get("y", "")
        add = top_bars.get("add", "")
        if tx:
            _draw_slab_bars(msp, ox, oy, w, l, "x", tx, s, layer)
        if ty:
            _draw_slab_bars(msp, ox, oy, w, l, "y", ty, s, layer)
        if add:
            # 附加筋在支座处（板四边）
            _add_bars_marker(msp, ox, oy, w, l, add, s, layer)

    # 板厚标注
    txt_h = 2.5 * s
    t_str = f"h={thickness}"
    t = msp.add_text(t_str, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((ox + w / 2, oy + l / 2),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.0 * s, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + l + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + w, oy + l)


def _draw_slab_bars(msp, ox, oy, w, l, direction, spec, s, layer):
    """板内钢筋示意线。"""
    if direction == "x":
        n = max(2, int(w / (15 * s)))
        for i in range(n):
            bx = ox + w * (i + 0.5) / n
            msp.add_line((bx, oy + 1 * s), (bx, oy + l - 1 * s),
                         dxfattribs={"layer": layer})
    else:
        n = max(2, int(l / (15 * s)))
        for i in range(n):
            by = oy + l * (i + 0.5) / n
            msp.add_line((ox + 1 * s, by), (ox + w - 1 * s, by),
                         dxfattribs={"layer": layer})

    # 标注
    txt_h = 2.0 * s
    if direction == "x":
        tx, ty = ox + w / 2, oy - 3 * s
    else:
        tx, ty = ox - 3 * s, oy + l / 2

    t = msp.add_text(spec, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_CENTER)


def _add_bars_marker(msp, ox, oy, w, l, spec, s, layer):
    """附加筋标注。"""
    txt_h = 2.0 * s
    # 四边标注
    positions = [
        (ox + w / 2, oy + l + 3 * s),
        (ox + w / 2, oy - 3 * s),
        (ox - 5 * s, oy + l / 2),
        (ox + w + 5 * s, oy + l / 2),
    ]
    for px, py in positions:
        t = msp.add_text(spec, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((px, py), align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  剪力墙布置
# ══════════════════════════════════════════════════════════

def draw_shear_wall(msp, origin, width: float, length: float,
                     thickness: float = 250,
                     openings: List[dict] = None,
                     scale: float = 100.0,
                     label: str = "",
                     params: dict = None,
                     layer: str = "结构",
                     tracker=None):
    """剪力墙平面/立面布置。

    参数:
        openings: [{"type":"door","x":1200,"width":1000,"height":2100},...]
        params: {"concrete":"C40","vertical":"Φ14@150","horizontal":"Φ12@200",...}
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    l = length * s
    t = thickness * s

    # 墙身（填充/粗线）
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + l), (ox, oy + l)],
        close=True, dxfattribs={"layer": layer, "lineweight": 50}
    )

    # 洞口
    if openings:
        for op in openings:
            op_x = ox + op.get("x", 0) * s
            op_w = op.get("width", 1000) * s
            op_h = op.get("height", 2100) * s
            op_y = oy + l * 0.1

            # 洞口（空白区域标记）
            msp.add_lwpolyline(
                [(op_x, op_y), (op_x + op_w, op_y),
                 (op_x + op_w, op_y + op_h), (op_x, op_y + op_h)],
                close=True,
                dxfattribs={"layer": layer, "linetype": "DASHED"}
            )

            # 洞口标注
            t = msp.add_text(f"{op.get('width',0)}×{op.get('height',0)}",
                              dxfattribs={
                                  "layer": "文字", "height": 2.2 * s,
                                  "style": "ENG",
                              })
            t.set_placement((op_x + op_w / 2, op_y + op_h / 2),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + l + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + l + 4 * s + 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((ox + w / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + w, oy + l)


# ══════════════════════════════════════════════════════════
#  楼梯详图
# ══════════════════════════════════════════════════════════

def draw_stair_section(msp, origin, n_rises: int = 18,
                        rise: float = 150, tread: float = 280,
                        width: float = 1200,
                        scale: float = 100.0,
                        label: str = "",
                        layer: str = "结构",
                        tracker=None):
    """楼梯剖面详图。

    参数:
        n_rises: 踏步级数
        rise: 踏步高 mm
        tread: 踏步宽 mm
        width: 梯段宽度 mm
    """
    s = scale
    ox, oy = _r(*origin)
    r_h = rise * s
    t_w = tread * s

    # 踏步线（锯齿）
    cx, cy = ox, oy
    for i in range(n_rises + 1):
        if i < n_rises:
            msp.add_line((cx + t_w * i, cy + r_h * i),
                         (cx + t_w * i + t_w, cy + r_h * i),
                         dxfattribs={"layer": layer})
        msp.add_line((cx + t_w * i, cy + r_h * i),
                     (cx + t_w * i, cy + r_h * (i + 1)),
                     dxfattribs={"layer": layer})

    # 平台
    plat_w = 4.0 * s
    plat_x = cx - plat_w
    plat_y = oy
    msp.add_line((plat_x, plat_y), (cx, plat_y),
                 dxfattribs={"layer": layer})

    # 扶手
    handrail_off = 1.0 * s
    top_y = cy + r_h * n_rises + handrail_off
    msp.add_line((cx - plat_w * 0.5, plat_y + handrail_off),
                 (cx + t_w * n_rises, top_y),
                 dxfattribs={"layer": "细实线"})

    # 楼梯走向箭头
    mid_x = cx + t_w * n_rises / 2
    mid_y = cy + r_h * n_rises / 2
    msp.add_line((mid_x - 4 * s, mid_y), (mid_x + 4 * s, mid_y),
                 dxfattribs={"layer": layer})
    _tri_arrow(msp, (mid_x + 4 * s, mid_y), (1, 0), s, layer)

    # 标注
    txt_h = 2.5 * s
    t = msp.add_text(f"{rise}×{tread}", dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((cx + t_w * n_rises / 2, top_y + 5 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.0 * s, "style": "HZ",
        })
        t.set_placement((cx + t_w * n_rises / 2, top_y + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + t_w * n_rises, top_y)


# ══════════════════════════════════════════════════════════
#  挡土墙
# ══════════════════════════════════════════════════════════

def draw_retaining_wall(msp, origin, w_type: str = "gravity",
                         height: float = 4000, top_w: float = 300,
                         base_w: float = 2400, base_h: float = 600,
                         scale: float = 100.0,
                         label: str = "",
                         params: dict = None,
                         layer: str = "结构",
                         tracker=None):
    """挡土墙断面图。

    参数:
        w_type: "gravity"重力式 / "cantilever"悬臂式 / "counterfort"扶臂式
        height: 墙高 mm
        top_w/bottom_w: 墙顶/底宽
        base_w/base_h: 底板宽/厚
        params: {"concrete":"C25","backfill":"砂砾石","drain":"Φ100PVC@2000",...}
    """
    s = scale
    ox, oy = _r(*origin)
    h = height * s
    tw = top_w * s
    bw = base_w * s
    bh = base_h * s

    # 墙体（梯形）
    half_bw = bw / 2
    half_tw = tw / 2

    if w_type == "gravity":
        msp.add_lwpolyline(
            [(ox - half_bw, oy), (ox + half_bw, oy),
             (ox + half_tw, oy + h), (ox - half_tw, oy + h)],
            close=True, dxfattribs={"layer": layer}
        )
    elif w_type == "cantilever":
        # 立臂
        msp.add_lwpolyline(
            [(ox - half_tw, oy + bh), (ox + half_tw, oy + bh),
             (ox + half_tw, oy + h), (ox - half_tw, oy + h)],
            close=True, dxfattribs={"layer": layer}
        )
        # 底板
        msp.add_lwpolyline(
            [(ox - half_bw, oy), (ox + half_bw, oy),
             (ox + half_bw, oy + bh), (ox - half_bw, oy + bh)],
            close=True, dxfattribs={"layer": layer}
        )
        # 踵板加厚
        _hatch_zone(msp, ox - half_bw, oy, ox - half_tw - s, oy + bh,
                     s, layer)

    # 墙后填土（斜线）
    fill_x = ox + half_bw * 0.3
    for i in range(5):
        fy = oy + h * i / 5
        msp.add_line((fill_x, fy), (fill_x + bx(s) * 2, fy + 4 * s),
                     dxfattribs={"layer": "细实线"})

    # 地面线
    msp.add_line((ox - bw, oy), (ox + bw, oy),
                 dxfattribs={"layer": "细实线", "linetype": "DASHDOT"})

    # 泄水孔
    drain_y = oy + h * 0.3
    for d in [-1, 0, 1]:
        dx = d * 2 * s
        msp.add_circle((ox + dx, drain_y), 1.5 * s,
                       dxfattribs={"layer": layer})

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox, oy + h + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + h + 5 * s + 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((ox, py), align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + bw / 2, oy + h)


def bx(s): return s  # 简写


# ══════════════════════════════════════════════════════════
#  基坑支护
# ══════════════════════════════════════════════════════════

def draw_excavation_support(msp, origin, depth: float = 6000,
                             s_type: str = "pile",
                             scale: float = 100.0,
                             label: str = "",
                             params: dict = None,
                             layer: str = "支护",
                             tracker=None):
    """基坑支护剖面。

    参数:
        s_type: "pile"排桩 / "diaphragm"地下连续墙 / "anchor"锚杆 /
                "soil_nail"土钉 / "slope"放坡
        params: {"pile_dia":"800","spacing":"1200","depth":"15m",
                  "anchor":"3道","concrete":"C30",...}
    """
    s = scale
    ox, oy = _r(*origin)
    d = depth * s

    # 开挖轮廓
    msp.add_line((ox, oy), (ox + d * 0.7, oy),
                 dxfattribs={"layer": layer})
    msp.add_line((ox, oy), (ox, oy - d),
                 dxfattribs={"layer": layer})
    msp.add_line((ox, oy - d), (ox + d * 0.5, oy - d),
                 dxfattribs={"layer": layer})

    if s_type == "pile":
        # 排桩
        for i in range(5):
            py = oy - d * (i + 0.5) / 5
            rx = ox - 2 * s
            msp.add_circle((rx, py), 3 * s,
                           dxfattribs={"layer": layer})
        # 冠梁
        msp.add_lwpolyline(
            [(ox - 5 * s, oy), (ox + 1 * s, oy),
             (ox + 1 * s, oy - 4 * s), (ox - 5 * s, oy - 4 * s)],
            close=True, dxfattribs={"layer": layer})
    elif s_type == "anchor":
        # 锚杆
        for i in range(3):
            ay = oy - d * (i + 1) / 4
            msp.add_line((ox, ay), (ox + 8 * s, ay - 3 * s),
                         dxfattribs={"layer": layer, "lineweight": 40})
            # 锚头
            msp.add_lwpolyline(
                [(ox - 3 * s, ay - 1 * s),
                 (ox + 1 * s, ay - 1 * s),
                 (ox + 1 * s, ay + 1 * s),
                 (ox - 3 * s, ay + 1 * s)],
                close=True, dxfattribs={"layer": layer})
    elif s_type == "soil_nail":
        # 土钉 + 面层
        for i in range(4):
            ny = oy - d * (i + 0.5) / 4
            msp.add_line((ox, ny), (ox + 6 * s, ny),
                         dxfattribs={"layer": layer})
            _tri_arrow(msp, (ox + 6 * s, ny), (1, 0), s, layer)
        # 面层
        msp.add_line((ox - 1 * s, oy), (ox - 1 * s, oy - d),
                     dxfattribs={"layer": layer, "lineweight": 30})
    elif s_type == "slope":
        # 放坡
        slope_pts = [(ox, oy), (ox + d * 0.8, oy),
                     (ox + d * 0.3, oy - d), (ox + d * 0.8, oy - d)]
        msp.add_line(slope_pts[0], slope_pts[2],
                     dxfattribs={"layer": layer})
        msp.add_line(slope_pts[1], slope_pts[3],
                     dxfattribs={"layer": "细实线"})

    # 地面线
    msp.add_line((ox - 5 * s, oy), (ox + 10 * s, oy),
                 dxfattribs={"layer": "细实线", "linetype": "DASHDOT"})

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + 12 * s, oy),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if params:
        py = oy - 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((ox + 12 * s, py),
                            align=TextEntityAlignment.MIDDLE_LEFT)
            py -= 2.5 * s

    return (ox + 12 * s, oy - d)


# ─── 辅助 ──────────────────────────────────────────────

def _draw_axis(msp, x0, y0, x1, y1, s):
    """轴线圆标记。"""
    r = 5.0 * s
    for pt in [(x0, y0), (x1, y0), (x0, y1)]:
        msp.add_circle(pt, r, dxfattribs={"layer": "细实线"})


def _dim_arrows(msp, x1, y1, x2, y2, text, s, layer):
    """尺寸箭头标注。"""
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})
    _tri_arrow(msp, (x1, y1), (-1 if x1 > x2 else 1, 0) if abs(x1 - x2) > abs(y1 - y2) else (0, -1 if y1 > y2 else 1), s, layer)
    _tri_arrow(msp, (x2, y2), (1 if x1 > x2 else -1, 0) if abs(x1 - x2) > abs(y1 - y2) else (0, 1 if y1 > y2 else -1), s, layer)
    t = msp.add_text(text, dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "ENG",
    })
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    t.set_placement((mx, my - 3 * s), align=TextEntityAlignment.MIDDLE_CENTER)


def _elevation(msp, x, y, text, s):
    """标高标记。"""
    tri_w, tri_h = 3.0 * s, 3.0 * s
    pts = [(x, y), (x - tri_w, y - tri_h / 2),
           (x - tri_w, y + tri_h / 2)]
    msp.add_lwpolyline(pts, close=True,
                       dxfattribs={"layer": "细实线-尺寸"})
    t = msp.add_text(text, dxfattribs={
        "layer": "文字", "height": 2.0 * s, "style": "ENG",
    })
    t.set_placement((x - tri_w - 2 * s, y),
                    align=TextEntityAlignment.MIDDLE_RIGHT)


def _tri_arrow(msp, tip, direction, scale, layer):
    """三角箭头。"""
    tx, ty = tip
    dx, dy = direction
    h = 3.5 * scale
    w = 1.8 * scale
    px, py = -dy * w, dx * w
    pts = [(tx, ty), (tx - h * dx + px, ty - h * dy + py),
           (tx - h * dx - px, ty - h * dy - py)]
    try:
        msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def _hatch_zone(msp, x0, y0, x1, y1, s, layer):
    """区域填充。"""
    for _ in range(3):
        sx = x0 + (x1 - x0 - 5 * s)
        msp.add_line((x0 + 1 * s, y0 + 1 * s),
                     (x1 - 1 * s, y1 - 1 * s),
                     dxfattribs={"layer": "细实线"})

# ══════ v1.5+ 基础增补：桩群/筏板/承台 ══════
def draw_pile_group(msp,origin,n_piles=9,pile_dia=0.6,pile_len=15.0,capt_w=3.0,capt_th=1.0,spacing=1.8,scale=100.0,label="",layer="基础",tracker=None):
    s=scale;ox,oy=_r(*origin);d=pile_dia*s;ps=spacing*s;cw=capt_w*s
    msp.add_lwpolyline([(ox,oy),(ox+cw,oy),(ox+cw,oy+cw),(ox,oy+cw)],close=True,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(ox+1*s,oy+1*s),(ox+cw-1*s,oy+1*s),(ox+cw-1*s,oy+cw-1*s),(ox+1*s,oy+cw-1*s)],close=True,dxfattribs={"layer":"细实线"})
    n=int(n_piles**0.5)+1
    for i in range(n):
        for j in range(n):
            px=ox+cw/2+(i-n/2+0.5)*ps;py=oy+cw/2+(j-n/2+0.5)*ps
            msp.add_circle((px,py),d/2,dxfattribs={"layer":layer})
            msp.add_line((px-d/2,py),(px+d/2,py),dxfattribs={"layer":"点画线","linetype":"CENTER"})
    t=msp.add_text(f"D{pile_dia*1000:.0f} L{pile_len:.0f}m",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"});t.set_placement((ox+cw/2,oy-5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+cw/2,oy+cw+6*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_raft_foundation(msp,origin,width=15.0,length=20.0,thickness=1.2,scale=100.0,label="",layer="基础",tracker=None):
    s=scale;ox,oy=_r(*origin);w=width*s;l=length*s
    msp.add_lwpolyline([(ox,oy),(ox+w,oy),(ox+w,oy+l),(ox,oy+l)],close=True,dxfattribs={"layer":layer})
    for i in range(5):msp.add_line((ox,oy+l*i/5),(ox+w,oy+l*i/5),dxfattribs={"layer":"细实线"})
    for i in range(7):msp.add_line((ox+w*i/7,oy),(ox+w*i/7,oy+l),dxfattribs={"layer":"细实线"})
    t=msp.add_text(f"厚{thickness*1000:.0f}mm",dxfattribs={"layer":"文字","height":3*s,"style":"HZ"});t.set_placement((ox+w/2,oy+l+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+w/2,oy+l+9*s),align=TextEntityAlignment.MIDDLE_CENTER)


def draw_caisson(msp, origin, D=6.0, H=12.0, wall_t=0.8, n_sections=4,
                 scale=100.0, label="沉井", layer="基础", tracker=None):
    """沉井剖面：井壁+隔墙+刃脚+各段标记。"""
    s=scale;ox,oy=_r(*origin);ds,hs,wt=D*s,H*s,wall_t*s
    # 外壁
    msp.add_lwpolyline([(ox,oy),(ox+ds,oy),(ox+ds,oy-hs),(ox,oy-hs)],close=True,dxfattribs={"layer":layer})
    # 内腔（线框）
    inner_ox=ox+wt;inner_d=ds-2*wt
    msp.add_lwpolyline([(inner_ox,oy),(inner_ox+inner_d,oy),(inner_ox+inner_d,oy-hs),(inner_ox,oy-hs)],close=True,dxfattribs={"layer":"细实线"})
    # 刃脚（底部三角形）
    msp.add_lwpolyline([(ox,oy-hs),(inner_ox,oy-hs),(ox+ds/2,oy-hs-1.5*s)],close=True,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(ox+ds,oy-hs),(inner_ox+inner_d,oy-hs),(ox+ds/2,oy-hs-1.5*s)],close=True,dxfattribs={"layer":layer})
    # 各段标记
    sh=hs/n_sections
    for si in range(n_sections):
        sy=oy-si*sh;msp.add_line((ox,oy-si*sh),(ox+ds,oy-si*sh),dxfattribs={"layer":"细实线","linetype":"DASHED"})
        t=msp.add_text(f"{si+1}段",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
        t.set_placement((ox-3*s,sy-sh/2),align=TextEntityAlignment.MIDDLE_RIGHT)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+ds/2,oy+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+ds+5*s,oy-hs-3*s)
