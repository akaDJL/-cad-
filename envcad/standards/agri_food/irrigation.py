"""模块 20 —— 滴灌 / 喷灌系统平面布置图。

**最大化复用 envcad.standards.plumbing**：
  * ``draw_plumbing_pipe``  → 干管 / 支管 / 毛管（管线 + DN 标注）
  * ``draw_valve_plumbing`` → 控制阀、逆止阀、水表、过滤器
  * ``draw_sprinkler``      → 喷灌喷头
本模块只新增"滴头（灌水器）"这一个微灌专用符号，其余全部调用原函数。

标准依据：
  * **GB/T 50485—2020 微灌工程技术标准**（原 GB/T 50485—2009）——
    首部枢纽组成（水泵 + 施肥装置 + 过滤器 + 计量 + 控制阀）、
    干管/支管/毛管三级管网、灌水器工作水头与灌水均匀度要求。
  * GB/T 50288—2018 灌溉与排水工程设计标准（渠系与管道系统）
  * GB/T 50106—2010 建筑给水排水制图标准（管线线型与 DN 标注，envcad 已内置）

.. warning::
   envcad 内置知识库 ``standards_kb.json`` 目前仅覆盖 building / mechanical /
   electrical 三个行业，**不含 GB/T 50485 条文数值**。下列默认值取自常用工程
   经验，出图前必须按项目复核：
   ``# TODO: verify against GB/T 50485-2020`` —— 灌水器额定工作水头 100kPa、
   灌水均匀度 Cu≥0.80、微灌水利用系数 ≥0.90、过滤精度 120 目。

全部尺寸为实物 mm（1m = 1000）。
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from envcad.standards.plumbing import (
    draw_plumbing_pipe, draw_sprinkler, draw_valve_plumbing,
)

from ._common import (
    L_CENTER, L_MED, L_THICK, L_THIN,
    dim_h, dim_v, label, leader, poly, rect, sym_scale_for, tech_notes,
)

#: 微灌系统默认参数（实物 mm；GB/T 50485 术语）
DEFAULTS: Dict[str, float] = {
    "field_w": 60000.0,          # 田块宽（干管方向）
    "field_l": 42000.0,          # 田块长
    "n_submains": 3.0,           # 支管数量
    "submain_spacing": 18000.0,  # 支管间距
    "n_laterals": 6.0,           # 每条支管上的毛管数
    "lateral_spacing": 4500.0,   # 毛管间距（≈作物行距）
    "lateral_len": 15000.0,      # 毛管铺设长度（GB/T 50485 按水头偏差控制）
    "emitter_spacing": 1500.0,   # 灌水器（滴头）间距
    "dn_main": 110.0,            # 干管公称外径 De110 PE
    "dn_submain": 75.0,          # 支管 De75 PE
    "dn_lateral": 16.0,          # 毛管 De16 滴灌带
    "head_x": 4000.0,            # 首部枢纽相对田块左边距
}

#: GB/T 50485—2020 关键控制指标（供技术要求块引用）
GB50485_NOTES: List[str] = [
    "本系统按 GB/T 50485—2020《微灌工程技术标准》设计。",
    "灌水器额定工作水头 100kPa，同一灌水小区流量偏差率不大于 20%。"
    "  # TODO: verify against GB/T 50485-2020",
    "灌水均匀度 Cu 不应低于 0.80；微灌系统灌溉水利用系数不应低于 0.90。"
    "  # TODO: verify against GB/T 50485-2020",
    "首部过滤精度按滴头流道尺寸的 1/7~1/10 选取，本图采用 120 目叠片过滤器。"
    "  # TODO: verify against GB/T 50485-2020",
    "管材采用 PE 管，干/支管公称压力不低于 0.63MPa，毛管不低于 0.25MPa。",
    "毛管末端设冲洗阀，系统投运前及每灌溉季结束后应冲洗管网。",
]


def draw_emitter(msp, center: Tuple[float, float], scale: float = 200.0,
                 size: float = 260.0, e_type: str = "drip",
                 layer: str = L_MED):
    """绘制灌水器符号（滴头 / 微喷头）。

    Args:
        center: 灌水器中心（实物 mm）
        size: 符号直径（实物 mm）
        e_type: ``"drip"`` 滴头（实心小圆）/ ``"micro"`` 微喷头（圆 + 射流线）
    """
    cx, cy = center
    r = size / 2.0
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    if e_type == "micro":
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            msp.add_line((cx + dx * r, cy + dy * r),
                         (cx + dx * r * 2.2, cy + dy * r * 2.2),
                         dxfattribs={"layer": L_THIN})
    else:
        msp.add_line((cx - r * 0.6, cy), (cx + r * 0.6, cy),
                     dxfattribs={"layer": L_THIN})
    return (cx, cy)


def draw_head_unit(msp, x: float, y: float, scale: float = 200.0,
                   spacing: float = 3200.0, tracker=None) -> Tuple[float, float]:
    """绘制首部枢纽（GB/T 50485 第 4 章）。

    自左至右依次为：水泵 → 逆止阀 → 施肥罐 → 叠片过滤器 → 水表 → 控制阀。
    阀门/水表符号全部复用 ``plumbing.draw_valve_plumbing``。

    Args:
        x, y: 首部起点（干管中心线上）
        spacing: 各元件间距（实物 mm）

    Returns:
        干管接出点 (x, y)
    """
    v_scale = sym_scale_for(spacing * 0.34, 10.0)  # 阀门符号总宽 ≈10×scale
    cx = x

    # 水泵（圆 + 出流三角）
    r = spacing * 0.26
    msp.add_circle((cx, y), r, dxfattribs={"layer": L_THICK})
    poly(msp, [(cx - r * 0.35, y - r * 0.5), (cx - r * 0.35, y + r * 0.5),
               (cx + r * 0.6, y)], layer=L_THICK, closed=True)
    label(msp, "离心泵", (cx, y - r * 2.0), scale, height=2.5, tracker=tracker)
    cx += spacing

    draw_valve_plumbing(msp, (cx, y), "check", scale=v_scale, label="逆止阀")
    cx += spacing

    # 施肥（注肥）罐
    rect(msp, cx - spacing * 0.22, y, cx + spacing * 0.22, y + spacing * 0.62,
         layer=L_THICK)
    msp.add_arc((cx, y + spacing * 0.62), spacing * 0.22,
                start_angle=0, end_angle=180, dxfattribs={"layer": L_THICK})
    msp.add_line((cx, y), (cx, y + spacing * 0.20), dxfattribs={"layer": L_THIN})
    label(msp, "施肥罐", (cx, y - spacing * 0.45), scale, height=2.5,
          tracker=tracker)
    cx += spacing

    # 叠片过滤器
    rect(msp, cx - spacing * 0.26, y - spacing * 0.3,
         cx + spacing * 0.26, y + spacing * 0.3, layer=L_THICK)
    for i in range(1, 5):
        px = cx - spacing * 0.26 + i * spacing * 0.104
        msp.add_line((px, y - spacing * 0.3), (px, y + spacing * 0.3),
                     dxfattribs={"layer": L_THIN})
    label(msp, "叠片过滤器120目", (cx, y - spacing * 0.62), scale, height=2.5,
          tracker=tracker)
    cx += spacing

    draw_valve_plumbing(msp, (cx, y), "meter", scale=v_scale, label="水表")
    cx += spacing
    draw_valve_plumbing(msp, (cx, y), "gate", scale=v_scale, label="总控制阀")
    cx += spacing * 0.8

    # 元件间连管
    draw_plumbing_pipe(msp, (x + spacing * 0.26, y), (cx, y),
                       pipe_type="cold", scale=scale)
    return (cx, y)


def draw_irrigation(msp, x: float, y: float, scale: float = 200.0,
                    system: str = "drip", with_dims: bool = True,
                    with_notes: bool = True, tracker=None,
                    **params) -> Dict[str, object]:
    """绘制滴灌 / 喷灌系统平面布置图。

    Args:
        msp: ezdxf modelspace
        x, y: 田块左下角（实物 mm）
        scale: 出图比例倒数（田块级图纸建议 1:200 ~ 1:500）
        system: ``"drip"`` 滴灌（毛管 + 滴头）/ ``"sprinkler"`` 喷灌（竖管 + 喷头）
        **params: 覆盖 :data:`DEFAULTS`

    Returns:
        dict：``bbox``、``main_line``、``n_emitters``、``params``
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})

    # ── 田块边界（点画线用地界）──
    rect(msp, x, y, x + p["field_w"], y + p["field_l"], layer=L_CENTER)

    # ── 首部枢纽 ──
    head_y = y - p["field_l"] * 0.10
    head_out = draw_head_unit(msp, x + p["head_x"], head_y, scale,
                              spacing=p["field_w"] * 0.055, tracker=tracker)

    # ── 干管（沿田块下边界）──
    main_y = head_y
    main_x0, main_x1 = head_out[0], x + p["field_w"] - 1500
    draw_plumbing_pipe(msp, (main_x0, main_y), (main_x1, main_y),
                       pipe_type="cold", dn=int(p["dn_main"]), scale=scale,
                       label=f"干管 De{p['dn_main']:.0f}")

    # ── 支管 + 毛管 + 灌水器 ──
    n_sub = int(p["n_submains"])
    n_lat = int(p["n_laterals"])
    v_scale = sym_scale_for(p["field_w"] * 0.020, 10.0)
    n_emitters = 0
    submain_x: List[float] = []

    for i in range(n_sub):
        sx = main_x0 + p["field_w"] * 0.10 + i * p["submain_spacing"]
        if sx > main_x1:
            break
        submain_x.append(sx)
        sub_top = y + p["lateral_spacing"] * n_lat
        # 支管控制阀（复用 plumbing 阀门符号）
        draw_valve_plumbing(msp, (sx, main_y + p["field_l"] * 0.035),
                            "gate", scale=v_scale, label=f"V-{i + 1}")
        draw_plumbing_pipe(msp, (sx, main_y), (sx, sub_top),
                           pipe_type="cold", dn=int(p["dn_submain"]),
                           scale=scale,
                           label=f"支管 De{p['dn_submain']:.0f}" if i == 0 else "")
        # 毛管
        for j in range(n_lat):
            ly = y + p["lateral_spacing"] * (j + 1)
            lx1 = sx + p["lateral_len"]
            msp.add_line((sx, ly), (lx1, ly), dxfattribs={"layer": L_THIN})
            if system == "drip":
                k = 0
                ex = sx + p["emitter_spacing"]
                while ex < lx1:
                    draw_emitter(msp, (ex, ly), scale,
                                 size=p["field_w"] * 0.0045)
                    ex += p["emitter_spacing"]
                    k += 1
                n_emitters += k
            else:
                # 喷灌：每 3 个毛管间距设 1 个喷头（复用 plumbing 喷头符号）
                for k in range(3):
                    px = sx + p["lateral_len"] * (k + 1) / 4.0
                    draw_sprinkler(msp, (px, ly), "upright",
                                   scale=sym_scale_for(p["field_w"] * 0.006, 3.5),
                                   layer=L_MED)
                    n_emitters += 1

    # 毛管图例说明（只标一次，避免图面拥挤）
    if submain_x:
        leader(msp, (submain_x[0] + p["lateral_len"] * 0.6,
                     y + p["lateral_spacing"]),
               f"毛管 De{p['dn_lateral']:.0f}  滴头间距{p['emitter_spacing']:.0f}",
               scale, bend=(6, -6), tracker=tracker)

    # ── 尺寸 ──
    if with_dims:
        dim_h(msp, (x, y), (x + p["field_w"], y), scale, offset=30,
              text=f"{p['field_w']:.0f}", tracker=tracker)
        dim_v(msp, (x, y), (x, y + p["field_l"]), scale, offset=14,
              text=f"{p['field_l']:.0f}", tracker=tracker)
        if len(submain_x) >= 2:
            dim_h(msp, (submain_x[0], y + p["field_l"]),
                  (submain_x[1], y + p["field_l"]), scale, offset=-12,
                  text=f"{p['submain_spacing']:.0f}", tracker=tracker)

    # ── 技术要求（GB/T 50485）──
    if with_notes:
        tech_notes(msp, (x + p["field_w"] * 1.02, y + p["field_l"]), scale,
                   GB50485_NOTES, title="设计说明（GB/T 50485—2020）",
                   width=86.0, tracker=tracker)

    return {
        "bbox": (x, head_y - p["field_l"] * 0.12,
                 x + p["field_w"] * 1.02, y + p["field_l"]),
        "main_line": ((main_x0, main_y), (main_x1, main_y)),
        "submain_x": submain_x,
        "n_emitters": n_emitters,
        "params": p,
    }
