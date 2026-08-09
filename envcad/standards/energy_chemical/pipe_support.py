"""管道支吊架（Pipe Support & Hanger）详图模块。

依据标准
--------
* GB/T 17116.1~17116.3—2018《管道支吊架》
  - 第 1 部分：技术规范
  - 第 2 部分：管道连接部件
  - 第 3 部分：中间连接件和建筑结构连接件
* GB 50316—2000(2008版)《工业金属管道设计规范》——支吊架间距与荷载
* HG/T 21629—1999《管架标准图》——管架型式代号
* SH/T 3073—2016《石油化工管道支吊架设计规范》
* GB/T 706—2016《热轧型钢》——工字钢/槽钢规格

.. note::
   支吊架 **最大允许跨距** 与管径、介质、温度相关（GB 50316 附录），
   envcad standards_kb.json 未收录该数表；``span`` 一律作为参数由
   设计者按规范查取，见 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = 支架 **底面中心**（基础/楼面标高处）；
吊架时 ``(x, y)`` 为 **生根点（梁底）中心**。
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from . import _common as C


def _pipe(msp, cx: float, cy: float, od: float, insulation: float = 0.0,
          layer: str = C.L_THICK):
    """管道端面（圆），可选保温层（细实线）。"""
    msp.add_circle((cx, cy), od / 2.0, dxfattribs={"layer": layer})
    msp.add_circle((cx, cy), od / 2.0 * 0.86, dxfattribs={"layer": C.L_THIN})
    if insulation > 0:
        msp.add_circle((cx, cy), od / 2.0 + insulation,
                       dxfattribs={"layer": C.L_THIN})
    C.centerline(msp, (cx - od, cy), (cx + od, cy))
    C.centerline(msp, (cx, cy - od), (cx, cy + od))


def _i_beam(msp, x0: float, x1: float, cy: float, h: float, tf: float,
            tw: float, layer: str = C.L_THICK):
    """工字钢横梁侧视/正视轮廓（GB/T 706）。"""
    C.rect(msp, x0, cy + h / 2 - tf, x1, cy + h / 2, layer=layer)   # 上翼缘
    C.rect(msp, x0, cy - h / 2, x1, cy - h / 2 + tf, layer=layer)   # 下翼缘
    mid = (x0 + x1) / 2.0
    C.rect(msp, mid - tw / 2, cy - h / 2 + tf, mid + tw / 2,
           cy + h / 2 - tf, layer=layer)


def _u_bolt(msp, cx: float, cy: float, od: float, scale: float,
            layer: str = C.L_MID):
    """U 型管卡（GB/T 17116.2 管道连接部件）。"""
    r = od / 2.0 * 1.10
    msp.add_arc((cx, cy), r, start_angle=0, end_angle=180,
                dxfattribs={"layer": layer})
    msp.add_arc((cx, cy), r * 1.12, start_angle=0, end_angle=180,
                dxfattribs={"layer": layer})
    for sg in (-1, 1):
        msp.add_line((cx + sg * r, cy), (cx + sg * r, cy - od * 0.9),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + sg * r * 1.12, cy), (cx + sg * r * 1.12,
                                                cy - od * 0.9),
                     dxfattribs={"layer": layer})
        # 螺母
        C.rect(msp, cx + sg * r - C.P(1.2, scale), cy - od * 0.78,
               cx + sg * r * 1.12 + C.P(1.2, scale), cy - od * 0.62,
               layer=C.L_THIN)


def draw_pipe_support(msp, x: float, y: float, scale: float = 50.0,
                      support_type: str = "fixed",
                      pipe_od: float = 219.0,
                      n_pipes: int = 3,
                      pipe_spacing: float = 450.0,
                      insulation: float = 0.0,
                      height: float = 2000.0,
                      beam_height: float = 200.0,
                      beam_flange: float = 12.0,
                      beam_web: float = 8.0,
                      column_section: str = "HW200×200",
                      beam_section: str = "I20a",
                      baseplate: float = 320.0,
                      baseplate_thk: float = 20.0,
                      n_anchor: int = 4,
                      anchor_spec: str = "M20",
                      guide_gap: float = 3.0,
                      spring_travel: float = 0.0,
                      span: float = 6000.0,
                      tag: str = "PS-01",
                      name: str = "管道支架",
                      design_load: str = "",
                      material: str = "Q235B",
                      with_dims: bool = True,
                      with_table: bool = True,
                      **params):
    """绘制管道支吊架详图（GB/T 17116 / GB 50316 / HG/T 21629）。

    参数
    ----
    support_type ``fixed``   固定支架（管部焊接，限制三向位移）
                 ``sliding`` 滑动支架（GB/T 17116.2 滑动管托）
                 ``guide``   导向支架（限制横向位移，留 ``guide_gap``）
                 ``hanger``  刚性吊架（吊杆 + 管卡）
                 ``spring``  弹簧吊架（GB/T 17116.1 可变弹簧）
    pipe_od      管道外径 mm（GB/T 8163 / GB/T 12459 系列）
    n_pipes      同一支架上敷设的管道根数
    pipe_spacing 管中心间距 mm
    height       支架高度（基础顶面到梁顶）mm；吊架时为吊杆长度
    span         支架间距 mm，仅用于标注
                 # TODO: verify against GB 50316 附录 A 最大允许跨距表
                 #       （随管径、材质、介质密度、温度变化）
    spring_travel 弹簧位移量 mm（support_type="spring" 时标注）

    返回 ``dict``：管中心坐标列表与关键标高。
    """
    s = scale
    od_t = pipe_od + insulation * 2.0
    total_w = pipe_spacing * (n_pipes - 1) + od_t * 2.4
    pipe_xs = [x + (i - (n_pipes - 1) / 2.0) * pipe_spacing
               for i in range(n_pipes)]

    if support_type in ("hanger", "spring"):
        return _draw_hanger(msp, x, y, s, support_type, pipe_od, n_pipes,
                            pipe_spacing, insulation, height, pipe_xs,
                            spring_travel, span, tag, name, design_load,
                            material, anchor_spec, with_dims, with_table)

    # ══ 落地支架 ══
    y_base = y
    y_bp_top = y_base + baseplate_thk
    y_beam_c = y_base + height - beam_height / 2.0
    y_pipe_c = y_base + height + od_t / 2.0 + max(od_t * 0.10, C.P(1.2, s))

    # ── 基础地面 ──
    gx0, gx1 = x - total_w * 0.78, x + total_w * 0.78
    msp.add_line((gx0, y_base), (gx1, y_base), dxfattribs={"layer": C.L_THICK})
    for i in range(15):
        gx = gx0 + (gx1 - gx0) * i / 14.0
        msp.add_line((gx, y_base), (gx - C.P(3, s), y_base - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # ── 立柱（型钢，双柱门型架）──
    col_w = max(total_w * 0.06, 120.0)
    col_xs = [x - total_w / 2 + col_w, x + total_w / 2 - col_w]
    for cxp in col_xs:
        C.rect(msp, cxp - col_w / 2, y_bp_top, cxp + col_w / 2,
               y_beam_c - beam_height / 2, layer=C.L_THICK)
        C.rect(msp, cxp - col_w / 2 + beam_web, y_bp_top,
               cxp + col_w / 2 - beam_web, y_beam_c - beam_height / 2,
               layer=C.L_THIN)
        # 柱底板 + 地脚螺栓（GB/T 17116.3 建筑结构连接件）
        C.rect(msp, cxp - baseplate / 2, y_base, cxp + baseplate / 2,
               y_bp_top, layer=C.L_THICK)
        for k in range(n_anchor // 2):
            bx = cxp + (k - (n_anchor // 2 - 1) / 2.0) * baseplate * 0.55
            msp.add_line((bx, y_base - C.P(6, s)), (bx, y_bp_top + C.P(2, s)),
                         dxfattribs={"layer": C.L_THIN})
        # 加劲肋
        for sg in (-1, 1):
            msp.add_lwpolyline([
                (cxp + sg * col_w / 2, y_bp_top),
                (cxp + sg * baseplate * 0.42, y_bp_top),
                (cxp + sg * col_w / 2, y_bp_top + col_w * 0.9)],
                close=True, dxfattribs={"layer": C.L_THIN})

    # ── 横梁（工字钢，GB/T 706）──
    _i_beam(msp, x - total_w / 2, x + total_w / 2, y_beam_c,
            beam_height, beam_flange, beam_web)

    # ── 管道与管部 ──
    for px in pipe_xs:
        _pipe(msp, px, y_pipe_c, pipe_od, insulation)
        shoe_h = y_pipe_c - pipe_od / 2.0 - (y_beam_c + beam_height / 2)
        if support_type == "fixed":
            # 固定管托：焊接管托 + 双侧挡板
            C.rect(msp, px - pipe_od * 0.55, y_beam_c + beam_height / 2,
                   px + pipe_od * 0.55, y_pipe_c - pipe_od / 2.0,
                   layer=C.L_THICK)
            for sg in (-1, 1):
                C.rect(msp, px + sg * pipe_od * 0.62,
                       y_beam_c + beam_height / 2,
                       px + sg * pipe_od * 0.74, y_pipe_c + pipe_od * 0.2,
                       layer=C.L_THICK)
            _u_bolt(msp, px, y_pipe_c, od_t, s)
        elif support_type == "guide":
            C.rect(msp, px - pipe_od * 0.55, y_beam_c + beam_height / 2,
                   px + pipe_od * 0.55, y_pipe_c - pipe_od / 2.0,
                   layer=C.L_THICK)
            for sg in (-1, 1):
                gx = px + sg * (pipe_od * 0.55 + guide_gap)
                C.rect(msp, gx, y_beam_c + beam_height / 2,
                       gx + sg * pipe_od * 0.12, y_pipe_c, layer=C.L_MID)
            C.leader_note(msp, (px + pipe_od * 0.62, y_pipe_c - pipe_od * 0.3),
                          f"导向间隙 {guide_gap}mm", s, dx=16, dy=-12)
        else:  # sliding
            # 滑动管托 + 滑板（GB/T 17116.2）
            C.rect(msp, px - pipe_od * 0.55,
                   y_beam_c + beam_height / 2 + max(shoe_h * 0.22, C.P(0.6, s)),
                   px + pipe_od * 0.55, y_pipe_c - pipe_od / 2.0,
                   layer=C.L_THICK)
            C.rect(msp, px - pipe_od * 0.72, y_beam_c + beam_height / 2,
                   px + pipe_od * 0.72,
                   y_beam_c + beam_height / 2 + max(shoe_h * 0.22, C.P(0.6, s)),
                   layer=C.L_MID)
            C.arrow(msp, (px + pipe_od * 1.05, y_pipe_c - pipe_od * 0.9),
                    (1, 0), s, size=3.0)
            C.arrow(msp, (px - pipe_od * 1.05, y_pipe_c - pipe_od * 0.9),
                    (-1, 0), s, size=3.0)

    top_y = y_pipe_c + od_t / 2.0

    # ── 标注 ──
    st = {"fixed": "固定支架", "sliding": "滑动支架",
          "guide": "导向支架"}.get(support_type, support_type)
    if with_dims:
        C.dim_linear(msp, (x - total_w / 2, y_base), (x + total_w / 2, y_base),
                     offset=22, scale=s, label=f"{int(total_w)}")
        if n_pipes >= 2:
            C.dim_linear(msp, (pipe_xs[0], top_y), (pipe_xs[1], top_y),
                         offset=-14, scale=s, label=f"{int(pipe_spacing)}")
        C.dim_linear(msp, (x + total_w / 2, y_base), (x + total_w / 2, y_pipe_c),
                     offset=-26, scale=s, label=f"H={int(y_pipe_c - y_base)}")
        C.leader_note(msp, (col_xs[0], y_base + height * 0.5),
                      f"立柱 {column_section} {material}", s, dx=-26, dy=10)
        C.leader_note(msp, (x, y_beam_c), f"横梁 {beam_section}", s,
                      dx=24, dy=-18)
        C.leader_note(msp, (col_xs[1], y_base + baseplate_thk / 2),
                      f"{n_anchor}-{anchor_spec} 地脚螺栓", s, dx=24, dy=-14)
        C.leader_note(msp, (pipe_xs[-1], y_pipe_c),
                      f"管道 φ{int(pipe_od)}"
                      + (f" 保温{int(insulation)}" if insulation else ""),
                      s, dx=22, dy=20)
        C.elevation_mark(msp, (gx0 + C.P(4, s), y_base), "±0.000", s)

    C.eng_text(msp, tag, (x, top_y + C.P(30, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, f"{name}（{st}）", (x, top_y + C.P(24, s)), 3.5, s,
           layer=C.L_TITLE)

    if with_table:
        rows = [
            ["支架型式", st],
            ["管道规格", f"φ{int(pipe_od)} × {n_pipes}根"],
            ["支架间距", f"{int(span)} mm"],
            ["立柱", column_section],
            ["横梁", beam_section],
            ["材质", material],
            ["执行标准", "GB/T 17116-2018"],
        ]
        if design_load:
            rows.insert(3, ["设计荷载", design_load])
        C.spec_table(msp, (x + total_w * 0.62, top_y + C.P(20, s)),
                     rows, s, col_w=(28.0, 40.0), title="支架数据表")

    return {"tag": tag, "base": y_base, "beam_y": y_beam_c,
            "pipe_y": y_pipe_c, "pipe_xs": pipe_xs, "top": top_y}


def _draw_hanger(msp, x, y, s, support_type, pipe_od, n_pipes, pipe_spacing,
                 insulation, height, pipe_xs, spring_travel, span, tag, name,
                 design_load, material, anchor_spec, with_dims, with_table):
    """吊架（刚性/弹簧）—— GB/T 17116.1 & .3。(x, y) 为生根梁底中心。"""
    od_t = pipe_od + insulation * 2.0
    y_root = y
    y_pipe_c = y_root - height
    total_w = pipe_spacing * (n_pipes - 1) + od_t * 2.4
    is_spring = (support_type == "spring")

    # ── 生根钢梁（楼面/结构梁）──
    bh = max(pipe_od * 0.9, 200.0)
    _i_beam(msp, x - total_w * 0.62, x + total_w * 0.62, y_root + bh / 2,
            bh, bh * 0.10, bh * 0.06)
    C.hatch_area(msp, [(x - total_w * 0.62, y_root + bh),
                       (x + total_w * 0.62, y_root + bh),
                       (x + total_w * 0.62, y_root + bh * 1.35),
                       (x - total_w * 0.62, y_root + bh * 1.35)],
                 scale=s, pattern_scale=0.7)
    C.rect(msp, x - total_w * 0.62, y_root + bh, x + total_w * 0.62,
           y_root + bh * 1.35, layer=C.L_THICK)

    rod_d = max(pipe_od * 0.10, 16.0)
    for px in pipe_xs:
        # 梁夹（GB/T 17116.3 建筑结构连接件）
        C.rect(msp, px - rod_d * 2.2, y_root, px + rod_d * 2.2,
               y_root + bh * 0.30, layer=C.L_MID)
        y_rod_top = y_root
        y_rod_bot = y_pipe_c + od_t / 2.0 + rod_d * 2.6
        if is_spring:
            # 可变弹簧吊架：弹簧筒
            sp_h = max(height * 0.24, pipe_od * 1.4)
            sp_top = y_root - height * 0.16
            sp_bot = sp_top - sp_h
            C.rect(msp, px - rod_d * 2.6, sp_bot, px + rod_d * 2.6, sp_top,
                   layer=C.L_THICK)
            n_coil = 6
            for i in range(n_coil + 1):
                yy = sp_bot + sp_h * i / n_coil
                msp.add_line((px - rod_d * 2.0, yy),
                             (px + rod_d * 2.0, yy + sp_h / n_coil * 0.5),
                             dxfattribs={"layer": C.L_THIN})
            # 荷载指示标尺
            msp.add_line((px + rod_d * 2.6, sp_bot), (px + rod_d * 3.4, sp_bot),
                         dxfattribs={"layer": C.L_THIN})
            msp.add_line((px + rod_d * 2.6, sp_top), (px + rod_d * 3.4, sp_top),
                         dxfattribs={"layer": C.L_THIN})
            for seg in ((y_rod_top, sp_top), (sp_bot, y_rod_bot)):
                for sg in (-1, 1):
                    msp.add_line((px + sg * rod_d / 2, seg[0]),
                                 (px + sg * rod_d / 2, seg[1]),
                                 dxfattribs={"layer": C.L_THICK})
        else:
            for sg in (-1, 1):
                msp.add_line((px + sg * rod_d / 2, y_rod_top),
                             (px + sg * rod_d / 2, y_rod_bot),
                             dxfattribs={"layer": C.L_THICK})
            # 花篮螺栓（可调段）
            C.rect(msp, px - rod_d * 1.3, y_root - height * 0.42,
                   px + rod_d * 1.3, y_root - height * 0.28, layer=C.L_MID)

        # 管卡（GB/T 17116.2）
        _pipe(msp, px, y_pipe_c, pipe_od, insulation)
        r = od_t / 2.0 * 1.10
        msp.add_arc((px, y_pipe_c), r, start_angle=180, end_angle=360,
                    dxfattribs={"layer": C.L_MID})
        for sg in (-1, 1):
            msp.add_line((px + sg * r, y_pipe_c), (px + sg * r, y_rod_bot),
                         dxfattribs={"layer": C.L_MID})
        C.rect(msp, px - r, y_rod_bot, px + r, y_rod_bot + rod_d * 0.9,
               layer=C.L_MID)

    st = "弹簧吊架" if is_spring else "刚性吊架"
    top_y = y_root + bh * 1.35
    bot_y = y_pipe_c - od_t / 2.0

    if with_dims:
        C.dim_linear(msp, (x - total_w / 2, y_pipe_c),
                     (x + total_w / 2, y_pipe_c),
                     offset=-20, scale=s, label=f"{int(total_w)}")
        C.dim_linear(msp, (x + total_w * 0.62, y_pipe_c),
                     (x + total_w * 0.62, y_root),
                     offset=-24, scale=s, label=f"吊杆长 {int(height)}")
        C.leader_note(msp, (pipe_xs[0], y_root - height * 0.35),
                      f"吊杆 M{int(rod_d)} {material}", s, dx=-26, dy=8)
        if is_spring and spring_travel:
            C.leader_note(msp, (pipe_xs[-1], y_root - height * 0.28),
                          f"弹簧位移 {int(spring_travel)}mm GB/T 17116.1",
                          s, dx=24, dy=10)
        C.leader_note(msp, (x, y_root + bh / 2), "生根梁夹 GB/T 17116.3",
                      s, dx=26, dy=14)

    C.eng_text(msp, tag, (x, top_y + C.P(14, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, f"{name}（{st}）", (x, top_y + C.P(8, s)), 3.5, s,
           layer=C.L_TITLE)

    if with_table:
        rows = [
            ["支架型式", st],
            ["管道规格", f"φ{int(pipe_od)} × {n_pipes}根"],
            ["支架间距", f"{int(span)} mm"],
            ["吊杆", f"M{int(rod_d)}"],
            ["材质", material],
            ["执行标准", "GB/T 17116-2018"],
        ]
        if design_load:
            rows.insert(3, ["设计荷载", design_load])
        C.spec_table(msp, (x + total_w * 0.70, top_y),
                     rows, s, col_w=(28.0, 40.0), title="吊架数据表")

    return {"tag": tag, "root_y": y_root, "pipe_y": y_pipe_c,
            "pipe_xs": pipe_xs, "top": top_y, "bottom": bot_y}
