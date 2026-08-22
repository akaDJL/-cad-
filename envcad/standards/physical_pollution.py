"""物理污染防治制图 v1.0。

引用标准（均为现行最新版）：
  GB 8702-2014      电磁环境控制限值（代替GB 8702-88, GB 9175-88）
  GB 18871-2002     电离辐射防护与辐射源安全基本标准
  HJ 2.4-2021       环境影响评价技术导则 声环境（代替HJ 2.4-2009）
  GB 3096-2008      声环境质量标准
  GB/T 35626-2017   室外照明干扰光限制规范
  GB 10070-88       城市区域环境振动标准
  GB 8702-2014      电磁环境控制限值（含0.1MHz~300GHz全频段）

电磁辐射等值线、放射性监测网、高压输变电电磁场分布、
基站辐射防护区、光污染分区、振动传播衰减。

纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  电磁辐射
# ══════════════════════════════════════════════════════════

def draw_emf_contour(msp, center, source_type="transmission",
                      levels=None,
                      scale=100.0, label="", params=None,
                      layer="电磁", tracker=None):
    """电磁辐射场强等值线图。

    参数:
        source_type: "transmission"高压输电 / "substation"变电站 /
                     "base_station"基站 / "radar"雷达
        levels: [{"distance":50,"field":"4kV/m","label":"4kV/m"},
                 {"distance":100,"field":"2kV/m"}, ...]
        params: {"voltage":"500kV","current":"1000A","freq":"50Hz",...}
    """
    s = scale; cx, cy = _r(*center)

    if levels is None:
        levels = [
            {"distance": 30, "field": "10kV/m", "label": "10kV/m"},
            {"distance": 60, "field": "5kV/m", "label": "5kV/m"},
            {"distance": 100, "field": "2kV/m", "label": "2kV/m"},
            {"distance": 150, "field": "1kV/m", "label": "1kV/m(限值)"},
        ]

    # 源标记
    if source_type == "transmission":
        # 输电塔：倒三角
        r = 4 * s
        msp.add_lwpolyline(
            [(cx - r, cy + r), (cx + r, cy + r), (cx, cy - r)],
            close=True, dxfattribs={"layer": layer, "lineweight": 50})
        t = msp.add_text("T", dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG"})
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
    elif source_type == "substation":
        # 变电站：矩形
        w, h = 10 * s, 8 * s
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer, "lineweight": 50})
        t = msp.add_text("变电站", dxfattribs={
            "layer": "文字-标题", "height": 2 * s, "style": "HZ"})
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
    elif source_type == "base_station":
        # 基站：三角形+天线
        r = 3 * s
        msp.add_lwpolyline(
            [(cx - r, cy), (cx + r, cy), (cx, cy + r)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((cx, cy + r), (cx, cy + r + 4 * s),
                     dxfattribs={"layer": layer})
    elif source_type == "radar":
        # 雷达：圆+扇形
        msp.add_circle((cx, cy), 3 * s, dxfattribs={"layer": layer})
        msp.add_arc((cx, cy), radius=6 * s,
                    start_angle=-30, end_angle=30,
                    dxfattribs={"layer": layer, "linetype": "DASHED"})

    # 等值线（同心圆/椭圆）
    for lvl in levels:
        d = lvl.get("distance", 50) * s
        fld = lvl.get("field", "")
        lbl = lvl.get("label", fld)

        # 椭圆等值线（模拟场强分布）
        msp.add_ellipse((cx, cy), major_axis=(d, 0, 0), ratio=0.7,
                         dxfattribs={"layer": "细实线", "linetype": "DASHED"})

        if lbl:
            t = msp.add_text(lbl, dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "ENG"})
            t.set_placement((cx + d, cy + d * 0.7),
                            align=TextEntityAlignment.MIDDLE_LEFT)

    # 防护距离标注
    if levels:
        max_d = max(lvl.get("distance", 50) for lvl in levels) * s
        msp.add_line((cx, cy - 5 * s), (cx + max_d, cy - 5 * s),
                     dxfattribs={"layer": "细实线-尺寸"})
        t = msp.add_text(f"防护距离 {max_d / s:.0f}m", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((cx + max_d / 2, cy - 5 * s - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy + max(l.get("distance", 50) for l in levels) * s + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = cy - max(l.get("distance", 50) for l in levels) * s - 8 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (cx + max(l.get("distance", 50) for l in levels) * s,
            cy + max(l.get("distance", 50) for l in levels) * s)


def draw_emf_monitoring_network(msp, origin, n_points=6, radius=200.0,
                                 scale=100.0, label="", params=None,
                                 layer="电磁监测", tracker=None):
    """电磁辐射监测网布点图。

    参数:
        n_points: 监测点数量
        radius: 监测范围半径 m
        params: {"source":"500kV输电线","points":"6个",
                  "limit":"4kV/m(公众)","freq":"连续",...}
    """
    s = scale; cx, cy = _r(*origin)
    R = radius * s

    # 源（中心）
    msp.add_lwpolyline(
        [(cx - 4 * s, cy + 4 * s), (cx + 4 * s, cy + 4 * s), (cx, cy - 4 * s)],
        close=True, dxfattribs={"layer": layer, "lineweight": 50})

    # 监测范围圆
    msp.add_circle((cx, cy), R,
                   dxfattribs={"layer": "细实线", "linetype": "DASHED"})

    # 监测点（圆周均布）
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        px = cx + R * math.cos(angle)
        py = cy + R * math.sin(angle)
        # 监测点符号
        msp.add_circle((px, py), 3 * s, dxfattribs={"layer": layer})
        msp.add_line((px - 3 * s, py), (px + 3 * s, py),
                     dxfattribs={"layer": layer})
        # 编号
        t = msp.add_text(f"M{i+1}", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "ENG"})
        t.set_placement((px, py + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy + R + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = cy - R - 8 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (cx + R + 5 * s, cy + R + 5 * s)


# ══════════════════════════════════════════════════════════
#  放射性
# ══════════════════════════════════════════════════════════

def draw_radiation_zone(msp, center, source_type="sealed",
                         zones=None,
                         scale=100.0, label="", params=None,
                         layer="辐射", tracker=None):
    """放射性防护分区图。

    参数:
        source_type: "sealed"密封源 / "unsealed"开放源 /
                     "accelerator"加速器 / "reactor"反应堆
        zones: [{"radius":10,"level":"控制区","dose":">5mSv/a"},
                {"radius":30,"level":"监督区","dose":"1-5mSv/a"}, ...]
        params: {"source":"Co-60","activity":"3.7E14Bq",
                  "shielding":"铅+混凝土","half_life":"5.27a",...}
    """
    s = scale; cx, cy = _r(*center)

    if zones is None:
        zones = [
            {"radius": 5, "level": "控制区", "dose": ">5mSv/a"},
            {"radius": 15, "level": "监督区", "dose": "1-5mSv/a"},
            {"radius": 30, "level": "非限制区", "dose": "<1mSv/a"},
        ]

    # 源标记（三叶形辐射符号）
    r = 4 * s
    for ang in [90, 210, 330]:
        rad = math.radians(ang)
        msp.add_arc((cx + r * 0.6 * math.cos(rad),
                     cy + r * 0.6 * math.sin(rad)),
                    radius=r * 0.5,
                    start_angle=ang - 30, end_angle=ang + 30,
                    dxfattribs={"layer": layer, "lineweight": 50})
    msp.add_circle((cx, cy), r * 0.3,
                   dxfattribs={"layer": layer})

    # 分区圆
    zone_colors = {"控制区": 1, "监督区": 3, "非限制区": 4}
    for z in zones:
        rad_z = z.get("radius", 10) * s
        level = z.get("level", "")
        dose = z.get("dose", "")
        color = zone_colors.get(level, 7)

        msp.add_circle((cx, cy), rad_z,
                       dxfattribs={"layer": layer, "linetype": "DASHED"})
        t = msp.add_text(f"{level}({dose})", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((cx + rad_z * 0.7, cy + rad_z * 0.7),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        max_r = max(z.get("radius", 10) for z in zones) * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy + max_r + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        max_r = max(z.get("radius", 10) for z in zones) * s
        py = cy - max_r - 8 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    max_r = max(z.get("radius", 10) for z in zones) * s
    return (cx + max_r + 5 * s, cy + max_r + 5 * s)


def draw_radiation_shielding(msp, origin, wall_type="concrete",
                              thickness=1.0, height=3.0,
                              scale=100.0, label="", params=None,
                              layer="屏蔽", tracker=None):
    """辐射屏蔽墙剖面图。

    参数:
        wall_type: "concrete"混凝土 / "lead"铅板 / "steel"钢板 /
                   "composite"复合 / "water"水屏蔽
        thickness: 墙厚 m
        height: 墙高 m
        params: {"material":"重混凝土(ρ=3.5)","thickness":"1000mm",
                  "HVL":"50mmPb","source":"Co-60",...}
    """
    s = scale; ox, oy = _r(*origin)
    T = thickness * s; H = height * s

    # 墙体
    msp.add_lwpolyline(
        [(ox, oy), (ox + T, oy), (ox + T, oy + H), (ox, oy + H)],
        close=True, dxfattribs={"layer": layer, "lineweight": 50})

    # 材料填充标注
    materials = {
        "concrete": "混凝土",
        "lead": "铅板",
        "steel": "钢板",
        "composite": "复合屏蔽",
        "water": "水屏蔽",
    }
    mat_label = materials.get(wall_type, "屏蔽材料")

    # 剖面线
    if wall_type == "concrete":
        for i in range(0, int(T / (3 * s)) + 1):
            hx = ox + 3 * s * i
            msp.add_line((hx, oy), (hx + 2 * s, oy + H),
                         dxfattribs={"layer": "剖面线"})
    elif wall_type == "lead":
        # 实心填充（粗线）
        msp.add_lwpolyline(
            [(ox + T * 0.3, oy), (ox + T * 0.7, oy),
             (ox + T * 0.7, oy + H), (ox + T * 0.3, oy + H)],
            close=True, dxfattribs={"layer": layer, "lineweight": 60})
    elif wall_type == "composite":
        # 多层
        for frac in [0.25, 0.5, 0.75]:
            mx = ox + T * frac
            msp.add_line((mx, oy), (mx, oy + H),
                         dxfattribs={"layer": "细实线"})

    # 辐射源侧
    msp.add_lwpolyline(
        [(ox - 6 * s, oy + H / 2 - 3 * s),
         (ox - 2 * s, oy + H / 2),
         (ox - 6 * s, oy + H / 2 + 3 * s)],
        close=False, dxfattribs={"layer": layer, "lineweight": 50})
    t = msp.add_text("辐射源", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox - 8 * s, oy + H / 2 + 5 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)
    # 辐射方向箭头
    msp.add_line((ox - 4 * s, oy + H / 2), (ox, oy + H / 2),
                 dxfattribs={"layer": layer})
    _tri(msp, (ox, oy + H / 2), (1, 0), s, layer)

    # 屏蔽后侧
    msp.add_line((ox + T, oy + H / 2), (ox + T + 6 * s, oy + H / 2),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    t = msp.add_text("衰减后", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + T + 8 * s, oy + H / 2 + 2 * s),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    # 厚度标注
    t = msp.add_text(f"t={thickness*1000:.0f}mm", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "ENG"})
    t.set_placement((ox + T / 2, oy - 4 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 材料标注
    t = msp.add_text(mat_label, dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ox + T / 2, oy + H + 4 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + T / 2, oy + H + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy - 8 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + T / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + T + 12 * s, oy + H)


# ══════════════════════════════════════════════════════════
#  光污染
# ══════════════════════════════════════════════════════════

def draw_light_pollution_zone(msp, center, source_type="floodlight",
                               levels=None,
                               scale=100.0, label="", params=None,
                               layer="光污染", tracker=None):
    """光污染分区图。

    参数:
        source_type: "floodlight"泛光灯 / "stadium"体育场 /
                     "billboard"广告牌 / "street"路灯
        levels: [{"distance":20,"lux":"200lx","zone":"E4高亮度"},
                 {"distance":50,"lux":"50lx","zone":"E3中亮度"}, ...]
        params: {"power":"4x1000W","height":"25m","angle":"15°",
                  "uplight":"2%","standard":"CIE 150",...}
    """
    s = scale; cx, cy = _r(*center)

    if levels is None:
        levels = [
            {"distance": 20, "lux": "200lx", "zone": "E4高亮度区"},
            {"distance": 50, "lux": "50lx", "zone": "E3中亮度区"},
            {"distance": 100, "lux": "10lx", "zone": "E2低亮度区"},
            {"distance": 200, "lux": "2lx", "zone": "E1暗环境区"},
        ]

    # 光源标记
    if source_type == "floodlight":
        # 泛光灯：扇形
        msp.add_arc((cx, cy), radius=4 * s,
                    start_angle=-30, end_angle=30,
                    dxfattribs={"layer": layer, "lineweight": 50})
        msp.add_line((cx, cy), (cx + 4 * s * math.cos(math.radians(-30)),
                                 cy + 4 * s * math.sin(math.radians(-30))),
                     dxfattribs={"layer": layer})
        msp.add_line((cx, cy), (cx + 4 * s * math.cos(math.radians(30)),
                                 cy + 4 * s * math.sin(math.radians(30))),
                     dxfattribs={"layer": layer})
    elif source_type == "stadium":
        # 体育场：矩形
        w, h = 12 * s, 8 * s
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
    elif source_type == "billboard":
        # 广告牌：竖矩形
        w, h = 6 * s, 10 * s
        msp.add_lwpolyline(
            [(cx - w / 2, cy), (cx + w / 2, cy),
             (cx + w / 2, cy + h), (cx - w / 2, cy + h)],
            close=True, dxfattribs={"layer": layer})
    elif source_type == "street":
        # 路灯：圆+杆
        msp.add_circle((cx, cy + 6 * s), 2 * s,
                       dxfattribs={"layer": layer})
        msp.add_line((cx, cy), (cx, cy + 6 * s),
                     dxfattribs={"layer": layer})

    # 光照分区（扇形/圆形）
    for lvl in levels:
        d = lvl.get("distance", 50) * s
        lux = lvl.get("lux", "")
        zone = lvl.get("zone", "")

        # 光照范围（扇形扩展）
        msp.add_arc((cx, cy), radius=d,
                    start_angle=-45, end_angle=45,
                    dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        t = msp.add_text(f"{zone}({lux})", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((cx + d * 0.7, cy - 4 * s),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        max_d = max(l.get("distance", 50) for l in levels) * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy - max_d * 0.5 - 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        max_d = max(l.get("distance", 50) for l in levels) * s
        py = cy - max_d * 0.5 - 8 * s - 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    max_d = max(l.get("distance", 50) for l in levels) * s
    return (cx + max_d, cy)


def draw_vibration_contour(msp, center, source_type="railway",
                            levels=None,
                            scale=100.0, label="", params=None,
                            layer="振动", tracker=None):
    """振动传播衰减等值线图。

    参数:
        source_type: "railway"铁路 / "highway"公路 / "construction"施工 / "blasting"爆破
        levels: [{"distance":10,"vl":"80dB","label":"80dB"},
                 {"distance":30,"vl":"75dB"}, ...]
        params: {"source":"地铁","depth":"15m","freq":"10-30Hz",...}
    """
    s = scale; cx, cy = _r(*center)

    if levels is None:
        levels = [
            {"distance": 10, "vl": "80dB", "label": "80dB"},
            {"distance": 30, "vl": "75dB", "label": "75dB"},
            {"distance": 60, "vl": "70dB", "label": "70dB(限值)"},
        ]

    # 源标记
    source_labels = {
        "railway": "铁路",
        "highway": "公路",
        "construction": "施工",
        "blasting": "爆破",
    }
    src_label = source_labels.get(source_type, "振动源")

    if source_type == "railway":
        # 铁路：双线
        msp.add_line((cx - 8 * s, cy), (cx + 8 * s, cy),
                     dxfattribs={"layer": layer, "lineweight": 50})
        msp.add_line((cx - 8 * s, cy + 1.5 * s), (cx + 8 * s, cy + 1.5 * s),
                     dxfattribs={"layer": layer, "lineweight": 50})
    elif source_type == "construction":
        # 施工：打桩机符号
        msp.add_lwpolyline(
            [(cx - 3 * s, cy), (cx + 3 * s, cy), (cx, cy + 5 * s)],
            close=True, dxfattribs={"layer": layer})
    else:
        msp.add_circle((cx, cy), 4 * s, dxfattribs={"layer": layer})

    t = msp.add_text(src_label, dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((cx, cy - 6 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # 振动衰减等值线
    for lvl in levels:
        d = lvl.get("distance", 30) * s
        vl = lvl.get("vl", "")
        lbl = lvl.get("label", vl)

        # 椭圆等值线（振动沿水平传播更远）
        msp.add_ellipse((cx, cy), major_axis=(d, 0, 0), ratio=0.5,
                         dxfattribs={"layer": "细实线", "linetype": "DASHED"})

        if lbl:
            t = msp.add_text(lbl, dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "ENG"})
            t.set_placement((cx + d, cy),
                            align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        max_d = max(l.get("distance", 30) for l in levels) * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy + max_d * 0.5 + 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        max_d = max(l.get("distance", 30) for l in levels) * s
        py = cy - max_d * 0.5 - 8 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    max_d = max(l.get("distance", 30) for l in levels) * s
    return (cx + max_d, cy + max_d * 0.5)
