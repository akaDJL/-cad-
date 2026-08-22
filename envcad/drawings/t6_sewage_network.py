"""T6：小型生活区污水自流管网平面布置工程图 v2.2（GB给排水制图规范）。

v2.2 零重叠布局（坐标级碰撞推演 + 采样法复核）：
- 构筑物名称一律置池顶上方；标高+尺寸合并单行置池底下方（杜绝叠字）
- 管径+坡度合并标注「DN300 i=0.57%」置上方车道；下游段坡度单独标注置下方
  车道并嵌入支管走廊之间的空档（细引线回指管段中点）
- 井底标高置井下方车道，左右交替偏置；支管 DN200 标注奇偶分侧
- 技术要求与水力校验报告并排于内框左下/中下，底边收口于图框底边之上
- 图例内框右上、指北针内框左上、市政接口标注避开图例区
- 内置水力校验引擎：倒坡/坡度不足/井衔接/支管-构筑物空间碰撞 全检
"""
from __future__ import annotations

import math
import os
from typing import Dict, List, Tuple

from ezdxf.enums import TextEntityAlignment

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame, save_dxf_autofit
from ..standards.annotate import (
    _t, draw_elevation, draw_flow_arrow, draw_pipe_diameter,
)
from ..standards.legend import draw_legend
from ..components.pipe import draw_pipe

# ─── 几何工具 ────────────────────────────────────────────

def _seg_hits_rect(p1, p2, rect, n=60) -> bool:
    """采样法判断线段是否与矩形相交（空间碰撞检测）。"""
    x0, y0, x1, y1 = rect
    for i in range(n + 1):
        t = i / n
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def _x_at_y(p1, p2, y) -> float:
    """线段在指定 y 处的 x 坐标（用于支管走廊推算）。"""
    if abs(p2[1] - p1[1]) < 1e-6:
        return (p1[0] + p2[0]) / 2
    t = (y - p1[1]) / (p2[1] - p1[1])
    return p1[0] + (p2[0] - p1[0]) * t


# ─── 水力校验引擎 ────────────────────────────────────────

class HydraulicVerifier:
    """管网水力校验：倒坡积水 / 坡度不足 / 井衔接 / 空间碰撞。"""

    MIN_SLOPE = 0.003   # GB 最小自清坡度 0.3%

    def __init__(self):
        self.pipes: List[Dict] = []
        self.risks: List[Dict] = []

    def add_pipe(self, pipe_id, start_il, end_il, length_m, dn, kind="main"):
        slope = (start_il - end_il) / length_m if length_m > 0 else 0.0
        self.pipes.append(dict(id=pipe_id, start_il=start_il, end_il=end_il,
                               length=length_m, dn=dn, slope=slope, kind=kind))
        if slope < 0:
            self.risks.append(dict(pipe=pipe_id, type="倒坡积水",
                                   detail=f"逆坡 {slope*100:.2f}%（{start_il:.3f}→{end_il:.3f}）",
                                   suggestion="抬升下游或降低上游管底标高"))
        elif slope < self.MIN_SLOPE:
            self.risks.append(dict(pipe=pipe_id, type="坡度不足",
                                   detail=f"坡度 {slope*100:.2f}% < 0.30%",
                                   suggestion="增大坡降或缩小管径"))

    def check_junction(self, up_il, down_il, jid, tol=0.005):
        if up_il < down_il - tol:
            self.risks.append(dict(pipe=jid, type="标高衔接不良",
                                   detail=f"上游{up_il:.3f} < 下游{down_il:.3f}",
                                   suggestion="调整井内管底落差"))

    def check_collision(self, pipe_id, p1, p2, rect, rect_name):
        if _seg_hits_rect(p1, p2, rect):
            self.risks.append(dict(pipe=pipe_id, type="空间碰撞",
                                   detail=f"管段穿越{rect_name}",
                                   suggestion="调整管线走向绕开构筑物"))


# ─── 构件绘制 ────────────────────────────────────────────

