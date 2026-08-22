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


# ══════════════════════════════════════════════════════════
#  GB/T 50114-2010 暖通空调制图 · 风道阀门 / 附件 / 风口 图例符号库
#  依据标准 表3.2.3-1（风道阀门及附件）、表3.2.3-2（风口代号）、
#  表3.2.1（风道代号）实现。符号以 origin 为中心绘制，单位 mm，
#  按 scale×2 换算到图面，可直接用于 HVAC 原理图、平面图与图例说明。
# ══════════════════════════════════════════════════════════

def _hvac_label(msp, x, y, text, s, h=2.0, layer="文字"):
    """在 (x,y) 居中标注文字。"""
    t = msp.add_text(text, dxfattribs={"layer": layer, "height": h * s, "style": "HZ"})
    t.set_placement(_r(x, y), align=TextEntityAlignment.MIDDLE_CENTER)


def _hvac_executor(msp, cx, base_y, a, layer):
    """电动执行器：小方框 + 斜线（位于阀体上方）。"""
    top = base_y + a * 0.5
    msp.add_lwpolyline([(cx - a * 0.22, base_y), (cx + a * 0.22, base_y),
                        (cx + a * 0.22, top), (cx - a * 0.22, top)],
                       close=True, dxfattribs={"layer": layer})
    msp.add_line((cx - a * 0.22, top), (cx + a * 0.22, base_y),
                 dxfattribs={"layer": layer})


