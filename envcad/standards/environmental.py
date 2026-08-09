"""环境工程与环评制图 v1.0（HJ 2.1—2016、HJ 19—2022、GB 50014）。

基于 ezdxf 实现监测点位图、污染源分布、污水处理流程、废气处理、
噪声控制、绿化布置、雨污分流等环境工程与环评常用图纸。

所有监测数据、排放标准、处理效率等由 Agent 搜索后显式传入。
纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  监测点位图
# ══════════════════════════════════════════════════════════

def draw_monitoring_point(msp, center, point_id: str,
                           m_type: str = "air",
                           scale: float = 100.0,
                           params: dict = None,
                           layer: str = "监测点",
                           tracker=None):
    """环境监测点位符号。

    参数:
        m_type: "air"大气 / "water"地表水 / "groundwater"地下水 /
                "soil"土壤 / "noise"噪声 / "stack"排气筒
        params: {"pollutant":"SO2","frequency":"1次/季","standard":"GB 3095",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 5.0 * s

    if m_type == "air":
        # 大气：三角 + 圆
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        tri = [(cx, cy + r), (cx - r * 0.7, cy - r * 0.3),
               (cx + r * 0.7, cy - r * 0.3)]
        msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})
    elif m_type == "water":
        # 地表水：菱形 + 波浪
        msp.add_lwpolyline(
            [(cx, cy + r), (cx + r, cy), (cx, cy - r), (cx - r, cy)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - 3 * s, cy - 2 * s), (cx - 1 * s, cy - 2 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + 1 * s, cy - 2 * s), (cx + 3 * s, cy - 2 * s),
                     dxfattribs={"layer": layer})
    elif m_type == "groundwater":
        # 地下水：圆 + 向下箭头
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        msp.add_line((cx, cy - r), (cx, cy - r - 4 * s),
                     dxfattribs={"layer": layer})
        _tri_arrow(msp, (cx, cy - r - 4 * s), (0, -1), s, layer)
    elif m_type == "soil":
        # 土壤：方框 + 斜线
        msp.add_lwpolyline(
            [(cx - r, cy - r), (cx + r, cy - r),
             (cx + r, cy + r), (cx - r, cy + r)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - r, cy - r), (cx + r, cy + r),
                     dxfattribs={"layer": layer})
    elif m_type == "noise":
        # 噪声：喇叭形
        pts = [(cx - r, cy + r), (cx - r * 0.3, cy + r),
               (cx + r, cy + r * 0.3), (cx + r, cy - r * 0.3),
               (cx - r * 0.3, cy - r), (cx - r, cy - r)]
        msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": layer})
        # 声波弧线
        for i in range(3):
            arc_r = r * (0.6 + i * 0.3)
            msp.add_arc((cx + r, cy), radius=arc_r,
                         start_angle=270, end_angle=90,
                         dxfattribs={"layer": "细实线"})
    elif m_type == "stack":
        # 排气筒：烟囱形
        msp.add_lwpolyline(
            [(cx - 2 * s, cy - r), (cx + 2 * s, cy - r),
             (cx + 3 * s, cy + r), (cx - 3 * s, cy + r)],
            close=True, dxfattribs={"layer": layer})
        # 烟气
        for i in range(2):
            sx = cx + (i - 0.5) * 2 * s
            msp.add_line((sx, cy + r), (sx + s, cy + r + 3 * s),
                         dxfattribs={"layer": "细实线"})

    # 编号
    txt_h = 2.5 * s
    t = msp.add_text(point_id, dxfattribs={
        "layer": "文字-标题", "height": txt_h, "style": "ENG",
    })
    t.set_placement((cx, cy - r - 4 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 参数
    if params:
        cy_p = cy - r - 4 * s - txt_h * 1.3
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.2 * s

    return (cx + r, cy - r)


def _tri_arrow(msp, tip, direction, scale, layer):
    """三角箭头。"""
    tx, ty = tip
    dx, dy = direction
    h = 3.0 * scale
    w = 1.5 * scale
    px, py = -dy * w, dx * w
    pts = [(tx, ty), (tx - h * dx + px, ty - h * dy + py),
           (tx - h * dx - px, ty - h * dy - py)]
    try:
        msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


# ══════════════════════════════════════════════════════════
#  污染源分布图
# ══════════════════════════════════════════════════════════

def draw_pollution_source(msp, center, ps_type: str,
                           scale: float = 100.0,
                           label: str = "",
                           params: dict = None,
                           layer: str = "污染源",
                           tracker=None):
    """污染源分布符号。

    参数:
        ps_type: "stack"排气筒 / "wastewater"废水排口 /
                 "solid_waste"固废 / "fugitive"无组织 / "noise"噪声源
        params: {"height":"60m","diameter":"2m","flow":"50000Nm³/h",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 6.0 * s

    if ps_type == "stack":
        # 排气筒：烟囱
        msp.add_lwpolyline(
            [(cx - 3 * s, cy - r), (cx + 3 * s, cy - r),
             (cx + 3 * s, cy + r), (cx - 3 * s, cy + r)],
            close=True, dxfattribs={"layer": layer})
        # 顶部
        msp.add_line((cx - 3.5 * s, cy + r), (cx + 3.5 * s, cy + r),
                     dxfattribs={"layer": layer})
    elif ps_type == "wastewater":
        # 废水排口：矩形 + 波浪
        msp.add_lwpolyline(
            [(cx - r, cy - r * 0.6), (cx + r, cy - r * 0.6),
             (cx + r, cy + r * 0.6), (cx - r, cy + r * 0.6)],
            close=True, dxfattribs={"layer": layer})
        for i in range(2):
            wy = cy + (i - 0.5) * 2 * s
            msp.add_line((cx - r * 0.7, wy), (cx + r * 0.7, wy),
                         dxfattribs={"layer": "细实线"})
    elif ps_type == "solid_waste":
        # 固废：双框
        msp.add_lwpolyline(
            [(cx - r, cy - r), (cx + r, cy - r),
             (cx + r, cy + r), (cx - r, cy + r)],
            close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline(
            [(cx - r * 0.6, cy - r * 0.6),
             (cx + r * 0.6, cy - r * 0.6),
             (cx + r * 0.6, cy + r * 0.6),
             (cx - r * 0.6, cy + r * 0.6)],
            close=True, dxfattribs={"layer": "细实线"})
    elif ps_type == "fugitive":
        # 无组织：虚线框
        msp.add_lwpolyline(
            [(cx - r, cy - r), (cx + r, cy - r),
             (cx + r, cy + r), (cx - r, cy + r)],
            close=True, dxfattribs={"layer": layer, "linetype": "DASHED"})

    if label:
        txt_h = 2.5 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - r - 4 * s - 2.5 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.2 * s

    return (cx + r, cy - r)


# ══════════════════════════════════════════════════════════
#  污水处理工艺流程图
# ══════════════════════════════════════════════════════════

def draw_process_box(msp, center, width: float, height: float,
                      label: str = "",
                      params: dict = None,
                      scale: float = 100.0,
                      layer: str = "工艺",
                      tracker=None):
    """污水处理工艺单元框。

    参数:
        width/height: 尺寸（图纸 mm）
        label: 单元名称（如"调节池"、"MBR池"）
        params: {"volume":"500m³","HRT":"8h","MLSS":"8000mg/L",...}
    """
    s = scale
    cx, cy = _r(*center)
    w = width * s
    h = height * s
    x0, y0 = cx - w / 2, cy - h / 2

    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True, dxfattribs={"layer": layer}
    )

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy + h * 0.15),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - h * 0.3
        txt_h = 1.8 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": txt_h, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.3 * s

    if tracker:
        tracker.register(x0, y0, x0 + w, y0 + h, margin=10)

    return (x0 + w, y0 + h)


def draw_flow_arrow(msp, start, end, scale: float = 100.0,
                     label: str = "",
                     layer: str = "工艺",
                     tracker=None):
    """工艺流程箭头。"""
    sx, sy = _r(*start)
    ex, ey = _r(*end)

    msp.add_line((sx, sy), (ex, ey), dxfattribs={"layer": layer})

    # 箭头
    dx, dy = ex - sx, ey - sy
    lg = math.hypot(dx, dy)
    if lg > 0:
        ux, uy = dx / lg, dy / lg
        h = 4.0 * scale
        w = 2.0 * scale
        px, py = -uy * w, ux * w
        tri = [(ex, ey), (ex - h * ux + px, ey - h * uy + py),
               (ex - h * ux - px, ey - h * uy - py)]
        try:
            msp.add_solid(tri + [tri[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})

    if label:
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        txt_h = 2.0 * scale
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((mx + 3 * scale, my + 3 * scale),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  废气处理系统
# ══════════════════════════════════════════════════════════

def draw_scrubber(msp, center, s_type: str = "spray",
                   scale: float = 100.0,
                   label: str = "",
                   params: dict = None,
                   layer: str = "设备",
                   tracker=None):
    """废气处理设备符号。

    参数:
        s_type: "spray"喷淋塔 / "baghouse"布袋除尘 / "esp"静电除尘 /
                "activated_carbon"活性炭 / "rto"蓄热氧化 / "biofilter"生物滤池
    """
    s = scale
    cx, cy = _r(*center)
    w, h = 12.0 * s, 18.0 * s

    if s_type == "spray":
        # 喷淋塔：圆筒 + 喷嘴
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        # 内部喷淋
        for i in range(3):
            ny = cy + h * 0.2 * i
            msp.add_line((cx - 3 * s, ny), (cx + 3 * s, ny),
                         dxfattribs={"layer": "细实线"})
        msp.add_line((cx, cy + h / 2), (cx, cy + h / 2 + 4 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy - h / 2), (cx, cy - h / 2 - 4 * s),
                     dxfattribs={"layer": layer})
    elif s_type == "baghouse":
        # 布袋除尘：矩形 + 内部竖线
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        for i in range(4):
            bx = cx + (i - 1.5) * 2.5 * s
            msp.add_line((bx, cy - h * 0.3), (bx, cy + h * 0.3),
                         dxfattribs={"layer": "细实线"})
    elif s_type == "activated_carbon":
        # 活性炭：矩形 + X
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - w / 2, cy - h / 2), (cx + w / 2, cy + h / 2),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((cx + w / 2, cy - h / 2), (cx - w / 2, cy + h / 2),
                     dxfattribs={"layer": "细实线"})
    elif s_type == "rto":
        # RTO：矩形 + 火焰符号
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        # 火焰
        flame = [(cx, cy + h * 0.2), (cx - 2 * s, cy - h * 0.1),
                 (cx + 2 * s, cy - h * 0.1)]
        msp.add_lwpolyline(flame, close=True,
                           dxfattribs={"layer": layer})

    if label:
        txt_h = 2.5 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - h / 2 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + w / 2, cy - h / 2)


# ══════════════════════════════════════════════════════════
#  噪声控制 / 隔音屏障
# ══════════════════════════════════════════════════════════

def draw_noise_barrier(msp, start, end, height: float = 3.0,
                        b_type: str = "wall",
                        scale: float = 100.0,
                        label: str = "",
                        layer: str = "噪声控制",
                        tracker=None):
    """隔音屏障/声屏障。

    参数:
        b_type: "wall"直立式 / "bent"折臂式 / "enclosure"全封闭
    """
    s = scale
    sx, sy = _r(*start)
    ex, ey = _r(*end)
    h = height * s

    dx, dy = ex - sx, ey - sy
    lg = math.hypot(dx, dy)
    if lg == 0:
        return (ex, ey)
    ux, uy = dx / lg, dy / lg
    px, py = -uy, ux

    if b_type == "wall":
        # 直立式：粗线 + 基础
        for i in range(3):
            off = (i - 1) * 0.5 * s
            msp.add_line((sx + px * off, sy + py * off),
                         (sx + px * off, sy + py * off + uy * h),
                         dxfattribs={"layer": layer})
        msp.add_line((sx - px * 2 * s, sy - py * 2 * s),
                     (sx + px * 2 * s, sy + py * 2 * s),
                     dxfattribs={"layer": layer})
    elif b_type == "bent":
        # 折臂式
        msp.add_line((sx, sy), (sx, sy + h * uy),
                     dxfattribs={"layer": layer})
        bend_pt = (sx + h * ux * 0.5, sy + h * uy)
        msp.add_line((sx, sy + h * uy), bend_pt,
                     dxfattribs={"layer": layer})
    elif b_type == "enclosure":
        # 全封闭：弧形
        msp.add_arc((sx, sy), radius=h * 0.5, start_angle=0, end_angle=180,
                     dxfattribs={"layer": layer})

    if label:
        txt_h = 2.5 * s
        mx = (sx + ex) / 2
        my = (sy + ey) / 2 + h + 3 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((mx, my), align=TextEntityAlignment.MIDDLE_CENTER)

    return (ex, ey + h)


# ══════════════════════════════════════════════════════════
#  绿化 / 生态修复
# ══════════════════════════════════════════════════════════

def draw_tree_symbol(msp, center, tree_type: str = "broadleaf",
                      scale: float = 100.0,
                      layer: str = "绿化",
                      tracker=None):
    """绿化/树木符号。

    参数:
        tree_type: "broadleaf"阔叶 / "conifer"针叶 / "shrub"灌木 /
                   "lawn"草坪 / "wetland"湿地植物
    """
    s = scale
    cx, cy = _r(*center)
    r = 5.0 * s

    if tree_type == "broadleaf":
        # 阔叶树：圆 + 不规则边
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        for i in range(6):
            ang = i * 60
            rx = cx + r * 1.2 * math.cos(math.radians(ang))
            ry = cy + r * 1.2 * math.sin(math.radians(ang))
            msp.add_line((cx, cy), (rx, ry),
                         dxfattribs={"layer": "细实线"})
    elif tree_type == "conifer":
        # 针叶树：三角尖顶
        for i in range(3):
            ty = cy + r * (0.5 + i * 0.5)
            hh = r * (1.0 - i * 0.3)
            tw = r * (0.2 + i * 0.15)
            msp.add_line((cx - tw, ty), (cx + tw, ty),
                         dxfattribs={"layer": layer})
        msp.add_line((cx, cy - r * 1.2), (cx, cy + r * 1.5),
                     dxfattribs={"layer": layer})
    elif tree_type == "shrub":
        # 灌木：多个小圆
        for dx, dy in [(-2 * s, 0), (2 * s, 0), (0, 1.5 * s)]:
            msp.add_circle((cx + dx, cy + dy), 2.5 * s,
                           dxfattribs={"layer": layer})
    elif tree_type == "lawn":
        # 草坪：波浪线填充（简化：点阵）
        for i in range(5):
            for j in range(3):
                px = cx + (i - 2) * 2 * s
                py = cy + (j - 1) * 2 * s
                msp.add_line((px, py), (px + 0.5 * s, py),
                             dxfattribs={"layer": "细实线"})
    elif tree_type == "wetland":
        # 湿地植物：竖线 + 顶部短横
        for dx in [-2 * s, 0, 2 * s]:
            gx = cx + dx
            msp.add_line((gx, cy - r), (gx, cy + r * 0.7),
                         dxfattribs={"layer": layer})
            msp.add_line((gx - 1.5 * s, cy + r * 0.5),
                         (gx + 1.5 * s, cy + r * 0.5),
                         dxfattribs={"layer": layer})

    return (cx + r, cy - r)


def draw_green_belt(msp, start, end, width: float = 2.0,
                     scale: float = 100.0,
                     label: str = "",
                     layer: str = "绿化带",
                     tracker=None):
    """绿化带/生态缓冲带。"""
    s = scale
    sx, sy = _r(*start)
    ex, ey = _r(*end)
    w = width * s

    dx, dy = ex - sx, ey - sy
    lg = math.hypot(dx, dy)
    if lg == 0:
        return (ex, ey)
    px, py = -dy / lg * w, dx / lg * w

    # 双线边界
    msp.add_line((sx + px, sy + py), (ex + px, ey + py),
                 dxfattribs={"layer": layer})
    msp.add_line((sx - px, sy - py), (ex - px, ey - py),
                 dxfattribs={"layer": layer})
    # 填充图案（简化：斜线）
    for i in range(int(lg / (3 * s))):
        frac = (i + 0.5) / int(lg / (3 * s) + 1)
        gx = sx + dx * frac
        gy = sy + dy * frac
        msp.add_line((gx - px * 0.6, gy - py * 0.6),
                     (gx + px * 0.6, gy + py * 0.6),
                     dxfattribs={"layer": "细实线"})

    if label:
        mx, my = (sx + ex) / 2, (sy + ey) / 2 + w + 2 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "HZ",
        })
        t.set_placement((mx, my), align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  雨污分流系统
# ══════════════════════════════════════════════════════════

def draw_catchment(msp, center, area_label: str = "",
                    width: float = 30.0, height: float = 20.0,
                    scale: float = 100.0,
                    params: dict = None,
                    layer: str = "汇水区",
                    tracker=None):
    """汇水区/雨污分区分块。

    参数:
        params: {"area":"2.5ha","runoff_coef":"0.65","pipe":"DN400",...}
    """
    s = scale
    cx, cy = _r(*center)
    w = width * s
    h = height * s
    x0, y0 = cx - w / 2, cy - h / 2

    # 虚线框
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True, dxfattribs={"layer": layer, "linetype": "DASHED"}
    )

    # 流向箭头（右下角）
    arr_x = x0 + w * 0.8
    arr_y = y0 + h * 0.15
    msp.add_line((x0 + w * 0.3, arr_y), (arr_x, arr_y),
                 dxfattribs={"layer": layer})
    _tri_arrow(msp, (arr_x, arr_y), (1, 0), s, layer)

    if area_label:
        t = msp.add_text(area_label, dxfattribs={
            "layer": "文字-标题", "height": 3.0 * s, "style": "HZ",
        })
        t.set_placement((cx, cy + h * 0.25),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - h * 0.15
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.5 * s

    return (x0 + w, y0)


def draw_noise_monitoring(msp, origin, points=8, radius=50.0, scale=100.0,
                          label="噪声监测布点", tracker=None):
    """噪声监测点平面布置图。环形+放射状监测点位。"""
    s=scale;ox,oy=_r(*origin);r=radius*s
    import math
    cx,cy=ox,oy
    msp.add_circle((cx,cy),r,dxfattribs={"layer":"细实线","linetype":"DASHED"})
    for i in range(points):
        ang=i*2*math.pi/points
        px,py=cx+r*math.cos(ang),cy+r*math.sin(ang)
        msp.add_line((cx,cy),(px,py),dxfattribs={"layer":"细实线"})
        msp.add_circle((px,py),2*s,dxfattribs={"layer":"粗实线"})
        t=msp.add_text(str(i+1),dxfattribs={"layer":"文字","height":2*s,"style":"ENG"})
        t.set_placement((px+3*s,py+2*s),align=TextEntityAlignment.MIDDLE_LEFT)
    msp.add_circle((cx,cy),2.5*s,dxfattribs={"layer":"粗实线"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((cx,cy+r+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx+r+8*s,cy-r-8*s)