def draw_well(msp, center, scale, well_id, tracker=None):
    """圆形砖砌检查井 φ1000，编号置井正上方。"""
    s = scale
    cx, cy = center
    r = 500
    msp.add_circle((cx, cy), r, dxfattribs={"layer": "检查井"})
    msp.add_circle((cx, cy), r - 120, dxfattribs={"layer": "中实线"})
    _t(msp, well_id, (cx, cy + r + 2.2 * s), 3 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题", tracker=tracker)
    if tracker is not None:
        tracker.register(cx - r - s, cy - r - s, cx + r + s, cy + r + 4 * s, margin=40)


def _struct_frame(msp, box, s, name, sub_txt, tracker, name_y):
    """构筑物标注：名称置池顶上方；标高+尺寸合并单行置池底下方。"""
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    _t(msp, name, (cx, name_y), 3 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题", tracker=tracker)
    _t(msp, sub_txt, (cx, y0 - 2.2 * s), 2.2 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)


def draw_septic(msp, origin, scale, tank_id, sub_txt, tracker=None):
    """化粪池平面：3.0×2.0m 三格，壁200。"""
    s = scale
    ox, oy = origin
    L, W, t = 3000, 2000, 200
    x0, y0 = ox, oy
    x1, y1 = ox + L + 2 * t, oy + W + 2 * t
    ix0, iy0 = ox + t, oy + t
    ix1, iy1 = ox + L + t, oy + W + t
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": "池体-壁"})
    msp.add_lwpolyline([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)],
                       close=True, dxfattribs={"layer": "中实线"})
    g1 = ix0 + L * 0.4
    g2 = ix0 + L * 0.7
    msp.add_line((g1, iy0), (g1, iy1), dxfattribs={"layer": "虚线"})
    msp.add_line((g2, iy0), (g2, iy1), dxfattribs={"layer": "虚线"})
    _struct_frame(msp, (x0, y0, x1, y1), s, tank_id, sub_txt, tracker, y1 + 2.2 * s)
    if tracker is not None:
        tracker.register(x0 - 2 * s, y0 - 4 * s, x1 + 2 * s, y1 + 4.5 * s, margin=60)
    return (x0, y0, x1, y1)


def draw_screen(msp, origin, scale, well_id, sub_txt, tracker=None):
    """格栅井平面：1.5×1.0m，壁150，栅条间隙20mm。"""
    s = scale
    ox, oy = origin
    L, W, t = 1500, 1000, 150
    x0, y0 = ox, oy
    x1, y1 = ox + L + 2 * t, oy + W + 2 * t
    ix0, iy0 = ox + t, oy + t
    ix1, iy1 = ox + L + t, oy + W + t
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": "池体-壁"})
    msp.add_lwpolyline([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)],
                       close=True, dxfattribs={"layer": "中实线"})
    for i in range(5):
        gx = ix0 + (i + 1) * L / 6
        msp.add_line((gx, iy0), (gx, iy1), dxfattribs={"layer": "细实线"})
    _struct_frame(msp, (x0, y0, x1, y1), s, well_id, sub_txt, tracker, y1 + 2.2 * s)
    if tracker is not None:
        tracker.register(x0 - 2 * s, y0 - 4 * s, x1 + 2 * s, y1 + 4.5 * s, margin=60)
    return (x0, y0, x1, y1)


def draw_regulating(msp, origin, scale, tank_id, sub_txt, tracker=None):
    """调节池平面：4.0×3.0m，壁250，中央搅拌器符号。"""
    s = scale
    ox, oy = origin
    L, W, t = 4000, 3000, 250
    x0, y0 = ox, oy
    x1, y1 = ox + L + 2 * t, oy + W + 2 * t
    ix0, iy0 = ox + t, oy + t
    ix1, iy1 = ox + L + t, oy + W + t
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": "池体-壁"})
    msp.add_lwpolyline([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)],
                       close=True, dxfattribs={"layer": "中实线"})
    cxp, cyp = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    msp.add_circle((cxp, cyp), 4 * s, dxfattribs={"layer": "细实线"})
    msp.add_line((cxp - 6 * s, cyp), (cxp + 6 * s, cyp), dxfattribs={"layer": "细实线"})
    msp.add_line((cxp, cyp - 6 * s), (cxp, cyp + 6 * s), dxfattribs={"layer": "细实线"})
    _struct_frame(msp, (x0, y0, x1, y1), s, tank_id, sub_txt, tracker, y1 + 2.2 * s)
    if tracker is not None:
        tracker.register(x0 - 2 * s, y0 - 4 * s, x1 + 2 * s, y1 + 4.5 * s, margin=60)
    return (x0, y0, x1, y1)


