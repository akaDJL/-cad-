"""环评报告附图画图 v1.0（HJ 2.1—2016、HJ 19—2022、HJ 2.2—2018）。

基于 ezdxf 实现总平面布置图、敏感目标分布图、环境质量现状图、
事故应急池、固废/危废暂存间、排污口规范化、初期雨水收集等环评专用图。

纯 ezdxf，零新依赖。所有数据由 Agent 搜索后传入。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  敏感目标分布图
# ══════════════════════════════════════════════════════════

def draw_sensitive_target(msp, center, t_type: str,
                           label: str = "",
                           distance: float = 0,
                           scale: float = 100.0,
                           layer: str = "敏感目标",
                           tracker=None):
    """环评敏感目标符号。

    参数:
        t_type: "village"村庄 / "school"学校 / "hospital"医院 /
                "water"水源地 / "reserve"自然保护区 / "residential"居住区
        distance: 距项目距离 m
    """
    s = scale
    cx, cy = _r(*center)
    r = 5.0 * s

    if t_type == "village":
        # 村庄：星号
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            msp.add_line((cx, cy), (cx + r * 0.8 * math.cos(rad),
                                     cy + r * 0.8 * math.sin(rad)),
                         dxfattribs={"layer": "细实线"})
    elif t_type == "school":
        # 学校：方框 + 旗
        msp.add_lwpolyline(
            [(cx - r, cy - r), (cx + r, cy - r),
             (cx + r, cy + r), (cx - r, cy + r)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - r * 0.3, cy + r),
                     (cx - r * 0.3, cy + r + 3 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - r * 0.3, cy + r + 3 * s),
                     (cx + r * 0.5, cy + r + 1.5 * s),
                     dxfattribs={"layer": layer})
    elif t_type == "hospital":
        # 医院：方框 + 十字
        msp.add_lwpolyline(
            [(cx - r, cy - r), (cx + r, cy - r),
             (cx + r, cy + r), (cx - r, cy + r)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx, cy - r * 0.6), (cx, cy + r * 0.6),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - r * 0.6, cy), (cx + r * 0.6, cy),
                     dxfattribs={"layer": layer})
    elif t_type == "water":
        # 水源地：双圈
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        msp.add_circle((cx, cy), r * 0.6, dxfattribs={"layer": layer})
    elif t_type == "reserve":
        # 自然保护区：叶子形
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        msp.add_line((cx - r * 0.4, cy - r * 0.7),
                     (cx, cy + r * 0.5),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((cx + r * 0.4, cy - r * 0.7),
                     (cx, cy + r * 0.5),
                     dxfattribs={"layer": "细实线"})
    elif t_type == "residential":
        # 居住区：房屋形
        msp.add_line((cx - r, cy - r * 0.5),
                     (cx, cy + r),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy + r),
                     (cx + r, cy - r * 0.5),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - r, cy - r * 0.5),
                     (cx + r, cy - r * 0.5),
                     dxfattribs={"layer": layer})

    if label:
        txt_h = 2.5 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if distance > 0:
        t = msp.add_text(f"{distance:.0f}m", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((cx, cy - r - 4 * s - 2.5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + r, cy - r)


# ══════════════════════════════════════════════════════════
#  事故应急池
# ══════════════════════════════════════════════════════════

def draw_emergency_pond(msp, origin, volume: float = 500,
                          depth: float = 3.0,
                          scale: float = 100.0,
                          label: str = "",
                          params: dict = None,
                          layer: str = "应急",
                          tracker=None):
    """事故应急池平/剖面。

    参数:
        volume: 有效容积 m³
        depth: 池深 m
        params: {"length":"15m","width":"12m","material":"钢筋混凝土",
                  "lining":"HDPE防渗膜","pump":"Q=50m³/h",...}
    """
    s = scale
    ox, oy = _r(*origin)

    # 计算平面尺寸
    area = volume / depth
    ratio = 1.2
    l = math.sqrt(area * ratio) * s
    w = math.sqrt(area / ratio) * s

    # 池体轮廓（双线表示壁厚）
    wall = 1.5 * s
    msp.add_lwpolyline(
        [(ox, oy), (ox + l, oy), (ox + l, oy + w), (ox, oy + w)],
        close=True, dxfattribs={"layer": layer}
    )
    msp.add_lwpolyline(
        [(ox + wall, oy + wall), (ox + l - wall, oy + wall),
         (ox + l - wall, oy + w - wall), (ox + wall, oy + w - wall)],
        close=True, dxfattribs={"layer": "细实线"}
    )

    # 进水管（虚线箭头）
    in_x, in_y = ox + l * 0.2, oy + w
    msp.add_line((in_x, in_y), (in_x, in_y + 5 * s),
                 dxfattribs={"layer": layer})
    _tri_arrow(msp, (in_x, in_y), (0, -1), s, layer)

    # 溢流管
    ov_x, ov_y = ox + l * 0.7, oy + w
    msp.add_line((ov_x, ov_y), (ov_x, ov_y + 3 * s),
                 dxfattribs={"layer": "细实线"})

    # 液位标记
    msp.add_line((ox + l - wall, oy + wall + w * 0.1),
                 (ox + l - wall - 4 * s, oy + wall + w * 0.1),
                 dxfattribs={"layer": "细实线-尺寸"})

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + l / 2, oy + w + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + w + 8 * s + 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((ox + l / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + l, oy + w)


# ══════════════════════════════════════════════════════════
#  固废/危废暂存间
# ══════════════════════════════════════════════════════════

def draw_waste_storage(msp, origin, w_type: str = "hazardous",
                        width: float = 10.0, length: float = 8.0,
                        scale: float = 100.0,
                        label: str = "",
                        params: dict = None,
                        layer: str = "固废",
                        tracker=None):
    """固废/危废暂存间平面图。

    参数:
        w_type: "hazardous"危废 / "general"一般固废 / "recycling"回收
        width/length: 平面尺寸 m
        params: {"area":"80m²","floor":"防渗环氧地坪","leak_collection":"导流沟+集液井",
                  "ventilation":"防爆风机6次/h","fire":"干粉灭火器4具",...}
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    l = length * s

    # 外墙
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + l), (ox, oy + l)],
        close=True, dxfattribs={"layer": layer, "lineweight": 50}
    )

    # 围堰/导流沟（内缩）
    curb = 0.8 * s
    msp.add_lwpolyline(
        [(ox + curb, oy + curb), (ox + w - curb, oy + curb),
         (ox + w - curb, oy + l - curb), (ox + curb, oy + l - curb)],
        close=True, dxfattribs={"layer": "细实线", "linetype": "DASHED"}
    )

    # 分区标记
    msp.add_line((ox + w * 0.5, oy + curb),
                 (ox + w * 0.5, oy + l - curb),
                 dxfattribs={"layer": "细实线"})

    # 集液井（角落）
    pit_r = 2.0 * s
    pit_x, pit_y = ox + curb + pit_r, oy + curb + pit_r
    msp.add_circle((pit_x, pit_y), pit_r, dxfattribs={"layer": layer})
    t = msp.add_text("集液井", dxfattribs={
        "layer": "文字", "height": 2.0 * s, "style": "HZ",
    })
    t.set_placement((pit_x, pit_y - pit_r - 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 危废专用标识（骷髅/警告三角）
    if w_type == "hazardous":
        tri_r = 4.0 * s
        tri_x, tri_y = ox + w / 2, oy + l / 2
        tri = [(tri_x, tri_y + tri_r),
               (tri_x - tri_r, tri_y - tri_r * 0.5),
               (tri_x + tri_r, tri_y - tri_r * 0.5)]
        msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})
        t = msp.add_text("危废", dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ",
        })
        t.set_placement((tri_x, tri_y - tri_r * 0.5 - 3 * s),
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
#  排污口规范化
# ══════════════════════════════════════════════════════════

def draw_discharge_outlet(msp, center, o_type: str = "wastewater",
                           scale: float = 100.0,
                           label: str = "",
                           params: dict = None,
                           layer: str = "排污口",
                           tracker=None):
    """规范化排污口符号。

    参数:
        o_type: "wastewater"废水 / "stormwater"雨水 / "cooling"冷却水
        params: {"no":"WS-001","flow":"200m³/d","online":"COD/NH3-N/TP/流量",
                  "standard":"GB 8978-1996","sign":"标识牌+监控",...}
    """
    s = scale
    cx, cy = _r(*center)
    w, h = 12.0 * s, 8.0 * s

    # 矩形排口
    msp.add_lwpolyline(
        [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
         (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
        close=True, dxfattribs={"layer": layer}
    )

    # 流向箭头
    msp.add_line((cx - w / 2 - 5 * s, cy), (cx + w / 2 + 5 * s, cy),
                 dxfattribs={"layer": layer})
    _tri_arrow(msp, (cx + w / 2 + 5 * s, cy), (1, 0), s, layer)

    # 在线监测标记
    mon_y = cy + h / 2 + 3 * s
    msp.add_lwpolyline(
        [(cx - 4 * s, mon_y), (cx + 4 * s, mon_y),
         (cx + 4 * s, mon_y + 4 * s), (cx - 4 * s, mon_y + 4 * s)],
        close=True, dxfattribs={"layer": "细实线"})
    t = msp.add_text("在线监测", dxfattribs={
        "layer": "文字", "height": 2.0 * s, "style": "HZ",
    })
    t.set_placement((cx, mon_y + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - h / 2 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = cy - h / 2 - 4 * s - 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (cx + w / 2 + 5 * s, cy)


# ══════════════════════════════════════════════════════════
#  初期雨水收集池
# ══════════════════════════════════════════════════════════

def draw_initial_rainwater_tank(msp, origin, volume: float = 100,
                                 scale: float = 100.0,
                                 label: str = "",
                                 params: dict = None,
                                 layer: str = "雨水",
                                 tracker=None):
    """初期雨水收集池（含分流井）。

    参数:
        volume: 有效容积 m³
    """
    s = scale
    ox, oy = _r(*origin)

    l = math.sqrt(volume * 1.5) * s
    w = math.sqrt(volume / 1.5) * s

    # 收集池
    msp.add_lwpolyline(
        [(ox, oy), (ox + l, oy), (ox + l, oy + w), (ox, oy + w)],
        close=True, dxfattribs={"layer": layer}
    )

    # 分流井（左侧）
    well_w = 4.0 * s
    well_x = ox - well_w - 3 * s
    well_y = oy + w / 2
    msp.add_circle((well_x, well_y), well_w,
                   dxfattribs={"layer": layer})

    # 进水管 → 分流井
    msp.add_line((well_x - 8 * s, well_y), (well_x - well_w, well_y),
                 dxfattribs={"layer": layer})

    # 分流井 → 收集池（前15min）
    msp.add_line((well_x + well_w, well_y + well_w),
                 (ox, oy + w * 0.3),
                 dxfattribs={"layer": layer})
    _tri_arrow(msp, (ox, oy + w * 0.3), (1, -1), s, layer)

    # 分流井 → 溢流（15min后）
    msp.add_line((well_x + well_w, well_y - well_w),
                 (ox - 3 * s, oy - 4 * s),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})

    # 水泵
    pump_x, pump_y = ox + l / 2, oy - 3 * s
    msp.add_lwpolyline(
        [(pump_x - 2 * s, pump_y - 2 * s),
         (pump_x + 2 * s, pump_y - 2 * s),
         (pump_x + 2 * s, pump_y + 2 * s),
         (pump_x - 2 * s, pump_y + 2 * s)],
        close=True, dxfattribs={"layer": "设备"})
    t = msp.add_text("P", dxfattribs={
        "layer": "文字", "height": 2.0 * s, "style": "ENG",
    })
    t.set_placement((pump_x, pump_y),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + l / 2, oy + w + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + l, oy + w)


# ══════════════════════════════════════════════════════════
#  地下水监测井
# ══════════════════════════════════════════════════════════

def draw_monitoring_well(msp, center, well_id: str = "",
                          depth: float = 30,
                          scale: float = 100.0,
                          params: dict = None,
                          layer: str = "监测井",
                          tracker=None):
    """地下水监测井符号。

    参数:
        depth: 井深 m
        params: {"aquifer":"潜水层","screen":"10-25m","filter":"石英砂",
                  "seal":"膨润土","casing":"PVC-U",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 4.0 * s

    # 井口（双圆）
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    msp.add_circle((cx, cy), r * 0.6, dxfattribs={"layer": layer})

    # 剖面标记（竖线 + 滤管标记）
    msp.add_line((cx, cy), (cx, cy - r * 4), dxfattribs={"layer": layer})
    # 滤管段
    msp.add_line((cx - 2 * s, cy - r * 3.5), (cx + 2 * s, cy - r * 3.5),
                 dxfattribs={"layer": layer})
    msp.add_line((cx - 2 * s, cy - r * 2), (cx + 2 * s, cy - r * 2),
                 dxfattribs={"layer": layer})

    if well_id:
        t = msp.add_text(well_id, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((cx, cy + r + 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = cy + r + 3 * s + 2.5 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.3 * s

    return (cx + r, cy)


# ─── 辅助 ──────────────────────────────────────────────

def _tri_arrow(msp, tip, direction, scale, layer):
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
#  v1.5+ 环评增补：评价范围/监测布点/规划符合性
# ══════════════════════════════════════════════════════════

def draw_eia_scope(msp, origin, width=200.0, height=150.0,
                    core_r=500, eval_r=2500, scale=100.0, label="",
                    layer="细实线", tracker=None):
    """评价范围图（同心圆模式）。

    参数:
        width/height: 图幅 m
        core_r: 核心区半径 m（项目区）
        eval_r: 评价范围半径 m
    """
    s = scale; ox, oy = _r(*origin)
    cx, cy = ox + width * s / 2, oy + height * s / 2

    msp.add_lwpolyline([(ox, oy), (ox + width * s, oy),
                         (ox + width * s, oy + height * s), (ox, oy + height * s)],
                       close=True, dxfattribs={"layer": "细实线"})

    # 评价范围（同心圆）
    msp.add_circle((cx, cy), eval_r * s / 10, dxfattribs={
        "layer": "细实线", "linetype": "DASHED"})
    msp.add_circle((cx, cy), core_r * s / 10, dxfattribs={
        "layer": layer})

    # 标注
    t = msp.add_text(f"评价范围 R={eval_r}m", dxfattribs={
        "layer": "文字", "height": 3 * s, "style": "HZ"})
    t.set_placement((cx + eval_r * s / 10 + 5 * s, cy),
                    align=TextEntityAlignment.MIDDLE_LEFT)
    t2 = msp.add_text(f"项目区", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t2.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    # 风向玫瑰图（简画）
    wind_x = ox + 15 * s
    wind_y = oy + 15 * s
    wind_r = 10 * s
    for ang, freq in [(0, 0.8), (45, 0.6), (90, 0.4), (135, 0.5),
                        (180, 1.0), (225, 0.7), (270, 0.3), (315, 0.4)]:
        import math
        rad = math.radians(ang)
        ex = wind_x + wind_r * freq * math.cos(rad)
        ey = wind_y + wind_r * freq * math.sin(rad)
        msp.add_line((wind_x, wind_y), (ex, ey), dxfattribs={"layer": "细实线"})
    t3 = msp.add_text("N", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t3.set_placement((wind_x, wind_y + wind_r + 3 * s),
                     align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((cx, oy + height * s + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_monitoring_layout(msp, origin, width=200.0, height=150.0,
                            points=None, scale=100.0, label="", layer="细实线",
                            tracker=None):
    """监测布点图。

    参数:
        points: [{"x":30,"y":40,"type":"大气","code":"A1","param":"PM2.5"}, ...]
    """
    s = scale; ox, oy = _r(*origin)

    msp.add_lwpolyline([(ox, oy), (ox + width * s, oy),
                         (ox + width * s, oy + height * s), (ox, oy + height * s)],
                       close=True, dxfattribs={"layer": "细实线"})

    if points:
        for pt in points:
            px = ox + pt.get("x", 0) * s
            py = oy + pt.get("y", 0) * s
            ptype = pt.get("type", "监测点")
            pcode = pt.get("code", "")
            pparam = pt.get("param", "")

            # 点位标记（三角+圆）
            msp.add_circle((px, py), 3 * s, dxfattribs={"layer": layer})
            _tri(msp, (px, py + 3 * s), (0, -1), s, layer)

            t = msp.add_text(f"{pcode}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((px, py + 6 * s), align=TextEntityAlignment.MIDDLE_CENTER)

            t2 = msp.add_text(f"{ptype}({pparam})", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "HZ"})
            t2.set_placement((px, py + 9 * s), align=TextEntityAlignment.MIDDLE_CENTER)

    # 图例
    legend_x = ox + width * s + 5 * s
    legend_y = oy + height * s
    for i, (ltype, desc) in enumerate([("大气", "PM2.5/PM10/SO2/NOx"),
                                        ("地表水", "COD/NH3-N/TP"),
                                        ("噪声", "Leq dB(A)"),
                                        ("土壤", "重金属/pH")]):
        ly = legend_y - i * 8 * s
        msp.add_circle((legend_x, ly), 2 * s, dxfattribs={"layer": "细实线"})
        t = msp.add_text(f"{ltype}: {desc}", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((legend_x + 4 * s, ly), align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((ox + width * s / 2, oy + height * s + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_planning_compliance(msp, origin, width=200.0, height=150.0,
                              zones=None, scale=100.0, label="", layer="细实线",
                              tracker=None):
    """规划符合性分析图。

    参数:
        zones: [{"x":10,"y":10,"w":40,"h":30,"type":"居住","match":"符合"},...]
    """
    s = scale; ox, oy = _r(*origin)

    msp.add_lwpolyline([(ox, oy), (ox + width * s, oy),
                         (ox + width * s, oy + height * s), (ox, oy + height * s)],
                       close=True, dxfattribs={"layer": "细实线"})

    if zones:
        for z in zones:
            zx = ox + z.get("x", 0) * s
            zy = oy + z.get("y", 0) * s
            zw = z.get("w", 30) * s
            zh = z.get("h", 20) * s
            ztype = z.get("type", "")
            zmatch = z.get("match", "符合")

            msp.add_lwpolyline([(zx, zy), (zx + zw, zy), (zx + zw, zy + zh),
                                (zx, zy + zh)], close=True,
                               dxfattribs={"layer": layer})

            t = msp.add_text(f"规划{ztype}用地\n{zmatch}", dxfattribs={
                "layer": "文字", "height": 2.5 * s, "style": "HZ"})
            t.set_placement((zx + zw / 2, zy + zh / 2),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((ox + width * s / 2, oy + height * s + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
