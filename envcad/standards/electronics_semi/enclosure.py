"""16. enclosure —— 机箱壳体 / 面板开孔（复用 building 墙体 + 标注模式）。

依据标准:
  * GB/T 1804—2000 一般公差——线性和角度尺寸的未注公差（钣金件常取 m 级）
  * GB/T 13914—2013 冲压件尺寸公差 / GB/T 15055—2021 冲压件未注公差尺寸
  * IEC 60297-3-100（等同 GB/T 3047.1—1995）482.6mm（19in）机柜面板系列，
      基本高度单位 U = 44.45mm，安装孔中心距 465.1mm
      # TODO: verify 安装孔纵向节距 15.875/15.875/12.7 against IEC 60297-3-100
  * GB/T 4458.4—2003 尺寸注法

复用说明:
  侧板立面直接调用 envcad.standards.building.draw_wall_elevation（墙体立面
  + 洞口画法），通过 _wall_mm() 把毫米尺寸换算成该函数期望的"米×scale"输入，
  从而复用已验证的洞口/立面绘制逻辑。

绘图约定: 19in 面板建议 1:2 出图，scale 默认 2.0。
"""
from __future__ import annotations

import sys

from ._common import (
    ENVCAD_ROOT, L_CENTER, L_HIDDEN, L_MID, L_OUTLINE, L_PHANTOM, L_TEXT,
    L_THIN, TextEntityAlignment, dim_line, gb1804_tolerance, hole, notes,
    param_table, rect, rounded_rect, text, view_title,
)

if ENVCAD_ROOT not in sys.path:  # pragma: no cover
    sys.path.insert(0, ENVCAD_ROOT)
from envcad.standards.building import draw_wall_elevation  # noqa: E402

#: IEC 60297-3-100 / GB/T 3047.1 机柜基本参数
RACK_WIDTH = 482.6      # 面板宽度 (19 in)
RACK_U = 44.45          # 高度单位 U
RACK_HOLE_SPAN = 465.1  # 左右安装孔中心距
RACK_PANEL_GAP = 0.8    # 面板间装配间隙


