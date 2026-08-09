"""电气自动化工程制图 v1.0（GB/T 4728、GB 50054、GB 50052）。

基于 ezdxf 实现电气原理图、单线图、电机控制回路、端子表、电缆表。
所有标准数值（线径、断路器整定值、电缆载流量等）由 Agent 搜索后显式传入。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ══════════════════════════════════════════════════════════
#  电气符号库（GB/T 4728）
# ══════════════════════════════════════════════════════════

def draw_breaker(msp, center, poles: int = 3,
                  b_type: str = "mccb",
                  scale: float = 100.0,
                  label: str = "",
                  params: dict = None,
                  layer: str = "元件",
                  tracker=None):
    """断路器符号。

    参数:
        poles: 极数 1/2/3/4
        b_type: "mccb"塑壳 / "mcb"小型 / "acb"框架 / "rcbo"漏电
        params: {"In":"63A","Icu":"10kA","curve":"C",...}
    """
    s = scale
    cx, cy = _r(*center)
    spacing = 6.0 * s
    total_h = poles * spacing

    # 多极联动线（虚线）
    if poles > 1:
        y0 = cy - total_h / 2 + spacing / 2
        msp.add_line((cx, y0), (cx, y0 + spacing * (poles - 1)),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})

    for i in range(poles):
        py = cy - total_h / 2 + spacing * (i + 0.5)

        # 进线 / 出线
        msp.add_line((cx - 5 * s, py), (cx - 2 * s, py),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + 2 * s, py), (cx + 5 * s, py),
                     dxfattribs={"layer": layer})

        if b_type == "rcbo":
            # 漏电：加漏电线圈符号（椭圆）
            msp.add_ellipse((cx - 1 * s, py), radius_x=1.5*s, radius_y=2*s,
                             dxfattribs={"layer": layer})

        # 触头（交叉线）
        msp.add_line((cx - 2 * s, py + 1.5 * s),
                     (cx + 1 * s, py), dxfattribs={"layer": layer})
        msp.add_circle((cx + 1 * s, py), 1.0 * s,
                       dxfattribs={"layer": layer})

        # 热脱扣（小矩形）
        msp.add_lwpolyline(
            [(cx + 1.5 * s, py - 2 * s), (cx + 3 * s, py - 2 * s),
             (cx + 3 * s, py + 2 * s), (cx + 1.5 * s, py + 2 * s)],
            close=True, dxfattribs={"layer": layer})

    txt_h = 2.2 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - total_h / 2 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - total_h / 2 - 4 * s - txt_h * 1.3
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.2 * s

    return (cx + 5 * s, cy - total_h / 2 - 8 * s)


def draw_contactor(msp, center, contacts: int = 3,
                    coil: bool = True, aux: int = 0,
                    scale: float = 100.0,
                    label: str = "",
                    layer: str = "元件",
                    tracker=None):
    """接触器/继电器符号。

    参数:
        contacts: 主触头数量
        coil: 是否画线圈
        aux: 辅助触头数量
    """
    s = scale
    cx, cy = _r(*center)
    sp = 6.0 * s

    cy_start = cy - (contacts + aux) * sp / 2

    # 联动虚线
    if contacts + aux > 1:
        msp.add_line((cx, cy_start + sp / 2),
                     (cx, cy_start + sp * (contacts + aux - 0.5)),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})

    # 主触头
    for i in range(contacts):
        py = cy_start + sp * (i + 0.5)
        msp.add_line((cx - 5 * s, py), (cx - 1.5 * s, py),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + 1.5 * s, py), (cx + 5 * s, py),
                     dxfattribs={"layer": layer})
        msp.add_circle((cx - 1 * s, py), 1.2 * s,
                       dxfattribs={"layer": layer})
        msp.add_circle((cx + 1 * s, py), 1.2 * s,
                       dxfattribs={"layer": layer})

    # 辅助触头（常开）
    aux_start_y = cy_start + contacts * sp
    for i in range(aux):
        py = aux_start_y + sp * (i + 0.5)
        msp.add_line((cx - 4 * s, py), (cx - 1.5 * s, py),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + 1.5 * s, py), (cx + 4 * s, py),
                     dxfattribs={"layer": layer})
        # 常开标记
        msp.add_line((cx - 1 * s, py - 1.5 * s),
                     (cx + 1 * s, py + 1.5 * s),
                     dxfattribs={"layer": layer})

    # 线圈
    if coil:
        coil_x = cx + 10 * s
        coil_y = cy
        msp.add_lwpolyline(
            [(coil_x - 3 * s, coil_y - 4 * s),
             (coil_x + 3 * s, coil_y - 4 * s),
             (coil_x + 3 * s, coil_y + 4 * s),
             (coil_x - 3 * s, coil_y + 4 * s)],
            close=True, dxfattribs={"layer": layer})
        # 线圈端子
        msp.add_text("A1", dxfattribs={
            "layer": "文字", "height": 1.8 * s, "style": "ENG",
        }).set_placement((coil_x - 5 * s, coil_y + 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_text("A2", dxfattribs={
            "layer": "文字", "height": 1.8 * s, "style": "ENG",
        }).set_placement((coil_x - 5 * s, coil_y - 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.2 * s, "style": "HZ",
        })
        t.set_placement((cx, cy_start - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + 15 * s, cy_start)


def draw_motor_symbol(msp, center, m_type: str = "induction",
                       scale: float = 100.0,
                       label: str = "",
                       params: dict = None,
                       layer: str = "元件",
                       tracker=None):
    """电机符号。

    参数:
        m_type: "induction"异步 / "sync"同步 / "dc"直流 / "servo"伺服 / "stepper"步进
        params: {"P":"5.5kW","V":"380V","I":"11.5A","rpm":"1450",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 8.0 * s

    # 圆
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    if m_type == "induction":
        # M 字母
        t = msp.add_text("M", dxfattribs={
            "layer": "文字", "height": 4.0 * s, "style": "ENG",
        })
        t.set_placement((cx, cy),
                        align=TextEntityAlignment.MIDDLE_CENTER)
        # 异步电机：下加波浪（~）
        t2 = msp.add_text("3~", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t2.set_placement((cx, cy - r - 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)
    elif m_type == "dc":
        t = msp.add_text("M", dxfattribs={
            "layer": "文字", "height": 3.5 * s, "style": "ENG",
        })
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
        t2 = msp.add_text("=", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t2.set_placement((cx, cy - r - 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)
    elif m_type == "servo":
        t = msp.add_text("SM", dxfattribs={
            "layer": "文字", "height": 3.0 * s, "style": "ENG",
        })
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    # 接线端子（上、下各3个）
    for dx_off in [-2 * s, 0, 2 * s]:
        msp.add_line((cx + dx_off, cy + r), (cx + dx_off, cy + r + 3 * s),
                     dxfattribs={"layer": layer})
        msp.add_circle((cx + dx_off, cy + r + 3.5 * s), 0.8 * s,
                       dxfattribs={"layer": layer})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - r - 10 * s - 2.5 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.2 * s

    return (cx + r, cy + r + 5 * s)


def draw_transformer(msp, center, t_type: str = "power",
                      scale: float = 100.0,
                      label: str = "",
                      params: dict = None,
                      layer: str = "元件",
                      tracker=None):
    """变压器符号。

    参数:
        t_type: "power"电力变压器 / "ct"电流互感器 / "vt"电压互感器 /
                "isolation"隔离变压器 / "auto"自耦变压器
    """
    s = scale
    cx, cy = _r(*center)
    w, h = 10.0 * s, 8.0 * s

    if t_type in ("ct", "vt"):
        # 互感器：双半圆
        r = 4.0 * s
        msp.add_arc((cx - 1.5 * s, cy), radius=r, start_angle=270, end_angle=90,
                     dxfattribs={"layer": layer})
        msp.add_arc((cx + 1.5 * s, cy), radius=r, start_angle=90, end_angle=270,
                     dxfattribs={"layer": layer})
        # 一次侧/二次侧标注
        t = msp.add_text("P1/P2" if t_type == "ct" else "U/V",
                         dxfattribs={"layer": "文字", "height": 2.0 * s,
                                     "style": "ENG"})
        t.set_placement((cx, cy + r + 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
        t2 = msp.add_text("S1/S2" if t_type == "ct" else "u/v",
                          dxfattribs={"layer": "文字", "height": 2.0 * s,
                                      "style": "ENG"})
        t2.set_placement((cx, cy - r - 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)
    else:
        # 电力变压器：双绕组（上下两个半圆环）
        r1, r2 = 3.5 * s, 3.5 * s
        # 上绕组
        msp.add_arc((cx, cy - 2 * s), radius=r1, start_angle=0, end_angle=180,
                     dxfattribs={"layer": layer})
        msp.add_arc((cx, cy - 2 * s), radius=r1 * 0.7, start_angle=0,
                     end_angle=180, dxfattribs={"layer": layer})
        # 下绕组
        msp.add_arc((cx, cy + 2 * s), radius=r2, start_angle=180, end_angle=360,
                     dxfattribs={"layer": layer})
        msp.add_arc((cx, cy + 2 * s), radius=r2 * 0.7, start_angle=180,
                     end_angle=360, dxfattribs={"layer": layer})

        if t_type == "auto":
            # 自耦：连接上下绕组
            msp.add_line((cx - r1, cy - 2 * s), (cx - r2, cy + 2 * s),
                         dxfattribs={"layer": layer})

    if label:
        txt_h = 2.2 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - h / 2 - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - h / 2 - 5 * s - 2.2 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.2 * s

    return (cx + w / 2, cy + h / 2)


def draw_terminal(msp, center, t_id: str = "X1",
                   pin: int = 1, wire_tag: str = "",
                   scale: float = 100.0,
                   label: str = "",
                   layer: str = "元件",
                   tracker=None):
    """端子符号。

    参数:
        t_id: 端子排编号
        pin: 端子序号
        wire_tag: 线号
    """
    s = scale
    cx, cy = _r(*center)

    # 小圆圈
    r = 1.5 * s
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    # 连线
    msp.add_line((cx - 4 * s, cy), (cx - r, cy),
                 dxfattribs={"layer": layer})
    msp.add_line((cx + r, cy), (cx + 4 * s, cy),
                 dxfattribs={"layer": layer})

    if pin:
        t = msp.add_text(str(pin), dxfattribs={
            "layer": "文字", "height": 1.8 * s, "style": "ENG",
        })
        t.set_placement((cx + 3 * s, cy + 2 * s),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if wire_tag:
        t = msp.add_text(wire_tag, dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((cx, cy - r - 2.5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + 4 * s, cy)


# ══════════════════════════════════════════════════════════
#  单线图 / 配电系统图
# ══════════════════════════════════════════════════════════

def draw_busbar(msp, start, end, scale: float = 100.0,
                 layer: str = "母线", tracker=None):
    """母线/汇流排（粗线）。"""
    sx, sy = _r(*start)
    ex, ey = _r(*end)
    msp.add_line((sx, sy), (ex, ey),
                 dxfattribs={"layer": layer, "lineweight": 80})
    if tracker:
        tracker.register(min(sx, ex) - 2 * scale, min(sy, ey) - 2 * scale,
                         max(sx, ex) + 2 * scale, max(sy, ey) + 2 * scale,
                         margin=10)
    return (ex, ey)


def draw_feeder(msp, origin, length: float, direction: str = "down",
                 scale: float = 100.0,
                 label: str = "",
                 params: dict = None,
                 layer: str = "馈线",
                 tracker=None):
    """单线图馈线回路。

    参数:
        origin: 起点（母线接口点）
        length: 馈线长度（图纸 mm）
        direction: "down"/"up"/"left"/"right"
        label: 回路编号
        params: {"cable":"YJV-4×25+1×16","breaker":"63A/3P","load":"30kW",...}
    """
    s = scale
    ox, oy = _r(*origin)
    L = length * s

    dirs = {"down": (0, -1), "up": (0, 1), "left": (-1, 0), "right": (1, 0)}
    dx, dy = dirs.get(direction, (0, -1))

    ex, ey = ox + dx * L, oy + dy * L

    # 馈线
    msp.add_line((ox, oy), (ex, ey), dxfattribs={"layer": layer})

    # 断路符号（馈线上的一点）
    brk_frac = 0.25
    bx = ox + dx * L * brk_frac
    by = oy + dy * L * brk_frac
    # 小交叉标记
    perp_x, perp_y = -dy, dx
    msp.add_line((bx - perp_x * 2 * s, by - perp_y * 2 * s),
                 (bx + perp_x * 2 * s, by + perp_y * 2 * s),
                 dxfattribs={"layer": layer})

    # 末端箭头
    arr_h = 3.0 * s
    arr_w = 1.5 * s
    px, py = -dy * arr_w, dx * arr_w
    arr_pts = [(ex, ey),
               (ex - dx * arr_h + px, ey - dy * arr_h + py),
               (ex - dx * arr_h - px, ey - dy * arr_h - py)]
    try:
        msp.add_solid(arr_pts + [arr_pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        msp.add_lwpolyline(arr_pts, close=True, dxfattribs={"layer": layer})

    # 标注
    txt_h = 2.2 * s
    cur_off = 3 * s
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        nx, ny = (ox + ex) / 2 + perp_x * cur_off, (oy + ey) / 2 + perp_y * cur_off
        t.set_placement((nx, ny), align=TextEntityAlignment.MIDDLE_LEFT)
        cur_off += 4 * s

    if params:
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            nx, ny = (ox + ex) / 2 + perp_x * cur_off, (ox + ey) / 2 + perp_y * cur_off
            t.set_placement((nx, ny), align=TextEntityAlignment.MIDDLE_LEFT)
            cur_off += 3 * s

    if tracker:
        tracker.register(ox - 10 * s, min(oy, ey) - 5 * s,
                         ex + cur_off, max(oy, ey) + 5 * s, margin=20)

    return (ex + dx * arr_h, ey + dy * arr_h)


# ══════════════════════════════════════════════════════════
#  电机控制回路
# ══════════════════════════════════════════════════════════

def draw_control_circuit(msp, origin, components: List[dict],
                          scale: float = 100.0,
                          layer: str = "控制回路",
                          tracker=None):
    """绘制电机控制回路图（起保停电路等）。

    参数:
        origin: 左上角起点
        components: 元件列表（从上到下），每项:
            {"type":"breaker", "label":"QF1", "params":{...}}
            {"type":"contactor", "label":"KM1", "coil":"A1-A2"}
            {"type":"relay", "label":"FR1", "contacts":"95-96"}
            {"type":"motor", "label":"M1", "params":{...}}
            {"type":"wire", "from":"L1","to":"L2","label":"1.5mm²"}
    """
    s = scale
    ox, oy = _r(*origin)

    # 主回路竖线（L1, L2, L3）
    l_sp = 10.0 * s  # 相间距
    L = 60.0 * s      # 回路长度
    phases = 3

    for i in range(phases):
        lx = ox + l_sp * i
        msp.add_line((lx, oy), (lx, oy - L),
                     dxfattribs={"layer": layer})
        # 相序标注
        t = msp.add_text(f"L{i + 1}", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((lx, oy + 2 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # 元件放置（沿竖线均布）
    cy = oy - L * 0.15
    for comp in components:
        ctype = comp.get("type", "")
        clabel = comp.get("label", "")
        cparams = comp.get("params", {})

        if ctype == "breaker":
            # 断路器标记
            for i in range(phases):
                lx = ox + l_sp * i
                msp.add_circle((lx, cy), 1.5 * s,
                               dxfattribs={"layer": layer})

            t = msp.add_text(clabel, dxfattribs={
                "layer": "文字-标题", "height": 2.2 * s, "style": "HZ",
            })
            t.set_placement((ox - 15 * s, cy),
                            align=TextEntityAlignment.MIDDLE_RIGHT)

            # 参数
            txt_h = 1.8 * s
            py = cy
            for key, val in cparams.items():
                py -= 2.5 * s
                t = msp.add_text(f"{key}:{val}", dxfattribs={
                    "layer": "文字", "height": txt_h, "style": "ENG",
                })
                t.set_placement((ox - 15 * s, py),
                                align=TextEntityAlignment.MIDDLE_RIGHT)

            cy -= 12 * s

        elif ctype == "contactor":
            # 接触器：方框跨三相
            msp.add_lwpolyline(
                [(ox - 1 * s, cy - 2 * s),
                 (ox + l_sp * 2 + 1 * s, cy - 2 * s),
                 (ox + l_sp * 2 + 1 * s, cy + 2 * s),
                 (ox - 1 * s, cy + 2 * s)],
                close=True, dxfattribs={"layer": "控制回路", "linetype": "DASHED"})
            # 主触头标记
            for i in range(phases):
                lx = ox + l_sp * i
                msp.add_line((lx - 1.5 * s, cy - 1.2 * s),
                             (lx + 1.5 * s, cy + 1.2 * s),
                             dxfattribs={"layer": layer})

            t = msp.add_text(clabel, dxfattribs={
                "layer": "文字-标题", "height": 2.2 * s, "style": "HZ",
            })
            t.set_placement((ox - 15 * s, cy),
                            align=TextEntityAlignment.MIDDLE_RIGHT)
            cy -= 8 * s

        elif ctype == "relay":
            # 热继电器
            for i in range(phases):
                lx = ox + l_sp * i
                msp.add_lwpolyline(
                    [(lx - 3 * s, cy - 2 * s), (lx + 3 * s, cy - 2 * s),
                     (lx + 3 * s, cy + 2 * s), (lx - 3 * s, cy + 2 * s)],
                    close=True, dxfattribs={"layer": layer})

            t = msp.add_text(clabel, dxfattribs={
                "layer": "文字-标题", "height": 2.2 * s, "style": "HZ",
            })
            t.set_placement((ox - 15 * s, cy),
                            align=TextEntityAlignment.MIDDLE_RIGHT)
            cy -= 8 * s

        elif ctype == "motor":
            # 电机
            mx = ox + l_sp * 1  # 中间相
            msp.add_circle((mx, cy), 6.0 * s, dxfattribs={"layer": layer})
            t = msp.add_text("M", dxfattribs={
                "layer": "文字", "height": 3.5 * s, "style": "ENG",
            })
            t.set_placement((mx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
            t2 = msp.add_text("3~", dxfattribs={
                "layer": "文字", "height": 2.2 * s, "style": "ENG",
            })
            t2.set_placement((mx, cy - 9 * s),
                             align=TextEntityAlignment.MIDDLE_CENTER)

            # 接线
            for i in range(phases):
                lx = ox + l_sp * i
                msp.add_line((lx, cy + 6 * s), (lx, cy - 6 * s),
                             dxfattribs={"layer": layer})

            # 电机参数
            if cparams:
                txt_h = 1.8 * s
                py2 = cy + 10 * s
                for key, val in cparams.items():
                    t = msp.add_text(f"{key}:{val}", dxfattribs={
                        "layer": "文字", "height": txt_h, "style": "ENG",
                    })
                    t.set_placement((ox + l_sp * 2 + 10 * s, py2),
                                    align=TextEntityAlignment.MIDDLE_LEFT)
                    py2 -= 2.5 * s

            cy -= 20 * s

    if tracker:
        tracker.register(ox - 20 * s, oy - L - 10 * s,
                         ox + l_sp * 2 + 20 * s, oy + 5 * s, margin=40)

    return (ox + l_sp * 2, oy - L)


# ══════════════════════════════════════════════════════════
#  电缆表 / 端子表
# ══════════════════════════════════════════════════════════

def draw_cable_schedule(msp, origin, cables: List[dict],
                         scale: float = 100.0,
                         title: str = "电缆表",
                         layer_grid: str = "细实线",
                         layer_text: str = "文字",
                         layer_header: str = "粗实线",
                         tracker=None):
    """电缆清册/端子接线表。

    参数:
        cables: 电缆列表
            [{"no":"W01","from":"MCC","to":"M1","type":"YJV",
              "spec":"4×25+1×16","length":85,"note":""}, ...]
    """
    s = scale
    ox, oy = _r(*origin)

    cols = [
        ("编号",  8.0, "center"),
        ("起点", 14.0, "left"),
        ("终点", 14.0, "left"),
        ("型号", 18.0, "left"),
        ("规格", 18.0, "center"),
        ("长度", 10.0, "center"),
        ("备注", 14.0, "left"),
    ]

    col_w = [c[1] * s for c in cols]
    total_w = sum(col_w)
    row_h = 7.0 * s
    txt_h = 2.3 * s

    # 标题
    title_h = 5.0 * s
    _elec_cell(msp, ox, oy - title_h, total_w, title_h, title,
               "center", 3.5 * s, layer_grid, layer_text)
    cur_y = oy - title_h

    # 表头
    cx = ox
    for i, (name, _, align) in enumerate(cols):
        _elec_cell(msp, cx, cur_y - row_h, col_w[i], row_h, name,
                   "center", 2.8 * s, layer_grid, layer_text,
                   bold_layer=layer_header)
        cx += col_w[i]
    cur_y -= row_h

    # 数据
    for cable in cables:
        vals = [
            str(cable.get("no", "")),
            str(cable.get("from", "")),
            str(cable.get("to", "")),
            str(cable.get("type", "")),
            str(cable.get("spec", "")),
            f"{cable.get('length', 0)}m" if cable.get("length") else "",
            str(cable.get("note", "")),
        ]
        cx = ox
        for i, val in enumerate(vals):
            _elec_cell(msp, cx, cur_y - row_h, col_w[i], row_h, val,
                       cols[i][2], txt_h, layer_grid, layer_text)
            cx += col_w[i]
        cur_y -= row_h

    msp.add_lwpolyline(
        [(ox, oy - title_h), (ox + total_w, oy - title_h),
         (ox + total_w, cur_y), (ox, cur_y)],
        close=True, dxfattribs={"layer": layer_header}
    )

    return (ox + total_w, cur_y)


def _elec_cell(msp, x0, y0, w, h, text, align, txt_h,
               layer_grid, layer_text, bold_layer=None):
    """电气表格单元格。"""
    layer = bold_layer if bold_layer else layer_grid
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True, dxfattribs={"layer": layer})
    if not text:
        return
    alignment = {
        "left": TextEntityAlignment.MIDDLE_LEFT,
        "center": TextEntityAlignment.MIDDLE_CENTER,
        "right": TextEntityAlignment.MIDDLE_RIGHT,
    }.get(align, TextEntityAlignment.MIDDLE_CENTER)
    if align == "left":
        px = x0 + 1.0 * txt_h
    elif align == "right":
        px = x0 + w - 1.0 * txt_h
    else:
        px = x0 + w / 2
    py = y0 + h / 2
    t = msp.add_text(str(text), dxfattribs={
        "layer": layer_text, "height": txt_h, "style": "HZ",
    })
    t.set_placement((px, py), align=alignment)

# ══════ v1.5+ 电气增补：继电器/熔断器/母线/桥架/配电箱/PLC/按钮 ══════
def draw_relay(msp,origin,rated_voltage=220.0,contacts=4,scale=100.0,label="",layer="控制回路",tracker=None):
    s=scale;ox,oy=_r(*origin);w=12*s;h=16*s
    msp.add_lwpolyline([(ox,oy),(ox+w,oy),(ox+w,oy+h),(ox,oy+h)],close=True,dxfattribs={"layer":layer})
    for i in range(contacts):msp.add_circle((ox+w/2,oy+h*(0.7-i*0.15)),1.5*s,dxfattribs={"layer":layer})
    t=msp.add_text("CR",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"});t.set_placement((ox+w/2,oy+h/2),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+w/2,oy+h+3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_fuse(msp,origin,rated_current=32.0,scale=100.0,label="",layer="主回路",tracker=None):
    s=scale;ox,oy=_r(*origin);w=8*s;h=14*s
    msp.add_lwpolyline([(ox,oy),(ox+w,oy),(ox+w,oy+h),(ox,oy+h)],close=True,dxfattribs={"layer":layer})
    msp.add_line((ox,oy+h/2),(ox+w,oy+h/2),dxfattribs={"layer":"细实线"})
    t=msp.add_text(f"{rated_current:.0f}A",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"});t.set_placement((ox+w/2,oy-3*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"});t.set_placement((ox+w/2,oy+h+3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_disconnect_switch(msp,origin,scale=100.0,label="",layer="主回路",tracker=None):
    s=scale;ox,oy=_r(*origin);w=8*s;h=12*s
    msp.add_line((ox,oy+h/2),(ox+w,oy+h/2),dxfattribs={"layer":layer})
    msp.add_line((ox+w/2,oy),(ox+w/2,oy+h),dxfattribs={"layer":"细实线"})
    msp.add_line((ox,oy+h/2-2*s),(ox+w/2-1*s,oy+h/2-2*s),dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"});t.set_placement((ox+w/2,oy-3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_busbar(msp,origin,length=50.0,width=5.0,phases=3,scale=100.0,label="",layer="主回路",tracker=None):
    s=scale;ox,oy=_r(*origin);L=length*s;W=width*s
    for i in range(phases):msp.add_lwpolyline([(ox,oy+i*W*2),(ox+L,oy+i*W*2),(ox+L,oy+i*W*2+W),(ox,oy+i*W*2+W)],close=True,dxfattribs={"layer":layer})
    t=msp.add_text(f"{phases}P",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"});t.set_placement((ox+L+3*s,oy+phases*W),align=TextEntityAlignment.MIDDLE_LEFT)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+L/2,oy+phases*W*2+3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_cable_tray(msp,origin,length=40.0,width=0.6,height=0.2,scale=100.0,label="",layer="桥架",tracker=None):
    s=scale;ox,oy=_r(*origin);L=length*s;W=width*s
    msp.add_lwpolyline([(ox,oy),(ox+L,oy),(ox+L,oy+W),(ox,oy+W)],close=True,dxfattribs={"layer":layer})
    for i in range(1,int(L/(8*s))):msp.add_line((ox+i*8*s,oy),(ox+i*8*s,oy+W),dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"});t.set_placement((ox+L/2,oy-3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_control_panel(msp,origin,width=0.8,height=1.2,depth=0.3,scale=100.0,label="",layer="设备",tracker=None):
    s=scale*5;ox,oy=_r(*origin);W=width*s;H=height*s
    msp.add_lwpolyline([(ox,oy),(ox+W,oy),(ox+W,oy+H),(ox,oy+H)],close=True,dxfattribs={"layer":layer})
    msp.add_line((ox,oy+H*0.8),(ox+W,oy+H*0.8),dxfattribs={"layer":"细实线"})
    t=msp.add_text("PLC/DDC",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"});t.set_placement((ox+W/2,oy+H/2),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+W/2,oy+H+4*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_pushbutton(msp,origin,button_type="start",scale=100.0,label="",layer="控制回路",tracker=None):
    s=scale;ox,oy=_r(*origin);r=5*s
    msp.add_circle((ox+r,oy+r),r,dxfattribs={"layer":layer})
    color="绿" if button_type=="start"else"红"if button_type=="stop"else"黄"
    t=msp.add_text(f"{color}",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"});t.set_placement((ox+r,oy+r),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"});t.set_placement((ox+r,oy-r-3*s),align=TextEntityAlignment.MIDDLE_CENTER)


def draw_single_line_diagram(msp, origin, branches=None, scale=100.0,
                             label="单线图", layer="主回路", tracker=None):
    """电气单线图。branches=[{name,load, breaker}, ...]。"""
    s=scale;ox,oy=_r(*origin)
    if not branches:branches=[{"name":"M1","load":"15kW","breaker":"63A/3P"},{"name":"M2","load":"7.5kW","breaker":"32A/3P"},{"name":"照明","load":"5kW","breaker":"16A/1P"}]
    msp.add_line((ox,oy),(ox,oy-2*s),dxfattribs={"layer":"粗实线"})
    msp.add_text("~380V",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"}).set_placement((ox,oy+1.5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    by=oy-3*s;bx=ox
    for i,b in enumerate(branches):
        bx=ox+i*20*s
        msp.add_line((bx,by),(bx,by-4*s),dxfattribs={"layer":layer})
        msp.add_lwpolyline([(bx-3*s,by-4*s),(bx+3*s,by-4*s),(bx+3*s,by-5*s),(bx-3*s,by-5*s)],close=True,dxfattribs={"layer":"细实线"})
        t=msp.add_text(b["breaker"],dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
        t.set_placement((bx,by-4.5*s),align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_circle((bx+6*s,by-6*s),3*s,dxfattribs={"layer":layer})
        t2=msp.add_text(f"{b['name']}\n{b['load']}",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
        t2.set_placement((bx+6*s,by-6*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"}).set_placement((ox,oy+4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+(len(branches)-1)*20*s+10*s,by-8*s)


def draw_lighting_layout(msp, origin, rooms=None, scale=100.0, label="照明布置", tracker=None):
    """照明布置图。rooms=[{name,w,d,lux, count}, ...]。"""
    s=scale;ox,oy=_r(*origin)
    if not rooms:rooms=[{"name":"办公室","w":6,"d":4,"lux":300,"count":2},{"name":"走廊","w":3,"d":8,"lux":150,"count":4}]
    cy=oy
    for ri,r in enumerate(rooms):
        rw,rd=r["w"]*s,r["d"]*s;cx=ox
        msp.add_lwpolyline([(cx,cy),(cx+rw,cy),(cx+rw,cy-rd),(cx,cy-rd)],close=True,dxfattribs={"layer":"细实线"})
        t=msp.add_text(f"{r['name']} {r['lux']}lx",dxfattribs={"layer":"文字","height":2.2*s,"style":"HZ"})
        t.set_placement((cx+rw/2,cy-rd-2*s),align=TextEntityAlignment.MIDDLE_CENTER)
        # 灯符号（叉 + 圆）
        for li in range(r.get("count",1)):
            lx=cx+rw*(li+1)/(r["count"]+1);ly=cy-rd/2
            msp.add_line((lx-2*s,ly-2*s),(lx+2*s,ly+2*s),dxfattribs={"layer":"照明"})
            msp.add_line((lx-2*s,ly+2*s),(lx+2*s,ly-2*s),dxfattribs={"layer":"照明"})
            msp.add_circle((lx,ly),3*s,dxfattribs={"layer":"照明"})
        cy-=rd+4*s
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"}).set_placement((ox,oy+3*s),align=TextEntityAlignment.MIDDLE_LEFT)
    return (ox+rw+5*s,cy)
