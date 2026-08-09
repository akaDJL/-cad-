"""模块 18 —— 自走式谷物联合收割机侧视图（割台 + 脱粒 + 驾驶室）。

复用 envcad：GB/T 17450 图层体系、仿宋 GB2312 文字样式、
``standards.dim`` 线性标注、``standards.annotate.draw_leader`` 指引线、
``_common.wheel`` 轮胎画法（与 tractor 模块共用）。

标准依据：
  * GB/T 14689—2008 图纸幅面 / GB/T 4457.4—2002 图线
  * GB/T 8097—2025 收获机械 联合收割机 试验方法  # TODO: verify against GB/T 8097（2025版替代2008版，2025-12-01实施）
    （割幅、喂入量、脱粒滚筒直径等术语；envcad standards_kb.json 未收录农机行业，
     故全部数值以参数传入，不做硬编码校核）

全部尺寸为实物 mm。
"""
from __future__ import annotations

import math
from typing import Dict

from ._common import (
    L_CENTER, L_HIDDEN, L_MED, L_THICK, L_THIN,
    centerline, cross_center, dim_h, dim_v, ground_line, leader, poly, rect,
    wheel,
)

#: 5kg/s 级自走式谷物联合收割机默认外廓（实物 mm）
DEFAULTS: Dict[str, float] = {
    "header_len": 1250.0,       # 割台纵向长度（侧视可见）
    "header_h": 900.0,          # 割台高度
    "cut_height": 180.0,        # 割茬高度（切割器离地）
    "reel_d": 1050.0,           # 拨禾轮直径
    "reel_bats": 6.0,           # 拨禾轮压板数
    "feeder_len": 1500.0,       # 输送槽长度
    "body_len": 4200.0,         # 机体（脱粒-清选）长度
    "body_h": 1900.0,           # 机体高度
    "drum_d": 600.0,            # 脱粒滚筒直径
    "tank_h": 950.0,            # 粮箱高度
    "tank_len": 2400.0,         # 粮箱长度
    "cab_len": 1350.0,          # 驾驶室长度
    "cab_h": 1450.0,            # 驾驶室高度
    "front_wheel_d": 1300.0,    # 前驱动轮外径
    "rear_wheel_d": 780.0,      # 后转向轮外径
    "auger_len": 3200.0,        # 卸粮搅龙长度
    "auger_angle": 22.0,        # 卸粮搅龙仰角（°）
    "chassis_h": 780.0,         # 机体底板高
}


def _draw_header(msp, x0, y_ground, p):
    """割台：切割器 + 输送搅龙壳体 + 分禾器（粗实线轮廓）。"""
    y_cut = y_ground + p["cut_height"]
    x1 = x0 + p["header_len"]
    poly(msp, [
        (x0, y_cut),                                  # 切割器刀尖
        (x0 + p["header_len"] * 0.18, y_cut - 60),    # 分禾器下沿
        (x1, y_cut + 40),
        (x1, y_cut + p["header_h"]),
        (x0 + p["header_len"] * 0.10, y_cut + p["header_h"] * 0.82),
    ], layer=L_THICK, closed=True)
    # 切割器刀齿（细实线锯齿）
    n = 10
    for i in range(n):
        tx = x0 + i * (p["header_len"] * 0.16) / n
        msp.add_line((tx, y_cut), (tx + 40, y_cut - 45),
                     dxfattribs={"layer": L_THIN})
    # 割台搅龙（虚线，壳体内不可见）
    ay = y_cut + p["header_h"] * 0.45
    msp.add_circle((x1 - 260, ay), 190, dxfattribs={"layer": L_HIDDEN})
    return x1, y_cut


def _draw_reel(msp, cx, cy, d, n_bats, scale):
    """拨禾轮：节圆 + 均布压板（弹齿杆）。"""
    r = d / 2.0
    msp.add_circle((cx, cy), r, dxfattribs={"layer": L_MED})
    for i in range(int(n_bats)):
        a = 2 * math.pi * i / int(n_bats)
        bx, by = cx + r * math.cos(a), cy + r * math.sin(a)
        msp.add_line((cx, cy), (bx, by), dxfattribs={"layer": L_THIN})
        # 压板（切向短线）
        msp.add_line((bx - 90 * math.sin(a), by + 90 * math.cos(a)),
                     (bx + 90 * math.sin(a), by - 90 * math.cos(a)),
                     dxfattribs={"layer": L_MED})
    cross_center(msp, cx, cy, r, scale)


