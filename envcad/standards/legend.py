"""图例表 v1.5 — 符号 + 名称 + 规格（环保工艺管线/设备/阀门/仪表图例）。

图例为标准表格，符号按 GB/T 50106—2010《给水排水制图标准》
及 HG/T 20519《化工工艺设计施工图内容和深度统一规定》。

支持符号类型：
  管道类：pipe_solid / pipe_dashed / pipe_hdpe / pipe_upvc / pipe_carbon_steel
  阀门类：valve_gate / valve_butterfly / valve_diaphragm_no / valve_diaphragm_nc /
          valve_diaphragm_lined / valve_globe / valve_ball / valve_check /
          valve_sampling / valve_regulating / valve_plug
  仪表类：flow_meter / level_gauge / ph_meter / pressure_gauge /
          instr_field / instr_panel / instr_dcs
  管件类：elbow_90 / tee_equal / reducer_conc / flange_pair / cross / cap
  设备类：pump_centrifugal / mixer / blower / screen / blower_root
  其他：soft_joint / sleeve / arrow_flow / elevation / wall / water /
        manhole / septic_tank / screen_well / regulating_tank / slope / check_valve
"""
from __future__ import annotations

from ezdxf.enums import TextEntityAlignment

from .annotate import _t, _arrow
from ..components.fittings import (
    draw_butterfly_valve, draw_diaphragm_valve, draw_globe_valve,
    draw_ball_valve, draw_check_valve, draw_sampling_valve,
    draw_regulating_valve, draw_plug_valve, draw_elbow, draw_tee,
    draw_reducer, draw_flange_pair, draw_cross, draw_instrument_symbol,
)