def draw_enclosure(msp, x, y, scale=2.0,
                   rack_u=3,
                   panel_w=None, panel_h=None,
                   depth=350.0,
                   thickness=1.5,
                   corner_r=3.0,
                   cutouts=None,
                   vent_slots=True,
                   vent_slot=(40.0, 3.0), vent_cols=6, vent_rows=4,
                   vent_gap=(8.0, 8.0), vent_origin=None,
                   rack_holes=True,
                   mount_hole=6.5,
                   tolerance_grade="m",
                   material="SPCC 冷轧钢板",
                   show_side_panel=True,
                   show_dims=True,
                   show_table=True,
                   show_notes=True,
                   tracker=None):
    """绘制机箱面板正视图（开孔 + 通风窗）与侧板立面。

    参数（单位 mm，全部可调）:
        x, y            面板左下角定位点
        rack_u          机箱高度 U 数；>0 时自动取 19in 面板尺寸
        panel_w/panel_h 面板宽/高；给定时覆盖 rack_u 推算值
        depth           机箱深度（侧板立面用）
        thickness       板厚（钣金）
        corner_r        面板圆角
        cutouts         开孔列表，每项 dict:
                        {"type":"rect"/"round"/"slot", "x":.., "y":..,
                         "w":.., "h":.., "dia":.., "r":.., "label":".."}
                        x,y 为开孔中心相对面板左下角的坐标
        vent_slots      是否绘制通风百叶阵列
        vent_slot       单条通风槽 (长, 宽)
        vent_cols/rows  通风槽列数/行数
        vent_gap        通风槽 (列间距, 行间距)
        vent_origin     通风阵列左下角相对坐标；None 则自动居右
        rack_holes      是否绘制 19in 安装孔
        mount_hole      安装孔径（M6 过孔 6.5）
        tolerance_grade GB/T 1804 未注公差等级

    返回 dict: 面板范围、开孔清单、未注公差值。
    """
    s = scale
    if panel_w is None:
        panel_w = RACK_WIDTH if rack_u > 0 else 300.0
    if panel_h is None:
        panel_h = rack_u * RACK_U - RACK_PANEL_GAP if rack_u > 0 else 180.0

    # ── 面板外形（粗实线，圆角）──
    rounded_rect(msp, x, y, panel_w, panel_h, corner_r, L_OUTLINE)
    # 折边线（钣金折弯，虚线）
    rect(msp, x + thickness * 2, y + thickness * 2,
         panel_w - 4 * thickness, panel_h - 4 * thickness, L_HIDDEN)

    ccx, ccy = x + panel_w / 2, y + panel_h / 2
    msp.add_line((x - 6 * s, ccy), (x + panel_w + 6 * s, ccy),
                 dxfattribs={"layer": L_CENTER})
    msp.add_line((ccx, y - 6 * s), (ccx, y + panel_h + 6 * s),
                 dxfattribs={"layer": L_CENTER})

    # ── 19in 安装孔（左右各上下两处）──
    holes = []
    if rack_holes and rack_u > 0:
        hx = [ccx - RACK_HOLE_SPAN / 2, ccx + RACK_HOLE_SPAN / 2]
        hy = [y + 6.35, y + panel_h - 6.35]
        for a in hx:
            for b in hy:
                hole(msp, a, b, mount_hole, L_OUTLINE)
                holes.append((a, b, mount_hole))

    # ── 面板开孔 ──
    cut_list = []
    if cutouts is None:
        cutouts = _default_cutouts(panel_w, panel_h)
    for cut in cutouts:
        cut_list.append(_draw_cutout(msp, x, y, cut, s))

    # ── 通风百叶阵列 ──
    if vent_slots and vent_cols > 0 and vent_rows > 0:
        sw, sh = vent_slot
        gx, gy = vent_gap
        if vent_origin is None:
            arr_w = vent_cols * sw + (vent_cols - 1) * gx
            arr_h = vent_rows * sh + (vent_rows - 1) * gy
            vent_origin = (panel_w - arr_w - 25.0, (panel_h - arr_h) / 2)
        vx, vy = vent_origin
        for r in range(vent_rows):
            for c in range(vent_cols):
                sx = x + vx + c * (sw + gx)
                sy = y + vy + r * (sh + gy)
                rounded_rect(msp, sx, sy, sw, sh, sh / 2.0, L_MID)
        text(msp, f"{vent_rows}×{vent_cols} 通风槽 {sw:g}×{sh:g}",
             (x + vx, y + vy - 5.0 * s), 2.2 * s, layer=L_TEXT)

    # ── 尺寸标注 ──
    tol = gb1804_tolerance(max(panel_w, panel_h), tolerance_grade)
    if show_dims:
        dim_line(msp, (x, y), (x + panel_w, y), 14.0 * s, s,
                 f"{panel_w:g}", tracker=tracker)
        dim_line(msp, (x, y), (x, y + panel_h), 12.0 * s, s,
                 f"{panel_h:g}", tracker=tracker)
        if holes:
            dim_line(msp, (holes[0][0], holes[0][1]),
                     (holes[2][0], holes[2][1]), 7.0 * s, s,
                     f"{RACK_HOLE_SPAN:g}", tracker=tracker)
            text(msp, f"4-φ{mount_hole:g} 安装孔",
                 (holes[0][0], y + panel_h + 4.0 * s), 2.5 * s,
                 align=TextEntityAlignment.MIDDLE_LEFT, layer=L_TEXT)
        for c in cut_list:
            if c.get("label"):
                text(msp, c["label"], (c["cx"], c["top"] + 3.0 * s), 2.2 * s,
                     align=TextEntityAlignment.MIDDLE_CENTER, layer=L_TEXT)

    view_title(msp, f"{rack_u}U 面板正视图" if rack_u > 0 else "面板正视图",
               ccx, y - 22.0 * s, s)

    # ── 侧板立面（复用 building.draw_wall_elevation）──
    side = None
    if show_side_panel:
        sx = x
        sy = y + panel_h + 26.0 * s
        side = _wall_mm(msp, (sx, sy), length_mm=depth, height_mm=panel_h,
                        thickness_mm=thickness, scale=s,
                        openings_mm=[{"x": depth * 0.55, "w": depth * 0.3,
                                      "y_sill": panel_h * 0.25,
                                      "h": panel_h * 0.5,
                                      "type": "window"}],
                        label="")
        view_title(msp, "侧板立面（含散热窗）", sx + depth / 2,
                   sy - 10.0 * s, s)
        dim_line(msp, (sx, sy), (sx + depth, sy), 8.0 * s, s,
                 f"{depth:g}", tracker=tracker)

    # ── 参数表 ──
    if show_table:
        param_table(msp, (x + panel_w + 16.0 * s, y + panel_h), [
            ("规格", f"19in {rack_u}U" if rack_u > 0 else "非标"),
            ("面板 W×H", f"{panel_w:g}×{panel_h:g}"),
            ("机箱深度", f"{depth:g}"),
            ("板厚 t", f"{thickness:g}"),
            ("材质", material),
            ("开孔数", str(len(cut_list))),
            ("安装孔", f"4-φ{mount_hole:g}" if holes else "—"),
            ("未注公差", f"GB/T 1804-{tolerance_grade} (±{tol:g})"),
        ], s, title="壳体参数")

    if show_notes:
        notes(msp, (x, y - 30.0 * s), [
            f"材质 {material}，板厚 {thickness:g}mm，展开后数控冲/激光下料。",
            f"未注线性尺寸公差按 GB/T 1804-{tolerance_grade}（±{tol:g}mm）；"
            "未注冲压件公差按 GB/T 15055。",
            "折弯内 R1.0，折弯角公差 ±0.5°；面板平面度 ≤0.5/500。",
            "开孔位置度 φ0.5（相对面板基准 A—B）。",
            "表面处理：喷塑 RAL7035，膜厚 60~80μm，附着力 ≥1 级。",
            "去毛刺，锐边倒钝 R0.3；焊点打磨平整。",
        ], s, title="技术要求", width=95.0, tracker=tracker)

    return {"panel": (x, y, x + panel_w, y + panel_h),
            "cutouts": cut_list, "rack_holes": holes,
            "tolerance": tol, "side_panel": side}


