"""模块 22 —— 连续式包装封口机（输送带 + 封口机头）侧视图。

复用 envcad：
  * ``standards.hydraulic.draw_cylinder`` → 封口压合气缸（缸体/活塞杆画法）；
  * ``standards.hydraulic.draw_motor``    → 输送带 / 封口履带驱动电机；
  * GB/T 17450 图层、仿宋 GB2312 文字样式、``standards.dim`` 标注、
    ``standards.annotate.draw_leader`` 指引线、``standards.notes`` 技术要求块。

标准依据：
  * GB/T 14689—2008 图纸幅面 / GB/T 4457.4—2002 图线
  * GB 16798-2023 食品机械安全卫生  # TODO: verify against GB 16798（2023版替代1997版，2024-04-01实施）
    （与物料接触表面材质、清洗性、防护罩要求）
  * GB/T 19812 / GB/T 4122.2 包装机械术语  # TODO: verify against GB/T 4122.2
  * GB 5226.1—2019 机械电气安全 机械电气设备 第1部分：通用技术条件（急停/电控柜）

envcad 内置 ``standards_kb.json`` 未收录食品机械行业，上述条文号需人工复核。
全部尺寸为实物 mm。
"""
from __future__ import annotations

from typing import Dict

from envcad.standards.hydraulic import draw_cylinder, draw_motor

from ._common import (
    L_CENTER, L_HIDDEN, L_MED, L_THICK, L_THIN,
    centerline, cross_center, dim_h, dim_v, ground_line, label, leader,
    poly, rect, sym_scale_for, tech_notes,
)

#: 连续式枕式封口机默认参数（实物 mm）
DEFAULTS: Dict[str, float] = {
    "conv_len": 2400.0,        # 输送带长度（两端辊中心距）
    "belt_h": 900.0,           # 输送面标高（离地）
    "pulley_d": 160.0,         # 输送辊直径
    "belt_w": 60.0,            # 带厚（双线间距）
    "frame_w": 90.0,           # 机架立柱宽
    "head_x": 1350.0,          # 封口机头中心距输送带入口
    "head_w": 700.0,           # 封口机头宽
    "head_h": 900.0,           # 封口机头高（自封口线向上）
    "seal_gap": 220.0,         # 封口履带（上下热封块）开口高
    "jaw_len": 420.0,          # 热封块长度
    "cyl_len": 520.0,          # 压合气缸长度
    "film_roll_d": 420.0,      # 薄膜卷直径
    "motor_d": 300.0,          # 驱动电机符号直径
    "cabinet_w": 520.0,        # 电控柜宽
    "cabinet_h": 1250.0,       # 电控柜高
    "pkg_w": 260.0,            # 被包装物宽
    "pkg_h": 150.0,            # 被包装物高
    "pkg_pitch": 500.0,        # 包装件节距
}


def draw_conveyor(msp, x: float, y: float, scale: float = 20.0,
                  length: float = 2400.0, belt_h: float = 900.0,
                  pulley_d: float = 160.0, belt_w: float = 60.0,
                  frame_w: float = 90.0, tracker=None):
    """绘制带式输送机侧视：两端辊 + 上下带面 + 机架立柱。

    Args:
        x, y: 入口端辊中心正下方的地面点（实物 mm）
        length: 两端辊中心距
    Returns:
        (入口辊中心, 出口辊中心, 输送面 Y)
    """
    r = pulley_d / 2.0
    cy = y + belt_h - r
    p_in = (x, cy)
    p_out = (x + length, cy)
    for cx, _ in (p_in, p_out):
        msp.add_circle((cx, cy), r, dxfattribs={"layer": L_THICK})
        cross_center(msp, cx, cy, r, scale)
    # 带面（上下双线）
    for dy in (r, -r):
        msp.add_line((x, cy + dy), (x + length, cy + dy),
                     dxfattribs={"layer": L_THICK})
    for dy in (r - belt_w, -r + belt_w):
        msp.add_line((x, cy + dy), (x + length, cy + dy),
                     dxfattribs={"layer": L_THIN})
    # 机架
    rect(msp, x, cy - r - 40, x + length, cy - r - 40 - 90, layer=L_MED)
    for lx in (x + length * 0.12, x + length * 0.88):
        rect(msp, lx - frame_w / 2, y, lx + frame_w / 2, cy - r - 130,
             layer=L_MED)
        msp.add_line((lx - frame_w * 1.6, y), (lx + frame_w * 1.6, y),
                     dxfattribs={"layer": L_THICK})
    return p_in, p_out, cy + r