def _draw_body(msp, x0, y0, p):
    """机体：脱粒清选箱体 + 脱粒滚筒 + 凹板筛 + 逐稿器。"""
    x1 = x0 + p["body_len"]
    y1 = y0 + p["body_h"]
    rect(msp, x0, y0, x1, y1, layer=L_THICK)
    # 脱粒滚筒（前部）
    dx = x0 + p["drum_d"] * 0.85
    dy = y0 + p["body_h"] * 0.62
    msp.add_circle((dx, dy), p["drum_d"] / 2, dxfattribs={"layer": L_MED})
    msp.add_circle((dx, dy), p["drum_d"] / 2 * 0.35, dxfattribs={"layer": L_THIN})
    cross_center(msp, dx, dy, p["drum_d"] / 2, 50.0)
    # 凹板筛（滚筒下 130° 圆弧）
    msp.add_arc((dx, dy), p["drum_d"] / 2 + 55, start_angle=200, end_angle=340,
                dxfattribs={"layer": L_MED})
    # 逐稿器 / 清选筛（细实线水平层）
    for i, f in enumerate((0.28, 0.42)):
        sy = y0 + p["body_h"] * f
        msp.add_line((dx + p["drum_d"], sy), (x1 - 120, sy),
                     dxfattribs={"layer": L_THIN})
    # 抛草口
    poly(msp, [(x1, y0 + p["body_h"] * 0.18), (x1 + 320, y0 + p["body_h"] * 0.10),
               (x1 + 320, y0 + p["body_h"] * 0.42), (x1, y0 + p["body_h"] * 0.50)],
         layer=L_MED, closed=True)
    return x1, y1, (dx, dy)


def _draw_auger(msp, x0, y0, length, angle_deg, layer=L_MED):
    """卸粮搅龙：等宽斜筒 + 端部卸粮口。"""
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    w = 220.0
    px, py = -uy * w / 2, ux * w / 2
    x1, y1 = x0 - ux * length, y0 + uy * length
    poly(msp, [(x0 + px, y0 + py), (x1 + px, y1 + py),
               (x1 - px, y1 - py), (x0 - px, y0 - py)],
         layer=layer, closed=True)
    # 卸粮口
    rect(msp, x1 - 200, y1 - 320, x1 + 120, y1 - 120, layer=layer)
    return (x1, y1)