def draw_legend(msp, origin, scale: float, items, title: str = "图  例",
                col_widths=(18, 32, 30), row_h: float = 8.0,
                tracker=None):
    """绘制图例表 v1.4 — 支持碰撞检测。

    items: [(kind, name, spec), ...]，kind 见 _draw_symbol。
    origin: 图例左上角 (x, y)，表格向下、向右展开。
    """
    s = scale
    ox, oy = origin
    cw = [w * s for w in col_widths]
    total_w = sum(cw)
    rh = row_h * s
    n = len(items)
    title_h = rh
    total_h = title_h + n * rh
    # 外框
    x0, y0 = ox, oy - total_h
    x1, y1 = ox + total_w, oy
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                       dxfattribs={"layer": "图框"})
    # 注册图例外框
    if tracker is not None:
        tracker.register(x0, y0, x1, y1, margin=100)
    # 标题行
    # 注：图例内部文字为表格单元格精确定位，不参与碰撞避让
    # （否则会被自身外框注册区顶出图框边界）；外框已注册，外部标注自会避让。
    msp.add_line((x0, y1 - title_h), (x1, y1 - title_h), dxfattribs={"layer": "图框"})
    _t(msp, title, ((x0 + x1) / 2, y1 - title_h / 2 + 0.5 * s), 3.5 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题")
    # 列分隔
    cx = x0
    col_x = [x0]
    for w in cw[:-1]:
        cx += w
        msp.add_line((cx, y0), (cx, y1), dxfattribs={"layer": "图框"})
        col_x.append(cx)
    col_x.append(x1)
    # 行
    for i, (kind, name, spec) in enumerate(items):
        ry = y1 - title_h - (i + 0.5) * rh
        if i > 0:
            msp.add_line((x0, ry + rh / 2), (x1, ry + rh / 2), dxfattribs={"layer": "图框"})
        # 符号区
        sym_cx = (col_x[0] + col_x[1]) / 2
        _draw_symbol(msp, kind, (sym_cx, ry), s)
        # 名称
        _t(msp, name, ((col_x[1] + col_x[2]) / 2, ry + 0.5 * s), 2.8 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
        # 规格
        _t(msp, spec, ((col_x[2] + col_x[3]) / 2, ry + 0.5 * s), 2.8 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    return (x0, y0, x1, y1)


def _draw_symbol(msp, kind: str, center, s):
    cx, cy = center
    L = 6 * s

    # ── 管道类 ──
    if kind in ("pipe_solid", "pipe_sewage", "pipe_hdpe"):
        layer = "管道-污水" if kind != "pipe_hdpe" else "管道-给水"
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": layer})
    elif kind == "pipe_dashed":
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "虚线"})
    elif kind == "pipe_upvc":
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "管道-给水"})
        # UPVC 标记：中间小短线
        msp.add_line((cx, cy - s), (cx, cy + s), dxfattribs={"layer": "细实线"})
    elif kind == "pipe_carbon_steel":
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "管道-污水", "lineweight": 50})

    # ── 阀门类 ──
    elif kind == "valve":  # 手动闸阀（兼容旧版）
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx + L, cy + L / 2),
                            (cx + L, cy - L / 2), (cx - L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
    elif kind == "valve_gate":
        # 闸阀：两三角相对
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L, cy), (cx - L - 1 * s, cy), dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx + L, cy), (cx + L + 1 * s, cy), dxfattribs={"layer": "管道-污水"})
    elif kind == "valve_butterfly":
        # 蝶阀：两侧短竖线 + 中间圆
        msp.add_line((cx - L, cy - L / 2), (cx - L, cy + L / 2),
                     dxfattribs={"layer": "阀门"})
        msp.add_line((cx + L, cy - L / 2), (cx + L, cy + L / 2),
                     dxfattribs={"layer": "阀门"})
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L * 0.5, cy), (cx + L * 0.5, cy),
                     dxfattribs={"layer": "阀门"})
        # 上方执行机构（气动）
        msp.add_line((cx, cy + L * 0.5), (cx, cy + L * 0.9),
                     dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.3, cy + L * 0.9),
                            (cx + L * 0.3, cy + L * 0.9),
                            (cx + L * 0.3, cy + L * 1.3),
                            (cx - L * 0.3, cy + L * 1.3)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L, cy), (cx - L - 1 * s, cy),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx + L, cy), (cx + L + 1 * s, cy),
                     dxfattribs={"layer": "管道-污水"})
    elif kind == "valve_diaphragm_no":
        # 气动常开隔膜阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L * 0.3, cy), (cx + L * 0.3, cy),
                     dxfattribs={"layer": "阀门"})
        # 气动执行机构
        msp.add_lwpolyline([(cx - L * 0.3, cy + L / 2),
                            (cx + L * 0.3, cy + L / 2),
                            (cx + L * 0.3, cy + L * 1.1),
                            (cx - L * 0.3, cy + L * 1.1)],
                           close=True, dxfattribs={"layer": "阀门"})
        _t(msp, "NO", (cx, cy + L * 1.25), 1.8 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    elif kind == "valve_diaphragm_nc":
        # 气动常闭隔膜阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L * 0.3, cy), (cx + L * 0.3, cy),
                     dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.3, cy + L / 2),
                            (cx + L * 0.3, cy + L / 2),
                            (cx + L * 0.3, cy + L * 1.1),
                            (cx - L * 0.3, cy + L * 1.1)],
                           close=True, dxfattribs={"layer": "阀门"})
        _t(msp, "NC", (cx, cy + L * 1.25), 1.8 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    elif kind == "valve_diaphragm_lined":
        # 衬胶隔膜阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L * 0.3, cy), (cx + L * 0.3, cy),
                     dxfattribs={"layer": "阀门"})
        # 衬胶交叉线
        msp.add_line((cx - L * 0.4, cy - L * 0.3),
                     (cx + L * 0.4, cy + L * 0.3),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((cx - L * 0.4, cy + L * 0.3),
                     (cx + L * 0.4, cy - L * 0.3),
                     dxfattribs={"layer": "细实线"})
    elif kind == "valve_globe":
        # 截止阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx, cy), (cx, cy + L * 0.9),
                     dxfattribs={"layer": "阀门"})
        msp.add_circle((cx, cy + L * 1.1), L * 0.25,
                       dxfattribs={"layer": "阀门"})
    elif kind == "valve_ball":
        # 球阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_circle((cx, cy), L * 0.35, dxfattribs={"layer": "阀门"})
        msp.add_line((cx, cy + L * 0.35), (cx, cy + L * 0.7),
                     dxfattribs={"layer": "阀门"})
        msp.add_line((cx - L * 0.3, cy + L * 0.7),
                     (cx + L * 0.3, cy + L * 0.7),
                     dxfattribs={"layer": "阀门"})
    elif kind == "valve_check":
        # 止回阀：圆 + 单向三角
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.2, cy - L * 0.3),
                            (cx - L * 0.2, cy + L * 0.3),
                            (cx + L * 0.5, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
    elif kind == "valve_sampling":
        # 取样阀
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx, cy), (cx, cy - L * 0.6), dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.25, cy - L * 0.9),
                            (cx + L * 0.25, cy - L * 0.9),
                            (cx, cy - L * 0.6)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx, cy - L * 0.9), (cx, cy - L * 1.2),
                     dxfattribs={"layer": "阀门"})
    elif kind == "valve_regulating":
        # 气动调节阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx - L, cy + L / 2), (cx, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx, cy), (cx + L, cy - L / 2), (cx + L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_line((cx, cy), (cx, cy + L * 0.7),
                     dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.35, cy + L * 0.7),
                            (cx + L * 0.35, cy + L * 0.7),
                            (cx + L * 0.35, cy + L * 1.3),
                            (cx - L * 0.35, cy + L * 1.3)],
                           close=True, dxfattribs={"layer": "阀门"})
        # 对角箭头（调节符号）
        msp.add_line((cx - L * 0.2, cy + L * 0.85),
                     (cx + L * 0.2, cy + L * 1.15),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((cx + L * 0.2, cy + L * 0.85),
                     (cx - L * 0.2, cy + L * 1.15),
                     dxfattribs={"layer": "细实线"})
    elif kind == "valve_plug":
        # 旋塞阀/插板阀
        msp.add_lwpolyline([(cx - L, cy - L / 2), (cx + L, cy - L / 2),
                            (cx + L, cy + L / 2), (cx - L, cy + L / 2)],
                           close=True, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.25, cy - L * 0.3),
                            (cx + L * 0.25, cy - L * 0.3),
                            (cx + L * 0.2, cy + L * 0.3),
                            (cx - L * 0.2, cy + L * 0.3)],
                           close=True, dxfattribs={"layer": "阀门"})

    # ── 仪表类 ──
    elif kind == "flow_meter":  # 电磁流量计：圆中 M
        msp.add_circle((cx, cy), L * 0.6, dxfattribs={"layer": "设备"})
        _t(msp, "M", (cx, cy - 0.5 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    elif kind == "level_gauge":
        # 液位计：圆 + L
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "仪表"})
        _t(msp, "L", (cx, cy - 0.5 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    elif kind == "ph_meter":
        # PH 计：圆 + PH
        msp.add_circle((cx, cy), L * 0.55, dxfattribs={"layer": "仪表"})
        _t(msp, "PH", (cx, cy - 0.5 * s), 2.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    elif kind == "pressure_gauge":
        # 压力表：圆 + P
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "仪表"})
        _t(msp, "P", (cx, cy - 0.5 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    elif kind == "instr_field":
        # 就地安装：单圆
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "仪表"})
    elif kind == "instr_panel":
        # 就地盘面安装：圆 + 中间横线
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "仪表"})
        msp.add_line((cx - L * 0.5, cy), (cx + L * 0.5, cy),
                     dxfattribs={"layer": "仪表"})
    elif kind == "instr_dcs":
        # 计算机功能：方框 + 内圆
        box_s = L * 0.9
        msp.add_lwpolyline([(cx - box_s / 2, cy - box_s / 2),
                            (cx + box_s / 2, cy - box_s / 2),
                            (cx + box_s / 2, cy + box_s / 2),
                            (cx - box_s / 2, cy + box_s / 2)],
                           close=True, dxfattribs={"layer": "仪表"})
        msp.add_circle((cx, cy), L * 0.35, dxfattribs={"layer": "仪表"})

    # ── 管件类 ──
    elif kind == "elbow_90":
        # 90°弯头
        msp.add_arc((cx - L * 0.3, cy - L * 0.3), L * 0.7,
                     start_angle=0, end_angle=90,
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx + L * 0.4, cy - L * 0.3), (cx - L * 0.3, cy - L * 0.3),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx - L * 0.3, cy + L * 0.4), (cx - L * 0.3, cy - L * 0.3),
                     dxfattribs={"layer": "管道-污水"})
    elif kind == "tee_equal":
        # 等径三通
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx, cy), (cx, cy + L * 0.8), dxfattribs={"layer": "管道-污水"})
    elif kind == "reducer_conc":
        # 同心异径管
        msp.add_line((cx - L, cy - L * 0.4), (cx + L, cy - L * 0.25),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx - L, cy + L * 0.4), (cx + L, cy + L * 0.25),
                     dxfattribs={"layer": "管道-污水"})
    elif kind == "flange_pair":
        # 法兰对
        msp.add_line((cx - L * 0.2, cy - L * 0.6),
                     (cx - L * 0.2, cy + L * 0.6),
                     dxfattribs={"layer": "设备"})
        msp.add_line((cx + L * 0.2, cy - L * 0.6),
                     (cx + L * 0.2, cy + L * 0.6),
                     dxfattribs={"layer": "设备"})
        msp.add_line((cx - L * 0.6, cy), (cx - L * 0.2, cy),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx + L * 0.2, cy), (cx + L * 0.6, cy),
                     dxfattribs={"layer": "管道-污水"})
    elif kind == "cross":
        # 四通
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx, cy - L * 0.7), (cx, cy + L * 0.7),
                     dxfattribs={"layer": "管道-污水"})
    elif kind == "cap":
        # 管帽
        msp.add_line((cx - L * 0.5, cy - L * 0.4),
                     (cx + L * 0.3, cy - L * 0.4),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx - L * 0.5, cy + L * 0.4),
                     (cx + L * 0.3, cy + L * 0.4),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_arc((cx + L * 0.3, cy), L * 0.4,
                     start_angle=270, end_angle=90,
                     dxfattribs={"layer": "管道-污水"})

    # ── 设备类（简化符号） ──
    elif kind == "pump_centrifugal":
        # 离心泵：圆 + 进出口
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "设备"})
        msp.add_line((cx - L * 0.5, cy), (cx - L, cy),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx, cy + L * 0.5), (cx, cy + L),
                     dxfattribs={"layer": "设备"})
        # 电机（上方小方框）
        msp.add_lwpolyline([(cx - L * 0.25, cy + L),
                            (cx + L * 0.25, cy + L),
                            (cx + L * 0.25, cy + L * 1.4),
                            (cx - L * 0.25, cy + L * 1.4)],
                           close=True, dxfattribs={"layer": "设备"})
    elif kind == "mixer":
        # 搅拌机：竖线 + 桨叶
        msp.add_line((cx, cy + L), (cx, cy - L * 0.3),
                     dxfattribs={"layer": "设备"})
        # 电机
        msp.add_lwpolyline([(cx - L * 0.25, cy + L),
                            (cx + L * 0.25, cy + L),
                            (cx + L * 0.25, cy + L * 1.4),
                            (cx - L * 0.25, cy + L * 1.4)],
                           close=True, dxfattribs={"layer": "设备"})
        # 桨叶（三叶）
        msp.add_line((cx - L * 0.5, cy - L * 0.3),
                     (cx + L * 0.5, cy - L * 0.3),
                     dxfattribs={"layer": "设备"})
        msp.add_line((cx - L * 0.4, cy - L * 0.5),
                     (cx + L * 0.4, cy - L * 0.5),
                     dxfattribs={"layer": "设备"})
    elif kind == "blower":
        # 风机/鼓风机：圆 + 进风口 + 出风口
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "设备"})
        msp.add_line((cx - L * 0.5, cy), (cx - L, cy),
                     dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx + L * 0.5, cy), (cx + L, cy),
                     dxfattribs={"layer": "管道-污水"})
        # 电机
        msp.add_lwpolyline([(cx - L * 0.2, cy + L * 0.5),
                            (cx + L * 0.2, cy + L * 0.5),
                            (cx + L * 0.2, cy + L * 0.9),
                            (cx - L * 0.2, cy + L * 0.9)],
                           close=True, dxfattribs={"layer": "设备"})
    elif kind == "screen":
        # 格栅：矩形 + 栅条
        msp.add_lwpolyline([(cx - L * 0.6, cy - L * 0.4),
                            (cx + L * 0.6, cy - L * 0.4),
                            (cx + L * 0.6, cy + L * 0.4),
                            (cx - L * 0.6, cy + L * 0.4)],
                           close=True, dxfattribs={"layer": "池体-壁"})
        for i in range(5):
            gx = cx - L * 0.5 + i * L * 0.25
            msp.add_line((gx, cy - L * 0.4), (gx, cy + L * 0.4),
                         dxfattribs={"layer": "细实线"})

    # ── 其他（兼容旧版） ──
    elif kind == "soft_joint":  # 橡胶软接头：波浪
        msp.add_line((cx - L, cy), (cx - L / 2, cy), dxfattribs={"layer": "管道-污水"})
        msp.add_line((cx + L / 2, cy), (cx + L, cy), dxfattribs={"layer": "管道-污水"})
        msp.add_lwpolyline([(cx - L / 2, cy), (cx - L / 4, cy + L / 3),
                            (cx, cy - L / 3), (cx + L / 4, cy + L / 3),
                            (cx + L / 2, cy)], dxfattribs={"layer": "管道-污水"})
    elif kind == "sleeve":  # 刚性防水套管：管两侧短粗线
        msp.add_line((cx - L, cy), (cx + L, cy), dxfattribs={"layer": "管道-污水"})
        for dx in (-L * 0.5, L * 0.5):
            msp.add_line((cx + dx, cy - L * 0.6), (cx + dx, cy + L * 0.6),
                         dxfattribs={"layer": "设备"})
    elif kind == "arrow_flow":  # 流向箭头
        _arrow(msp, (cx - L, cy), (cx + L, cy), s, layer="流向")
    elif kind == "elevation":  # 标高符号
        msp.add_lwpolyline([(cx, cy - L / 2), (cx - L / 2, cy + L / 2),
                            (cx + L / 2, cy + L / 2), (cx, cy - L / 2)],
                           close=True, dxfattribs={"layer": "标高"})
    elif kind == "wall":  # 池壁/墙体（双线+剖面线）
        msp.add_line((cx - L, cy - L / 2), (cx + L, cy - L / 2), dxfattribs={"layer": "粗实线"})
        msp.add_line((cx - L, cy + L / 2), (cx + L, cy + L / 2), dxfattribs={"layer": "粗实线"})
    elif kind == "water":  # 水面（~）
        msp.add_lwpolyline([(cx - L, cy), (cx - L / 2, cy + L / 3),
                            (cx, cy - L / 3), (cx + L / 2, cy + L / 3),
                            (cx + L, cy)], dxfattribs={"layer": "池体-水"})
    elif kind == "manhole":  # 检查井：双圆
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "检查井"})
        msp.add_circle((cx, cy), L * 0.3, dxfattribs={"layer": "中实线"})
    elif kind == "septic_tank":  # 化粪池：矩形+三格
        msp.add_lwpolyline([(cx - L, cy - L * 0.6), (cx + L, cy - L * 0.6),
                            (cx + L, cy + L * 0.6), (cx - L, cy + L * 0.6)],
                           close=True, dxfattribs={"layer": "池体-壁"})
        msp.add_line((cx - L * 0.2, cy - L * 0.6), (cx - L * 0.2, cy + L * 0.6),
                     dxfattribs={"layer": "虚线"})
        msp.add_line((cx + L * 0.4, cy - L * 0.6), (cx + L * 0.4, cy + L * 0.6),
                     dxfattribs={"layer": "虚线"})
    elif kind == "screen_well":  # 格栅井：矩形+栅条
        msp.add_lwpolyline([(cx - L, cy - L * 0.4), (cx + L, cy - L * 0.4),
                            (cx + L, cy + L * 0.4), (cx - L, cy + L * 0.4)],
                           close=True, dxfattribs={"layer": "池体-壁"})
        for i in range(4):
            gx = cx - L + (i + 1) * 2 * L / 5
            msp.add_line((gx, cy - L * 0.4), (gx, cy + L * 0.4),
                         dxfattribs={"layer": "细实线"})
    elif kind == "regulating_tank":  # 调节池：矩形+十字
        msp.add_lwpolyline([(cx - L, cy - L * 0.6), (cx + L, cy - L * 0.6),
                            (cx + L, cy + L * 0.6), (cx - L, cy + L * 0.6)],
                           close=True, dxfattribs={"layer": "池体-壁"})
        msp.add_line((cx - L * 0.5, cy), (cx + L * 0.5, cy), dxfattribs={"layer": "细实线"})
        msp.add_line((cx, cy - L * 0.5), (cx, cy + L * 0.5), dxfattribs={"layer": "细实线"})
    elif kind == "slope":  # 坡度符号：箭头+i
        _arrow(msp, (cx - L, cy), (cx + L, cy), s, layer="标注")
        _t(msp, "i", (cx + L + 2 * s, cy), 2.0 * s,
           align=TextEntityAlignment.MIDDLE_LEFT, layer="文字")
    elif kind == "check_valve":  # 兼容旧版
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "阀门"})
        msp.add_lwpolyline([(cx - L * 0.2, cy - L * 0.3),
                            (cx - L * 0.2, cy + L * 0.3),
                            (cx + L * 0.5, cy)],
                           close=True, dxfattribs={"layer": "阀门"})
    else:
        msp.add_circle((cx, cy), L * 0.5, dxfattribs={"layer": "图框"})