def draw_hvac_valve(msp, origin, valve_type="butterfly", scale=100.0,
                    layer="设备", tracker=None):
    """风道阀门（GB/T 50114 表 3.2.3-1 编号 15~21）。

    valve_type:
        butterfly          蝶阀(16)
        multileaf          对开多叶调节风阀(15，手动)
        multileaf_electric 对开多叶调节风阀(15，电动，带执行器)
        check              风管止回阀(18)
        three_way          三通调节阀(20)
        slide              插板阀(17)
        fire               防烟防火阀(70℃ 常开)(21)
        smoke              排烟阀(280℃)(21)
        electric           电动阀(阀体+执行器)
    """
    s = scale * 2
    cx, cy = _r(*origin)
    a = 60.0 * s
    duct = a * 1.8
    msp.add_line((cx - duct, cy), (cx + duct, cy), dxfattribs={"layer": "风管"})

    if valve_type == "butterfly":
        # 蝶阀：中心菱形阀板
        msp.add_lwpolyline([(cx - a * 0.55, cy), (cx, cy + a * 0.55),
                            (cx + a * 0.55, cy), (cx, cy - a * 0.55)],
                           close=True, dxfattribs={"layer": layer})
    elif valve_type in ("multileaf", "multileaf_electric"):
        # 对开多叶调节风阀：阀体矩形 + 平行叶片
        msp.add_lwpolyline([(cx - a * 0.5, cy - a * 0.6), (cx + a * 0.5, cy - a * 0.6),
                            (cx + a * 0.5, cy + a * 0.6), (cx - a * 0.5, cy + a * 0.6)],
                           close=True, dxfattribs={"layer": layer})
        for i in range(1, 4):
            x = cx - a * 0.5 + a * i / 4
            msp.add_line((x, cy - a * 0.6), (x, cy + a * 0.6), dxfattribs={"layer": layer})
        if valve_type == "multileaf_electric":
            _hvac_executor(msp, cx, cy + a * 0.6, a, layer)
    elif valve_type == "check":
        # 风管止回阀：阀体 + 单向箭头
        msp.add_lwpolyline([(cx - a * 0.5, cy - a * 0.5), (cx + a * 0.5, cy - a * 0.5),
                            (cx + a * 0.5, cy + a * 0.5), (cx - a * 0.5, cy + a * 0.5)],
                           close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline([(cx - a * 0.28, cy - a * 0.22), (cx + a * 0.28, cy),
                            (cx - a * 0.28, cy + a * 0.22), (cx - a * 0.28, cy - a * 0.22)],
                           close=True, dxfattribs={"layer": layer})
    elif valve_type == "three_way":
        # 三通调节阀：主管 + 支管 + 阀体
        msp.add_line((cx, cy - a * 1.6), (cx, cy + a * 0.5), dxfattribs={"layer": "风管"})
        msp.add_lwpolyline([(cx - a * 0.5, cy - a * 0.5), (cx + a * 0.5, cy - a * 0.5),
                            (cx + a * 0.5, cy + a * 0.5), (cx - a * 0.5, cy + a * 0.5)],
                           close=True, dxfattribs={"layer": layer})
        for i in range(1, 4):
            x = cx - a * 0.5 + a * i / 4
            msp.add_line((x, cy - a * 0.5), (x, cy + a * 0.5), dxfattribs={"layer": layer})
    elif valve_type == "slide":
        # 插板阀：阀体矩形 + 上方阀杆
        msp.add_lwpolyline([(cx - a * 0.5, cy - a * 0.5), (cx + a * 0.5, cy - a * 0.5),
                            (cx + a * 0.5, cy + a * 0.5), (cx - a * 0.5, cy + a * 0.5)],
                           close=True, dxfattribs={"layer": layer})
        msp.add_line((cx, cy + a * 0.5), (cx, cy + a * 1.4), dxfattribs={"layer": layer})
        msp.add_line((cx - a * 0.3, cy + a * 1.4), (cx + a * 0.3, cy + a * 1.4),
                     dxfattribs={"layer": layer})
    elif valve_type in ("fire", "smoke"):
        # 防烟防火阀 / 排烟阀：矩形 + 温度标注
        msp.add_lwpolyline([(cx - a * 0.55, cy - a * 0.5), (cx + a * 0.55, cy - a * 0.5),
                            (cx + a * 0.55, cy + a * 0.5), (cx - a * 0.55, cy + a * 0.5)],
                           close=True, dxfattribs={"layer": layer})
        _hvac_label(msp, cx, cy, "70℃" if valve_type == "fire" else "280℃",
                    s, h=1.6, layer="文字")
    elif valve_type == "electric":
        # 电动阀：阀体 + 执行器
        msp.add_lwpolyline([(cx - a * 0.5, cy - a * 0.5), (cx + a * 0.5, cy - a * 0.5),
                            (cx + a * 0.5, cy + a * 0.5), (cx - a * 0.5, cy + a * 0.5)],
                           close=True, dxfattribs={"layer": layer})
        _hvac_executor(msp, cx, cy + a * 0.5, a, layer)
    else:
        raise ValueError(f"未知 valve_type: {valve_type}")


def draw_hvac_outlet(msp, origin, outlet_type="grille_single", scale=100.0,
                     layer="设备", tracker=None):
    """风口（GB/T 50114 表 3.2.3-2 风口代号 / 表 3.2.3-1 编号22~27）。

    outlet_type:
        general        风口（通用）
        grille_single  单层格栅风口(AV/AH)
        grille_double  双层格栅风口(BV/BH)
        diffuser_rect  矩形散流器(C*)
        diffuser_round 圆形散流器(DF/DS/DP)
        slot           条缝形风口(E*)
        swirl          旋流风口(SD)
        louver         百叶回风口(H)
        louver_rain    防雨百叶
        nozzle         喷口(J)
    """
    s = scale * 2
    cx, cy = _r(*origin)
    a = 60.0 * s
    half = a * 0.5

    if outlet_type == "general":
        msp.add_lwpolyline([(cx - half, cy - half), (cx + half, cy - half),
                            (cx + half, cy + half), (cx - half, cy + half)],
                           close=True, dxfattribs={"layer": layer})
    elif outlet_type in ("grille_single", "grille_double", "louver"):
        msp.add_lwpolyline([(cx - half, cy - half), (cx + half, cy - half),
                            (cx + half, cy + half), (cx - half, cy + half)],
                           close=True, dxfattribs={"layer": layer})
        rows = 4 if outlet_type != "grille_double" else 7
        for i in range(1, rows):
            y = cy - half + a * i / rows
            msp.add_line((cx - half * 0.85, y), (cx + half * 0.85, y),
                         dxfattribs={"layer": layer})
        if outlet_type == "grille_double":
            for i in range(1, rows):
                x = cx - half + a * i / rows
                msp.add_line((x, cy - half * 0.85), (x, cy + half * 0.85),
                             dxfattribs={"layer": layer})
    elif outlet_type == "diffuser_rect":
        for k in range(1, 4):
            m = half * k / 4
            msp.add_lwpolyline([(cx - m, cy - m), (cx + m, cy - m),
                                (cx + m, cy + m), (cx - m, cy + m)],
                               close=True, dxfattribs={"layer": layer})
    elif outlet_type == "diffuser_round":
        for k in range(1, 4):
            msp.add_circle((cx, cy), half * k / 4, dxfattribs={"layer": layer})
    elif outlet_type == "slot":
        msp.add_lwpolyline([(cx - a, cy - half * 0.5), (cx + a, cy - half * 0.5),
                            (cx + a, cy + half * 0.5), (cx - a, cy + half * 0.5)],
                           close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - a * 0.8, cy), (cx + a * 0.8, cy), dxfattribs={"layer": layer})
    elif outlet_type == "swirl":
        msp.add_circle((cx, cy), half, dxfattribs={"layer": layer})
        for ang in range(0, 360, 60):
            rad = math.radians(ang)
            msp.add_line((cx, cy), (cx + half * math.cos(rad), cy + half * math.sin(rad)),
                         dxfattribs={"layer": layer})
    elif outlet_type == "louver_rain":
        msp.add_lwpolyline([(cx - half, cy - half), (cx + half, cy - half),
                            (cx + half, cy + half), (cx - half, cy + half)],
                           close=True, dxfattribs={"layer": layer})
        for i in range(-2, 3):
            msp.add_line((cx - half, cy + half * 0.5 + i * a * 0.18),
                         (cx + half, cy - half * 0.5 + i * a * 0.18),
                         dxfattribs={"layer": layer})
    elif outlet_type == "nozzle":
        msp.add_circle((cx, cy), half * 0.8, dxfattribs={"layer": layer})
        for ang in (-22, 0, 22):
            rad = math.radians(ang)
            msp.add_line((cx, cy), (cx + a * 0.95 * math.cos(rad), cy + a * 0.95 * math.sin(rad)),
                         dxfattribs={"layer": layer})
    else:
        raise ValueError(f"未知 outlet_type: {outlet_type}")