def draw_combine(msp, x: float, y: float, scale: float = 50.0,
                 with_dims: bool = True, with_labels: bool = True,
                 tracker=None, **params) -> Dict[str, object]:
    """绘制自走式联合收割机侧视外形图（机头朝左）。

    Args:
        msp: ezdxf modelspace
        x, y: 插入基点 —— 割台切割器刀尖正下方的**地平线**点（实物 mm）
        scale: 出图比例倒数
        with_dims / with_labels: 是否绘制尺寸 / 指引线标注
        **params: 覆盖 :data:`DEFAULTS`（实物 mm，如 body_len=4600）

    Returns:
        dict：``bbox``、``drum_center``、``length``、``height``
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})

    ground_line(msp, x - 500, x + 12000, y, scale, n_ticks=30)

    # ── 割台 ──
    x_hd_end, y_cut = _draw_header(msp, x, y, p)
    # ── 拨禾轮（悬于割台前上方）──
    reel_cx = x + p["header_len"] * 0.42
    reel_cy = y_cut + p["header_h"] * 0.90 + p["reel_d"] * 0.22
    _draw_reel(msp, reel_cx, reel_cy, p["reel_d"], p["reel_bats"], scale)
    # 拨禾轮支臂
    poly(msp, [(reel_cx, reel_cy), (x_hd_end + 260, y_cut + p["header_h"] * 0.95)],
         layer=L_MED)

    # ── 输送槽（倾斜，接机体）──
    y_body0 = y + p["chassis_h"]
    x_body0 = x_hd_end + p["feeder_len"]
    poly(msp, [(x_hd_end, y_cut + 60), (x_body0, y_body0 + 120),
               (x_body0, y_body0 + p["body_h"] * 0.55),
               (x_hd_end, y_cut + p["header_h"])],
         layer=L_THICK, closed=True)

    # ── 机体（脱粒 + 清选）──
    x_body1, y_body1, drum_c = _draw_body(msp, x_body0, y_body0, p)

    # ── 粮箱（机体上方后部）──
    tank_x0 = x_body0 + p["body_len"] * 0.32
    tank_x1 = min(tank_x0 + p["tank_len"], x_body1)
    poly(msp, [(tank_x0, y_body1), (tank_x1, y_body1),
               (tank_x1, y_body1 + p["tank_h"]),
               (tank_x0 - 220, y_body1 + p["tank_h"])],
         layer=L_THICK, closed=True)

    # ── 驾驶室（机体上方前部）──
    cab_x0 = x_body0 - 120
    cab_x1 = cab_x0 + p["cab_len"]
    poly(msp, [(cab_x0, y_body1), (cab_x1, y_body1),
               (cab_x1, y_body1 + p["cab_h"]),
               (cab_x0 + 180, y_body1 + p["cab_h"]),
               (cab_x0, y_body1 + p["cab_h"] * 0.45)],
         layer=L_THICK, closed=True)
    rect(msp, cab_x0 + 260, y_body1 + p["cab_h"] * 0.42,
         cab_x1 - 140, y_body1 + p["cab_h"] * 0.86, layer=L_THIN)

    # ── 卸粮搅龙（自粮箱顶向前上方伸出）──
    auger_end = _draw_auger(msp, tank_x0 + 200, y_body1 + p["tank_h"] * 0.78,
                            p["auger_len"], p["auger_angle"])

    # ── 行走系 ──
    fw_cx = x_body0 + p["body_len"] * 0.22
    rw_cx = x_body1 - p["body_len"] * 0.12
    wheel(msp, fw_cx, y + p["front_wheel_d"] / 2, p["front_wheel_d"], scale,
          n_lugs=18)
    wheel(msp, rw_cx, y + p["rear_wheel_d"] / 2, p["rear_wheel_d"], scale,
          n_lugs=10)
    centerline(msp, (fw_cx, y + p["front_wheel_d"] / 2),
               (rw_cx, y + p["rear_wheel_d"] / 2), scale, ext=1.0,
               layer=L_CENTER)

    total_len = (x_body1 + 320) - x
    total_h = (y_body1 + p["tank_h"]) - y

    # ── 尺寸 ──
    if with_dims:
        dim_h(msp, (x, y), (x_body1 + 320, y), scale, offset=28,
              text=f"{total_len:.0f}", tracker=tracker)
        dim_h(msp, (fw_cx, y), (rw_cx, y), scale, offset=17,
              text=f"{rw_cx - fw_cx:.0f}", tracker=tracker)
        dim_v(msp, (x, y), (x, y + total_h), scale, offset=15,
              text=f"{total_h:.0f}", tracker=tracker)
        dim_v(msp, (drum_c[0] - p["drum_d"] / 2, drum_c[1] - p["drum_d"] / 2),
              (drum_c[0] - p["drum_d"] / 2, drum_c[1] + p["drum_d"] / 2),
              scale, offset=6, text=f"φ{p['drum_d']:.0f}", tracker=tracker)

    # ── 零件标注 ──
    if with_labels:
        leader(msp, (reel_cx, reel_cy + p["reel_d"] / 2), "拨禾轮", scale,
               bend=(-7, 8), text_dir="left", tracker=tracker)
        leader(msp, (x + p["header_len"] * 0.1, y_cut), "往复式切割器", scale,
               bend=(-6, -6), text_dir="left", tracker=tracker)
        leader(msp, drum_c, "脱粒滚筒", scale, bend=(-8, 7), text_dir="left",
               tracker=tracker)
        leader(msp, ((tank_x0 + tank_x1) / 2, y_body1 + p["tank_h"]),
               "粮箱", scale, bend=(6, 7), tracker=tracker)
        leader(msp, ((cab_x0 + cab_x1) / 2, y_body1 + p["cab_h"]),
               "驾驶室", scale, bend=(-5, 9), text_dir="left", tracker=tracker)
        leader(msp, auger_end, "卸粮搅龙", scale, bend=(5, 6), tracker=tracker)
        leader(msp, (x_body1 + 320, y_body0 + p["body_h"] * 0.3),
               "排草口", scale, bend=(7, -6), tracker=tracker)

    return {
        "bbox": (x, y, x_body1 + 400, y_body1 + p["tank_h"]),
        "drum_center": drum_c,
        "length": total_len,
        "height": total_h,
        "params": p,
    }