def _draw_sealing_head(msp, cx: float, y_belt: float, scale: float, p,
                       tracker=None):
    """封口机头：立柱框架 + 上下热封块 + 压合气缸 + 冷却块。"""
    hw, hh = p["head_w"] / 2, p["head_h"]
    gap = p["seal_gap"]
    y0 = y_belt + 40                      # 下热封块上表面
    y_top = y0 + gap + hh

    # 机头立柱框架
    rect(msp, cx - hw, y0 - 260, cx + hw, y_top, layer=L_THICK)
    msp.add_line((cx - hw, y0 + gap), (cx + hw, y0 + gap),
                 dxfattribs={"layer": L_THIN})

    # 上下热封块（履带式封口块）
    jl = p["jaw_len"] / 2
    rect(msp, cx - jl, y0 + gap, cx + jl, y0 + gap + 120, layer=L_THICK)
    rect(msp, cx - jl, y0 - 120, cx + jl, y0, layer=L_THICK)
    # 热封齿纹（细实线）
    for i in range(7):
        tx = cx - jl + i * (2 * jl) / 6
        msp.add_line((tx, y0 + gap), (tx, y0 + gap + 40),
                     dxfattribs={"layer": L_THIN})
        msp.add_line((tx, y0), (tx, y0 - 40), dxfattribs={"layer": L_THIN})

    # 封口线（点画线）
    centerline(msp, (cx - hw * 1.4, y0 + gap / 2), (cx + hw * 1.4, y0 + gap / 2),
               scale, ext=2.0, layer=L_CENTER)

    # 压合气缸 —— 复用 envcad hydraulic.draw_cylinder（缸筒长 24×scale）
    draw_cylinder(msp, (cx, y_top - p["cyl_len"] * 0.55), c_type="double",
                  scale=sym_scale_for(p["cyl_len"], 24.0),
                  label="压合气缸", layer=L_MED)
    msp.add_line((cx, y_top - p["cyl_len"] * 0.9), (cx, y0 + gap + 120),
                 dxfattribs={"layer": L_HIDDEN})
    return y_top, y0 + gap / 2


