"""暖通空调制图 v1.0（GB/T 50155—2015、GB 50736—2012、GB 50243—2016）。

风管平面/剖面、风口布置、空调机组、风机盘管、冷却塔、冷水机组、锅炉。
纯 ezdxf，零新依赖。所有参数由 Agent 搜索后显式传入。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

# ══════════════════════════════════════════════════════════
#  风管平面图
# ══════════════════════════════════════════════════════════

def draw_duct_plan(msp, origin, length=8.0, width=0.6, ducts=None,
                    scale=100.0, label="", layer="风管", tracker=None):
    """风管平面布置图。

    参数:
        length: 主管长 m
        width: 主管宽 m
        ducts: 支管列表 [{"x":2,"l":3,"w":0.4,"dir":"up","label":"送风"}, ...]
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; W = width * s

    # 主管（双线）
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + W), (ox, oy + W)],
                       close=True, dxfattribs={"layer": layer})

    # 支管
    if ducts:
        for d in ducts:
            dx = ox + d.get("x", 0) * s
            dl = d.get("l", 2.0) * s
            dw = d.get("w", 0.3) * s
            direction = d.get("dir", "up")
            dlbl = d.get("label", "")

            if direction == "up":
                dy = oy + W
                msp.add_lwpolyline([(dx, dy), (dx + dl, dy), (dx + dl, dy + dw), (dx, dy + dw)],
                                   close=True, dxfattribs={"layer": layer})
            elif direction == "down":
                dy = oy
                msp.add_lwpolyline([(dx, dy - dw), (dx + dl, dy - dw), (dx + dl, dy), (dx, dy)],
                                   close=True, dxfattribs={"layer": layer})

            if dlbl:
                t = msp.add_text(dlbl, dxfattribs={
                    "layer": "文字", "height": 2.0 * s, "style": "HZ"})
                t.set_placement((dx + dl / 2, (dy + dw / 2) if direction == "up" else dy - dw / 2),
                                align=TextEntityAlignment.MIDDLE_CENTER)

    # 中心线
    msp.add_line((ox, oy + W / 2), (ox + L, oy + W / 2),
                 dxfattribs={"layer": "点画线", "linetype": "CENTER"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  风管剖面
# ══════════════════════════════════════════════════════════

def draw_duct_section(msp, origin, diameter=500.0, insulation=30.0,
                       scale=100.0, label="", layer="风管", tracker=None):
    """圆形风管剖面（截面）。

    参数:
        diameter: 风管直径 mm
        insulation: 保温层厚 mm
    """
    s = scale * 1.5; ox, oy = _r(*origin)
    D = diameter * s; ins = insulation * s
    r = D / 2
    cx, cy = ox + r + ins + 3 * s, oy + r + ins + 3 * s

    # 保温层外圈（细实线）
    msp.add_circle((cx, cy), r + ins, dxfattribs={"layer": "细实线"})
    # 风管内圈（粗实线）
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
    # 中心线
    cs = r + ins + 3 * s
    msp.add_line((cx - cs, cy), (cx + cs, cy),
                 dxfattribs={"layer": "点画线", "linetype": "CENTER"})
    msp.add_line((cx, cy - cs), (cx, cy + cs),
                 dxfattribs={"layer": "点画线", "linetype": "CENTER"})
    # 标注
    t = msp.add_text(f"D={diameter:.0f} 保温{insulation:.0f}mm", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((cx, cy - r - ins - 4 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx, cy + r + ins + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  风口/散流器
# ══════════════════════════════════════════════════════════

def draw_air_outlet(msp, origin, width=400.0, height=200.0, outlet_type="grille",
                     scale=100.0, label="", layer="细实线", tracker=None):
    """风口（百叶/散流器/喷口）。

    参数:
        width/height: 风口尺寸 mm
        outlet_type: grille(百叶)/diffuser(散流器)/nozzle(喷口)
    """
    s = scale * 2; ox, oy = _r(*origin)
    w = width * s; h = height * s

    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": layer})

    if outlet_type == "grille":
        # 百叶横线
        n_blades = 6
        for i in range(1, n_blades):
            by = oy + h * i / n_blades
            msp.add_line((ox + w * 0.1, by), (ox + w * 0.9, by),
                         dxfattribs={"layer": "细实线"})
    elif outlet_type == "diffuser":
        # 散流器：同心方格
        n_grid = 4
        for i in range(1, n_grid + 1):
            margin_x = w * i / (n_grid + 1) * 0.5
            margin_y = h * i / (n_grid + 1) * 0.5
            msp.add_lwpolyline([
                (ox + margin_x, oy + margin_y),
                (ox + w - margin_x, oy + margin_y),
                (ox + w - margin_x, oy + h - margin_y),
                (ox + margin_x, oy + h - margin_y)],
                close=True, dxfattribs={"layer": "细实线"})
    elif outlet_type == "nozzle":
        # 喷口：圆形 + 扩散线
        cx, cy = ox + w / 2, oy + h / 2
        r = min(w, h) / 2
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        # 扩散扇形
        for ang in [-30, -15, 0, 15, 30]:
            rad = math.radians(ang)
            msp.add_line((cx, cy), (cx + w * 0.7 * math.cos(rad), cy + w * 0.7 * math.sin(rad)),
                         dxfattribs={"layer": "细实线"})

    t = msp.add_text(f"{width:.0f}×{height:.0f}", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + w / 2, oy - 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + h + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  组合式空调机组 AHU
# ══════════════════════════════════════════════════════════

def draw_ahu(msp, origin, length=4.0, width=1.5, height=2.0,
              sections=None, scale=100.0, label="", layer="设备", tracker=None):
    """组合式空调机组。

    参数:
        length/width/height: 机组外形 m
        sections: 功能段 ["混合","初效","表冷","加热","加湿","风机","中效","送风"]
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; W = width * s; H = height * s

    # 机组轮廓
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + H), (ox, oy + H)],
                       close=True, dxfattribs={"layer": layer})

    # 功能段分隔
    secs = sections or ["混合", "过滤", "表冷", "加热", "风机"]
    n = len(secs)
    for i in range(1, n):
        sx = ox + L * i / n
        msp.add_line((sx, oy), (sx, oy + H), dxfattribs={"layer": "细实线"})

    # 段名称标注
    for i, name in enumerate(secs):
        sx = ox + L * (i + 0.5) / n
        t = msp.add_text(name, dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((sx, oy + H / 2), align=TextEntityAlignment.MIDDLE_CENTER)

    # 进出风口（两侧箭头）
    _tri(msp, (ox - 3 * s, oy + H / 2), (-1, 0), s, "粗实线")
    _tri(msp, (ox + L + 3 * s, oy + H / 2), (1, 0), s, "粗实线")

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + H + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  风机盘管
# ══════════════════════════════════════════════════════════

def draw_fan_coil(msp, origin, length=1.0, width=0.6, height=0.3,
                   fc_type="卧式暗装", scale=100.0, label="", layer="设备", tracker=None):
    """风机盘管（卧式/立式/卡式）。

    参数:
        length/width/height: 外形尺寸 m
        fc_type: 卧式暗装/立式明装/卡式
    """
    s = scale * 3; ox, oy = _r(*origin)
    L = length * s; W = width * s; H = height * s

    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + W), (ox, oy + W)],
                       close=True, dxfattribs={"layer": layer})

    # 内部风机示意（圆）
    cx, cy = ox + L * 0.3, oy + W / 2
    r = W * 0.3
    msp.add_circle((cx, cy), r, dxfattribs={"layer": "细实线"})
    # 风叶十字
    msp.add_line((cx - r, cy), (cx + r, cy), dxfattribs={"layer": "细实线"})
    msp.add_line((cx, cy - r), (cx, cy + r), dxfattribs={"layer": "细实线"})

    # 盘管区（右侧）
    hx = ox + L * 0.6
    msp.add_lwpolyline([(hx, oy + W * 0.2), (ox + L - 1 * s, oy + W * 0.2),
                          (ox + L - 1 * s, oy + W * 0.8), (hx, oy + W * 0.8)],
                       close=False, dxfattribs={"layer": "细实线"})
    for i in range(5):
        cy_i = oy + W * (0.2 + 0.6 * i / 4)
        msp.add_line((hx, cy_i), (ox + L - 1 * s, cy_i),
                     dxfattribs={"layer": "细实线"})

    t = msp.add_text(fc_type, dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + L / 2, oy - 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + W + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  冷却塔
# ══════════════════════════════════════════════════════════

def draw_cooling_tower(msp, origin, diameter=3.0, height=4.0, n_cells=2,
                        scale=100.0, label="", layer="设备", tracker=None):
    """冷却塔（圆形逆流/横流）。

    参数:
        diameter: 塔直径 m
        height: 塔高 m
        n_cells: 隔间数
    """
    s = scale; ox, oy = _r(*origin)
    D = diameter * s; H = height * s
    r = D / 2
    cx = ox + r + 3 * s

    # 立面
    msp.add_lwpolyline([(ox, oy), (ox + D, oy), (ox + D, oy + H), (ox, oy + H)],
                       close=True, dxfattribs={"layer": layer})
    # 隔板
    if n_cells > 1:
        for i in range(1, n_cells):
            sx = ox + D * i / n_cells
            msp.add_line((sx, oy), (sx, oy + H), dxfattribs={"layer": "细实线"})
    # 百叶进风口（下部斜线）
    for i in range(6):
        lx = ox + D * 0.1
        ly = oy + H * 0.05 * (i + 1)
        msp.add_line((lx, ly), (ox + D * 0.9, ly + H * 0.02),
                     dxfattribs={"layer": "细实线"})
    # 收水器（顶部弧线）
    msp.add_arc((cx, oy + H), r, 0, 180, dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, oy + H + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  冷水机组
# ══════════════════════════════════════════════════════════

def draw_chiller(msp, origin, length=3.5, width=1.2, height=1.8,
                  chiller_type="螺杆式", capacity=500, scale=100.0, label="",
                  layer="设备", tracker=None):
    """冷水机组。

    参数:
        length/width/height: 外形 m
        chiller_type: 螺杆式/离心式/涡旋式
        capacity: 制冷量 kW
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; W = width * s; H = height * s

    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + H), (ox, oy + H)],
                       close=True, dxfattribs={"layer": layer})

    # 压缩机区（左1/3）
    msp.add_line((ox + L * 0.33, oy), (ox + L * 0.33, oy + H),
                 dxfattribs={"layer": "细实线"})
    t = msp.add_text("压缩机", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + L * 0.17, oy + H / 2),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 蒸发-冷凝区（中）
    msp.add_line((ox + L * 0.66, oy), (ox + L * 0.66, oy + H),
                 dxfattribs={"layer": "细实线"})
    t = msp.add_text("蒸发器", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + L * 0.5, oy + H * 0.7),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    t2 = msp.add_text("冷凝器", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t2.set_placement((ox + L * 0.5, oy + H * 0.3),
                     align=TextEntityAlignment.MIDDLE_CENTER)

    # 进出管接口
    msp.add_line((ox - 2 * s, oy + H * 0.3), (ox, oy + H * 0.3),
                 dxfattribs={"layer": "粗实线"})
    msp.add_line((ox - 2 * s, oy + H * 0.7), (ox, oy + H * 0.7),
                 dxfattribs={"layer": "粗实线"})
    msp.add_line((ox + L, oy + H * 0.3), (ox + L + 2 * s, oy + H * 0.3),
                 dxfattribs={"layer": "粗实线"})
    msp.add_line((ox + L, oy + H * 0.7), (ox + L + 2 * s, oy + H * 0.7),
                 dxfattribs={"layer": "粗实线"})

    t3 = msp.add_text(f"{chiller_type} {capacity}kW", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t3.set_placement((ox + L / 2, oy - 3 * s),
                     align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + H + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  锅炉
# ══════════════════════════════════════════════════════════

def draw_boiler(msp, origin, diameter=2.0, length=5.0, boiler_type="燃气热水",
                 capacity=2.8, scale=100.0, label="", layer="设备", tracker=None):
    """锅炉（卧式快装）。

    参数:
        diameter: 炉体直径 m
        length: 炉体长度 m
        boiler_type: 燃气热水/燃气蒸汽/电热
        capacity: 容量 MW 或 t/h
    """
    s = scale; ox, oy = _r(*origin)
    D = diameter * s; L = length * s
    r = D / 2

    # 炉体
    msp.add_lwpolyline([(ox, oy), (ox + L, oy), (ox + L, oy + D), (ox, oy + D)],
                       close=True, dxfattribs={"layer": layer})

    # 前端弧形封头
    msp.add_arc((ox, oy + r), r, 90, 270, dxfattribs={"layer": layer})
    # 后端弧形封头
    msp.add_arc((ox + L, oy + r), r, 270, 90, dxfattribs={"layer": layer})

    # 烟囱（顶部）
    stack_x = ox + L * 0.3
    stack_h = D * 0.8
    msp.add_lwpolyline([(stack_x, oy + D), (stack_x + D * 0.3, oy + D),
                          (stack_x + D * 0.2, oy + D + stack_h),
                          (stack_x + D * 0.1, oy + D + stack_h)],
                       close=True, dxfattribs={"layer": layer})

    # 燃烧器（前端）
    msp.add_lwpolyline([(ox - 1 * s, oy + r - D * 0.15),
                          (ox, oy + r - D * 0.15),
                          (ox, oy + r + D * 0.15),
                          (ox - 1 * s, oy + r + D * 0.15)],
                       close=True, dxfattribs={"layer": "细实线"})
    t = msp.add_text("燃烧器", dxfattribs={
        "layer": "文字", "height": 1.5 * s, "style": "HZ"})
    t.set_placement((ox - 0.5 * s, oy + r + D * 0.15 + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    t2 = msp.add_text(f"{boiler_type} {capacity}MW", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t2.set_placement((ox + L / 2, oy - 3 * s),
                     align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + D + stack_h + 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
