"""环境应急与风险制图 v1.0。

引用标准（均为现行最新版）：
  HJ 169-2018       建设项目环境风险评价技术导则（代替HJ/T 169-2004）
  GB 18218-2018     危险化学品重大危险源辨识（代替GB 18218-2009）
  AQ/T 9007-2019    生产安全事故应急演练基本规范（代替AQ/T 9007-2011）
  GB/T 38315-2019   社会单位灭火和应急疏散预案编制及实施导则
  HJ 589-2021       突发环境事件应急监测技术规范

环境风险源分布图、事故风险扩散范围图、应急疏散路线图、
应急设施平面布置图、应急物资储备分布、环境敏感保护目标风险图。

纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri  # v1.5: 统一工具函数


# ══════════════════════════════════════════════════════════
#  风险源分布与扩散
# ══════════════════════════════════════════════════════════

def draw_risk_source_map(msp, origin, sources, scale=100.0,
                          label="", layer="风险源", tracker=None):
    """环境风险源分布图。

    sources: [{"type":"tank","label":"储罐区","x":50,"y":80,
               "substance":"苯","quantity":"500t","level":"重大"},
              {"type":"warehouse","label":"危废库","x":120,"y":60,
               "substance":"废酸","quantity":"200t","level":"较大"}, ...]
    """
    s = scale; ox, oy = _r(*origin)

    level_colors = {"重大": 1, "较大": 3, "一般": 5}

    for src in sources:
        sx = ox + src.get("x", 0) * s
        sy = oy + src.get("y", 0) * s
        stype = src.get("type", "")
        slabel = src.get("label", "")
        substance = src.get("substance", "")
        quantity = src.get("quantity", "")
        level = src.get("level", "一般")

        r = 5 * s
        if stype == "tank":
            # 储罐：圆形
            msp.add_circle((sx, sy), r, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((sx - r, sy), (sx + r, sy),
                         dxfattribs={"layer": layer})
        elif stype == "warehouse":
            # 仓库：矩形
            msp.add_lwpolyline(
                [(sx - r, sy - r), (sx + r, sy - r),
                 (sx + r, sy + r), (sx - r, sy + r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
        elif stype == "pipeline":
            # 管线：线段
            msp.add_line((sx - r, sy), (sx + r, sy),
                         dxfattribs={"layer": layer, "lineweight": 50})
        elif stype == "stack":
            # 排气筒：三角形
            msp.add_lwpolyline(
                [(sx - r, sy + r), (sx + r, sy + r), (sx, sy - r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
        else:
            msp.add_circle((sx, sy), r, dxfattribs={"layer": layer})

        # 风险等级标注（颜色环）
        level_r = r + 3 * s
        msp.add_circle((sx, sy), level_r,
                       dxfattribs={"layer": layer, "linetype": "DASHED"})

        # 标签
        t = msp.add_text(slabel, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((sx, sy + r + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        # 物质和量
        if substance or quantity:
            t = msp.add_text(f"{substance} {quantity}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((sx, sy - r - 4 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

        # 风险等级
        t = msp.add_text(f"[{level}]", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((sx + level_r + 3 * s, sy),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + 80 * s, oy + 120 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + 150 * s, oy + 100 * s)


def draw_risk_dispersion(msp, center, substance_type="gas",
                          wind_dir="E", wind_speed=3.0,
                          zones=None,
                          scale=100.0, label="", params=None,
                          layer="风险扩散", tracker=None):
    """事故风险扩散范围图。

    参数:
        substance_type: "gas"气体 / "liquid"液体 / "dust"粉尘
        wind_dir: 风向 E/W/N/S/NE/SE/SW/NW
        wind_speed: 风速 m/s
        zones: [{"radius":200,"level":"致死区","time":"5min"},
                {"radius":500,"level":"重伤区","time":"15min"},
                {"radius":1000,"level":"轻伤区","time":"30min"},
                {"radius":2000,"level":"警戒区","time":"60min"}]
        params: {"substance":"氯气","leak_rate":"5kg/s","stability":"D",
                  "population":"下风向2000m",...}
    """
    s = scale; cx, cy = _r(*center)

    if zones is None:
        zones = [
            {"radius": 200, "level": "致死区", "time": "5min"},
            {"radius": 500, "level": "重伤区", "time": "15min"},
            {"radius": 1000, "level": "轻伤区", "time": "30min"},
            {"radius": 2000, "level": "警戒区", "time": "60min"},
        ]

    wind_angles = {
        "E": 0, "W": 180, "N": 90, "S": 270,
        "NE": 45, "SE": 315, "SW": 225, "NW": 135,
    }
    wind_angle = wind_angles.get(wind_dir, 0)
    rad = math.radians(wind_angle)

    # 泄漏源
    msp.add_circle((cx, cy), 4 * s, dxfattribs={"layer": layer, "lineweight": 50})
    msp.add_line((cx - 4 * s, cy), (cx + 4 * s, cy),
                 dxfattribs={"layer": layer})
    msp.add_line((cx, cy - 4 * s), (cx, cy + 4 * s),
                 dxfattribs={"layer": layer})
    t = msp.add_text("泄漏源", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((cx, cy - 7 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 风向箭头
    arrow_len = 20 * s
    ax = cx + arrow_len * math.cos(rad)
    ay = cy + arrow_len * math.sin(rad)
    msp.add_line((cx, cy), (ax, ay),
                 dxfattribs={"layer": layer, "lineweight": 50})
    _tri(msp, (ax, ay), (math.cos(rad), math.sin(rad)), s, layer)
    t = msp.add_text(f"风 {wind_dir} {wind_speed}m/s", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ax + 3 * s, ay + 3 * s),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    # 扩散区域（扇形，沿风向延伸）
    for z in zones:
        r = z.get("radius", 500) * s
        level = z.get("level", "")
        time = z.get("time", "")

        # 扇形扩散（风向±30°）
        msp.add_arc((cx, cy), radius=r,
                    start_angle=wind_angle - 30,
                    end_angle=wind_angle + 30,
                    dxfattribs={"layer": "细实线", "linetype": "DASHED"})

        # 扇形边界线
        a1 = math.radians(wind_angle - 30)
        a2 = math.radians(wind_angle + 30)
        msp.add_line((cx, cy),
                     (cx + r * math.cos(a1), cy + r * math.sin(a1)),
                     dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        msp.add_line((cx, cy),
                     (cx + r * math.cos(a2), cy + r * math.sin(a2)),
                     dxfattribs={"layer": "细实线", "linetype": "DASHED"})

        # 标注
        mid_a = math.radians(wind_angle)
        lbl_x = cx + r * 0.8 * math.cos(mid_a)
        lbl_y = cy + r * 0.8 * math.sin(mid_a)
        t = msp.add_text(f"{level}\n{time}", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((lbl_x, lbl_y),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        max_r = max(z.get("radius", 500) for z in zones) * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy + max_r * 0.7 + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        max_r = max(z.get("radius", 500) for z in zones) * s
        py = cy - max_r * 0.7 - 8 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    max_r = max(z.get("radius", 500) for z in zones) * s
    return (cx + max_r, cy + max_r)


# ══════════════════════════════════════════════════════════
#  应急疏散路线
# ══════════════════════════════════════════════════════════

def draw_evacuation_route(msp, origin, routes, scale=100.0,
                           label="", layer="疏散", tracker=None):
    """应急疏散路线图。

    routes: [{"points":[(10,10),(50,10),(50,80),(100,80)],
              "label":"主疏散路线A","dest":"应急集合点1"},
             {"points":[(10,10),(30,50),(80,50)],
              "label":"备用路线B","dest":"应急集合点2"}]
    """
    s = scale; ox, oy = _r(*origin)

    route_styles = [
        {"linetype": "CONTINUOUS", "lineweight": 50},
        {"linetype": "DASHED", "lineweight": 35},
    ]

    for ri, route in enumerate(routes):
        pts = route.get("points", [])
        rlabel = route.get("label", f"路线{ri+1}")
        dest = route.get("dest", "")
        style = route_styles[ri % len(route_styles)]

        if len(pts) < 2:
            continue

        # 绘制路径
        for i in range(len(pts) - 1):
            p1 = (ox + pts[i][0] * s, oy + pts[i][1] * s)
            p2 = (ox + pts[i + 1][0] * s, oy + pts[i + 1][1] * s)
            msp.add_line(p1, p2,
                         dxfattribs={"layer": layer, **style})

            # 路径方向箭头
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            d_len = math.sqrt(dx * dx + dy * dy)
            if d_len > 0:
                ndx, ndy = dx / d_len, dy / d_len
                _tri(msp, (mid_x, mid_y), (ndx, ndy), s, layer)

        # 起点（泄漏源/危险区）
        sp = (ox + pts[0][0] * s, oy + pts[0][1] * s)
        msp.add_circle(sp, 4 * s, dxfattribs={"layer": layer, "lineweight": 50})
        msp.add_line((sp[0] - 4 * s, sp[1]), (sp[0] + 4 * s, sp[1]),
                     dxfattribs={"layer": layer})
        msp.add_line((sp[0], sp[1] - 4 * s), (sp[0], sp[1] + 4 * s),
                     dxfattribs={"layer": layer})

        # 终点（集合点）
        ep = (ox + pts[-1][0] * s, oy + pts[-1][1] * s)
        # 集合点符号：绿色圆+人形
        msp.add_circle(ep, 5 * s, dxfattribs={"layer": layer, "lineweight": 50})
        msp.add_circle((ep[0], ep[1] + 1.5 * s), 1.5 * s,
                       dxfattribs={"layer": layer})
        msp.add_line((ep[0], ep[1] + 0.5 * s), (ep[0], ep[1] - 2 * s),
                     dxfattribs={"layer": layer})
        msp.add_line((ep[0] - 2 * s, ep[1] - 1 * s),
                     (ep[0] + 2 * s, ep[1] - 1 * s),
                     dxfattribs={"layer": layer})

        # 标签
        t = msp.add_text(rlabel, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        mid_idx = len(pts) // 2
        mid_pt = (ox + pts[mid_idx][0] * s, oy + pts[mid_idx][1] * s)
        t.set_placement((mid_pt[0], mid_pt[1] + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        if dest:
            t = msp.add_text(dest, dxfattribs={
                "layer": "文字-标题", "height": 2 * s, "style": "HZ"})
            t.set_placement((ep[0], ep[1] + 8 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + 60 * s, oy + 110 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + 120 * s, oy + 100 * s)


# ══════════════════════════════════════════════════════════
#  应急设施布置
# ══════════════════════════════════════════════════════════

def draw_emergency_facilities(msp, origin, facilities, scale=100.0,
                               label="", layer="应急设施", tracker=None):
    """应急设施平面布置图。

    facilities: [{"type":"command","label":"应急指挥中心","x":50,"y":50},
                 {"type":"assembly","label":"集合点A","x":100,"y":80},
                 {"type":"medical","label":"医疗救护站","x":30,"y":90},
                 {"type":"supplies","label":"物资储备库","x":80,"y":20},
                 {"type":"fire","label":"消防站","x":60,"y":60},
                 {"type":"shelter","label":"临时避难所","x":110,"y":30}]
    """
    s = scale; ox, oy = _r(*origin)

    for fac in facilities:
        fx = ox + fac.get("x", 0) * s
        fy = oy + fac.get("y", 0) * s
        ftype = fac.get("type", "")
        flabel = fac.get("label", "")
        r = 5 * s

        if ftype == "command":
            # 指挥中心：方形+旗标
            msp.add_lwpolyline(
                [(fx - r, fy - r), (fx + r, fy - r),
                 (fx + r, fy + r), (fx - r, fy + r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx, fy + r), (fx, fy + r + 4 * s),
                         dxfattribs={"layer": layer})
            msp.add_lwpolyline(
                [(fx, fy + r + 4 * s), (fx + 4 * s, fy + r + 3 * s),
                 (fx, fy + r + 2 * s)],
                close=True, dxfattribs={"layer": layer})

        elif ftype == "assembly":
            # 集合点：圆+人形
            msp.add_circle((fx, fy), r, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_circle((fx, fy + 1.5 * s), 1.5 * s,
                           dxfattribs={"layer": layer})
            msp.add_line((fx, fy + 0.5 * s), (fx, fy - 2 * s),
                         dxfattribs={"layer": layer})
            msp.add_line((fx - 2 * s, fy - 1 * s),
                         (fx + 2 * s, fy - 1 * s),
                         dxfattribs={"layer": layer})

        elif ftype == "medical":
            # 医疗站：方形+十字
            msp.add_lwpolyline(
                [(fx - r, fy - r), (fx + r, fy - r),
                 (fx + r, fy + r), (fx - r, fy + r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx - 3 * s, fy), (fx + 3 * s, fy),
                         dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx, fy - 3 * s), (fx, fy + 3 * s),
                         dxfattribs={"layer": layer, "lineweight": 50})

        elif ftype == "supplies":
            # 物资库：方形+X
            msp.add_lwpolyline(
                [(fx - r, fy - r), (fx + r, fy - r),
                 (fx + r, fy + r), (fx - r, fy + r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx - r, fy - r), (fx + r, fy + r),
                         dxfattribs={"layer": layer})
            msp.add_line((fx - r, fy + r), (fx + r, fy - r),
                         dxfattribs={"layer": layer})

        elif ftype == "fire":
            # 消防站：方形+F
            msp.add_lwpolyline(
                [(fx - r, fy - r), (fx + r, fy - r),
                 (fx + r, fy + r), (fx - r, fy + r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx - 2 * s, fy - 3 * s), (fx - 2 * s, fy + 3 * s),
                         dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx - 2 * s, fy + 3 * s), (fx + 2 * s, fy + 3 * s),
                         dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx - 2 * s, fy), (fx + 1 * s, fy),
                         dxfattribs={"layer": layer, "lineweight": 50})

        elif ftype == "shelter":
            # 避难所：三角形（帐篷）
            msp.add_lwpolyline(
                [(fx - r, fy - r), (fx + r, fy - r), (fx, fy + r)],
                close=True, dxfattribs={"layer": layer, "lineweight": 50})
            msp.add_line((fx, fy - r), (fx, fy + r * 0.5),
                         dxfattribs={"layer": layer})
        else:
            msp.add_circle((fx, fy), r, dxfattribs={"layer": layer})

        # 标签
        t = msp.add_text(flabel, dxfattribs={
            "layer": "文字-标题", "height": 2.2 * s, "style": "HZ"})
        t.set_placement((fx, fy - r - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + 60 * s, oy + 110 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + 120 * s, oy + 100 * s)


# ══════════════════════════════════════════════════════════
#  应急响应流程
# ══════════════════════════════════════════════════════════

def draw_emergency_response_flow(msp, origin, scale=100.0,
                                  label="", params=None,
                                  layer="应急流程", tracker=None):
    """环境应急响应流程图。

    流程: 发现→报告→评估→启动预案→应急处置→监测→终止→善后
    """
    s = scale; ox, oy = _r(*origin)
    spacing = 26 * s

    steps = [
        ("发现事故", "1"),
        ("立即报告", "2"),
        ("风险评估", "3"),
        ("启动预案", "4"),
        ("应急处置", "5"),
        ("环境监测", "6"),
        ("终止响应", "7"),
        ("善后恢复", "8"),
    ]

    bw, bh = 18 * s, 10 * s

    for i, (name, num) in enumerate(steps):
        cx = ox + spacing * i

        # 步骤框
        msp.add_lwpolyline(
            [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
             (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
            close=True, dxfattribs={"layer": layer, "lineweight": 50})

        # 编号圆
        msp.add_circle((cx, oy + bh / 2 + 2 * s), 2 * s,
                       dxfattribs={"layer": layer})
        t = msp.add_text(num, dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "ENG"})
        t.set_placement((cx, oy + bh / 2 + 2 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        # 步骤名
        t = msp.add_text(name, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((cx, oy),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        # 连接箭头
        if i < len(steps) - 1:
            nx = ox + spacing * (i + 1)
            msp.add_line((cx + bw / 2, oy), (nx - bw / 2, oy),
                         dxfattribs={"layer": layer})
            _tri(msp, (nx - bw / 2, oy), (1, 0), s, layer)

    # 分支：第4步启动预案后→通知应急队伍
    branch_x = ox + spacing * 3
    branch_y = oy - bh / 2 - 8 * s
    msp.add_line((branch_x, oy - bh / 2), (branch_x, branch_y),
                 dxfattribs={"layer": layer})
    msp.add_line((branch_x, branch_y), (branch_x + 2 * spacing, branch_y),
                 dxfattribs={"layer": layer})
    msp.add_line((branch_x + 2 * spacing, branch_y),
                 (branch_x + 2 * spacing, oy - bh / 2),
                 dxfattribs={"layer": layer})
    _tri(msp, (branch_x + 2 * spacing, oy - bh / 2), (0, 1), s, layer)

    t = msp.add_text("通知应急队伍/环保部门", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((branch_x + spacing, branch_y - 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + spacing * 3.5, oy + bh / 2 + 10 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + spacing * len(steps), oy)