def draw_packaging(msp, x: float, y: float, scale: float = 20.0,
                   with_dims: bool = True, with_labels: bool = True,
                   with_notes: bool = True, n_packages: int = 4,
                   tracker=None, **params) -> Dict[str, object]:
    """绘制连续式包装封口机侧视图（进料在左，出料在右）。

    Args:
        msp: ezdxf modelspace
        x, y: 插入基点 —— 输送带入口辊中心正下方的**地面点**（实物 mm）
        scale: 出图比例倒数
        n_packages: 带面上示意包装件数量
        **params: 覆盖 :data:`DEFAULTS`，如 conv_len=3000, seal_gap=260

    Returns:
        dict：``bbox``、``seal_line``、``belt_top``、``params``
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})

    total_len = p["conv_len"] + p["cabinet_w"] * 2.2
    ground_line(msp, x - 600, x + total_len + 600, y, scale, n_ticks=24)

    # ── 输送带 ──
    p_in, p_out, y_belt = draw_conveyor(
        msp, x, y, scale, length=p["conv_len"], belt_h=p["belt_h"],
        pulley_d=p["pulley_d"], belt_w=p["belt_w"], frame_w=p["frame_w"],
        tracker=tracker)

    # ── 封口机头 ──
    head_cx = x + p["head_x"]
    y_head_top, y_seal = _draw_sealing_head(msp, head_cx, y_belt, scale, p,
                                            tracker=tracker)

    # ── 薄膜卷（机头后上方）──
    film_cx = head_cx + p["head_w"] * 0.75 + p["film_roll_d"] * 0.6
    film_cy = y_head_top - p["film_roll_d"] * 0.7
    rd = p["film_roll_d"] / 2
    msp.add_circle((film_cx, film_cy), rd, dxfattribs={"layer": L_THICK})
    msp.add_circle((film_cx, film_cy), rd * 0.22, dxfattribs={"layer": L_MED})
    cross_center(msp, film_cx, film_cy, rd, scale)
    # 薄膜走向（细实线）
    poly(msp, [(film_cx - rd, film_cy), (head_cx + p["head_w"] * 0.3, y_seal + 320),
               (head_cx, y_seal + 140)], layer=L_THIN)

    # ── 驱动电机（复用 hydraulic.draw_motor）──
    mot_cx = x + p["conv_len"] * 0.88
    mot_cy = y_belt - p["belt_h"] * 0.45
    draw_motor(msp, (mot_cx, mot_cy), m_type="fixed_uni",
               scale=sym_scale_for(p["motor_d"] / 2, 6.0),
               label="调速电机", layer=L_MED)
    msp.add_line((mot_cx, mot_cy + p["motor_d"] / 2), (mot_cx, y_belt - 60),
                 dxfattribs={"layer": L_THIN})

    # ── 电控柜（出料端）──
    cab_x0 = x + p["conv_len"] + p["cabinet_w"] * 0.5
    rect(msp, cab_x0, y, cab_x0 + p["cabinet_w"], y + p["cabinet_h"],
         layer=L_THICK)
    rect(msp, cab_x0 + 70, y + p["cabinet_h"] * 0.62,
         cab_x0 + p["cabinet_w"] - 70, y + p["cabinet_h"] * 0.88, layer=L_THIN)
    msp.add_circle((cab_x0 + p["cabinet_w"] / 2, y + p["cabinet_h"] * 0.45), 55,
                   dxfattribs={"layer": L_MED})  # 急停按钮 GB 5226.1

    # ── 带面上的包装件 ──
    for i in range(max(0, n_packages)):
        px = x + p["pkg_pitch"] * (i + 0.6)
        if px + p["pkg_w"] > x + p["conv_len"]:
            break
        rect(msp, px, y_belt, px + p["pkg_w"], y_belt + p["pkg_h"],
             layer=L_MED)
        msp.add_line((px, y_belt + p["pkg_h"] * 0.5),
                     (px + p["pkg_w"], y_belt + p["pkg_h"] * 0.5),
                     dxfattribs={"layer": L_THIN})

    # ── 尺寸 ──
    if with_dims:
        dim_h(msp, (x, y), (cab_x0 + p["cabinet_w"], y), scale, offset=22,
              text=f"{cab_x0 + p['cabinet_w'] - x:.0f}", tracker=tracker)
        dim_h(msp, (x, y), (head_cx, y), scale, offset=13,
              text=f"{p['head_x']:.0f}", tracker=tracker)
        dim_v(msp, (x, y), (x, y_belt), scale, offset=12,
              text=f"{p['belt_h']:.0f}", tracker=tracker)
        dim_v(msp, (head_cx - p["head_w"] / 2, y_belt + 40),
              (head_cx - p["head_w"] / 2, y_belt + 40 + p["seal_gap"]),
              scale, offset=6, text=f"{p['seal_gap']:.0f}", tracker=tracker)

    if with_labels:
        leader(msp, (x + p["conv_len"] * 0.35, y_belt), "不锈钢网带输送机",
               scale, bend=(-6, -8), text_dir="left", tracker=tracker)
        leader(msp, (head_cx, y_seal), "热封（封口）机头", scale, bend=(-7, 7),
               text_dir="left", tracker=tracker)
        leader(msp, (film_cx, film_cy + rd), "薄膜卷", scale, bend=(6, 6),
               tracker=tracker)
        leader(msp, (cab_x0 + p["cabinet_w"], y + p["cabinet_h"]), "电控柜",
               scale, bend=(5, 5), tracker=tracker)
        label(msp, "进料", (x - 8 * scale, y_belt + 4 * scale), scale,
              height=3.0, tracker=tracker)
        label(msp, "出料", (x + p["conv_len"] + 6 * scale, y_belt + 4 * scale),
              scale, height=3.0, tracker=tracker)

    if with_notes:
        tech_notes(msp, (x, y + p["cabinet_h"] + p["head_h"] * 1.9), scale, [
            "与物料接触零件采用 06Cr19Ni10（304）不锈钢，表面 Ra≤0.8μm。"
            "  # TODO: verify against GB 16798",
            "热封温度 120~200℃ 可调，温控精度 ±2℃；封口速度与输送速度同步。",
            "运动部位设防护罩，电气系统按 GB 5226.1—2019 设急停回路。",
            "整机接地电阻不大于 0.1Ω；清洗时电控柜防护等级不低于 IP54。",
        ], title="技术要求", width=88.0, tracker=tracker)

    return {
        "bbox": (x - 600, y, cab_x0 + p["cabinet_w"] + 400,
                 y_head_top + p["film_roll_d"]),
        "seal_line": (head_cx, y_seal),
        "belt_top": y_belt,
        "params": p,
    }
