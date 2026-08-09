"""土壤与地下水修复制图 v1.0。

引用标准（均为现行最新版）：
  HJ 25.1-2019      建设用地土壤污染状况调查技术导则（代替HJ 25.1-2014）
  HJ 25.2-2019      建设用地土壤污染风险管控和修复监测技术导则（代替HJ 25.2-2014）
  HJ 25.3-2019      建设用地土壤污染风险评估技术导则（代替HJ 25.3-2014）
  HJ 25.4-2019      建设用地土壤修复技术导则（代替HJ 25.4-2014）
  HJ 25.5-2018      污染地块风险管控与土壤修复效果评估技术导则
  GB 36600-2018     土壤环境质量 建设用地土壤污染风险管控标准（试行）
  HJ 610-2016       环境影响评价技术导则 地下水环境（代替HJ 610-2011）
  HJ 1165-2021      污染土壤修复工程技术规范 原位热脱附
  HJ 1166-2021      污染土壤修复工程技术规范 异位热脱附
  HJ 2057-2018      危险废物集中焚烧处置工程技术规范

原位化学氧化注入井网、抽出处理系统(P&T)、热脱附装置、
土壤气相抽提(SVE)、生物修复、固化/稳定化、垂直防渗墙。

纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  原位化学氧化/还原注入
# ══════════════════════════════════════════════════════════

def draw_injection_well_grid(msp, origin, n_rows=3, n_cols=4,
                              spacing=5.0, depth=10.0,
                              oxidant="permanganate",
                              scale=100.0, label="", params=None,
                              layer="注入井", tracker=None):
    """原位注入井网平面布置图。

    参数:
        n_rows/n_cols: 井网行列数
        spacing: 井间距 m
        depth: 注入深度 m
        oxidant: "permanganate"高锰酸盐 / "persulfate"过硫酸盐 /
                 "ozone"臭氧 / "h2o2"双氧水 / "zero_valent_iron"零价铁
        params: {"radius":"2.5m","volume":"500L/井","concentration":"5%",
                  "flow":"2L/min","pump_pressure":"0.3MPa",...}
    """
    s = scale; ox, oy = _r(*origin)
    sp = spacing * s

    oxidant_labels = {
        "permanganate": "KMnO₄",
        "persulfate": "Na₂S₂O₈",
        "ozone": "O₃",
        "h2o2": "H₂O₂",
        "zero_valent_iron": "ZVI",
    }
    oxid_label = oxidant_labels.get(oxidant, "药剂")

    for i in range(n_rows):
        for j in range(n_cols):
            wx = ox + sp * j
            wy = oy + sp * i
            # 注入井：圆+十字
            r = 3 * s
            msp.add_circle((wx, wy), r, dxfattribs={"layer": layer})
            msp.add_line((wx - r, wy), (wx + r, wy),
                         dxfattribs={"layer": layer})
            msp.add_line((wx, wy - r), (wx, wy + r),
                         dxfattribs={"layer": layer})
            # 影响半径（虚线圆）
            inf_r = spacing * s * 0.55
            msp.add_circle((wx, wy), inf_r,
                           dxfattribs={"layer": "细实线", "linetype": "DASHED"})

            # 编号
            t = msp.add_text(f"I{i*n_cols+j+1}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG"})
            t.set_placement((wx, wy + r + 2 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    # 注入主管（水平连接第一行）
    main_y = oy - sp * 0.3
    total_w = sp * (n_cols - 1)
    msp.add_line((ox, main_y), (ox + total_w, main_y),
                 dxfattribs={"layer": "管道-加药", "lineweight": 50})
    for j in range(n_cols):
        wx = ox + sp * j
        msp.add_line((wx, main_y), (wx, oy),
                     dxfattribs={"layer": "管道-加药", "lineweight": 35})

    # 药剂罐
    tank_x = ox - 12 * s; tank_y = main_y
    tank_r = 4 * s
    msp.add_circle((tank_x, tank_y), tank_r, dxfattribs={"layer": "设备"})
    msp.add_line((tank_x, tank_y - tank_r), (tank_x, tank_y),
                 dxfattribs={"layer": layer})
    t = msp.add_text(oxid_label, dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "ENG"})
    t.set_placement((tank_x, tank_y + tank_r + 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    # 罐到主管
    msp.add_line((tank_x + tank_r, tank_y), (ox, main_y),
                 dxfattribs={"layer": "管道-加药", "lineweight": 50})
    _tri(msp, (ox, main_y), (1, 0), s, "管道-加药")

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + total_w / 2, oy + sp * n_rows + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + sp * n_rows + 5 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + total_w / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + total_w + 5 * s, oy + sp * n_rows)


def draw_injection_profile(msp, origin, depth=10.0, gw_depth=3.0,
                            n_screens=2, scale=100.0, label="",
                            params=None, layer="注入剖面", tracker=None):
    """原位注入剖面图。

    参数:
        depth: 注入深度 m
        gw_depth: 地下水埋深 m
        n_screens: 注射段数量
        params: {"oxidant":"KMnO₄","conc":"5%","flow":"2L/min",
                  "screen":"1-3m,6-8m","radius":"2.5m",...}
    """
    s = scale; ox, oy = _r(*origin)
    D = depth * s; GW = gw_depth * s
    well_w = 3 * s

    # 地面线
    msp.add_line((ox - 8 * s, oy), (ox + 12 * s, oy),
                 dxfattribs={"layer": layer, "lineweight": 35})

    # 井管（竖管）
    msp.add_lwpolyline(
        [(ox - well_w / 2, oy), (ox - well_w / 2, oy - D),
         (ox + well_w / 2, oy - D), (ox + well_w / 2, oy)],
        close=True, dxfattribs={"layer": layer})

    # 地下水位线
    msp.add_line((ox - 8 * s, oy - GW), (ox + 12 * s, oy - GW),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    t = msp.add_text("地下水位", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + 10 * s, oy - GW + 2 * s),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    # 注射段（筛管，虚线表示）
    screen_h = (D - GW) / (n_screens * 2 + 1)
    for i in range(n_screens):
        sy_top = oy - GW - screen_h * (2 * i + 1)
        sy_bot = oy - GW - screen_h * (2 * i + 2)
        msp.add_line((ox - well_w / 2 - 1 * s, sy_top),
                     (ox + well_w / 2 + 1 * s, sy_top),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((ox - well_w / 2 - 1 * s, sy_bot),
                     (ox + well_w / 2 + 1 * s, sy_bot),
                     dxfattribs={"layer": "细实线"})
        # 筛管区域标记
        msp.add_line((ox - well_w / 2, sy_top), (ox - well_w / 2, sy_bot),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
        msp.add_line((ox + well_w / 2, sy_top), (ox + well_w / 2, sy_bot),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
        # 影响范围弧线
        for ang in range(180, 361, 30):
            rad = math.radians(ang)
            r = 5 * s
            px = ox + r * math.cos(rad)
            py = (sy_top + sy_bot) / 2 + r * math.sin(rad) * 0.3
            msp.add_line((ox, (sy_top + sy_bot) / 2), (px, py),
                         dxfattribs={"layer": "细实线", "linetype": "DOTTED"})

    # 井口装置
    msp.add_lwpolyline(
        [(ox - well_w, oy + 2 * s), (ox + well_w, oy + 2 * s),
         (ox + well_w, oy), (ox - well_w, oy)],
        close=True, dxfattribs={"layer": layer})
    # 注入管
    msp.add_line((ox - 6 * s, oy + 1 * s), (ox - well_w, oy + 1 * s),
                 dxfattribs={"layer": "管道-加药"})
    _tri(msp, (ox - well_w, oy + 1 * s), (1, 0), s, "管道-加药")
    t = msp.add_text("药剂注入", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox - 8 * s, oy + 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 深度标注
    for d_mark in [GW, D]:
        t = msp.add_text(f"-{d_mark/s:.1f}m", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "ENG"})
        t.set_placement((ox + 6 * s, oy - d_mark),
                        align=TextEntityAlignment.MIDDLE_LEFT)
        msp.add_line((ox + well_w / 2, oy - d_mark),
                     (ox + 5 * s, oy - d_mark),
                     dxfattribs={"layer": "细实线-尺寸"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox, oy + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy - D - 5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + 12 * s, oy)


# ══════════════════════════════════════════════════════════
#  抽出处理系统 (Pump & Treat)
# ══════════════════════════════════════════════════════════

def draw_pump_treat_flow(msp, origin, scale=100.0, label="",
                          params=None, layer="工艺", tracker=None):
    """抽出处理系统(P&T)工艺流程图。

    params: {"wells":"6口","flow":"10m³/h","contaminant":"TCE",
              "treatment":"GAC+氧化","effluent":"<5μg/L",...}
    """
    s = scale; ox, oy = _r(*origin); spacing = 26 * s

    stages = [
        ("抽提井群", "EX-101"),
        ("集水池", "T-201"),
        ("调节池", "T-301"),
        ("处理单元", "P-401"),
        ("排放/回灌", "D-501"),
    ]
    bh = 12 * s; bw = 18 * s

    for i, (name, tag) in enumerate(stages):
        cx = ox + spacing * i

        if i == 0:
            # 抽提井群：3个小圆
            for j in range(3):
                jx = cx - 6 * s + j * 6 * s
                msp.add_circle((jx, oy), 2.5 * s, dxfattribs={"layer": layer})
                msp.add_line((jx, oy - 2.5 * s), (jx, oy + 2.5 * s),
                             dxfattribs={"layer": layer})
        elif i == 3:
            # 处理单元：矩形+内部处理标记
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})
            # GAC符号
            msp.add_lwpolyline(
                [(cx - 5 * s, oy - 3 * s), (cx - 2 * s, oy - 3 * s),
                 (cx - 2 * s, oy + 3 * s), (cx - 5 * s, oy + 3 * s)],
                close=True, dxfattribs={"layer": "细实线"})
            t = msp.add_text("GAC", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG"})
            t.set_placement((cx - 3.5 * s, oy),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            # 氧化符号
            msp.add_lwpolyline(
                [(cx + 2 * s, oy - 3 * s), (cx + 5 * s, oy - 3 * s),
                 (cx + 5 * s, oy + 3 * s), (cx + 2 * s, oy + 3 * s)],
                close=True, dxfattribs={"layer": "细实线"})
            t = msp.add_text("OX", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG"})
            t.set_placement((cx + 3.5 * s, oy),
                            align=TextEntityAlignment.MIDDLE_CENTER)
        elif i == 4:
            # 排放：箭头向下
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})
            msp.add_line((cx, oy - bh / 2), (cx, oy - bh / 2 - 4 * s),
                         dxfattribs={"layer": layer})
            _tri(msp, (cx, oy - bh / 2 - 4 * s), (0, -1), s, layer)
        else:
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})

        t = msp.add_text(name, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((cx, oy + bh / 2 + 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
        t2 = msp.add_text(tag, dxfattribs={
            "layer": "文字", "height": 1.8 * s, "style": "ENG"})
        t2.set_placement((cx, oy - bh / 2 - 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)

        if i < len(stages) - 1:
            nx = ox + spacing * (i + 1)
            msp.add_line((cx + bw / 2, oy), (nx - bw / 2, oy),
                         dxfattribs={"layer": layer})
            _tri(msp, (nx - bw / 2, oy), (1, 0), s, layer)

    # 回灌支路（处理→抽提井）
    ret_y = oy - bh / 2 - 8 * s
    ret_x_start = ox + spacing * 3
    msp.add_line((ret_x_start, oy - bh / 2), (ret_x_start, ret_y),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    msp.add_line((ret_x_start, ret_y), (ox, ret_y),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    msp.add_line((ox, ret_y), (ox, oy - 2.5 * s),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    _tri(msp, (ox, oy - 2.5 * s), (0, 1), s, "细实线")
    t = msp.add_text("回灌", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + spacing * 1.5, ret_y + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + spacing * 2, oy + bh / 2 + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + bh / 2 + 8 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + spacing * 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + spacing * len(stages), oy)


# ══════════════════════════════════════════════════════════
#  热脱附
# ══════════════════════════════════════════════════════════

def draw_thermal_desorption(msp, origin, t_type="rotary",
                             scale=100.0, label="", params=None,
                             layer="热脱附", tracker=None):
    """热脱附系统工艺图。

    参数:
        t_type: "rotary"回转窑 / "indirect"间接加热 / "microwave"微波
        params: {"temp":"350-550℃","residence":"15-30min",
                  "capacity":"5t/h","energy":"天然气","off_gas":"→催化氧化",...}
    """
    s = scale; ox, oy = _r(*origin); spacing = 30 * s

    # 进料单元
    bw, bh = 16 * s, 12 * s
    msp.add_lwpolyline(
        [(ox - bw / 2, oy - bh / 2), (ox + bw / 2, oy - bh / 2),
         (ox + bw / 2, oy + bh / 2), (ox - bw / 2, oy + bh / 2)],
        close=True, dxfattribs={"layer": layer})
    t = msp.add_text("进料", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ox, oy), align=TextEntityAlignment.MIDDLE_CENTER)

    # 热脱附炉
    dx = ox + spacing
    if t_type == "rotary":
        # 回转窑：倾斜圆柱
        msp.add_lwpolyline(
            [(dx - bw / 2, oy - bh / 2 + 3 * s),
             (dx + bw / 2, oy - bh / 2),
             (dx + bw / 2, oy + bh / 2),
             (dx - bw / 2, oy + bh / 2 - 3 * s)],
            close=True, dxfattribs={"layer": layer})
        # 旋转方向标记
        msp.add_arc((dx, oy), radius=bw * 0.25,
                    start_angle=30, end_angle=150,
                    dxfattribs={"layer": "细实线"})
        # 燃烧器
        msp.add_line((dx + bw / 2 + 2 * s, oy - bh / 2 + 2 * s),
                     (dx + bw / 2 + 8 * s, oy - bh / 2 + 2 * s),
                     dxfattribs={"layer": layer})
        t = msp.add_text("燃烧器", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((dx + bw / 2 + 6 * s, oy - bh / 2 + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    elif t_type == "indirect":
        # 间接加热：双层矩形
        msp.add_lwpolyline(
            [(dx - bw / 2, oy - bh / 2), (dx + bw / 2, oy - bh / 2),
             (dx + bw / 2, oy + bh / 2), (dx - bw / 2, oy + bh / 2)],
            close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline(
            [(dx - bw / 2 + 2 * s, oy - bh / 2 + 2 * s),
             (dx + bw / 2 - 2 * s, oy - bh / 2 + 2 * s),
             (dx + bw / 2 - 2 * s, oy + bh / 2 - 2 * s),
             (dx - bw / 2 + 2 * s, oy + bh / 2 - 2 * s)],
            close=True, dxfattribs={"layer": "细实线"})
        # 加热夹套标注
        for j in range(3):
            hy = oy - bh / 2 + bh * (j + 0.5) / 3
            msp.add_line((dx - bw / 2, hy), (dx - bw / 2 - 3 * s, hy),
                         dxfattribs={"layer": layer})
            _tri(msp, (dx - bw / 2, hy), (1, 0), s, layer)
    elif t_type == "microwave":
        # 微波：矩形+微波符号
        msp.add_lwpolyline(
            [(dx - bw / 2, oy - bh / 2), (dx + bw / 2, oy - bh / 2),
             (dx + bw / 2, oy + bh / 2), (dx - bw / 2, oy + bh / 2)],
            close=True, dxfattribs={"layer": layer})
        for j in range(3):
            mx = dx - 4 * s + j * 4 * s
            msp.add_arc((mx, oy), radius=3 * s,
                        start_angle=0, end_angle=180,
                        dxfattribs={"layer": "细实线"})

    t = msp.add_text("热脱附炉", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((dx, oy + bh / 2 + 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 连接进料→脱附炉
    msp.add_line((ox + bw / 2, oy), (dx - bw / 2, oy),
                 dxfattribs={"layer": layer})
    _tri(msp, (dx - bw / 2, oy), (1, 0), s, layer)

    # 尾气处理
    ex_x = dx + spacing
    msp.add_lwpolyline(
        [(ex_x - bw / 2, oy - bh / 2), (ex_x + bw / 2, oy - bh / 2),
         (ex_x + bw / 2, oy + bh / 2), (ex_x - bw / 2, oy + bh / 2)],
        close=True, dxfattribs={"layer": layer})
    t = msp.add_text("尾气处理", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ex_x, oy + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    t2 = msp.add_text("催化氧化", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t2.set_placement((ex_x, oy - 2 * s),
                     align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_line((dx + bw / 2, oy), (ex_x - bw / 2, oy),
                 dxfattribs={"layer": layer})
    _tri(msp, (ex_x - bw / 2, oy), (1, 0), s, layer)

    # 处理后土壤出料
    msp.add_line((dx, oy - bh / 2), (dx, oy - bh / 2 - 5 * s),
                 dxfattribs={"layer": layer})
    t = msp.add_text("洁净土", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((dx + 5 * s, oy - bh / 2 - 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + spacing, oy + bh / 2 + 10 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + bh / 2 + 10 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + spacing, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ex_x + bw / 2, oy)


# ══════════════════════════════════════════════════════════
#  土壤气相抽提 (SVE)
# ══════════════════════════════════════════════════════════

def draw_sve_system(msp, origin, n_wells=4, well_spacing=6.0,
                     scale=100.0, label="", params=None,
                     layer="SVE", tracker=None):
    """土壤气相抽提(SVE)系统。

    params: {"vacuum":"-0.05MPa","flow":"500m³/h",
              "radius":"3m","contaminant":"VOCs","treatment":"GAC",...}
    """
    s = scale; ox, oy = _r(*origin)
    sp = well_spacing * s

    # 抽提井
    for i in range(n_wells):
        wx = ox + sp * i
        # 井（矩形）
        msp.add_lwpolyline(
            [(wx - 1.5 * s, oy), (wx + 1.5 * s, oy),
             (wx + 1.5 * s, oy + 8 * s), (wx - 1.5 * s, oy + 8 * s)],
            close=True, dxfattribs={"layer": layer})
        # 筛管段（虚线）
        msp.add_line((wx - 1.5 * s, oy + 2 * s),
                     (wx + 1.5 * s, oy + 2 * s),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
        msp.add_line((wx - 1.5 * s, oy + 6 * s),
                     (wx + 1.5 * s, oy + 6 * s),
                     dxfattribs={"layer": layer, "linetype": "DASHED"})
        # 影响半径
        msp.add_arc((wx, oy + 4 * s), radius=sp * 0.45,
                    start_angle=0, end_angle=180,
                    dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        # 编号
        t = msp.add_text(f"V{i+1}", dxfattribs={
            "layer": "文字", "height": 1.8 * s, "style": "ENG"})
        t.set_placement((wx, oy - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
        # 向上气流箭头
        msp.add_line((wx, oy + 8 * s), (wx, oy + 12 * s),
                     dxfattribs={"layer": layer})
        _tri(msp, (wx, oy + 12 * s), (0, 1), s, layer)

    # 集气管（水平）
    header_y = oy + 12 * s
    total_w = sp * (n_wells - 1)
    msp.add_line((ox, header_y), (ox + total_w, header_y),
                 dxfattribs={"layer": "管道-加药", "lineweight": 50})

    # 真空泵
    vp_x = ox + total_w + 8 * s
    msp.add_lwpolyline(
        [(vp_x - 4 * s, header_y - 3 * s),
         (vp_x + 4 * s, header_y - 3 * s),
         (vp_x + 4 * s, header_y + 3 * s),
         (vp_x - 4 * s, header_y + 3 * s)],
        close=True, dxfattribs={"layer": "设备"})
    t = msp.add_text("真空泵", dxfattribs={
        "layer": "文字-标题", "height": 2 * s, "style": "HZ"})
    t.set_placement((vp_x, header_y),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_line((ox + total_w, header_y), (vp_x - 4 * s, header_y),
                 dxfattribs={"layer": "管道-加药", "lineweight": 50})
    _tri(msp, (vp_x - 4 * s, header_y), (1, 0), s, "管道-加药")

    # 尾气处理
    treat_x = vp_x + 10 * s
    msp.add_lwpolyline(
        [(treat_x - 5 * s, header_y - 4 * s),
         (treat_x + 5 * s, header_y - 4 * s),
         (treat_x + 5 * s, header_y + 4 * s),
         (treat_x - 5 * s, header_y + 4 * s)],
        close=True, dxfattribs={"layer": "设备"})
    t = msp.add_text("GAC", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "ENG"})
    t.set_placement((treat_x, header_y),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_line((vp_x + 4 * s, header_y), (treat_x - 5 * s, header_y),
                 dxfattribs={"layer": "管道-加药"})
    _tri(msp, (treat_x - 5 * s, header_y), (1, 0), s, "管道-加药")

    # 排气
    msp.add_line((treat_x + 5 * s, header_y),
                 (treat_x + 10 * s, header_y),
                 dxfattribs={"layer": "管道-加药"})
    _tri(msp, (treat_x + 10 * s, header_y), (1, 0), s, "管道-加药")
    t = msp.add_text("排放", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((treat_x + 13 * s, header_y + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + total_w / 2, header_y + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = header_y + 8 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + total_w / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (treat_x + 13 * s, header_y)


# ══════════════════════════════════════════════════════════
#  垂直防渗墙
# ══════════════════════════════════════════════════════════

def draw_cutoff_wall(msp, origin, length=50.0, depth=15.0,
                      wall_type="smspw",
                      scale=100.0, label="", params=None,
                      layer="防渗墙", tracker=None):
    """垂直防渗墙剖面图。

    参数:
        wall_type: "smspw"SMW工法桩 / "secant"素混凝土咬合桩 /
                   "slurry"地下连续墙 / "sheet_pile"钢板桩
        params: {"thickness":"800mm","depth":"15m","k":"<1E-7cm/s",...}
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; D = depth * s

    # 地面线
    msp.add_line((ox - 5 * s, oy), (ox + L + 5 * s, oy),
                 dxfattribs={"layer": layer, "lineweight": 35})

    # 防渗墙
    wall_w = 3 * s
    msp.add_lwpolyline(
        [(ox, oy), (ox, oy - D), (ox + L, oy - D), (ox + L, oy)],
        close=False, dxfattribs={"layer": layer, "lineweight": 50})

    if wall_type == "smspw":
        # SMW：型钢+搅拌桩（间隔竖线）
        n_piles = int(L / (3 * s))
        for i in range(n_piles + 1):
            px = ox + (L / n_piles) * i if n_piles > 0 else ox
            msp.add_line((px, oy), (px, oy - D),
                         dxfattribs={"layer": layer})
            # 型钢（每隔一个桩）
            if i % 2 == 0:
                msp.add_line((px - 0.5 * s, oy), (px - 0.5 * s, oy - D),
                             dxfattribs={"layer": "细实线"})
                msp.add_line((px + 0.5 * s, oy), (px + 0.5 * s, oy - D),
                             dxfattribs={"layer": "细实线"})

    elif wall_type == "secant":
        # 咬合桩：交错圆
        n_piles = int(L / (4 * s))
        for i in range(n_piles + 1):
            px = ox + (L / n_piles) * i if n_piles > 0 else ox
            msp.add_circle((px, oy - D / 2), 2.5 * s,
                           dxfattribs={"layer": "细实线"})

    elif wall_type == "slurry":
        # 连续墙：双线+导墙
        msp.add_line((ox + wall_w, oy), (ox + wall_w, oy - D),
                     dxfattribs={"layer": layer})
        # 导墙
        msp.add_lwpolyline(
            [(ox - 2 * s, oy + 2 * s), (ox + wall_w + 2 * s, oy + 2 * s),
             (ox + wall_w + 2 * s, oy), (ox - 2 * s, oy)],
            close=True, dxfattribs={"layer": layer})

    elif wall_type == "sheet_pile":
        # 钢板桩：Z形截面
        n_piles = int(L / (3 * s))
        for i in range(n_piles + 1):
            px = ox + (L / n_piles) * i if n_piles > 0 else ox
            msp.add_lwpolyline(
                [(px, oy), (px, oy - D * 0.3),
                 (px + 1 * s, oy - D * 0.4),
                 (px + 1 * s, oy - D * 0.7),
                 (px, oy - D)],
                close=False, dxfattribs={"layer": layer})

    # 不透水层（底部）
    msp.add_line((ox - 5 * s, oy - D), (ox + L + 5 * s, oy - D),
                 dxfattribs={"layer": layer, "lineweight": 50})
    # 阴影线
    for i in range(0, int(L / (4 * s)) + 1):
        hx = ox + 4 * s * i
        msp.add_line((hx, oy - D), (hx + 2 * s, oy - D - 2 * s),
                     dxfattribs={"layer": "剖面线"})

    t = msp.add_text("不透水层", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + L / 2, oy - D - 5 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 深度标注
    t = msp.add_text(f"H={depth:.1f}m", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "ENG"})
    t.set_placement((ox + L + 5 * s, oy - D / 2),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + 6 * s + 3 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + L / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + L, oy)
