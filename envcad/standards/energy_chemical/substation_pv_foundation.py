"""变电站电气平面 / 风机·光伏基础模块。

依据标准
--------
* GB 50059—2011《35kV~110kV 变电站设计规范》——总平面与电气布置
* GB 50060—2008《3~110kV 高压配电装置设计规范》——间隔与安全净距
* GB 50797—2012《光伏发电站设计规范》——方阵布置、间距计算
* GB 50794—2012《光伏发电站施工规范》
* NB/T 10311—2019《陆上风电场工程风电机组基础设计规范》
* GB 50007—2011《建筑地基基础设计规范》——扩展基础
* GB/T 4728《电气简图用图形符号》（经 envcad.standards.electrical 实现）

.. note::
   光伏阵列 **前后排间距 D** 应按当地纬度、冬至日真太阳时 9:00—15:00
   不遮挡原则计算（GB 50797 附录）；风机基础尺寸由荷载与地勘确定。
   envcad standards_kb.json 未收录这些数值，均以参数暴露，
   见各函数 ``# TODO: verify`` 标记。

坐标约定
--------
``(x, y)`` = 图形 **左下角**（平面图）或 **基础底面中心**（基础剖面图）。
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from ezdxf.enums import TextEntityAlignment

from envcad.standards import building, electrical

from . import _common as C


# ══════════════════════════════════════════════════════════
#  1) 变电站电气总平面
# ══════════════════════════════════════════════════════════

def draw_substation_pv_foundation(msp, x: float, y: float, scale: float = 200.0,
                                  mode: str = "substation",
                                  **params):
    """能源电气类图形统一入口。

    参数
    ----
    mode : ``substation`` 变电站电气总平面（GB 50059）
           ``pv``        光伏方阵布置 + 支架基础（GB 50797）
           ``wtg``       风机独立扩展基础剖面（NB/T 10311 / GB 50007）

    其余参数透传给对应子函数，见
    :func:`draw_substation_plan` / :func:`draw_pv_array_foundation` /
    :func:`draw_wtg_foundation`。
    """
    if mode == "pv":
        return draw_pv_array_foundation(msp, x, y, scale, **params)
    if mode == "wtg":
        return draw_wtg_foundation(msp, x, y, scale, **params)
    return draw_substation_plan(msp, x, y, scale, **params)


def draw_substation_plan(msp, x: float, y: float, scale: float = 200.0,
                         site_width: float = 60000.0,
                         site_depth: float = 42000.0,
                         voltage_hv: str = "110kV",
                         voltage_lv: str = "10kV",
                         n_hv_bays: int = 4,
                         bay_width: float = 8000.0,
                         n_transformers: int = 2,
                         transformer_size: Sequence[float] = (7000.0, 5000.0),
                         control_building: Sequence[float] = (24000.0, 12000.0),
                         road_width: float = 4000.0,
                         fence_offset: float = 2000.0,
                         tag: str = "DQ-01",
                         name: str = "变电站电气总平面布置图",
                         with_dims: bool = True,
                         with_table: bool = True,
                         **params):
    """绘制变电站电气总平面（GB 50059—2011 / GB 50060—2008）。

    参数
    ----
    site_width/site_depth 站区围墙内尺寸 mm
    n_hv_bays             高压间隔数
    bay_width             间隔宽度 mm
                          # TODO: verify against GB 50060 表 5.1.2 安全净距
                          #       （随电压等级 35/110/220kV 变化）
    transformer_size      主变压器外形 (长, 宽) mm
    control_building      配电装置楼 (长, 宽) mm

    返回 ``dict``：主要区块坐标。
    """
    s = scale
    x0, y0 = x, y
    x1, y1 = x + site_width, y + site_depth

    # ── 围墙（GB 50059 §4 站区总平面）──
    C.rect(msp, x0 - fence_offset, y0 - fence_offset,
           x1 + fence_offset, y1 + fence_offset, layer=C.L_THICK)
    C.rect(msp, x0, y0, x1, y1, layer=C.L_THIN)
    C.text(msp, "站区围墙", (x0 - fence_offset, y1 + fence_offset + C.P(3, s)),
           3.0, s, layer=C.L_TEXT, align=TextEntityAlignment.MIDDLE_LEFT)

    # ── 站内道路（环形）──
    rx0, ry0 = x0 + road_width * 0.5, y0 + road_width * 0.5
    rx1, ry1 = x1 - road_width * 0.5, y1 - road_width * 0.5
    C.rect(msp, rx0, ry0, rx1, ry1, layer=C.L_DASH)
    C.rect(msp, rx0 + road_width, ry0 + road_width,
           rx1 - road_width, ry1 - road_width, layer=C.L_DASH)
    C.leader_note(msp, (rx0 + road_width / 2, (ry0 + ry1) / 2),
                  f"环形道路 宽{int(road_width)}", s, dx=14, dy=10)

    # ── 高压配电装置区（户外 GIS/AIS 间隔）──
    bay_y0 = y1 - road_width * 2 - 10000.0
    bay_y1 = y1 - road_width * 2
    hv_x0 = rx0 + road_width * 1.4
    for i in range(n_hv_bays):
        bx0 = hv_x0 + bay_width * i
        bx1 = bx0 + bay_width * 0.86
        C.rect(msp, bx0, bay_y0, bx1, bay_y1, layer=C.L_MID)
        cxm = (bx0 + bx1) / 2.0
        # 复用 envcad electrical 的 GB/T 4728 断路器符号
        try:
            electrical.draw_breaker(msp, (cxm, (bay_y0 + bay_y1) / 2),
                                    poles=3, scale=s * 0.14,
                                    label=f"{voltage_hv}-{i + 1}",
                                    layer=C.L_EQUIP)
        except Exception as _e:
            C.rect(msp, cxm - bay_width * 0.12, (bay_y0 + bay_y1) / 2 - 900,
                   cxm + bay_width * 0.12, (bay_y0 + bay_y1) / 2 + 900,
                   layer=C.L_EQUIP)
        C.eng_text(msp, f"{i + 1}#", (cxm, bay_y0 + C.P(3, s)), 2.8, s,
                   layer=C.L_TITLE)
    # 母线（GB/T 4728 粗实线）
    for k in (0.22, 0.34):
        by = bay_y0 + (bay_y1 - bay_y0) * k
        msp.add_line((hv_x0 - bay_width * 0.3, by),
                     (hv_x0 + bay_width * n_hv_bays, by),
                     dxfattribs={"layer": C.L_THICK})
    C.leader_note(msp, (hv_x0 + bay_width * n_hv_bays * 0.5, bay_y1),
                  f"{voltage_hv}配电装置区 {n_hv_bays}回", s, dx=10, dy=14)

    # ── 主变压器区 ──
    tw, td = transformer_size
    tf_y = bay_y0 - road_width - td
    tf_positions = []
    for i in range(n_transformers):
        tx0 = hv_x0 + (tw + 6000.0) * i
        C.rect(msp, tx0, tf_y, tx0 + tw, tf_y + td, layer=C.L_THICK)
        # 变压器本体符号（双圆，GB/T 4728）
        ccx, ccy = tx0 + tw / 2, tf_y + td / 2
        r = min(tw, td) * 0.20
        msp.add_circle((ccx, ccy + r * 0.55), r, dxfattribs={"layer": C.L_EQUIP})
        msp.add_circle((ccx, ccy - r * 0.55), r, dxfattribs={"layer": C.L_EQUIP})
        C.eng_text(msp, f"T{i + 1}", (ccx, tf_y + td * 0.12), 3.5, s,
                   layer=C.L_TITLE)
        # 事故油池（GB 50059 §4.5）
        C.rect(msp, tx0 - 800, tf_y - 1500, tx0 + tw + 800, tf_y,
               layer=C.L_DASH)
        tf_positions.append((ccx, ccy))
    C.leader_note(msp, tf_positions[0] if tf_positions else (hv_x0, tf_y),
                  f"主变压器 {voltage_hv}/{voltage_lv}", s, dx=-20, dy=-16)
    C.leader_note(msp, (hv_x0 + tw / 2, tf_y - 750),
                  "事故油池 GB 50059", s, dx=18, dy=-12)

    # ── 配电装置楼（复用 building.draw_floor_plan 的墙体表达）──
    cw, cd = control_building
    cb_x0 = rx0 + road_width * 1.4
    cb_y0 = ry0 + road_width * 1.2
    try:
        building.draw_floor_plan(msp, (cb_x0, cb_y0),
                                 width=cw / 1000.0, length=cd / 1000.0,
                                 wall_thickness=0.24, scale=s,
                                 label=f"{voltage_lv}配电装置楼")
    except Exception as _e:
        C.rect(msp, cb_x0, cb_y0, cb_x0 + cw, cb_y0 + cd, layer=C.L_THICK)
        C.rect(msp, cb_x0 + 240, cb_y0 + 240, cb_x0 + cw - 240,
               cb_y0 + cd - 240, layer=C.L_THIN)
        C.text(msp, f"{voltage_lv}配电装置楼", (cb_x0 + cw / 2, cb_y0 + cd / 2),
               3.5, s, layer=C.L_TEXT)

    # ── 指北针（GB/T 50001 §7）──
    nx, ny = x1 + fence_offset - 4000.0, y1 + fence_offset - 4000.0
    nr = 2000.0
    msp.add_circle((nx, ny), nr, dxfattribs={"layer": C.L_THIN})
    C.solid_tri(msp, [(nx, ny + nr * 1.25), (nx - nr * 0.30, ny - nr * 0.75),
                      (nx + nr * 0.30, ny - nr * 0.75)], layer=C.L_THICK)
    C.eng_text(msp, "N", (nx, ny + nr * 1.62), 4.0, s, layer=C.L_TITLE)

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x0, y0), (x1, y0), offset=22, scale=s,
                     label=f"{int(site_width)}")
        C.dim_linear(msp, (x0, y0), (x0, y1), offset=22, scale=s,
                     label=f"{int(site_depth)}")

    C.eng_text(msp, tag, (x0 + site_width / 2, y1 + fence_offset + C.P(14, s)),
               5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x0 + site_width / 2, y1 + fence_offset + C.P(7, s)),
           4.0, s, layer=C.L_TITLE)

    if with_table:
        C.spec_table(msp, (x1 + fence_offset + C.P(10, s), y1),
                     [["电压等级", f"{voltage_hv}/{voltage_lv}"],
                      ["主变台数", f"{n_transformers} 台"],
                      ["高压间隔", f"{n_hv_bays} 回"],
                      ["站区尺寸", f"{int(site_width)}×{int(site_depth)}"],
                      ["执行标准", "GB 50059-2011"]],
                     s, col_w=(26.0, 38.0), title="变电站技术指标")

    return {"tag": tag, "site": (x0, y0, x1, y1),
            "transformers": tf_positions,
            "control_building": (cb_x0, cb_y0, cb_x0 + cw, cb_y0 + cd)}


# ══════════════════════════════════════════════════════════
#  2) 光伏方阵布置 + 支架基础
# ══════════════════════════════════════════════════════════

def draw_pv_array_foundation(msp, x: float, y: float, scale: float = 200.0,
                             n_rows: int = 4,
                             n_cols: int = 6,
                             module_width: float = 2280.0,
                             module_height: float = 1134.0,
                             modules_per_string: int = 2,
                             row_pitch: float = 6500.0,
                             col_gap: float = 40.0,
                             tilt_angle: float = 33.0,
                             pile_type: str = "螺旋钢桩",
                             pile_diameter: float = 140.0,
                             pile_depth: float = 2500.0,
                             pile_spacing: float = 4000.0,
                             front_height: float = 800.0,
                             tag: str = "GF-01",
                             name: str = "光伏方阵布置及支架基础图",
                             with_section: bool = True,
                             with_dims: bool = True,
                             with_table: bool = True,
                             **params):
    """绘制光伏方阵平面布置 + 支架基础剖面（GB 50797—2012）。

    参数
    ----
    n_rows / n_cols     方阵行列数
    module_width/height 组件尺寸 mm
    row_pitch           前后排间距（阵列中心距）mm
                        # TODO: verify against GB 50797 附录 —— 应按当地纬度、
                        #       冬至日 9:00—15:00 不遮挡计算，此处为占位默认值
    tilt_angle          组件倾角（度）
                        # TODO: verify —— 应按最佳倾角计算（随纬度变化）
    pile_type           ``螺旋钢桩`` / ``预制管桩`` / ``混凝土独立基础``
    pile_depth          桩入土深度 mm（# TODO: verify，由地勘抗拔试验确定）
    front_height        组件前沿离地高度 mm（GB 50797 不宜小于 300mm）

    返回 ``dict``：平面范围与剖面关键标高。
    """
    s = scale
    array_w = module_width * n_cols + col_gap * (n_cols - 1)
    array_d = module_height * modules_per_string * math.cos(
        math.radians(tilt_angle))

    # ══ 平面图 ══
    C.text(msp, "光伏方阵平面布置图", (x + array_w / 2, y + row_pitch * n_rows
                                      + C.P(10, s)), 4.0, s, layer=C.L_TITLE)
    piles = []
    for r in range(n_rows):
        ry = y + row_pitch * r
        # 组件阵列
        for c in range(n_cols):
            cx0 = x + (module_width + col_gap) * c
            C.rect(msp, cx0, ry, cx0 + module_width, ry + array_d,
                   layer=C.L_MID)
            msp.add_line((cx0, ry + array_d / 2),
                         (cx0 + module_width, ry + array_d / 2),
                         dxfattribs={"layer": C.L_THIN})
        # 阵列外框（粗实线）
        C.rect(msp, x, ry, x + array_w, ry + array_d, layer=C.L_THICK)
        # 基础桩位（前后各一排）
        n_p = max(int(array_w / pile_spacing) + 1, 2)
        for i in range(n_p):
            px = x + array_w * i / (n_p - 1)
            for py in (ry + array_d * 0.12, ry + array_d * 0.88):
                msp.add_circle((px, py), pile_diameter * 1.2,
                               dxfattribs={"layer": C.L_THICK})
                msp.add_line((px - pile_diameter * 1.8, py),
                             (px + pile_diameter * 1.8, py),
                             dxfattribs={"layer": C.L_CENTER})
                piles.append((px, py))
        C.eng_text(msp, f"R{r + 1}", (x - C.P(8, s), ry + array_d / 2),
                   3.0, s, layer=C.L_TITLE)

    if with_dims:
        C.dim_linear(msp, (x, y), (x + array_w, y), offset=16, scale=s,
                     label=f"阵列宽 {int(array_w)}")
        if n_rows >= 2:
            C.dim_linear(msp, (x + array_w, y), (x + array_w, y + row_pitch),
                         offset=-18, scale=s, label=f"D={int(row_pitch)}")
        C.leader_note(msp, piles[0] if piles else (x, y),
                      f"{pile_type} φ{int(pile_diameter)} 埋深{int(pile_depth)}",
                      s, dx=-22, dy=-14)

    # ══ 支架基础剖面（右侧）══
    sec = {}
    if with_section:
        sx = x + array_w + C.P(46, s)
        sy = y + row_pitch * (n_rows - 1) * 0.5
        sec = _pv_section(msp, sx, sy, s, module_height * modules_per_string,
                          tilt_angle, front_height, pile_diameter, pile_depth,
                          pile_type, with_dims)

    C.eng_text(msp, tag, (x + array_w / 2, y + row_pitch * n_rows + C.P(18, s)),
               5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x + array_w / 2, y - C.P(26, s)), 4.0, s,
           layer=C.L_TITLE)

    if with_table:
        C.spec_table(msp, (x, y - C.P(34, s)),
                     [["组件规格", f"{int(module_width)}×{int(module_height)}"],
                      ["阵列规模", f"{n_rows}行×{n_cols}列"],
                      ["组件倾角", f"{tilt_angle}°"],
                      ["前后排间距", f"{int(row_pitch)} mm"],
                      ["基础型式", pile_type],
                      ["执行标准", "GB 50797-2012"]],
                     s, col_w=(28.0, 40.0), title="光伏方阵技术指标")

    return {"tag": tag, "array": (x, y, x + array_w,
                                  y + row_pitch * (n_rows - 1) + array_d),
            "piles": piles, "section": sec}


def _pv_section(msp, x, y, s, panel_len, tilt, front_h, pile_d, pile_depth,
                pile_type, with_dims):
    """光伏支架基础剖面（含地面线、桩、斜梁、组件）。"""
    a = math.radians(tilt)
    dx = panel_len * math.cos(a)
    dy = panel_len * math.sin(a)
    y_g = y                                   # 自然地面
    p_front = (x, y_g + front_h)
    p_back = (x + dx, y_g + front_h + dy)

    # 地面线 + 素土
    gx0, gx1 = x - C.P(10, s), x + dx + C.P(12, s)
    msp.add_line((gx0, y_g), (gx1, y_g), dxfattribs={"layer": C.L_THICK})
    for i in range(17):
        gx = gx0 + (gx1 - gx0) * i / 16.0
        msp.add_line((gx, y_g), (gx - C.P(3, s), y_g - C.P(3, s)),
                     dxfattribs={"layer": C.L_THIN})

    # 组件（斜面双线）
    t = panel_len * 0.035
    nx, ny = -math.sin(a) * t, math.cos(a) * t
    msp.add_lwpolyline([p_front, p_back,
                        (p_back[0] + nx, p_back[1] + ny),
                        (p_front[0] + nx, p_front[1] + ny)],
                       close=True, dxfattribs={"layer": C.L_THICK})
    # 檩条
    for k in (0.25, 0.72):
        px = p_front[0] + dx * k
        py = p_front[1] + dy * k
        msp.add_circle((px, py), t * 0.7, dxfattribs={"layer": C.L_MID})

    # 前后立柱 + 斜撑
    for (pp, is_front) in ((p_front, True), (p_back, False)):
        cx = pp[0]
        C.rect(msp, cx - pile_d * 0.6, y_g, cx + pile_d * 0.6, pp[1],
               layer=C.L_THICK)
        # 桩身（地面以下，虚线表示不可见）
        C.rect(msp, cx - pile_d / 2, y_g - pile_depth, cx + pile_d / 2, y_g,
               layer=C.L_DASH)
        if "螺旋" in pile_type:
            n = 6
            for i in range(n):
                yy = y_g - pile_depth * (0.35 + 0.6 * i / n)
                msp.add_line((cx - pile_d * 1.1, yy),
                             (cx + pile_d * 1.1, yy + pile_depth * 0.05),
                             dxfattribs={"layer": C.L_THIN})
    msp.add_line((p_front[0] + pile_d * 0.6, y_g + front_h * 0.35),
                 (p_back[0] - pile_d * 0.6, p_back[1] * 1.0 - dy * 0.30),
                 dxfattribs={"layer": C.L_MID})

    C.text(msp, "支架基础剖面 1-1", ((p_front[0] + p_back[0]) / 2,
                                     y_g - pile_depth - C.P(10, s)),
           3.5, s, layer=C.L_TITLE)

    if with_dims:
        C.dim_linear(msp, (p_front[0], y_g), (p_front[0], y_g + front_h),
                     offset=14, scale=s, label=f"{int(front_h)}")
        C.dim_linear(msp, (p_back[0], y_g - pile_depth), (p_back[0], y_g),
                     offset=-16, scale=s, label=f"埋深{int(pile_depth)}")
        C.leader_note(msp, ((p_front[0] + p_back[0]) / 2,
                            (p_front[1] + p_back[1]) / 2),
                      f"组件倾角 {tilt}°", s, dx=-18, dy=16)
        C.elevation_mark(msp, (gx0 + C.P(3, s), y_g), "±0.000", s)

    return {"ground": y_g, "front": p_front, "back": p_back}


# ══════════════════════════════════════════════════════════
#  3) 风机基础
# ══════════════════════════════════════════════════════════

def draw_wtg_foundation(msp, x: float, y: float, scale: float = 100.0,
                        base_diameter: float = 19000.0,
                        pedestal_diameter: float = 6000.0,
                        base_edge_thk: float = 1200.0,
                        base_center_thk: float = 3000.0,
                        pedestal_height: float = 1200.0,
                        embed_depth: float = 3000.0,
                        cushion_thk: float = 100.0,
                        anchor_cage_d: float = 4500.0,
                        n_anchor: int = 120,
                        anchor_spec: str = "M42",
                        concrete: str = "C40",
                        rebar_main: str = "HRB400",
                        turbine_model: str = "WTG-4.0MW",
                        tag: str = "FJ-01",
                        name: str = "风电机组扩展基础剖面图",
                        with_dims: bool = True,
                        with_table: bool = True,
                        **params):
    """绘制陆上风电机组重力式扩展基础剖面（NB/T 10311—2019 / GB 50007—2011）。

    参数
    ----
    base_diameter     基础底板直径 mm
                      # TODO: verify against NB/T 10311 —— 由倾覆力矩、
                      #       地基承载力与抗倾覆稳定性验算确定
    base_edge_thk     底板边缘厚度 mm
    base_center_thk   底板中心（台柱根部）厚度 mm
    embed_depth       基础埋深（自然地面到底板底面）mm
    anchor_cage_d     锚栓笼直径 mm
    n_anchor          锚栓总数

    返回 ``dict``：关键标高。
    """
    s = scale
    R = base_diameter / 2.0
    Rp = pedestal_diameter / 2.0

    y_bot = y                                   # 垫层顶 = 底板底
    y_edge = y_bot + base_edge_thk
    y_center = y_bot + base_center_thk
    y_ped_top = y_center + pedestal_height
    y_grade = y_bot + embed_depth               # 自然地面

    C.centerline(msp, (x, y_bot - C.P(12, s)), (x, y_ped_top + C.P(20, s)))

    # ── 垫层（GB 50007 §8.2 C15 素混凝土）──
    C.rect(msp, x - R - 100, y_bot - cushion_thk, x + R + 100, y_bot,
           layer=C.L_MID)

    # ── 底板（锥台形）──
    msp.add_lwpolyline([
        (x - R, y_bot), (x + R, y_bot), (x + R, y_edge),
        (x + Rp, y_center), (x - Rp, y_center), (x - R, y_edge),
    ], close=True, dxfattribs={"layer": C.L_THICK})
    # ── 台柱 ──
    C.rect(msp, x - Rp, y_center, x + Rp, y_ped_top, layer=C.L_THICK)
    C.hatch_area(msp, [(x - R, y_bot), (x + R, y_bot), (x + R, y_edge),
                       (x + Rp, y_center), (x + Rp, y_ped_top),
                       (x - Rp, y_ped_top), (x - Rp, y_center),
                       (x - R, y_edge)], scale=s, pattern_scale=1.6)

    # ── 锚栓笼（NB/T 10311 预应力锚栓）──
    ra = anchor_cage_d / 2.0
    for sg in (-1, 1):
        ax = x + sg * ra
        msp.add_line((ax, y_bot + base_edge_thk * 0.35), (ax, y_ped_top),
                     dxfattribs={"layer": C.L_THICK})
        msp.add_line((ax - 90, y_bot + base_edge_thk * 0.35),
                     (ax + 90, y_bot + base_edge_thk * 0.35),
                     dxfattribs={"layer": C.L_THICK})   # 下锚板
    C.rect(msp, x - ra - 400, y_ped_top - 120, x + ra + 400, y_ped_top,
           layer=C.L_MID)                                # 上锚板/基础环法兰

    # ── 塔筒段 ──
    tw = anchor_cage_d * 0.92
    for sg in (-1, 1):
        msp.add_line((x + sg * tw / 2, y_ped_top),
                     (x + sg * tw / 2, y_ped_top + C.P(22, s)),
                     dxfattribs={"layer": C.L_THICK})
    C.text(msp, "塔筒", (x, y_ped_top + C.P(14, s)), 3.5, s, layer=C.L_TEXT)

    # ── 配筋示意（径向 + 环向，细实线）──
    for k in (0.18, 0.82):
        yy = y_bot + base_edge_thk * k
        msp.add_line((x - R * 0.96, yy), (x + R * 0.96, yy),
                     dxfattribs={"layer": C.L_THIN})
    for i in range(9):
        bx = x - R * 0.9 + R * 1.8 * i / 8.0
        msp.add_line((bx, y_bot + base_edge_thk * 0.18),
                     (bx, y_bot + base_edge_thk * 0.82),
                     dxfattribs={"layer": C.L_THIN})

    # ── 自然地面线与回填 ──
    gx0, gx1 = x - R - C.P(14, s), x + R + C.P(14, s)
    msp.add_line((gx0, y_grade), (x - R, y_grade),
                 dxfattribs={"layer": C.L_THICK})
    msp.add_line((x + R, y_grade), (gx1, y_grade),
                 dxfattribs={"layer": C.L_THICK})
    for i in range(9):
        for gx in (gx0 + (x - R - gx0) * i / 8.0,
                   x + R + (gx1 - x - R) * i / 8.0):
            msp.add_line((gx, y_grade), (gx - C.P(3, s), y_grade - C.P(3, s)),
                         dxfattribs={"layer": C.L_THIN})
    # 回填土（双点画线示意坡面）
    msp.add_line((x - R, y_edge), (x - R - (y_grade - y_edge) * 1.5, y_grade),
                 dxfattribs={"layer": C.L_PHANTOM})
    msp.add_line((x + R, y_edge), (x + R + (y_grade - y_edge) * 1.5, y_grade),
                 dxfattribs={"layer": C.L_PHANTOM})

    # ── 标注 ──
    if with_dims:
        C.dim_linear(msp, (x - R, y_bot), (x + R, y_bot), offset=22, scale=s,
                     label=f"φ{int(base_diameter)}")
        C.dim_linear(msp, (x - Rp, y_ped_top), (x + Rp, y_ped_top),
                     offset=-16, scale=s, label=f"φ{int(pedestal_diameter)}")
        C.dim_linear(msp, (x + R, y_bot), (x + R, y_edge), offset=-14, scale=s,
                     label=f"{int(base_edge_thk)}")
        C.dim_linear(msp, (x - R, y_bot), (x - R, y_grade), offset=30, scale=s,
                     label=f"埋深 {int(embed_depth)}")
        C.leader_note(msp, (x + ra, y_center + pedestal_height * 0.5),
                      f"{n_anchor}-{anchor_spec} 预应力锚栓 NB/T 10311",
                      s, dx=20, dy=14)
        C.leader_note(msp, (x, y_bot + base_edge_thk * 0.5),
                      f"底板 {concrete} 主筋{rebar_main}", s, dx=-24, dy=-14)
        C.leader_note(msp, (x - R * 0.5, y_bot - cushion_thk / 2),
                      f"C15 素混凝土垫层 δ={int(cushion_thk)}", s,
                      dx=-18, dy=-16)
        C.elevation_mark(msp, (gx1 - C.P(6, s), y_grade), "±0.000", s)
        C.elevation_mark(msp, (x + R * 0.6, y_bot),
                         f"-{embed_depth / 1000.0:.3f}", s)

    C.eng_text(msp, tag, (x, y_ped_top + C.P(34, s)), 5.0, s, layer=C.L_TITLE)
    C.text(msp, name, (x, y_ped_top + C.P(28, s)), 4.0, s, layer=C.L_TITLE)

    if with_table:
        C.spec_table(msp, (x + R + C.P(18, s), y_ped_top + C.P(24, s)),
                     [["机组型号", turbine_model],
                      ["基础型式", "重力式扩展基础"],
                      ["底板直径", f"φ{int(base_diameter)}"],
                      ["基础埋深", f"{int(embed_depth)} mm"],
                      ["混凝土", concrete],
                      ["锚栓", f"{n_anchor}-{anchor_spec}"],
                      ["执行标准", "NB/T 10311-2019"]],
                     s, col_w=(28.0, 40.0), title="风机基础技术指标")

    return {"tag": tag, "bottom": y_bot, "grade": y_grade,
            "pedestal_top": y_ped_top, "radius": R}