def draw_hvac_accessory(msp, origin, acc_type="transition", scale=100.0,
                        layer="设备", tracker=None):
    """风道附件（GB/T 50114 表 3.2.3-1 编号 3/4/7/9/10/11/14）。

    acc_type:
        transition   天圆地方(7)：左矩形 + 右半圆
        flexible     风管软接头(14)：波折线
        silencer     消声器(11)：矩形 + 内部消声片
        elbow_arc    圆弧形弯头(9)
        elbow_guide  带导流片矩形弯头(10)
        up           风管向上(3)
        down         风管向下(4)
    """
    s = scale * 2
    cx, cy = _r(*origin)
    a = 60.0 * s
    half = a * 0.5

    if acc_type == "transition":
        # 天圆地方：左矩形，右半圆（矩形→圆过渡）
        w = a * 0.7
        msp.add_line((cx - w, cy - half), (cx, cy - half), dxfattribs={"layer": layer})
        msp.add_line((cx, cy - half), (cx, cy + half), dxfattribs={"layer": layer})
        msp.add_line((cx, cy + half), (cx - w, cy + half), dxfattribs={"layer": layer})
        msp.add_arc((cx, cy), half, -90, 90, dxfattribs={"layer": layer})
    elif acc_type == "flexible":
        # 风管软接头：两短管 + 波折连接
        msp.add_line((cx - a * 0.6, cy - half), (cx - a * 0.6, cy + half),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + a * 0.6, cy - half), (cx + a * 0.6, cy + half),
                     dxfattribs={"layer": layer})
        pts = []
        n = 6
        for i in range(n + 1):
            x = cx - a * 0.6 + a * 1.2 * i / n
            y = cy + (half * 0.6 if i % 2 else -half * 0.6)
            pts.append((x, y))
        msp.add_lwpolyline(pts, dxfattribs={"layer": layer})
    elif acc_type == "silencer":
        # 消声器：矩形外壳 + 内部消声片
        msp.add_lwpolyline([(cx - half, cy - half), (cx + half, cy - half),
                            (cx + half, cy + half), (cx - half, cy + half)],
                           close=True, dxfattribs={"layer": layer})
        for i in range(1, 5):
            x = cx - half + a * i / 5
            msp.add_line((x, cy - half * 0.6), (x, cy + half * 0.6),
                         dxfattribs={"layer": layer})
    elif acc_type == "elbow_arc":
        # 圆弧形弯头：竖管 + 水平管 + 外凸四分之一圆弧
        msp.add_line((cx, cy), (cx, cy - a), dxfattribs={"layer": "风管"})
        msp.add_arc((cx, cy), a, -90, 0, dxfattribs={"layer": layer})
        msp.add_line((cx + a, cy), (cx, cy), dxfattribs={"layer": "风管"})
    elif acc_type == "elbow_guide":
        # 带导流片矩形弯头：L 形 + 导流片
        msp.add_lwpolyline([(cx, cy - a), (cx, cy), (cx + a, cy)],
                           dxfattribs={"layer": layer})
        for i in range(1, 4):
            t = i / 4
            msp.add_line((cx, cy - a * (1 - t)), (cx + a * t, cy),
                         dxfattribs={"layer": layer})
    elif acc_type == "up":
        msp.add_line((cx, cy + a * 0.3), (cx, cy - a), dxfattribs={"layer": "风管"})
        msp.add_line((cx, cy - a), (cx - half * 0.5, cy - a * 0.5),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy - a), (cx + half * 0.5, cy - a * 0.5),
                     dxfattribs={"layer": layer})
    elif acc_type == "down":
        msp.add_line((cx, cy - a * 0.3), (cx, cy + a), dxfattribs={"layer": "风管"})
        msp.add_line((cx, cy + a), (cx - half * 0.5, cy + a * 0.5),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy + a), (cx + half * 0.5, cy + a * 0.5),
                     dxfattribs={"layer": layer})
    else:
        raise ValueError(f"未知 acc_type: {acc_type}")


