"""水处理工艺详图 v1.0（CJJ 40—2011、GB 50014、HJ 2015）。

基于 ezdxf 实现曝气系统、污泥脱水、加药系统、格栅/沉砂池详图、
MBR/反渗透、消毒系统、沉淀池内部结构等水处理专用图纸。

所有设计参数由 Agent 搜索后显式传入。
纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  曝气系统
# ══════════════════════════════════════════════════════════

def draw_aeration_tank(msp, origin, width: float, length: float,
                        depth: float = 5.0,
                        a_type: str = "diffused",
                        scale: float = 100.0,
                        label: str = "",
                        params: dict = None,
                        layer: str = "池体",
                        tracker=None):
    """曝气池平/剖面。

    参数:
        a_type: "diffused"微孔曝气 / "surface"表曝机 / "jet"射流 /
                "brush"转刷 / "disc"转盘
        params: {"volume":"2000m³","MLSS":"4000mg/L","DO":"2mg/L",
                  "SRT":"15d","blower":"Q=30m³/min",...}
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    l = length * s
    d = depth * s

    # 池体轮廓
    msp.add_lwpolyline(
        [(ox, oy), (ox + l, oy), (ox + l, oy + w), (ox, oy + w)],
        close=True, dxfattribs={"layer": layer}
    )

    # 曝气装置
    if a_type == "diffused":
        # 微孔曝气：沿池长均匀布点
        n_headers = int(l / (15 * s)) + 1
        for i in range(n_headers):
            bx = ox + l * (i + 0.5) / n_headers
            # 曝气管线（横线）
            msp.add_line((bx, oy + 2 * s), (bx, oy + w - 2 * s),
                         dxfattribs={"layer": "细实线"})
        # 供气主管
        msp.add_line((ox, oy + w / 2), (ox + l, oy + w / 2),
                     dxfattribs={"layer": layer, "lineweight": 40})
    elif a_type == "surface":
        # 表曝机：圆 + 十字
        ax, ay = ox + l * 0.3, oy + w / 2
        r = 5.0 * s
        msp.add_circle((ax, ay), r, dxfattribs={"layer": layer})
        msp.add_line((ax - r, ay), (ax + r, ay),
                     dxfattribs={"layer": layer})
        msp.add_line((ax, ay - r), (ax, ay + r),
                     dxfattribs={"layer": layer})
    elif a_type == "brush":
        # 转刷：水平长条
        msp.add_lwpolyline(
            [(ox + l * 0.3, oy + 1 * s),
             (ox + l * 0.7, oy + 1 * s),
             (ox + l * 0.7, oy + w - 1 * s),
             (ox + l * 0.3, oy + w - 1 * s)],
            close=True, dxfattribs={"layer": layer, "linetype": "DASHED"})

    # 标注
    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + l / 2, oy + w + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + w + 4 * s + 3 * s
        txt_h = 2.0 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": txt_h, "style": "ENG",
            })
            t.set_placement((ox + l / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + l, oy + w)


# ══════════════════════════════════════════════════════════
#  污泥处理
# ══════════════════════════════════════════════════════════

def draw_sludge_system(msp, origin, units: List[dict],
                        scale: float = 100.0,
                        layer: str = "设备",
                        tracker=None):
    """污泥处理系统流程图。

    units: [{"type":"thickener","label":"浓缩池","params":{...}},
            {"type":"digester","label":"消化池","params":{...}},
            {"type":"dewatering","label":"脱水机","params":{...}},
            {"type":"dryer","label":"干化","params":{...}},
            {"type":"incinerator","label":"焚烧","params":{...}}]
    """
    s = scale
    ox, oy = _r(*origin)
    spacing = 30.0 * s
    cur_x = ox

    for unit in units:
        utype = unit.get("type", "")
        ulabel = unit.get("label", "")
        uparams = unit.get("params", {})

        if utype == "thickener":
            # 浓缩池：圆形 + 中心竖管
            r = 8.0 * s
            msp.add_circle((cur_x, oy), r, dxfattribs={"layer": layer})
            msp.add_line((cur_x, oy - r * 0.3), (cur_x, oy + r * 0.3),
                         dxfattribs={"layer": layer})
        elif utype == "digester":
            # 消化池：椭圆 + 搅拌
            msp.add_ellipse((cur_x, oy), radius_x=6 * s, radius_y=10 * s,
                             dxfattribs={"layer": layer})
            msp.add_line((cur_x, oy + 8 * s), (cur_x - 3 * s, oy + 6 * s),
                         dxfattribs={"layer": "细实线"})
        elif utype == "dewatering":
            # 脱水机：矩形 + 滤液出口
            w, h = 12 * s, 8 * s
            msp.add_lwpolyline(
                [(cur_x - w / 2, oy - h / 2), (cur_x + w / 2, oy - h / 2),
                 (cur_x + w / 2, oy + h / 2), (cur_x - w / 2, oy + h / 2)],
                close=True, dxfattribs={"layer": layer})
            msp.add_line((cur_x, oy - h / 2),
                         (cur_x, oy - h / 2 - 4 * s),
                         dxfattribs={"layer": layer})
            t = msp.add_text("滤液", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "HZ",
            })
            t.set_placement((cur_x, oy - h / 2 - 5 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)
        elif utype == "dryer":
            # 干化：矩形 + 热源标记
            w, h = 12 * s, 8 * s
            msp.add_lwpolyline(
                [(cur_x - w / 2, oy - h / 2), (cur_x + w / 2, oy - h / 2),
                 (cur_x + w / 2, oy + h / 2), (cur_x - w / 2, oy + h / 2)],
                close=True, dxfattribs={"layer": layer})
            # 热源符号
            msp.add_line((cur_x - 3 * s, oy + h / 2 + 3 * s),
                         (cur_x, oy + h / 2), dxfattribs={"layer": layer})
            msp.add_line((cur_x + 3 * s, oy + h / 2 + 3 * s),
                         (cur_x, oy + h / 2), dxfattribs={"layer": layer})
            t = msp.add_text("Q", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG",
            })
            t.set_placement((cur_x, oy + h / 2 + 5 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

        # 标签
        txt_h = 2.5 * s
        t = msp.add_text(ulabel, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cur_x, oy - 10 * s - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        # 参数
        if uparams:
            py = oy - 10 * s - 4 * s - 2.5 * s
            txt_h2 = 1.8 * s
            for key, val in uparams.items():
                t = msp.add_text(f"{key}:{val}", dxfattribs={
                    "layer": "文字", "height": txt_h2, "style": "ENG",
                })
                t.set_placement((cur_x, py),
                                align=TextEntityAlignment.MIDDLE_CENTER)
                py -= 2.3 * s

        # 箭头连接下一个
        next_x = cur_x + spacing
        if unit != units[-1]:
            msp.add_line((cur_x + 10 * s, oy),
                         (next_x - 10 * s, oy),
                         dxfattribs={"layer": "工艺"})
            _arrow_head(msp, (next_x - 10 * s, oy), (1, 0), s, "工艺")

        cur_x = next_x

    return (cur_x, oy)


# ══════════════════════════════════════════════════════════
#  加药系统
# ══════════════════════════════════════════════════════════

def draw_chemical_dosing(msp, origin, dosing_points: List[dict],
                          scale: float = 100.0,
                          layer: str = "设备",
                          tracker=None):
    """加药系统图。

    dosing_points: [{"chemical":"PAC","dose":"30mg/L","tank":"1m³",
                      "pump":"Q=50L/h","point":"混合池"}, ...]
    """
    s = scale
    ox, oy = _r(*origin)
    cur_x = ox

    for dp in dosing_points:
        chem = dp.get("chemical", "")
        w, h = 16.0 * s, 20.0 * s
        cx = cur_x

        # 储药罐（上方）
        tank_r = 4.0 * s
        tank_y = oy + h * 0.6
        msp.add_circle((cx, tank_y), tank_r, dxfattribs={"layer": layer})
        msp.add_line((cx - tank_r, tank_y), (cx + tank_r, tank_y),
                     dxfattribs={"layer": "细实线"})

        # 计量泵（中间）
        pump_y = oy + h * 0.2
        msp.add_lwpolyline(
            [(cx - 3 * s, pump_y - 2 * s),
             (cx + 3 * s, pump_y - 2 * s),
             (cx + 3 * s, pump_y + 2 * s),
             (cx - 3 * s, pump_y + 2 * s)],
            close=True, dxfattribs={"layer": layer})
        t = msp.add_text("P", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((cx, pump_y), align=TextEntityAlignment.MIDDLE_CENTER)

        # 管道
        msp.add_line((cx, tank_y - tank_r), (cx, pump_y + 2 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, pump_y - 2 * s), (cx, oy - h * 0.3),
                     dxfattribs={"layer": layer})

        # 投加点（箭头）
        _arrow_head(msp, (cx, oy - h * 0.3), (0, -1), s, layer)

        # 标签
        txt_h = 2.5 * s
        t = msp.add_text(chem, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, tank_y + tank_r + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        # 参数
        py = oy - h * 0.3 - 4 * s
        txt_h2 = 1.8 * s
        for key in ["dose", "tank", "pump"]:
            val = dp.get(key, "")
            if val:
                t = msp.add_text(f"{key}:{val}", dxfattribs={
                    "layer": "文字", "height": txt_h2, "style": "ENG",
                })
                t.set_placement((cx, py),
                                align=TextEntityAlignment.MIDDLE_CENTER)
                py -= 2.3 * s

        cur_x += 25.0 * s

    return (cur_x, oy)


# ══════════════════════════════════════════════════════════
#  格栅 / 沉砂池详图
# ══════════════════════════════════════════════════════════

def draw_bar_screen(msp, origin, width: float, depth: float,
                     bar_spacing: float = 20.0,
                     scale: float = 100.0,
                     label: str = "",
                     params: dict = None,
                     layer: str = "设备",
                     tracker=None):
    """格栅详图。

    参数:
        bar_spacing: 栅条间距 mm
        params: {"width":"1.5m","depth":"1.2m","angle":"60°",
                  "head_loss":"0.15m","cleaning":"机械",...}
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    d = depth * s
    bs = bar_spacing * s

    # 渠道断面
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)],
        close=True, dxfattribs={"layer": layer}
    )

    # 栅条（竖线或斜线）
    n_bars = int(w / bs)
    if n_bars > 0:
        actual_sp = w / n_bars
        for i in range(n_bars + 1):
            bx = ox + actual_sp * i
            # 斜栅条（60°）
            offset = (i / n_bars) * d * 0.3
            msp.add_line((bx, oy), (bx + offset, oy + d),
                         dxfattribs={"layer": layer})

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + d + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + d + 4 * s + 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG",
            })
            t.set_placement((ox + w / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + w, oy + d)


# ══════════════════════════════════════════════════════════
#  MBR / 反渗透
# ══════════════════════════════════════════════════════════

def draw_membrane_system(msp, origin, m_type: str = "mbr",
                          modules: int = 4,
                          scale: float = 100.0,
                          label: str = "",
                          params: dict = None,
                          layer: str = "设备",
                          tracker=None):
    """膜系统布置图。

    参数:
        m_type: "mbr"膜生物反应器 / "ro"反渗透 / "uf"超滤 / "nf"纳滤
        modules: 膜组件数量
        params: {"flux":"15LMH","area":"1500m²","pore":"0.04μm",...}
    """
    s = scale
    ox, oy = _r(*origin)

    mod_w = 8.0 * s
    mod_h = 14.0 * s
    gap = 2.0 * s

    for i in range(modules):
        mx = ox + (mod_w + gap) * i
        my = oy

        # 膜组件矩形
        msp.add_lwpolyline(
            [(mx, my), (mx + mod_w, my),
             (mx + mod_w, my + mod_h), (mx, my + mod_h)],
            close=True, dxfattribs={"layer": layer}
        )

        # 内部膜丝标记（竖线）
        for j in range(3):
            fx = mx + mod_w * (j + 1) / 4
            msp.add_line((fx, my + 1 * s), (fx, my + mod_h - 1 * s),
                         dxfattribs={"layer": "细实线"})

        # 产水管
        msp.add_line((mx + mod_w / 2, my + mod_h),
                     (mx + mod_w / 2, my + mod_h + 3 * s),
                     dxfattribs={"layer": layer})

    # 产水集管
    total_w = (mod_w + gap) * modules - gap
    msp.add_line((ox, oy + mod_h + 3 * s),
                 (ox + total_w, oy + mod_h + 3 * s),
                 dxfattribs={"layer": layer, "lineweight": 40})

    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + total_w / 2, oy + mod_h + 7 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + mod_h + 7 * s + 3 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG",
            })
            t.set_placement((ox + total_w / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + total_w, oy + mod_h + 10 * s)


# ══════════════════════════════════════════════════════════
#  消毒系统
# ══════════════════════════════════════════════════════════

def draw_disinfection(msp, center, d_type: str = "uv",
                       scale: float = 100.0,
                       label: str = "",
                       params: dict = None,
                       layer: str = "设备",
                       tracker=None):
    """消毒系统符号。

    参数:
        d_type: "uv"紫外 / "chlorine"加氯 / "ozone"臭氧 / "clo2"二氧化氯
        params: {"dose":"40mJ/cm²","channels":2,"lamps":48,...}
    """
    s = scale
    cx, cy = _r(*center)
    w, h = 14.0 * s, 10.0 * s

    if d_type == "uv":
        # 紫外：矩形 + 灯管
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        for i in range(5):
            lx = cx + (i - 2) * 2 * s
            msp.add_line((lx, cy - h * 0.35),
                         (lx, cy + h * 0.35),
                         dxfattribs={"layer": "细实线"})
        # UV 标注
        t = msp.add_text("UV", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((cx, cy + h * 0.15),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    elif d_type == "chlorine":
        # 加氯：矩形 + Cl₂
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        t = msp.add_text("Cl₂", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((cx, cy + h * 0.15),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    elif d_type == "ozone":
        # 臭氧：矩形 + O₃
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        t = msp.add_text("O₃", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((cx, cy + h * 0.15),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # 进出水
    msp.add_line((cx - w / 2 - 4 * s, cy), (cx - w / 2, cy),
                 dxfattribs={"layer": layer})
    msp.add_line((cx + w / 2, cy), (cx + w / 2 + 4 * s, cy),
                 dxfattribs={"layer": layer})

    if label:
        txt_h = 2.5 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - h / 2 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = cy - h / 2 - 4 * s - 2.5 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.3 * s

    return (cx + w / 2 + 4 * s, cy)


# ─── 辅助 ──────────────────────────────────────────────

def _arrow_head(msp, tip, direction, scale, layer):
    """箭头。"""
    tx, ty = tip
    dx, dy = direction
    h = 4.0 * scale
    w = 2.0 * scale
    px, py = -dy * w, dx * w
    pts = [(tx, ty), (tx - h * dx + px, ty - h * dy + py),
           (tx - h * dx - px, ty - h * dy - py)]
    try:
        msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