# ══════════════════════════════════════════════════════════
#  内部
# ══════════════════════════════════════════════════════════

def _default_cutouts(panel_w, panel_h):
    """缺省面板开孔样例：电源插座方孔 + 圆形指示灯 + 长圆孔。"""
    return [
        {"type": "rect", "x": 60.0, "y": panel_h / 2,
         "w": 47.0, "h": 27.0, "r": 2.0, "label": "AC 插座 47×27"},
        {"type": "round", "x": 120.0, "y": panel_h / 2,
         "dia": 16.0, "label": "φ16 指示灯"},
        {"type": "slot", "x": 165.0, "y": panel_h / 2,
         "w": 30.0, "h": 10.0, "label": "USB 长圆孔"},
    ]


def _draw_cutout(msp, ox, oy, cut, s):
    """按类型绘制单个面板开孔，返回其几何信息。"""
    kind = cut.get("type", "rect")
    cx = ox + cut.get("x", 0.0)
    cy = oy + cut.get("y", 0.0)
    label = cut.get("label", "")
    if kind == "round":
        d = cut.get("dia", 10.0)
        hole(msp, cx, cy, d, L_OUTLINE)
        return {"type": kind, "cx": cx, "cy": cy, "top": cy + d / 2,
                "size": (d, d), "label": label}
    w = cut.get("w", 20.0)
    h = cut.get("h", 10.0)
    r = cut.get("r", h / 2.0 if kind == "slot" else 1.0)
    rounded_rect(msp, cx - w / 2, cy - h / 2, w, h, min(r, h / 2.0), L_OUTLINE)
    # 开孔中心线
    msp.add_line((cx - w / 2 - 2 * s, cy), (cx + w / 2 + 2 * s, cy),
                 dxfattribs={"layer": L_CENTER})
    return {"type": kind, "cx": cx, "cy": cy, "top": cy + h / 2,
            "size": (w, h), "label": label}


def _wall_mm(msp, origin, length_mm, height_mm, thickness_mm, scale,
             openings_mm=None, label=""):
    """毫米输入适配器 —— 复用 envcad.standards.building.draw_wall_elevation。

    building 模块以"米 × scale"作为图元长度，本包以实物 mm 建模，
    故传入前统一除以 scale，使最终图元长度 = 实物 mm。
    """
    ops = []
    for op in (openings_mm or []):
        ops.append({
            "x": op["x"] / scale,
            "w": op["w"] / scale,
            "y_sill": op.get("y_sill", 0.0) / scale,
            "h": op.get("h", 10.0) / scale,
            "type": op.get("type", "window"),
        })
    draw_wall_elevation(
        msp, origin,
        length=length_mm / scale,
        height=height_mm / scale,
        thickness=thickness_mm / scale,
        openings=ops, scale=scale, label=label,
        layer=L_OUTLINE,
    )
    return (origin[0], origin[1],
            origin[0] + length_mm, origin[1] + height_mm)
