"""环保工程专用设备图块 v1.5。

按参考图及行业惯用画法，提供污水处理/环保工程常用设备的
平面/剖面/安装图绘制函数。

设备清单：
  泵类：自吸泵（双泵）、立式多级离心泵、潜水排污泵、螺杆泵
  搅拌类：立式搅拌机、潜水搅拌机、框式搅拌机、桨叶式
  加药类：加药装置（一体化）、计量泵、溶药罐
  消毒类：二氧化氯发生器、紫外线消毒器、臭氧发生器
  闸门类：启闭机、插板阀、堰门、铸铁镶铜闸门
  其他：格栅除污机、螺旋输送机、污泥脱水机、鼓风机

所有尺寸单位 mm，scale 为图纸比例因子（如 1:100 时 scale=100）。
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..standards.annotate import _t
from .fittings import _line, _poly, _circle, _arc, _hatch


# ══════════════════════════════════════════════════════════
#  泵类设备
# ══════════════════════════════════════════════════════════

def draw_self_priming_pump(msp, origin, scale: float = 100.0,
                           pump_type: str = "double",
                           dn: float = 80.0,
                           label: str = "",
                           layer: str = "设备",
                           tracker=None):
    """自吸泵安装图（参考图1：双泵自吸泵）。

    pump_type: "single"单泵 / "double"双泵
    绘制内容：泵体、电机、底座底板、进出口法兰、测压口、排气口、隔振垫
    """
    s = scale
    ox, oy = origin

    if pump_type == "double":
        # 双泵：左右对称布置
        pump_w = 12 * s   # 单泵宽度
        pump_h = 20 * s   # 泵总高（含电机）
        base_w = 30 * s   # 底座宽
        base_h = 3 * s    # 底座高
        spacing = 6 * s   # 两泵间距

        cx_left = ox + base_w * 0.3
        cx_right = ox + base_w * 0.7
        base_y = oy

        # 底座底板
        _poly(msp, [(ox, base_y), (ox + base_w, base_y),
                    (ox + base_w, base_y + base_h),
                    (ox, base_y + base_h)], layer)

        # 隔振垫（4个）
        pad_w = 2 * s
        pad_h = 1.5 * s
        for px in [ox + 2 * s, ox + base_w - 2 * s]:
            for py in [base_y - pad_h, base_y + base_h]:
                _poly(msp, [(px - pad_w / 2, py),
                            (px + pad_w / 2, py),
                            (px + pad_w / 2, py + pad_h),
                            (px - pad_w / 2, py + pad_h)],
                      "细实线")

        # 左右泵体
        for cx in [cx_left, cx_right]:
            # 泵体（下部蜗壳）
            pump_body_y = base_y + base_h
            pump_body_h = 8 * s
            _poly(msp, [(cx - pump_w / 2, pump_body_y),
                        (cx + pump_w / 2, pump_body_y),
                        (cx + pump_w / 2, pump_body_y + pump_body_h),
                        (cx - pump_w / 2, pump_body_y + pump_body_h)],
                  layer)
            # 蜗壳圆
            _circle(msp, (cx, pump_body_y + pump_body_h * 0.4),
                    pump_w * 0.4, layer)

            # 电机（上部）
            motor_y = pump_body_y + pump_body_h
            motor_h = 8 * s
            motor_w = pump_w * 0.8
            _poly(msp, [(cx - motor_w / 2, motor_y),
                        (cx + motor_w / 2, motor_y),
                        (cx + motor_w / 2, motor_y + motor_h),
                        (cx - motor_w / 2, motor_y + motor_h)],
                  layer)
            # 电机散热片（竖线）
            for i in range(5):
                mx = cx - motor_w / 2 + motor_w * (i + 1) / 6
                _line(msp, (mx, motor_y + s), (mx, motor_y + motor_h - s),
                      "细实线")
            # 电机顶部端盖
            _poly(msp, [(cx - motor_w / 2 - s, motor_y + motor_h),
                        (cx + motor_w / 2 + s, motor_y + motor_h),
                        (cx + motor_w / 2 + s, motor_y + motor_h + 1.5 * s),
                        (cx - motor_w / 2 - s, motor_y + motor_h + 1.5 * s)],
                  layer)
            # 接线盒
            _poly(msp, [(cx - 2 * s, motor_y + motor_h * 0.4),
                        (cx + 2 * s, motor_y + motor_h * 0.4),
                        (cx + 2 * s, motor_y + motor_h * 0.7),
                        (cx - 2 * s, motor_y + motor_h * 0.7)],
                  layer)

        # 中间连接管（双泵共用出口）
        manifold_y = base_y + base_h + pump_body_h * 0.4
        _line(msp, (cx_left + pump_w / 2, manifold_y),
              (cx_right - pump_w / 2, manifold_y), layer)
        # 总出口（向上）
        _line(msp, ((cx_left + cx_right) / 2, manifold_y),
              ((cx_left + cx_right) / 2, base_y + base_h + pump_body_h),
              layer)
        _circle(msp, ((cx_left + cx_right) / 2,
                      base_y + base_h + pump_body_h * 0.7),
                2 * s, layer)

        # 测压口 RP2（泵体上方）
        for cx in [cx_left, cx_right]:
            _circle(msp, (cx, pump_body_y + pump_body_h - s),
                    0.8 * s, layer)
            _line(msp, (cx, pump_body_y + pump_body_h - s),
                  (cx, pump_body_y + pump_body_h + s), layer)

        # 排气口 RP3
        _circle(msp, ((cx_left + cx_right) / 2,
                      base_y + base_h + pump_body_h + 2 * s),
                0.8 * s, layer)

        # 底板尺寸标注（简化）
        _line(msp, (ox, base_y - 4 * s),
              (ox + base_w, base_y - 4 * s), "尺寸标注")

    if label:
        _t(msp, label, (ox + base_w / 2, oy - 8 * s), 3.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
           tracker=tracker)

    if tracker:
        tracker.register(ox - 5 * s, oy - 10 * s,
                         ox + base_w + 5 * s, oy + 25 * s, margin=50)

    return (ox + base_w, oy + pump_h + base_h)


def draw_vertical_multistage_pump(msp, origin, scale: float = 100.0,
                                   dn: float = 50.0,
                                   n_stages: int = 4,
                                   label: str = "",
                                   layer: str = "设备",
                                   tracker=None):
    """立式多级离心泵（参考图2：CDL/CDLF 型）。

    n_stages: 级数（中间段数）
    绘制内容：电机、泵体多级段、吸入法兰、吐出法兰、中间吐出、底座
    """
    s = scale
    ox, oy = origin

    total_h = 30 * s
    body_w = 6 * s
    base_w = 10 * s
    base_h = 2 * s
    motor_h = 10 * s
    motor_w = 7 * s
    cx = ox + base_w / 2

    # 底座
    base_y = oy
    _poly(msp, [(cx - base_w / 2, base_y),
                (cx + base_w / 2, base_y),
                (cx + base_w / 2, base_y + base_h),
                (cx - base_w / 2, base_y + base_h)], layer)

    # 泵体多级段
    pump_y = base_y + base_h
    stage_h = 3 * s
    # 吸入段（底部）
    _poly(msp, [(cx - body_w / 2, pump_y),
                (cx + body_w / 2, pump_y),
                (cx + body_w / 2, pump_y + stage_h),
                (cx - body_w / 2, pump_y + stage_h)], layer)
    # 吸入法兰（左侧）
    _line(msp, (cx - body_w / 2, pump_y + stage_h * 0.3),
          (cx - body_w / 2 - 3 * s, pump_y + stage_h * 0.3), layer)
    _line(msp, (cx - body_w / 2 - 3 * s, pump_y + stage_h * 0.1),
          (cx - body_w / 2 - 3 * s, pump_y + stage_h * 0.5), layer)

    # 中间各级
    for i in range(n_stages):
        sy = pump_y + stage_h + i * stage_h
        _poly(msp, [(cx - body_w / 2, sy),
                    (cx + body_w / 2, sy),
                    (cx + body_w / 2, sy + stage_h),
                    (cx - body_w / 2, sy + stage_h)], layer)
        # 级间法兰（横线）
        _line(msp, (cx - body_w / 2 - s, sy),
              (cx + body_w / 2 + s, sy), "细实线")

    # 中间吐出（可选，右侧）
    mid_y = pump_y + stage_h * 2
    _line(msp, (cx + body_w / 2, mid_y),
          (cx + body_w / 2 + 4 * s, mid_y), layer)
    _line(msp, (cx + body_w / 2 + 4 * s, mid_y - s),
          (cx + body_w / 2 + 4 * s, mid_y + s), layer)

    # 吐出段（顶部）
    top_y = pump_y + stage_h * (n_stages + 1)
    _poly(msp, [(cx - body_w / 2, top_y),
                (cx + body_w / 2, top_y),
                (cx + body_w / 2, top_y + stage_h),
                (cx - body_w / 2, top_y + stage_h)], layer)
    # 吐出法兰（右侧）
    _line(msp, (cx + body_w / 2, top_y + stage_h * 0.5),
          (cx + body_w / 2 + 4 * s, top_y + stage_h * 0.5), layer)
    _line(msp, (cx + body_w / 2 + 4 * s, top_y + stage_h * 0.3),
          (cx + body_w / 2 + 4 * s, top_y + stage_h * 0.7), layer)

    # 电机
    motor_y = top_y + stage_h + 2 * s
    _poly(msp, [(cx - motor_w / 2, motor_y),
                (cx + motor_w / 2, motor_y),
                (cx + motor_w / 2, motor_y + motor_h),
                (cx - motor_w / 2, motor_y + motor_h)], layer)
    # 电机散热片
    for i in range(6):
        mx = cx - motor_w / 2 + motor_w * (i + 0.5) / 6
        _line(msp, (mx, motor_y + s), (mx, motor_y + motor_h - s),
              "细实线")
    # 电机顶部
    _poly(msp, [(cx - motor_w / 2 - s, motor_y + motor_h),
                (cx + motor_w / 2 + s, motor_y + motor_h),
                (cx + motor_w / 2 + s, motor_y + motor_h + 2 * s),
                (cx - motor_w / 2 - s, motor_y + motor_h + 2 * s)], layer)
    # 接线盒
    _poly(msp, [(cx - 2.5 * s, motor_y + motor_h * 0.3),
                (cx + 2.5 * s, motor_y + motor_h * 0.3),
                (cx + 2.5 * s, motor_y + motor_h * 0.6),
                (cx - 2.5 * s, motor_y + motor_h * 0.6)], layer)

    # 联轴器（泵与电机之间）
    _poly(msp, [(cx - body_w / 3, top_y + stage_h + 0.5 * s),
                (cx + body_w / 3, top_y + stage_h + 0.5 * s),
                (cx + body_w / 3, motor_y - 0.5 * s),
                (cx - body_w / 3, motor_y - 0.5 * s)], layer)

    # 安装螺栓（底座4个）
    for bx in [cx - base_w / 2 + s, cx + base_w / 2 - s]:
        for by in [base_y + base_h / 2]:
            _circle(msp, (bx, by), 0.5 * s, "细实线")

    if label:
        _t(msp, label, (cx, oy - 5 * s), 3.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
           tracker=tracker)

    if tracker:
        tracker.register(ox - 8 * s, oy - 8 * s,
                         ox + base_w + 8 * s, oy + total_h + 5 * s, margin=50)

    return (ox + base_w, oy + total_h)


def draw_submersible_pump(msp, center, scale: float = 100.0,
                           dn: float = 100.0,
                           label: str = "",
                           layer: str = "设备",
                           tracker=None):
    """潜水排污泵（WQ型）。

    绘制内容：泵体、进水口、出水口、吊环、电缆
    """
    s = scale
    cx, cy = center

    body_w = 6 * s
    body_h = 10 * s

    # 泵体（上部电机 + 下部叶轮）
    _poly(msp, [(cx - body_w / 2, cy - body_h / 2),
                (cx + body_w / 2, cy - body_h / 2),
                (cx + body_w / 2, cy + body_h / 2),
                (cx - body_w / 2, cy + body_h / 2)], layer)

    # 进水口（底部滤网）
    _poly(msp, [(cx - body_w * 0.4, cy + body_h / 2),
                (cx + body_w * 0.4, cy + body_h / 2),
                (cx + body_w * 0.4, cy + body_h / 2 + 2 * s),
                (cx - body_w * 0.4, cy + body_h / 2 + 2 * s)], layer)
    for i in range(4):
        gx = cx - body_w * 0.3 + i * body_w * 0.2
        _line(msp, (gx, cy + body_h / 2 + 0.5 * s),
              (gx, cy + body_h / 2 + 1.5 * s), "细实线")

    # 出水口（侧面）
    _line(msp, (cx + body_w / 2, cy),
          (cx + body_w / 2 + 4 * s, cy), layer)
    _line(msp, (cx + body_w / 2 + 4 * s, cy - 1.5 * s),
          (cx + body_w / 2 + 4 * s, cy + 1.5 * s), layer)

    # 吊环（顶部）
    _arc(msp, (cx, cy - body_h / 2), 1.5 * s, 180, 360, layer)
    _line(msp, (cx - 1.5 * s, cy - body_h / 2),
          (cx + 1.5 * s, cy - body_h / 2), layer)

    # 电缆
    _line(msp, (cx - body_w / 2 + s, cy - body_h / 2 + s),
          (cx - body_w / 2 - 2 * s, cy - body_h / 2 - 3 * s),
          "细实线")

    if label:
        _t(msp, label, (cx, cy - body_h / 2 - 6 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)

    return (cx + body_w / 2 + 4 * s, cy + body_h / 2 + 2 * s)


# ══════════════════════════════════════════════════════════
#  搅拌设备
# ══════════════════════════════════════════════════════════

def draw_mixer(msp, center, scale: float = 100.0,
               mixer_type: str = "paddle",
               shaft_len: float = 20.0,
               label: str = "",
               layer: str = "设备",
               tracker=None):
    """搅拌机（立式）。

    mixer_type: "paddle"桨叶式 / "anchor"框式 / "propeller"推进式 /
                "turbine"涡轮式 / "submersible"潜水式
    """
    s = scale
    cx, cy = center
    shaft_l = shaft_len * s

    # 电机（顶部）
    motor_w = 5 * s
    motor_h = 4 * s
    motor_y = cy - shaft_l
    _poly(msp, [(cx - motor_w / 2, motor_y),
                (cx + motor_w / 2, motor_y),
                (cx + motor_w / 2, motor_y + motor_h),
                (cx - motor_w / 2, motor_y + motor_h)], layer)
    _t(msp, "M", (cx, motor_y + motor_h / 2 - 0.5 * s), 2.0 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    # 减速机
    reducer_y = motor_y + motor_h
    reducer_h = 2 * s
    _poly(msp, [(cx - motor_w / 2 + s, reducer_y),
                (cx + motor_w / 2 - s, reducer_y),
                (cx + motor_w / 2 - s, reducer_y + reducer_h),
                (cx - motor_w / 2 + s, reducer_y + reducer_h)], layer)

    # 搅拌轴
    shaft_top = reducer_y + reducer_h
    _line(msp, (cx, shaft_top), (cx, cy), layer)

    # 桨叶
    if mixer_type == "paddle":
        # 桨叶式：两层平直桨
        for y_off in [shaft_l * 0.5, shaft_l * 0.8]:
            py = motor_y + y_off
            blade_w = 6 * s
            _line(msp, (cx - blade_w / 2, py),
                  (cx + blade_w / 2, py), layer)
            _line(msp, (cx - blade_w / 2, py - s),
                  (cx - blade_w / 2, py + s), layer)
            _line(msp, (cx + blade_w / 2, py - s),
                  (cx + blade_w / 2, py + s), layer)

    elif mixer_type == "anchor":
        # 框式/锚式：U形框
        frame_w = 7 * s
        frame_h = shaft_l * 0.6
        fy = motor_y + shaft_l * 0.35
        _poly(msp, [(cx - frame_w / 2, fy),
                    (cx + frame_w / 2, fy),
                    (cx + frame_w / 2, fy + frame_h),
                    (cx - frame_w / 2, fy + frame_h)],
              layer, close=False)
        # 底部弧形（锚式）
        _arc(msp, (cx, fy + frame_h), frame_w / 2, 180, 360, layer)
        # 横梁
        _line(msp, (cx - frame_w / 2, fy + frame_h * 0.5),
              (cx + frame_w / 2, fy + frame_h * 0.5), layer)

    elif mixer_type == "propeller":
        # 推进式：三叶螺旋
        blade_r = 3 * s
        blade_y = cy - 2 * s
        for i in range(3):
            angle = i * 120
            rad = math.radians(angle)
            bx = cx + blade_r * math.cos(rad)
            by = blade_y + blade_r * 0.3 * math.sin(rad)
            _line(msp, (cx, blade_y), (bx, by), layer)
        # 轮毂
        _circle(msp, (cx, blade_y), 0.8 * s, layer)

    elif mixer_type == "turbine":
        # 涡轮式：圆盘 + 多叶片
        disc_r = 3 * s
        disc_y = cy - 3 * s
        _circle(msp, (cx, disc_y), disc_r, layer)
        for i in range(6):
            angle = i * 60
            rad = math.radians(angle)
            bx = cx + disc_r * 0.7 * math.cos(rad)
            by = disc_y + disc_r * 0.7 * math.sin(rad)
            tx = cx + disc_r * math.cos(rad)
            ty = disc_y + disc_r * math.sin(rad)
            _line(msp, (bx, by), (tx, ty), layer)

    elif mixer_type == "submersible":
        # 潜水搅拌机：水平安装
        body_w = 5 * s
        body_h = 3 * s
        _poly(msp, [(cx - body_w / 2, cy - body_h / 2),
                    (cx + body_w / 2, cy - body_h / 2),
                    (cx + body_w / 2, cy + body_h / 2),
                    (cx - body_w / 2, cy + body_h / 2)], layer)
        # 螺旋桨
        _circle(msp, (cx + body_w / 2 + 2 * s, cy), 2 * s, layer)
        for i in range(3):
            angle = i * 120
            rad = math.radians(angle)
            _line(msp, (cx + body_w / 2 + 2 * s, cy),
                  (cx + body_w / 2 + 2 * s + 2 * s * math.cos(rad),
                   cy + 2 * s * math.sin(rad)), layer)
        # 安装支架
        _line(msp, (cx - body_w / 2, cy), (cx - body_w / 2 - 3 * s, cy), layer)

    if label:
        _t(msp, label, (cx, motor_y - 3 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)

    return (cx + motor_w, cy)


# ══════════════════════════════════════════════════════════
#  加药装置
# ══════════════════════════════════════════════════════════

def draw_dosing_system(msp, origin, scale: float = 100.0,
                        system_type: str = "pac",
                        label: str = "",
                        layer: str = "设备",
                        tracker=None):
    """一体化加药装置。

    system_type: "pac" PAC加药 / "pam" PAM加药 / "naclo"次氯酸钠 /
                 "acid"加酸 / "alkali"加碱 / "carbon"活性炭
    绘制内容：溶药罐、搅拌器、计量泵、液位计、管路阀门
    """
    s = scale
    ox, oy = origin

    tank_w = 12 * s
    tank_h = 14 * s
    pump_w = 5 * s
    pump_h = 6 * s

    # 底座/框架
    base_h = 2 * s
    total_w = tank_w + pump_w + 6 * s
    _poly(msp, [(ox, oy), (ox + total_w, oy),
                (ox + total_w, oy + base_h),
                (ox, oy + base_h)], layer)

    # 溶药罐
    tank_x = ox + 2 * s
    tank_y = oy + base_h
    _poly(msp, [(tank_x, tank_y), (tank_x + tank_w, tank_y),
                (tank_x + tank_w, tank_y + tank_h),
                (tank_x, tank_y + tank_h)], layer)
    # 罐顶
    _poly(msp, [(tank_x - s, tank_y + tank_h),
                (tank_x + tank_w + s, tank_y + tank_h),
                (tank_x + tank_w + s, tank_y + tank_h + 1.5 * s),
                (tank_x - s, tank_y + tank_h + 1.5 * s)], layer)
    # 液位计（侧装）
    _line(msp, (tank_x - 2 * s, tank_y + 2 * s),
          (tank_x - 2 * s, tank_y + tank_h - 2 * s), "细实线")
    _circle(msp, (tank_x - 2 * s, tank_y + 2 * s), 0.5 * s, layer)
    _circle(msp, (tank_x - 2 * s, tank_y + tank_h - 2 * s), 0.5 * s, layer)

    # 搅拌器（罐顶）
    mixer_cx = tank_x + tank_w / 2
    _line(msp, (mixer_cx, tank_y + tank_h + 1.5 * s),
          (mixer_cx, tank_y + tank_h * 0.3), layer)
    # 桨叶
    _line(msp, (mixer_cx - 3 * s, tank_y + tank_h * 0.4),
          (mixer_cx + 3 * s, tank_y + tank_h * 0.4), layer)
    _line(msp, (mixer_cx - 2 * s, tank_y + tank_h * 0.6),
          (mixer_cx + 2 * s, tank_y + tank_h * 0.6), layer)
    # 电机
    _poly(msp, [(mixer_cx - 2 * s, tank_y + tank_h + 1.5 * s),
                (mixer_cx + 2 * s, tank_y + tank_h + 1.5 * s),
                (mixer_cx + 2 * s, tank_y + tank_h + 5 * s),
                (mixer_cx - 2 * s, tank_y + tank_h + 5 * s)], layer)

    # 计量泵（右侧）
    pump_x = tank_x + tank_w + 3 * s
    pump_y = oy + base_h + 2 * s
    _poly(msp, [(pump_x, pump_y), (pump_x + pump_w, pump_y),
                (pump_x + pump_w, pump_y + pump_h),
                (pump_x, pump_y + pump_h)], layer)
    _t(msp, "计量泵", (pump_x + pump_w / 2, pump_y + pump_h / 2 - 0.5 * s),
       1.8 * s, align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")
    # 泵电机
    _poly(msp, [(pump_x + 0.5 * s, pump_y + pump_h),
                (pump_x + pump_w - 0.5 * s, pump_y + pump_h),
                (pump_x + pump_w - 0.5 * s, pump_y + pump_h + 3 * s),
                (pump_x + 0.5 * s, pump_y + pump_h + 3 * s)], layer)

    # 连接管路
    # 罐出液 → 泵入口
    _line(msp, (tank_x + tank_w, tank_y + 3 * s),
          (pump_x, tank_y + 3 * s), "管道-污水")
    _line(msp, (pump_x, tank_y + 3 * s),
          (pump_x, pump_y + pump_h * 0.3), "管道-污水")
    # 泵出口（向上）
    _line(msp, (pump_x + pump_w, pump_y + pump_h * 0.3),
          (pump_x + pump_w + 2 * s, pump_y + pump_h * 0.3), "管道-污水")

    # 加药类型标注
    type_map = {
        "pac": "PAC 加药装置",
        "pam": "PAM 加药装置",
        "naclo": "NaClO 加药装置",
        "acid": "加酸装置",
        "alkali": "加碱装置",
        "carbon": "活性炭加药装置",
    }
    type_name = type_map.get(system_type, "加药装置")

    if label:
        _t(msp, label, (ox + total_w / 2, oy - 4 * s), 3.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
           tracker=tracker)
    else:
        _t(msp, type_name, (ox + total_w / 2, oy - 4 * s), 3.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
           tracker=tracker)

    if tracker:
        tracker.register(ox - 3 * s, oy - 7 * s,
                         ox + total_w + 3 * s, oy + tank_h + 8 * s, margin=50)

    return (ox + total_w, oy + tank_h + 7 * s)


# ══════════════════════════════════════════════════════════
#  消毒设备
# ══════════════════════════════════════════════════════════

def draw_clo2_generator(msp, origin, scale: float = 100.0,
                         capacity: str = "500g/h",
                         label: str = "",
                         layer: str = "设备",
                         tracker=None):
    """二氧化氯发生器（参考图4）。

    绘制内容：发生器主体、原料罐、计量泵、控制面板、出液口
    """
    s = scale
    ox, oy = origin

    body_w = 12 * s
    body_h = 20 * s
    base_h = 2 * s

    # 底座
    _poly(msp, [(ox, oy), (ox + body_w, oy),
                (ox + body_w, oy + base_h),
                (ox, oy + base_h)], layer)

    # 主体柜
    body_y = oy + base_h
    _poly(msp, [(ox, body_y), (ox + body_w, body_y),
                (ox + body_w, body_y + body_h),
                (ox, body_y + body_h)], layer)

    # 控制面板（上部）
    panel_h = 5 * s
    _poly(msp, [(ox + s, body_y + body_h - panel_h - s),
                (ox + body_w - s, body_y + body_h - panel_h - s),
                (ox + body_w - s, body_y + body_h - s),
                (ox + s, body_y + body_h - s)], "细实线")
    # 显示屏
    _poly(msp, [(ox + 2 * s, body_y + body_h - 4 * s),
                (ox + 6 * s, body_y + body_h - 2 * s),
                (ox + 6 * s, body_y + body_h - 4 * s),
                (ox + 2 * s, body_y + body_h - 2 * s)], "细实线")
    # 按钮
    for i in range(3):
        _circle(msp, (ox + 8 * s + i * 1.5 * s, body_y + body_h - 3 * s),
                0.4 * s, "细实线")

    # 反应釜（中部，透明观察窗）
    reactor_cx = ox + body_w / 2
    reactor_cy = body_y + body_h * 0.5
    _circle(msp, (reactor_cx, reactor_cy), 3 * s, layer)
    _circle(msp, (reactor_cx, reactor_cy), 2 * s, "细实线")

    # 计量泵（下部左右各一）
    pump_w = 3 * s
    pump_h = 4 * s
    for px in [ox + 2 * s, ox + body_w - 2 * s - pump_w]:
        _poly(msp, [(px, body_y + 2 * s),
                    (px + pump_w, body_y + 2 * s),
                    (px + pump_w, body_y + 2 * s + pump_h),
                    (px, body_y + 2 * s + pump_h)], layer)

    # 进出水口
    # 进水（左下）
    _line(msp, (ox, body_y + 4 * s),
          (ox - 2 * s, body_y + 4 * s), "管道-污水")
    _circle(msp, (ox - 2 * s, body_y + 4 * s), 0.5 * s, layer)
    # 出液（右下）
    _line(msp, (ox + body_w, body_y + 4 * s),
          (ox + body_w + 2 * s, body_y + 4 * s), "管道-污水")
    _circle(msp, (ox + body_w + 2 * s, body_y + 4 * s), 0.5 * s, layer)

    # 排气口（顶部）
    _line(msp, (ox + body_w / 2, body_y + body_h),
          (ox + body_w / 2, body_y + body_h + 3 * s), layer)
    _circle(msp, (ox + body_w / 2, body_y + body_h + 3 * s), 0.5 * s, layer)

    # 铭牌
    _poly(msp, [(ox + 2 * s, body_y + body_h * 0.75),
                (ox + body_w - 2 * s, body_y + body_h * 0.75),
                (ox + body_w - 2 * s, body_y + body_h * 0.85),
                (ox + 2 * s, body_y + body_h * 0.85)], "细实线")
    _t(msp, f"ClO₂ {capacity}",
       (ox + body_w / 2, body_y + body_h * 0.8 - 0.5 * s),
       2.0 * s, align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    if label:
        _t(msp, label, (ox + body_w / 2, oy - 4 * s), 3.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
           tracker=tracker)

    if tracker:
        tracker.register(ox - 4 * s, oy - 6 * s,
                         ox + body_w + 4 * s, oy + body_h + base_h + 5 * s,
                         margin=50)

    return (ox + body_w, oy + body_h + base_h + 3 * s)


# ══════════════════════════════════════════════════════════
#  闸门 / 启闭机
# ══════════════════════════════════════════════════════════

def draw_gate_valve(msp, origin, scale: float = 100.0,
                     gate_type: str = "cast_iron",
                     width: float = 600.0,
                     label: str = "",
                     layer: str = "设备",
                     tracker=None):
    """闸门 / 插板阀 / 堰门（参考图4）。

    gate_type:
        "cast_iron" 铸铁镶铜闸门（含启闭机）
        "slide" 插板阀（电动/手动）
        "weir" 堰门（可调节溢流堰）
        "hoist" 启闭机（单独）
    """
    s = scale
    ox, oy = origin

    if gate_type == "cast_iron":
        # 铸铁镶铜闸门 + 启闭机
        gate_w = 8 * s
        gate_h = 12 * s
        frame_w = 1.5 * s

        # 门框
        _poly(msp, [(ox, oy), (ox + gate_w, oy),
                    (ox + gate_w, oy + gate_h),
                    (ox, oy + gate_h)], layer)
        # 门板
        _poly(msp, [(ox + frame_w, oy + frame_w),
                    (ox + gate_w - frame_w, oy + frame_w),
                    (ox + gate_w - frame_w, oy + gate_h - frame_w),
                    (ox + frame_w, oy + gate_h - frame_w)], "细实线")
        # 加强筋
        for i in range(3):
            ry = oy + frame_w + (i + 1) * (gate_h - 2 * frame_w) / 4
            _line(msp, (ox + frame_w, ry),
                  (ox + gate_w - frame_w, ry), "细实线")

        # 启闭机（顶部）
        hoist_cx = ox + gate_w / 2
        hoist_y = oy + gate_h
        # 螺杆
        _line(msp, (hoist_cx, hoist_y), (hoist_cx, hoist_y + 4 * s), layer)
        # 启闭机箱体
        _poly(msp, [(hoist_cx - 3 * s, hoist_y + 4 * s),
                    (hoist_cx + 3 * s, hoist_y + 4 * s),
                    (hoist_cx + 3 * s, hoist_y + 8 * s),
                    (hoist_cx - 3 * s, hoist_y + 8 * s)], layer)
        # 手轮
        _circle(msp, (hoist_cx, hoist_y + 10 * s), 2 * s, layer)
        _line(msp, (hoist_cx - 2 * s, hoist_y + 10 * s),
              (hoist_cx + 2 * s, hoist_y + 10 * s), layer)
        _line(msp, (hoist_cx, hoist_y + 8 * s),
              (hoist_cx, hoist_y + 10 * s - 2 * s), layer)

    elif gate_type == "slide":
        # 插板阀
        body_w = 10 * s
        body_h = 6 * s
        _poly(msp, [(ox, oy), (ox + body_w, oy),
                    (ox + body_w, oy + body_h),
                    (ox, oy + body_h)], layer)
        # 阀板
        _poly(msp, [(ox + s, oy + s),
                    (ox + body_w - s, oy + s),
                    (ox + body_w - s, oy + body_h - s),
                    (ox + s, oy + body_h - s)], "细实线")
        # 阀杆
        cx = ox + body_w / 2
        _line(msp, (cx, oy + body_h), (cx, oy + body_h + 5 * s), layer)
        # 电动执行器
        _poly(msp, [(cx - 2.5 * s, oy + body_h + 5 * s),
                    (cx + 2.5 * s, oy + body_h + 5 * s),
                    (cx + 2.5 * s, oy + body_h + 9 * s),
                    (cx - 2.5 * s, oy + body_h + 9 * s)], layer)
        _t(msp, "M", (cx, oy + body_h + 7 * s - 0.5 * s), 2.0 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字")

    elif gate_type == "weir":
        # 堰门
        weir_w = 10 * s
        weir_h = 4 * s
        # 堰体
        _poly(msp, [(ox, oy), (ox + weir_w, oy),
                    (ox + weir_w, oy + weir_h),
                    (ox, oy + weir_h)], layer)
        # 溢流口（可调）
        _poly(msp, [(ox + 2 * s, oy + weir_h),
                    (ox + weir_w - 2 * s, oy + weir_h),
                    (ox + weir_w - 2 * s, oy + weir_h + 2 * s),
                    (ox + 2 * s, oy + weir_h + 2 * s)], "细实线")
        # 调节螺杆
        cx = ox + weir_w / 2
        _line(msp, (cx, oy + weir_h + 2 * s),
              (cx, oy + weir_h + 7 * s), layer)
        _circle(msp, (cx, oy + weir_h + 9 * s), 2 * s, layer)

    elif gate_type == "hoist":
        # 单独启闭机（侧摇式）
        body_w = 4 * s
        body_h = 6 * s
        cx = ox + body_w / 2
        # 箱体
        _poly(msp, [(ox, oy), (ox + body_w, oy),
                    (ox + body_w, oy + body_h),
                    (ox, oy + body_h)], layer)
        # 螺杆（向下）
        _line(msp, (cx, oy), (cx, oy - 6 * s), layer)
        # 手轮（侧摇）
        _circle(msp, (ox - 2 * s, oy + body_h / 2), 2 * s, layer)
        _line(msp, (ox, oy + body_h / 2),
              (ox - 2 * s + 2 * s, oy + body_h / 2), layer)

    if label:
        _t(msp, label, (ox + 5 * s, oy - 4 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)

    return (ox + 10 * s, oy + 12 * s)


# ══════════════════════════════════════════════════════════
#  格栅 / 输送机 / 脱水机
# ══════════════════════════════════════════════════════════

def draw_bar_screen(msp, origin, scale: float = 100.0,
                     screen_type: str = "mechanical",
                     label: str = "",
                     layer: str = "设备",
                     tracker=None):
    """格栅除污机。

    screen_type: "mechanical"机械格栅 / "manual"人工格栅 /
                 "rotary"回转式格栅 / "step"阶梯格栅
    """
    s = scale
    ox, oy = origin

    if screen_type == "mechanical":
        # 机械格栅：倾斜安装
        width = 8 * s
        height = 16 * s
        angle = 75  # 安装角度

        rad = math.radians(angle)
        # 框架
        x1, y1 = ox, oy
        x2 = ox + width * math.cos(math.radians(90 - angle))
        y2 = oy + height
        _poly(msp, [(x1, y1), (x1 + 2 * s, y1),
                    (x2 + 2 * s, y2), (x2, y2)],
              layer, close=False)
        # 栅条
        n_bars = 8
        for i in range(n_bars):
            t = (i + 1) / (n_bars + 1)
            bx = x1 + t * (x2 - x1)
            by = y1 + t * (y2 - y1)
            _line(msp, (bx, by), (bx + 2 * s, by + 0.5 * s), "细实线")

        # 上部驱动装置
        _poly(msp, [(x2 - s, y2 - 2 * s),
                    (x2 + 4 * s, y2 - 2 * s),
                    (x2 + 4 * s, y2 + 2 * s),
                    (x2 - s, y2 + 2 * s)], layer)
        # 电机
        _poly(msp, [(x2 + 4 * s, y2 - s),
                    (x2 + 7 * s, y2 - s),
                    (x2 + 7 * s, y2 + s),
                    (x2 + 4 * s, y2 + s)], layer)

    elif screen_type == "manual":
        # 人工格栅：垂直
        width = 6 * s
        height = 10 * s
        _poly(msp, [(ox, oy), (ox + width, oy),
                    (ox + width, oy + height),
                    (ox, oy + height)], layer)
        for i in range(6):
            gx = ox + (i + 1) * width / 7
            _line(msp, (gx, oy + s), (gx, oy + height - s), "细实线")

    if label:
        _t(msp, label, (ox + 4 * s, oy - 4 * s), 2.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
           tracker=tracker)

    return (ox + 15 * s, oy + 16 * s)


# ══════════════════════════════════════════════════════════
#  设备图例表（快速生成图例页）
# ══════════════════════════════════════════════════════════

ENV_EQUIPMENT_LEGEND = [
    # (函数名, 中文名, 规格示例)
    ("self_priming_pump", "自吸泵", "Q=50m³/h H=20m"),
    ("vertical_multistage_pump", "立式多级离心泵", "CDL4-80"),
    ("submersible_pump", "潜水排污泵", "WQ50-10-3"),
    ("mixer_paddle", "桨叶式搅拌机", "N=2.2kW"),
    ("mixer_anchor", "框式搅拌机", "N=4kW"),
    ("mixer_submersible", "潜水搅拌机", "N=1.5kW"),
    ("dosing_pac", "PAC加药装置", "500L 一用一备"),
    ("dosing_pam", "PAM加药装置", "1000L 一体化"),
    ("clo2_generator", "二氧化氯发生器", "500g/h"),
    ("gate_cast_iron", "铸铁镶铜闸门", "600×600"),
    ("gate_slide", "电动插板阀", "DN300"),
    ("gate_weir", "可调式堰门", "B=800"),
    ("hoist", "侧摇式启闭机", "3t"),
    ("screen_mechanical", "机械格栅", "B=600 b=5mm"),
]