def _hvac_legend_grid(msp, items, draw_fn, ox, oy, cols, cell_w, cell_h, scale, layer):
    """在网格中绘制 [符号 + 名称]，返回网格下方的新 y 坐标。"""
    s = scale * 2
    for i, (kw, label) in enumerate(items):
        col = i % cols
        row = i // cols
        cx = ox + col * cell_w + cell_w * 0.5
        cy = oy - row * cell_h - cell_h * 0.5
        draw_fn(msp, (cx, cy), scale=scale, layer=layer, **kw)
        _hvac_label(msp, cx, cy - cell_h * 0.40, label, s, h=1.8, layer="文字")
    n_rows = (len(items) + cols - 1) // cols
    return oy - n_rows * cell_h


def draw_hvac_legend(msp, origin, scale=100.0, layer="设备", tracker=None):
    """自动生成 GB/T 50114 暖通空调制图 图例说明栏。

    包含：风道代号表(3.2.1) + 风道阀门及附件图例(3.2.3-1) +
    风口图例(3.2.3-2) + 风道附件图例(3.2.3-1)，每格为 [符号 + 中文名称]，
    可直接作为 HVAC 图纸右下角“图例说明”栏。
    """
    s = scale * 2
    ox, oy = _r(*origin)
    _hvac_label(msp, ox + 1000 * s, oy + 700 * s,
                "暖通空调制图图例（GB/T 50114-2010）", s, h=4.5, layer="文字-标题")

    # 一、风道代号
    _hvac_label(msp, ox, oy + 380 * s, "一、风道代号（表 3.2.1）", s, h=2.6, layer="文字-标题")
    codes = [("SF", "送风管"), ("HF", "回风管"), ("PF", "排风管"), ("XF", "新风管"),
             ("PY", "消防排烟风道"), ("ZY", "加压送风管"), ("P(Y)", "排风排烟兼用"),
             ("XB", "消防补风"), ("S(B)", "送风兼消防补风")]
    cy = oy + 260 * s
    for j, (c, n) in enumerate(codes):
        x = ox + (j % 3) * 520 * s
        y = cy - (j // 3) * 80 * s
        _hvac_label(msp, x, y, f"{c} {n}", s, h=2.0, layer="文字")
    oy = cy - ((len(codes) + 2) // 3) * 80 * s - 80 * s

    # 二、风道阀门及附件
    _hvac_label(msp, ox, oy, "二、风道阀门及附件（表 3.2.3-1）", s, h=2.6, layer="文字-标题")
    valves = [
        ({"valve_type": "butterfly"}, "蝶阀"),
        ({"valve_type": "multileaf"}, "对开多叶调节风阀(手动)"),
        ({"valve_type": "multileaf_electric"}, "对开多叶调节风阀(电动)"),
        ({"valve_type": "check"}, "风管止回阀"),
        ({"valve_type": "three_way"}, "三通调节阀"),
        ({"valve_type": "slide"}, "插板阀"),
        ({"valve_type": "fire"}, "防烟防火阀 70℃"),
        ({"valve_type": "smoke"}, "排烟阀 280℃"),
        ({"valve_type": "electric"}, "电动阀"),
    ]
    oy = _hvac_legend_grid(msp, valves, draw_hvac_valve, ox, oy - 120 * s,
                           3, 380 * s, 240 * s, scale, layer)

    # 三、风口
    _hvac_label(msp, ox, oy - 40 * s, "三、风口（表 3.2.3-2）", s, h=2.6, layer="文字-标题")
    outlets = [
        ({"outlet_type": "general"}, "风口(通用)"),
        ({"outlet_type": "grille_single"}, "单层格栅风口"),
        ({"outlet_type": "grille_double"}, "双层格栅风口"),
        ({"outlet_type": "diffuser_rect"}, "矩形散流器"),
        ({"outlet_type": "diffuser_round"}, "圆形散流器"),
        ({"outlet_type": "slot"}, "条缝形风口"),
        ({"outlet_type": "swirl"}, "旋流风口"),
        ({"outlet_type": "louver"}, "百叶回风口"),
        ({"outlet_type": "louver_rain"}, "防雨百叶"),
        ({"outlet_type": "nozzle"}, "喷口"),
    ]
    oy = _hvac_legend_grid(msp, outlets, draw_hvac_outlet, ox, oy - 160 * s,
                           5, 250 * s, 220 * s, scale, layer)

    # 四、风道附件
    _hvac_label(msp, ox, oy - 40 * s, "四、风道附件（表 3.2.3-1）", s, h=2.6, layer="文字-标题")
    accs = [
        ({"acc_type": "transition"}, "天圆地方"),
        ({"acc_type": "flexible"}, "风管软接头"),
        ({"acc_type": "silencer"}, "消声器"),
        ({"acc_type": "elbow_arc"}, "圆弧形弯头"),
        ({"acc_type": "elbow_guide"}, "带导流片矩形弯头"),
        ({"acc_type": "up"}, "风管向上"),
        ({"acc_type": "down"}, "风管向下"),
    ]
    _hvac_legend_grid(msp, accs, draw_hvac_accessory, ox, oy - 160 * s,
                      4, 320 * s, 220 * s, scale, layer)
