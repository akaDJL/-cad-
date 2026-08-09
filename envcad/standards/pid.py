"""P&ID 工艺管道仪表图 v1.0（ISA S5.1 / GB/T 2625—1981）。

基于 ezdxf 实现工艺流程图、仪表符号、控制回路、设备标注。
所有工艺参数（温度、压力、流量设定值等）由 Agent 搜索后显式传入。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ══════════════════════════════════════════════════════════
#  工艺管道
# ══════════════════════════════════════════════════════════

def draw_process_line(msp, start, end, line_type: str = "main",
                       scale: float = 100.0,
                       label: str = "",
                       layer: str = "工艺管道",
                       tracker=None):
    """绘制 P&ID 工艺管线。

    参数:
        line_type: "main"主管道 / "secondary"次要 / "instrument"仪表管线 /
                   "jacket"伴热管 / "electrical"电信号 / "pneumatic"气动信号
        label: 管线标注（如 "4\"-CS-1A"）
    """
    sx, sy = _r(*start)
    ex, ey = _r(*end)

    style = {
        "main": {},
        "secondary": {},
        "instrument": {"linetype": "DASHED"},
        "jacket": {"linetype": "DASHDOT"},
        "electrical": {"linetype": "DASHED", "lineweight": 30},
        "pneumatic": {"linetype": "DASHDOT", "lineweight": 25},
    }.get(line_type, {})

    msp.add_line((sx, sy), (ex, ey),
                 dxfattribs={"layer": layer, **style})

    if label:
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        lg = math.hypot(dx, dy)
        txt_h = 2.2 * scale
        if lg > 0:
            px, py = -dy / lg, dx / lg
            tx = mx + px * 3 * scale
            ty = my + py * 3 * scale
        else:
            tx, ty = mx, my - 3 * scale
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(min(sx, ex) - 3 * scale, min(sy, ey) - 3 * scale,
                         max(sx, ex) + 10 * scale, max(sy, ey) + 10 * scale,
                         margin=20)

    return (ex, ey)


# ══════════════════════════════════════════════════════════
#  工艺设备
# ══════════════════════════════════════════════════════════

def draw_vessel(msp, center, v_type: str = "tank",
                 width: float = 30.0, height: float = 40.0,
                 scale: float = 100.0,
                 label: str = "",
                 tag: str = "",
                 layer: str = "设备",
                 tracker=None):
    """容器/塔器符号。

    参数:
        v_type: "tank"储罐 / "reactor"反应器 / "column"塔 /
                "drum"分离罐 / "heat_exchanger"换热器 / "filter"过滤器
        width/height: 设备图纸尺寸 mm
        tag: 设备位号（如 "V-101"）
    """
    s = scale
    cx, cy = _r(*center)
    w = width * s
    h = height * s
    x0, y0 = cx - w / 2, cy - h / 2

    if v_type == "tank":
        # 储罐：圆筒 + 碟形封头（简化半圆）
        msp.add_lwpolyline(
            [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h),
             (x0, y0 + h)],
            close=True, dxfattribs={"layer": layer})
        # 封头圆弧
        msp.add_arc((cx, y0), radius=w / 2, start_angle=0, end_angle=180,
                     dxfattribs={"layer": layer})
        msp.add_arc((cx, y0 + h), radius=w / 2, start_angle=180,
                     end_angle=360, dxfattribs={"layer": layer})

    elif v_type == "reactor":
        # 反应器：带搅拌的圆筒
        msp.add_lwpolyline(
            [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h),
             (x0, y0 + h)],
            close=True, dxfattribs={"layer": layer})
        # 搅拌器（中心竖线 + 底部桨叶）
        msp.add_line((cx, y0 + h + 5 * s), (cx, y0 + h * 0.5),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - 4 * s, y0 + h * 0.55),
                     (cx + 4 * s, y0 + h * 0.55),
                     dxfattribs={"layer": layer})
        # 电机
        msp.add_circle((cx, y0 + h + 7 * s), 3 * s,
                       dxfattribs={"layer": layer})

    elif v_type == "column":
        # 塔：长矩形 + 塔板标记
        msp.add_lwpolyline(
            [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h),
             (x0, y0 + h)],
            close=True, dxfattribs={"layer": layer})
        # 塔板横线
        for i in range(1, 5):
            ty = y0 + h * i / 5
            msp.add_line((x0, ty), (x0 + w, ty),
                         dxfattribs={"layer": "细实线"})

    elif v_type == "drum":
        # 分离罐：水平卧罐
        msp.add_lwpolyline(
            [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h),
             (x0, y0 + h)],
            close=True, dxfattribs={"layer": layer})
        msp.add_arc((cx, y0 + h / 2), radius=h / 2, start_angle=90,
                     end_angle=270, dxfattribs={"layer": layer})

    elif v_type == "heat_exchanger":
        # 换热器：双矩形
        msp.add_lwpolyline(
            [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h),
             (x0, y0 + h)],
            close=True, dxfattribs={"layer": layer})
        # 管束标记：多条斜线
        for i in range(4):
            gx = x0 + w * (i + 0.5) / 4
            msp.add_line((gx, y0 + 2 * s), (gx, y0 + h - 2 * s),
                         dxfattribs={"layer": "细实线"})

    elif v_type == "filter":
        # 过滤器：菱形
        msp.add_lwpolyline(
            [(cx, y0), (x0 + w, cy), (cx, y0 + h), (x0, cy)],
            close=True, dxfattribs={"layer": layer})

    # 位号
    if tag:
        txt_h = 2.8 * s
        t = msp.add_text(tag, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "ENG",
        })
        t.set_placement((x0 + w / 2, y0 - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # 设备名称
    if label:
        txt_h = 2.2 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((x0 + w / 2, y0 - 4 * s - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (x0 + w, y0 + h)


# ══════════════════════════════════════════════════════════
#  仪表符号（ISA S5.1）
# ══════════════════════════════════════════════════════════

def draw_instrument(msp, center, tag: str = "",
                     func_id: str = "",
                     mounting: str = "field",
                     signal: str = "",
                     scale: float = 100.0,
                     label: str = "",
                     layer: str = "仪表",
                     tracker=None):
    """仪表符号（ISA S5.1 标准）。

    参数:
        tag: 仪表位号（如 "TIC-101"）
        func_id: 功能标识（T/TI/TIC/PI/LI/FI 等）
        mounting: 安装位置
            "field" = 现场安装（圆）
            "panel" = 盘装（圆+横线）
            "dcc" = DCS（方框+圆）
            "plc" = PLC（菱形=方框）
        signal: 信号类型 "4-20mA"/"HART"/"FF"/"Pneumatic"
    """
    s = scale
    cx, cy = _r(*center)
    r = 6.0 * s

    if mounting == "field":
        # 现场安装：单圆
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    elif mounting == "panel":
        # 盘装：圆 + 横线
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        msp.add_line((cx - r, cy), (cx + r, cy),
                     dxfattribs={"layer": layer})

    elif mounting in ("dcc", "plc"):
        # DCS/PLC: 方框 + 内圆
        box_s = r * 2
        msp.add_lwpolyline(
            [(cx - box_s / 2, cy - box_s / 2),
             (cx + box_s / 2, cy - box_s / 2),
             (cx + box_s / 2, cy + box_s / 2),
             (cx - box_s / 2, cy + box_s / 2)],
            close=True, dxfattribs={"layer": layer})
        msp.add_circle((cx, cy), r * 0.7, dxfattribs={"layer": layer})

    # 位号
    if tag:
        txt_h = 2.0 * s
        t = msp.add_text(tag, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((cx, cy),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # 功能描述
    if func_id:
        txt_h = 1.8 * s
        t = msp.add_text(func_id, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # 信号线
    if signal:
        sig_y = cy - r - 5 * s
        msp.add_line((cx - 3 * s, sig_y), (cx + 3 * s, sig_y),
                     dxfattribs={"layer": "仪表回路", "linetype": "DASHED"})

    if tracker:
        tracker.register(cx - r - 5 * s, cy - r - 8 * s,
                         cx + r + 5 * s, cy + r + 3 * s, margin=20)

    return (cx + r, cy - r - 8 * s)


# ══════════════════════════════════════════════════════════
#  控制阀
# ══════════════════════════════════════════════════════════

def draw_control_valve(msp, center, cv_type: str = "globe",
                        actuator: str = "pneumatic",
                        fail: str = "FC",
                        scale: float = 100.0,
                        label: str = "",
                        layer: str = "控制阀",
                        tracker=None):
    """控制阀符号。

    参数:
        cv_type: "globe"直通 / "angle"角阀 / "three_way"三通 / "butterfly"蝶阀
        actuator: "pneumatic"气动 / "electric"电动 / "manual"手动 /
                  "solenoid"电磁 / "hydraulic"液动
        fail: "FC"故障关 / "FO"故障开 / "FL"故障保位
    """
    s = scale
    cx, cy = _r(*center)

    # 阀体
    w, h = 10.0 * s, 6.0 * s
    if cv_type == "globe":
        # 直通阀：蝶形（两三角相对）
        tri = [(cx - w / 2, cy), (cx, cy - h / 2), (cx, cy + h / 2)]
        tri2 = [(cx + w / 2, cy), (cx, cy - h / 2), (cx, cy + h / 2)]
        msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline(tri2, close=True, dxfattribs={"layer": layer})
    elif cv_type == "angle":
        # 角阀：L形
        msp.add_line((cx - w / 2, cy), (cx, cy), dxfattribs={"layer": layer})
        msp.add_line((cx, cy), (cx, cy + h), dxfattribs={"layer": layer})
        msp.add_circle((cx, cy), 2 * s, dxfattribs={"layer": layer})
    elif cv_type == "three_way":
        # 三通阀：T形
        msp.add_line((cx - w / 2, cy), (cx + w / 2, cy),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy - h), (cx, cy + h),
                     dxfattribs={"layer": layer})
        msp.add_circle((cx, cy), 2 * s, dxfattribs={"layer": layer})
    elif cv_type == "butterfly":
        # 蝶阀：双线 + 圆
        msp.add_line((cx - w / 2, cy - 1.5 * s),
                     (cx - w / 2, cy + 1.5 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + w / 2, cy - 1.5 * s),
                     (cx + w / 2, cy + 1.5 * s),
                     dxfattribs={"layer": layer})
        msp.add_circle((cx, cy), 2.5 * s, dxfattribs={"layer": layer})

    # 管线
    msp.add_line((cx - w / 2 - 5 * s, cy), (cx - w / 2, cy),
                 dxfattribs={"layer": "工艺管道"})
    msp.add_line((cx + w / 2, cy), (cx + w / 2 + 5 * s, cy),
                 dxfattribs={"layer": "工艺管道"})

    # 执行机构
    act_y = cy + h / 2
    if actuator == "pneumatic":
        # 气动膜头：半圆 + 弹簧标记
        act_r = 5.0 * s
        msp.add_line((cx - act_r, act_y + 3 * s),
                     (cx + act_r, act_y + 3 * s),
                     dxfattribs={"layer": layer})
        msp.add_arc((cx, act_y + 3 * s), radius=act_r,
                     start_angle=0, end_angle=180,
                     dxfattribs={"layer": layer})
        # 弹簧
        for i in range(3):
            msp.add_line((cx - 3 * s + i * 3 * s, act_y),
                         (cx - 3 * s + i * 3 * s, act_y + 3 * s),
                         dxfattribs={"layer": "细实线"})
    elif actuator == "electric":
        # 电动：方框 + M
        msp.add_lwpolyline(
            [(cx - 5 * s, act_y + 2 * s), (cx + 5 * s, act_y + 2 * s),
             (cx + 5 * s, act_y + 8 * s), (cx - 5 * s, act_y + 8 * s)],
            close=True, dxfattribs={"layer": layer})
        t = msp.add_text("M", dxfattribs={
            "layer": "文字", "height": 3.0 * s, "style": "ENG",
        })
        t.set_placement((cx, act_y + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    elif actuator == "solenoid":
        # 电磁：方框 + 斜线
        msp.add_lwpolyline(
            [(cx - 4 * s, act_y + 2 * s), (cx + 4 * s, act_y + 2 * s),
             (cx + 4 * s, act_y + 8 * s), (cx - 4 * s, act_y + 8 * s)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - 4 * s, act_y + 8 * s),
                     (cx + 4 * s, act_y + 2 * s),
                     dxfattribs={"layer": layer})

    # 故障位置标注
    if fail:
        txt_h = 2.0 * s
        t = msp.add_text(fail, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((cx + 8 * s, cy),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        txt_h = 2.2 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - h - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + w / 2 + 5 * s, cy)


# ══════════════════════════════════════════════════════════
#  控制回路
# ══════════════════════════════════════════════════════════

def draw_control_loop(msp, origin, loop_type: str,
                       components: List[dict],
                       scale: float = 100.0,
                       label: str = "",
                       layer: str = "控制回路",
                       tracker=None):
    """绘制 P&ID 控制回路。

    参数:
        origin: 起点
        loop_type: "cascade"串级 / "feedback"反馈 / "feedforward"前馈 /
                   "ratio"比值 / "split_range"分程
        components: [
            {"type":"sensor","tag":"TE-101","at":(x,y)},
            {"type":"transmitter","tag":"TT-101","at":(x,y)},
            {"type":"controller","tag":"TIC-101","at":(x,y)},
            {"type":"valve","tag":"TV-101","at":(x,y)},
        ]
    """
    s = scale
    ox, oy = _r(*origin)

    # 绘制各元件 + 连线
    prev_pos = None
    for comp in components:
        ctype = comp.get("type", "")
        ctag = comp.get("tag", "")
        cx, cy = comp.get("at", (ox, oy))

        if ctype == "sensor":
            # 传感器：小三角
            tri = [(cx, cy + 4 * s), (cx - 3 * s, cy - 2 * s),
                   (cx + 3 * s, cy - 2 * s)]
            msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})

        elif ctype == "transmitter":
            draw_instrument(msp, (cx, cy), tag=ctag,
                             func_id="T", mounting="field", scale=scale,
                             layer=layer)

        elif ctype == "controller":
            draw_instrument(msp, (cx, cy), tag=ctag,
                             func_id="C", mounting="dcc", scale=scale,
                             layer=layer)

        elif ctype == "valve":
            draw_control_valve(msp, (cx, cy), cv_type="globe",
                                actuator="pneumatic", fail="FC",
                                scale=scale, label=ctag, layer=layer)

        # 连线
        if prev_pos:
            msp.add_line(prev_pos, (cx, cy),
                         dxfattribs={"layer": "仪表回路", "linetype": "DASHED"})

        prev_pos = (cx, cy)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.0 * s, "style": "HZ",
        })
        t.set_placement((ox, oy), align=TextEntityAlignment.MIDDLE_LEFT)

    if tracker:
        tracker.register(ox - 10 * s, oy - 20 * s,
                         ox + 40 * s, oy + 10 * s, margin=40)

    return (ox, oy)


# ══════════════════════════════════════════════════════════
#  管线表 / 仪表索引
# ══════════════════════════════════════════════════════════

def draw_line_list(msp, origin, lines: List[dict],
                    scale: float = 100.0,
                    title: str = "管线表",
                    layer_grid: str = "细实线",
                    layer_text: str = "文字",
                    layer_header: str = "粗实线",
                    tracker=None):
    """工艺管线表。

    参数:
        lines: [{"no":"4\"-CS-1A","from":"V-101","to":"E-201",
                  "fluid":"冷却水","size":"DN100","spec":"CS Sch40",
                  "insulation":"50mm岩棉",...}, ...]
    """
    s = scale
    ox, oy = _r(*origin)

    cols = [
        ("管线号", 16.0, "left"),
        ("起点",  14.0, "left"),
        ("终点",  14.0, "left"),
        ("介质",  12.0, "center"),
        ("管径",  12.0, "center"),
        ("材质/等级", 16.0, "center"),
        ("保温",  14.0, "left"),
        ("备注",  14.0, "left"),
    ]

    col_w = [c[1] * s for c in cols]
    total_w = sum(col_w)
    row_h = 7.0 * s
    txt_h = 2.3 * s

    title_h = 5.0 * s
    _pid_cell(msp, ox, oy - title_h, total_w, title_h, title,
              "center", 3.5 * s, layer_grid, layer_text)
    cur_y = oy - title_h

    cx = ox
    for i, (name, _, align) in enumerate(cols):
        _pid_cell(msp, cx, cur_y - row_h, col_w[i], row_h, name,
                  "center", 2.8 * s, layer_grid, layer_text,
                  bold_layer=layer_header)
        cx += col_w[i]
    cur_y -= row_h

    for line in lines:
        vals = [
            str(line.get("no", "")),
            str(line.get("from", "")),
            str(line.get("to", "")),
            str(line.get("fluid", "")),
            str(line.get("size", "")),
            str(line.get("spec", "")),
            str(line.get("insulation", "")),
            str(line.get("note", "")),
        ]
        cx = ox
        for i, val in enumerate(vals):
            _pid_cell(msp, cx, cur_y - row_h, col_w[i], row_h, val,
                      cols[i][2], txt_h, layer_grid, layer_text)
            cx += col_w[i]
        cur_y -= row_h

    msp.add_lwpolyline(
        [(ox, oy - title_h), (ox + total_w, oy - title_h),
         (ox + total_w, cur_y), (ox, cur_y)],
        close=True, dxfattribs={"layer": layer_header}
    )

    return (ox + total_w, cur_y)


def _pid_cell(msp, x0, y0, w, h, text, align, txt_h,
              layer_grid, layer_text, bold_layer=None):
    """P&ID 表格单元格。"""
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


def draw_heat_exchanger(msp, origin, hx_type="shell_tube", d=0.4, L=1.2,
                        scale=100.0, label="", layer="设备", tracker=None):
    """换热器 P&ID 符号。hx_type=shell_tube(管壳)/plate(板式)/u_tube。"""
    s=scale;ox,oy=_r(*origin);ds,ls=d*s,L*s
    cx,cy=ox+ds/2,oy
    if hx_type=="shell_tube":
        msp.add_circle((cx,cy),ds/2,dxfattribs={"layer":layer})
        msp.add_line((cx-ds/2+2*s,cy-ds/2+2*s),(cx+ds/2-2*s,cy+ds/2-2*s),dxfattribs={"layer":"细实线"})
        msp.add_line((cx-ds/2+2*s,cy+ds/2-2*s),(cx+ds/2-2*s,cy-ds/2+2*s),dxfattribs={"layer":"细实线"})
        # 管嘴
        msp.add_line((cx-ds/2-3*s,cy),(cx-ds/2,cy),dxfattribs={"layer":layer})
        msp.add_line((cx+ds/2,cy),(cx+ds/2+3*s,cy),dxfattribs={"layer":layer})
    elif hx_type=="plate":
        msp.add_lwpolyline([(ox,oy),(ox+ls,oy),(ox+ls,oy-ds),(ox,oy-ds)],close=True,dxfattribs={"layer":layer})
        for xi in range(1,6):msp.add_line((ox+ls*xi/6,oy),(ox+ls*xi/6,oy-ds),dxfattribs={"layer":"细实线"})
    elif hx_type=="u_tube":
        msp.add_circle((cx,cy),ds/2,dxfattribs={"layer":layer})
        msp.add_arc((cx,cy-ds/2+1*s),radius=ds/3,start_angle=180,end_angle=0,dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,oy-ds),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+ls+5*s,oy)


def draw_distillation_tower(msp, origin, d=0.8, H=4.0, n_trays=8,
                            scale=100.0, label="", layer="设备", tracker=None):
    """精馏塔 P&ID 符号。塔体+塔板+进出料管嘴。"""
    s=scale;ox,oy=_r(*origin);ds=d*s;hs=H*s
    cx,cy=ox+ds/2,oy-hs/2
    # 塔体
    msp.add_lwpolyline([(ox,oy),(ox+ds,oy),(ox+ds,oy-hs),(ox,oy-hs)],close=True,dxfattribs={"layer":layer})
    # 塔板
    for ti in range(n_trays):
        ty=oy-(ti+1)*hs/(n_trays+1)
        msp.add_line((ox,ty),(ox+ds,ty),dxfattribs={"layer":"细实线"})
        msp.add_lwpolyline([(ox+ds,ty),(ox+ds-2*s,ty-1*s),(ox+ds,ty-2*s)],close=False,dxfattribs={"layer":"细实线"})
    # 管嘴
    msp.add_line((ox-3*s,oy-hs*0.15),(ox,oy-hs*0.15),dxfattribs={"layer":layer})
    msp.add_line((ox+ds,oy-hs*0.85),(ox+ds+3*s,oy-hs*0.85),dxfattribs={"layer":layer})
    msp.add_line((ox-3*s,oy-hs*0.9),(ox,oy-hs*0.9),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.8*s,"style":"HZ"})
        t.set_placement((cx,oy-hs-3*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+ds+5*s,oy)