def draw_building(msp, center, scale, name, tracker=None):
    """住宅楼轮廓 8×6m + 楼号，返回顶边中点（支管接驳点）。"""
    s = scale
    cx, cy = center
    w, h = 8000, 6000
    x0, y0 = cx - w / 2, cy - h / 2
    x1, y1 = cx + w / 2, cy + h / 2
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": "中实线"})
    _t(msp, name, (cx, cy), 3 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
    if tracker is not None:
        tracker.register(x0 - s, y0 - s, x1 + s, y1 + s, margin=60)
    return (cx, y1)


def draw_slope_tag(msp, pos, scale, slope_pct, leader_to=None, tracker=None):
    """坡度标注：小箭头+i=数值；可选细引线回指管段中点。"""
    s = scale
    x, y = pos
    # 小箭头（顺流向右下）
    msp.add_lwpolyline([(x, y), (x + 3 * s, y), (x + 2.4 * s, y + 0.8 * s)],
                       dxfattribs={"layer": "标注"})
    msp.add_lwpolyline([(x + 3 * s, y), (x + 2.4 * s, y - 0.8 * s)],
                       dxfattribs={"layer": "标注"})
    _t(msp, f"i={slope_pct:.2f}%", (x + 4 * s, y), 2.5 * s,
       align=TextEntityAlignment.MIDDLE_LEFT, layer="文字", tracker=tracker)
    if leader_to is not None:
        msp.add_line((x, y + 0.5 * s), leader_to, dxfattribs={"layer": "细实线-辅助"})


# ─── 主入口 ──────────────────────────────────────────────

def gen_t6(out_dir: str, scale: float = 200.0) -> str:
    s = scale
    doc, dim, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()

    info = FrameInfo(
        title="小型生活区污水自流管网平面布置图",
        drawing_no="T6-01",
        scale_str=f"1:{int(scale)}",
        project="生活区污水管网工程",
        unit="给排水工程",
        designer="EnvCAD",
        date="2026.08",
    )
    x0, y0, x1, y1 = draw_frame(doc, scale, info, tracker=tracker)

    # ════════ 布局总控（1:200，内框 ≈ 5000..82000 × 2000..57400） ════════
    Y_MAIN = 42000                # 主管线走廊中心
    Y_BUILD = 26000               # 住宅楼排中心
    LANE_DN = Y_MAIN + 4400       # 管径合并标注车道（上，文字落位≈44600）
    LANE_SLOPE = Y_MAIN - 3400    # 坡度标注车道（下，38600）
    LANE_WELL_EL = Y_MAIN - 2200  # 井底标高车道（下，39800）

    # ── 节点标高表（自上游向下游单调递减，水力自洽） ──
    IL = {
        "J1": -1.500, "GS-01": -1.520, "J2": -1.550,
        "HFC-01": -1.570, "J3": -1.610,
        "HFC-02": -1.630, "J4": -1.670,
        "HFC-03": -1.690, "J5": -1.730, "J6": -1.750,
        "TJC-01": -1.790, "J7": -1.830, "J8": -1.870,
        "MUNI": -2.200,
    }

    # ── 构筑物（沿主管自上游→下游；名称在顶、标高+尺寸合并在底） ──
    gs_box   = draw_screen(msp, (9000, 41200), s, "GS-01",
                           f"IL={IL['GS-01']:.3f}  1.5×1.0m 栅隙20mm", tracker)
    hfc1_box = draw_septic(msp, (17500, 41000), s, "HFC-01",
                           f"IL={IL['HFC-01']:.3f}  3.0×2.0m V=12m³", tracker)
    hfc2_box = draw_septic(msp, (27500, 41000), s, "HFC-02",
                           f"IL={IL['HFC-02']:.3f}  3.0×2.0m V=12m³", tracker)
    hfc3_box = draw_septic(msp, (37500, 41000), s, "HFC-03",
                           f"IL={IL['HFC-03']:.3f}  3.0×2.0m V=12m³", tracker)
    tjc_box  = draw_regulating(msp, (52500, 40500), s, "TJC-01",
                               f"IL={IL['TJC-01']:.3f}  4.0×3.0m V=30m³", tracker)

    # ── 检查井（主管8座） ──
    well_xy = {
        "J1": (6000, Y_MAIN), "J2": (14000, Y_MAIN), "J3": (24000, Y_MAIN),
        "J4": (34000, Y_MAIN), "J5": (44000, Y_MAIN), "J6": (49000, Y_MAIN),
        "J7": (60000, Y_MAIN), "J8": (64000, Y_MAIN),
    }
    for wid, pos in well_xy.items():
        draw_well(msp, pos, s, wid, tracker)

    # ── 节点表：名称 → (连接点, 管底标高) ──
    nodes: Dict[str, Tuple[Tuple[float, float], float]] = {
        "J1":       (well_xy["J1"], IL["J1"]),
        "GS-01.L":  ((gs_box[0], 41700), IL["GS-01"]),
        "GS-01.R":  ((gs_box[2], 41700), IL["GS-01"] - 0.010),
        "J2":       (well_xy["J2"], IL["J2"]),
        "HFC-01.L": ((hfc1_box[0], Y_MAIN), IL["HFC-01"]),
        "HFC-01.R": ((hfc1_box[2], Y_MAIN), IL["HFC-01"] - 0.020),
        "J3":       (well_xy["J3"], IL["J3"]),
        "HFC-02.L": ((hfc2_box[0], Y_MAIN), IL["HFC-02"]),
        "HFC-02.R": ((hfc2_box[2], Y_MAIN), IL["HFC-02"] - 0.020),
        "J4":       (well_xy["J4"], IL["J4"]),
        "HFC-03.L": ((hfc3_box[0], Y_MAIN), IL["HFC-03"]),
        "HFC-03.R": ((hfc3_box[2], Y_MAIN), IL["HFC-03"] - 0.020),
        "J5":       (well_xy["J5"], IL["J5"]),
        "J6":       (well_xy["J6"], IL["J6"]),
        "TJC-01.L": ((tjc_box[0], Y_MAIN), IL["TJC-01"]),
        "TJC-01.R": ((tjc_box[2], Y_MAIN), IL["TJC-01"] - 0.020),
        "J7":       (well_xy["J7"], IL["J7"]),
        "J8":       (well_xy["J8"], IL["J8"]),
        "MUNI":     ((67500, Y_MAIN), IL["MUNI"]),
    }

    route = ["J1", "GS-01.L", "GS-01.R", "J2", "HFC-01.L", "HFC-01.R",
             "J3", "HFC-02.L", "HFC-02.R", "J4", "HFC-03.L", "HFC-03.R",
             "J5", "J6", "TJC-01.L", "TJC-01.R", "J7", "J8", "MUNI"]

    verifier = HydraulicVerifier()

    # ── 主管绘制（先全部画线，后统一标注） ──
    segments = []   # (idx, a, b, pa, pb, ila, ilb, length_m, mid)
    seg_idx = 0
    for a, b in zip(route[:-1], route[1:]):
        pa, ila = nodes[a]
        pb, ilb = nodes[b]
        draw_pipe(msp, pa, pb, dn=300, scale=s, style="single", layer="管道-污水")
        seg_idx += 1
        length_m = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) / 1000.0
        verifier.add_pipe(f"W{seg_idx}", ila, ilb, length_m, 300, "main")
        mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        internal = (a.split(".")[0] == b.split(".")[0])
        segments.append((seg_idx, a, b, pa, pb, ila, ilb, length_m, mid, internal))
        # 流向箭头（贴管线）
        if length_m >= 1.5:
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            n = math.hypot(dx, dy) or 1.0
            draw_flow_arrow(msp, mid, (dx / n, dy / n), s,
                            length=8.0, label=None, tracker=tracker)

    # ── 主管标注：合并「DN300 i=x.xx%」→ 上方车道（代表性管段） ──
    ext = [sg for sg in segments if not sg[9] and sg[1] != "J8"]  # 外部段（末段除外）
    dn_segs = {4, 7, 10, 13, 17}          # 合并标注段（间距≥8m，互不重叠）
    slope_segs = {3, 6, 9, 12, 14, 16}    # 坡度单标段（下方车道空档）
    slope_slot_x = {3: 10000, 6: 18000, 9: 28000, 12: 38000, 14: 53000, 16: 56000}

    for sg in ext:
        idx, a, b, pa, pb, ila, ilb, length_m, mid, _ = sg
        slope_pct = (ila - ilb) / length_m * 100 if length_m > 0 else 0.0
        if idx in dn_segs:
            _t(msp, f"DN300  i={slope_pct:.2f}%", (mid[0] - 900, LANE_DN), 2.5 * s,
               align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)
            # 短引线：标注→管段中点
            msp.add_line((mid[0] - 900, LANE_DN - 1.2 * s), (mid[0], mid[1] + 0.8 * s),
                         dxfattribs={"layer": "细实线-辅助"})
        elif idx in slope_segs:
            sx = slope_slot_x[idx]
            draw_slope_tag(msp, (sx, LANE_SLOPE), s, slope_pct,
                           leader_to=(mid[0], mid[1] - 0.8 * s), tracker=tracker)

    # 井底标高：井下方车道，左右交替偏置
    for k, (wid, (wx, wy)) in enumerate(well_xy.items()):
        il = nodes[wid][1]
        side = "right" if k % 2 == 0 else "left"
        off = 900 if k % 2 == 0 else -900
        draw_elevation(msp, (wx + off, LANE_WELL_EL), f"{il:.3f}", s,
                       side=side, level=0, tracker=tracker)

    # ── 分支支管（DN200，住宅楼→检查井，顺坡≥1%） ──
    branches = [
        ("J1", (7000, Y_BUILD),  "6#楼"),
        ("J2", (11500, Y_BUILD), "1#楼"),
        ("J3", (21500, Y_BUILD), "2#楼"),
        ("J4", (31500, Y_BUILD), "3#楼"),
        ("J5", (41500, Y_BUILD), "4#楼"),
        ("J6", (49000, Y_BUILD), "5#楼"),
    ]
    struct_rects = {
        "GS-01": gs_box, "HFC-01": hfc1_box, "HFC-02": hfc2_box,
        "HFC-03": hfc3_box, "TJC-01": tjc_box,
    }
    for i, (wid, bcenter, bname) in enumerate(branches, start=1):
        wpos, wil = nodes[wid]
        bend = draw_building(msp, bcenter, s, bname, tracker)   # 楼顶边中点
        bil = wil + 0.15                                        # 楼端（上游）抬高0.15m
        draw_pipe(msp, bend, wpos, dn=200, scale=s, style="single", layer="管道-污水")
        length_m = math.hypot(wpos[0] - bend[0], wpos[1] - bend[1]) / 1000.0
        verifier.add_pipe(f"B{i}", bil, wil, length_m, 200, "branch")
        # 空间碰撞：支管 vs 各构筑物
        for sname, rect in struct_rects.items():
            verifier.check_collision(f"B{i}", bend, wpos, rect, sname)
        # 支管管径标注：奇偶分侧（B6 固定右侧避让 B5）
        mx, my = (bend[0] + wpos[0]) / 2, (bend[1] + wpos[1]) / 2
        if i == 6:
            side_off = 2600
        else:
            side_off = 2600 if i % 2 else -2600
        draw_pipe_diameter(msp, (mx + side_off, my), "DN200", s,
                           leader_dir=(-1 if side_off < 0 else 1, 0),
                           label="", tracker=tracker)
        # 楼端管底标高（楼顶上方）
        draw_elevation(msp, (bcenter[0] + 900, bcenter[1] + 4200), f"{bil:.3f}", s,
                       side="right", level=0, tracker=tracker)

    # ── 水力校验：井衔接逐段复核 ──
    for a, b in zip(route[:-1], route[1:]):
        verifier.check_junction(nodes[a][1], nodes[b][1], f"{a}→{b}")
    verifier.check_junction(nodes["J8"][1], nodes["MUNI"][1] + 0.30,
                            "J8→市政(≥0.3m)")

    # ── 市政接口标注（下方车道，避开图例区） ──
    mx, my = nodes["MUNI"][0]
    _t(msp, "接市政污水管网", (mx - 5500, LANE_SLOPE), 3 * s,
       align=TextEntityAlignment.MIDDLE_LEFT, layer="文字-标题", tracker=tracker)
    draw_elevation(msp, (mx - 1000, LANE_WELL_EL), f"{IL['MUNI']:.3f}", s,
                   side="right", level=0, tracker=tracker)

    # ── 图例（内框右上） ──
    legend_items = [
        ("pipe_solid", "污水主管", "DN300 HDPE"),
        ("pipe_dashed", "污水支管", "DN200 HDPE"),
        ("manhole", "检查井", "φ1000 砖砌"),
        ("septic_tank", "化粪池", "3.0×2.0m"),
        ("screen_well", "格栅井", "栅隙20mm"),
        ("regulating_tank", "调节池", "4.0×3.0m"),
        ("arrow_flow", "水流方向", "顺坡自流"),
        ("elevation", "管底标高", "单位 m"),
        ("slope", "管道坡度", "i=%"),
    ]
    draw_legend(msp, (x1 - 78 * s, y1 - 2.5 * s), s, legend_items,
                title="图  例", col_widths=(16, 28, 32), row_h=7.0, tracker=tracker)

    # ── 指北针（内框左上） ──
    nx, ny = x0 + 6 * s, y1 - 5 * s
    msp.add_circle((nx, ny), 3.5 * s, dxfattribs={"layer": "粗实线"})
    msp.add_lwpolyline([(nx, ny + 3.5 * s), (nx - 2 * s, ny - 2 * s),
                        (nx + 2 * s, ny - 2 * s)], close=True,
                       dxfattribs={"layer": "粗实线"})
    _t(msp, "N", (nx, ny - 0.2 * s), 3 * s,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题", tracker=tracker)

    # ── 技术要求（内框左下） ──
    from . import draw_tech_notes
    tech_notes = [
        "管材采用HDPE双壁波纹管，主管DN300、支管DN200，橡胶圈密封接口。",
        "管道坡度：主管≥0.3%、支管≥0.5%，坡向水流方向，严禁倒坡。",
        "检查井采用φ1000mm砖砌圆形井，间距≤30m，Φ700铸铁井盖。",
        "化粪池C30钢筋混凝土，有效容积12m³/座，三格比例4:3:3。",
        "管道基础采用120°砂石基础，压实度≥95%。",
        "施工及验收执行GB 50268—2008。",
    ]
    draw_tech_notes(msp, (x0 + 2 * s, y0 + 52 * s), s,
                    "施工技术要求", tech_notes, width=86, line_h=6.0,
                    tracker=tracker)

    # ── 水力校验报告（内框中下，与技术要求并排） ──
    if verifier.risks:
        lines = [f"[{r['type']}] {r['pipe']}: {r['detail']} → {r['suggestion']}"
                 for r in verifier.risks[:7]]
        report_title = f"水力校验报告（{len(verifier.risks)}项风险）"
    else:
        lines = [
            "全线管网水力校验通过：",
            "· 主管各段坡度≥0.3%，无倒坡积水；",
            "· 支管6条坡度约1.1%≥0.5%，坡向检查井；",
            "· 各井管底标高顺流递减，衔接良好；",
            "· 支管与构筑物无空间碰撞；",
            "· J8(-1.870)高于市政接口(-2.200)0.33m≥0.3m。",
        ]
        report_title = "水力校验报告（通过）"
    draw_tech_notes(msp, (x0 + 92 * s, y0 + 52 * s), s,
                    report_title, lines, width=86, line_h=6.0,
                    tracker=tracker)

    return save_dxf_autofit(doc, os.path.join(out_dir, "T6_污水自流管网平面布置图.dxf"), scale, info, tracker)
