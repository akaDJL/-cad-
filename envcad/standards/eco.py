"""生态环境与环评深度制图 v1.0（HJ 2.4—2021、HJ 19—2022、HJ 610）。

噪声等声线图、大气扩散浓度等值线、植被类型图、水土保持方案图、
环境风险评价图（风险源+影响范围+疏散路线）、排污许可管理图。

纯 ezdxf，零新依赖。所有数据由 Agent 搜索后传入。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

def draw_noise_contour(msp, center, levels: List[dict],
                        scale: float = 100.0, label: str = "",
                        layer: str = "噪声", tracker=None):
    """噪声等声线图（从声源向外扩散的同心等值线）。

    levels: [{"distance":50,"db":65,"label":"昼间65dB"},
             {"distance":100,"db":60}, ...]
    distance 单位 m
    """
    s = scale; cx, cy = _r(*center)
    # 声源标记
    msp.add_circle((cx, cy), 3 * s, dxfattribs={"layer": layer})
    t = msp.add_text("声源", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((cx, cy + 5 * s), align=TextEntityAlignment.MIDDLE_CENTER)

    for lvl in levels:
        d = lvl.get("distance", 50) * s
        db = lvl.get("db", 0)
        lbl = lvl.get("label", "")
        if db >= 70: l_layer = layer
        elif db >= 60: l_layer = "细实线"
        else: l_layer = "细实线"
        msp.add_circle((cx, cy), d, dxfattribs={"layer": l_layer})
        if lbl:
            t = msp.add_text(lbl, dxfattribs={
                "layer": "文字", "height": 2.0 * s, "style": "ENG"})
            t.set_placement((cx + d + 2 * s, cy), align=TextEntityAlignment.MIDDLE_LEFT)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((cx, cy - max(l.get("distance",50) for l in levels)*s - 8*s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx + max(l.get("distance",50) for l in levels)*s + 20*s, cy)


def draw_air_diffusion(msp, origin, source, wind_dir=0, contours:List[dict]=None,
                        scale=100.0, label="", layer="大气", tracker=None):
    """大气扩散浓度等值线（高斯烟羽示意）。

    source: 排气筒位置 (x,y) mm
    wind_dir: 主导风向 角度（0=右, 90=上）
    contours: [{"dist":200,"conc":0.5,"label":"0.5mg/m³"}, ...] 距离 m
    """
    s = scale; sx, sy = _r(*source); rad = math.radians(wind_dir)
    ux, uy = math.cos(rad), math.sin(rad)
    # 排气筒
    msp.add_lwpolyline([(sx-2*s,sy-4*s),(sx+2*s,sy-4*s),(sx+2*s,sy+4*s),(sx-2*s,sy+4*s)],close=True,dxfattribs={"layer":layer})
    msp.add_line((sx,sy+4*s),(sx,sy+8*s),dxfattribs={"layer":layer})
    # 风向箭头
    arr_x, arr_y = sx+ux*20*s, sy+uy*20*s
    msp.add_line((sx, sy), (arr_x, arr_y), dxfattribs={"layer": layer})
    _tri(msp, (arr_x, arr_y), (ux, uy), s, layer)
    # 浓度等值线（椭圆近似）
    if contours:
        for ct in contours:
            d = ct.get("dist", 200) * s
            cx_c = sx + ux * d
            cy_c = sy + uy * d
            rx = d * 0.8; ry = d * 0.15
            pts = []
            for a in range(0, 361, 15):
                angle = math.radians(a)
                px = cx_c + rx * math.cos(angle) * math.cos(rad) - ry * math.sin(angle) * math.sin(rad)
                py = cy_c + rx * math.cos(angle) * math.sin(rad) + ry * math.sin(angle) * math.cos(rad)
                pts.append((px, py))
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer":"细实线"})
            if ct.get("label"):
                t = msp.add_text(ct["label"], dxfattribs={
                    "layer": "文字", "height": 1.8 * s, "style": "ENG"})
                t.set_placement((cx_c+rx+2*s, cy_c), align=TextEntityAlignment.MIDDLE_LEFT)
    if label:
        t = msp.add_text(label, dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((sx, sy-12*s), align=TextEntityAlignment.MIDDLE_CENTER)
    return (sx+15*s if not contours else sx+max(c.get("dist",200) for c in contours)*s*1.5, sy)


def draw_vegetation_map(msp, origin, patches: List[dict],
                         scale=100.0, label="植被类型图", layer="生态", tracker=None):
    """植被类型/土地利用图斑。
    patches: [{"type":"forest","points":[(0,0),(20,0),(20,15),(0,15)],"label":"针叶林"},
              {"type":"grass","points":[(20,0),(40,0),(40,15),(20,15)],"label":"草地"},
              {"type":"water","points":[(0,15),(20,15),(20,30),(0,30)],"label":"水体"},
              {"type":"crop","points":[(20,15),(40,15),(40,30),(20,30)],"label":"农田"},
              {"type":"built","points":[...],"label":"建设用地"}, ...]
    """
    s = scale; ox, oy = _r(*origin)
    hatch_styles = {
        "forest": "ANS31", "grass": "ANSI37", "water": "ANSI34",
        "crop": "ANSI32", "built": "ANSI33", "wetland": "ANSI36",
        "bare": "AR-SAND", "shrub": "ANSI38",
    }
    for patch in patches:
        ptype = patch.get("type", "forest")
        pts = [(ox + p[0] * s, oy + p[1] * s) for p in patch.get("points", [])]
        if len(pts) < 3:
            continue
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        try:
            hatch = msp.add_hatch(dxfattribs={"layer": layer, "color": 8})
            hatch.paths.add_polyline_path(pts)
            hatch.set_pattern_fill(hatch_styles.get(ptype, "ANSI31"), scale=0.5)
        except Exception as _e:
            print(f'[WARNING] eco.py: {_e}')
        lbl = patch.get("label", "")
        if lbl:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            t = msp.add_text(lbl, dxfattribs={
                "layer": "文字", "height": 3 * s, "style": "HZ"})
            t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((ox, oy + max(p.get("points",[[0,0]])[-1][1] for p in patches)*s + 6*s),
                        align=TextEntityAlignment.MIDDLE_LEFT)
    return (ox + 50 * s, oy + 50 * s)


def draw_risk_zone(msp, source, radius: float, inner_radius: float = 0,
                    risk_type: str = "toxic",
                    scale: float = 100.0, label: str = "",
                    params: dict = None, layer: str = "风险", tracker=None):
    """环境风险评价：风险源 + 影响范围圈 + 疏散路线。

    risk_type: "toxic"有毒 / "fire"火灾 / "explosion"爆炸
    params: {"substance":"液氨","amount":"10t","leak_rate":"5kg/min",
              "LC50":"1390mg/m³","population":"500人",...}
    """
    s = scale; sx, sy = _r(*source); R = radius * s; Ri = inner_radius * s
    # 风险源
    tri_r = 4 * s
    tri = [(sx, sy + tri_r), (sx - tri_r, sy - tri_r*0.5), (sx + tri_r, sy - tri_r*0.5)]
    msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer, "lineweight": 50})
    t = msp.add_text(risk_type.upper(), dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "ENG"})
    t.set_placement((sx, sy - tri_r - 3 * s), align=TextEntityAlignment.MIDDLE_CENTER)
    # 致死/致伤范围（实线）
    if Ri > 0:
        msp.add_circle((sx, sy), Ri, dxfattribs={"layer": layer, "lineweight": 40})
        t = msp.add_text("致死区", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((sx + Ri + 2 * s, sy), align=TextEntityAlignment.MIDDLE_LEFT)
    # 影响范围（虚线）
    msp.add_circle((sx, sy), R, dxfattribs={"layer": layer, "linetype": "DASHED"})
    t = msp.add_text("影响区", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((sx + R + 2 * s, sy + 10 * s), align=TextEntityAlignment.MIDDLE_LEFT)
    # 疏散路线（向外箭头）
    for ang in [45, 135, 225, 315]:
        rad = math.radians(ang); ex = sx + R * 1.3 * math.cos(rad); ey = sy + R * 1.3 * math.sin(rad)
        mid_x = sx + R * 1.1 * math.cos(rad); mid_y = sy + R * 1.1 * math.sin(rad)
        msp.add_line((sx + R * 0.7 * math.cos(rad), sy + R * 0.7 * math.sin(rad)), (mid_x, mid_y), dxfattribs={"layer":"细实线"})
        _tri(msp, (ex, ey), (math.cos(rad), math.sin(rad)), s, "细实线")
    if label:
        t = msp.add_text(label, dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((sx, sy - R - 8 * s), align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py = sy - R - 8 * s - 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={"layer":"文字","height":1.8*s,"style":"HZ"})
            t.set_placement((sx, py), align=TextEntityAlignment.MIDDLE_CENTER); py -= 2.3 * s
    return (sx + R * 1.5, sy - R * 1.5)


def draw_soil_erosion(msp, origin, measures: List[dict],
                       scale=100.0, label="水土保持措施", layer="水保", tracker=None):
    """水土保持措施布置图。
    measures: [{"type":"terrace","origin":(x,y),"l":50,"w":20,"label":"梯田"},
               {"type":"check_dam","origin":(x,y),"w":30,"label":"谷坊"},
               {"type":"drain","from":(x1,y1),"to":(x2,y2),"label":"截水沟"},
               {"type":"revegetation","origin":(x,y),"w":40,"h":30,"label":"植被恢复区"}]
    """
    s = scale; ox, oy = _r(*origin)
    for m in measures:
        mtype = m.get("type", ""); mlbl = m.get("label", "")
        if mtype == "terrace":
            tx, ty = m.get("origin", (0, 0)); tl, tw = m.get("l", 50) * s, m.get("w", 20) * s
            for i in range(4):
                ly = ty + i * (tw / 4)
                msp.add_line((ox + tx * s, oy + ly), (ox + (tx + tl / s) * s, oy + ly), dxfattribs={"layer": layer})
            _dim_text(msp, ox + (tx + tl / s / 2) * s, oy + ty * s - 4 * s, mlbl, 2.5 * s)
        elif mtype == "check_dam":
            dx, dy = m.get("origin", (0, 0)); dw = m.get("w", 30) * s
            msp.add_line((ox + dx * s, oy + dy * s), (ox + (dx + dw / s) * s, oy + dy * s), dxfattribs={"layer": layer, "lineweight": 40})
            _dim_text(msp, ox + (dx + dw / s / 2) * s, oy + dy * s - 4 * s, mlbl, 2.5 * s)
        elif mtype == "drain":
            fr = m.get("from", (0, 0)); to = m.get("to", (0, 0))
            msp.add_line((ox + fr[0] * s, oy + fr[1] * s), (ox + to[0] * s, oy + to[1] * s), dxfattribs={"layer": layer, "linetype": "DASHED"})
            mx, my = (fr[0] + to[0]) / 2 * s + ox, (fr[1] + to[1]) / 2 * s + oy
            _dim_text(msp, mx + 3 * s, my, mlbl, 2 * s)
        elif mtype == "revegetation":
            rx, ry = m.get("origin", (0, 0)); rw, rh = m.get("w", 40) * s, m.get("h", 30) * s
            msp.add_lwpolyline([(ox+rx*s,oy+ry*s),(ox+(rx+rw/s)*s,oy+ry*s),(ox+(rx+rw/s)*s,oy+(ry+rh/s)*s),(ox+rx*s,oy+(ry+rh/s)*s)],close=True,dxfattribs={"layer":layer,"linetype":"DASHED"})
            for _ in range(5):
                gx = ox + (rx + rw/s*0.3 + (_%3)*rw/s*0.2)*s if False else ox+(rx+rw/(s*2))*s
                tri = [(gx, oy+(ry+rh/(s*2))*s), (gx-2*s, oy+ry*s), (gx+2*s, oy+ry*s)]
                msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": "细实线"})
            _dim_text(msp, ox+(rx+rw/(s*2))*s, oy+ry*s-4*s, mlbl, 2.5*s)
    if label:
        t = msp.add_text(label, dxfattribs={"layer":"文字-标题","height":4*s,"style":"HZ"})
        t.set_placement((ox+20*s, oy-10*s), align=TextEntityAlignment.MIDDLE_LEFT)
    return (ox+80*s, oy)

def _dim_text(msp, x, y, text, h):
    t = msp.add_text(text, dxfattribs={
        "layer": "文字", "height": h, "style": "HZ"})
    t.set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)


# ══════════════════════════════════════════════════════════
#  v1.5+ 生态增补：植被/红线/栖息地/廊道
# ══════════════════════════════════════════════════════════

def draw_vegetation_map(msp, origin, width=200.0, height=150.0,
                         zones=None, scale=100.0, label="", layer="生态",
                         tracker=None):
    """植被分布图。

    参数:
        width/height: 图幅范围 m
        zones: [{ "x":20,"y":30,"w":50,"h":40,"type":"乔木","coverage":80 }, ...]
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = height * s

    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": "细实线"})

    if zones:
        for z in zones:
            zx = ox + z.get("x", 0) * s
            zy = oy + z.get("y", 0) * s
            zw = z.get("w", 30) * s
            zh = z.get("h", 20) * s
            ztype = z.get("type", "植被")
            coverage = z.get("coverage", 50)

            msp.add_lwpolyline([(zx, zy), (zx + zw, zy), (zx + zw, zy + zh), (zx, zy + zh)],
                               close=True, dxfattribs={"layer": layer})

            # 覆盖度示意（点密度）
            n_dots = max(3, int(coverage / 10))
            for _ in range(n_dots):
                import random
                dx = zx + random.uniform(0.2, 0.8) * zw
                dy = zy + random.uniform(0.2, 0.8) * zh
                msp.add_circle((dx, dy), 1.5 * s, dxfattribs={"layer": "细实线"})

            t = msp.add_text(f"{ztype}({coverage}%)", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((zx + zw / 2, zy + zh / 2),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + h + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_ecological_redline(msp, origin, width=200.0, height=150.0,
                             redline_points=None, scale=100.0, label="",
                             layer="细实线", tracker=None):
    """生态红线范围图。

    参数:
        width/height: 图幅 m
        redline_points: [(x1,y1),(x2,y2),...] 红线拐点
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = height * s

    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": "细实线"})

    if redline_points:
        pts = [(ox + p[0] * s, oy + p[1] * s) for p in redline_points]
        msp.add_lwpolyline(pts, close=True, dxfattribs={
            "layer": layer, "linetype": "DASHED"})
        # 填充红线区域（稀疏斜线）
        for i in range(len(pts)):
            msp.add_line(pts[i], pts[(i + 1) % len(pts)],
                         dxfattribs={"layer": "粗实线"})

    # 图例
    t = msp.add_text("生态保护红线", dxfattribs={
        "layer": "文字", "height": 3 * s, "style": "HZ"})
    t.set_placement((ox + w + 5 * s, oy + h / 2),
                    align=TextEntityAlignment.MIDDLE_LEFT)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + h + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_habitat_range(msp, origin, width=200.0, height=150.0,
                        habitats=None, scale=100.0, label="", layer="生态",
                        tracker=None):
    """栖息地范围图。

    参数:
        habitats: [{ "x":30,"y":40,"r":25,"species":"黑颈鹤","type":"core" }, ...]
    """
    s = scale; ox, oy = _r(*origin)
    w = width * s; h = height * s

    msp.add_lwpolyline([(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
                       close=True, dxfattribs={"layer": "细实线"})

    if habitats:
        for hab in habitats:
            hx = ox + hab.get("x", 0) * s
            hy = oy + hab.get("y", 0) * s
            hr = hab.get("r", 20) * s
            species = hab.get("species", "")
            htype = hab.get("type", "core")

            if htype == "core":
                msp.add_circle((hx, hy), hr, dxfattribs={"layer": layer})
            elif htype == "buffer":
                msp.add_circle((hx, hy), hr, dxfattribs={
                    "layer": "细实线", "linetype": "DASHED"})
            elif htype == "corridor":
                # 廊道：椭圆
                for ang in range(0, 360, 15):
                    import math
                    rad = math.radians(ang)
                    ex = hx + hr * math.cos(rad)
                    ey = hy + hr * 0.5 * math.sin(rad)
                    if ang == 0:
                        pts = [(ex, ey)]
                    else:
                        pts.append((ex, ey))
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

            if species:
                t = msp.add_text(species, dxfattribs={
                    "layer": "文字", "height": 2 * s, "style": "HZ"})
                t.set_placement((hx, hy), align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 4 * s, "style": "HZ"})
        t.set_placement((ox + w / 2, oy + h + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)


def draw_ecological_corridor(msp, origin, points=None, width=50.0,
                              scale=100.0, label="", layer="生态", tracker=None):
    """生态廊道。

    参数:
        points: [(x1,y1),(x2,y2),...] 廊道路径 m
        width: 廊道宽度 m
    """
    s = scale; ox, oy = _r(*origin)
    cw = width * s

    if points and len(points) >= 2:
        pts = [(ox + p[0] * s, oy + p[1] * s) for p in points]
        msp.add_lwpolyline(pts, close=False, dxfattribs={
            "layer": layer, "linetype": "DASHED"})
        # 双线廊道
        for i in range(len(pts)):
            p = pts[i]
            msp.add_circle(p, cw / 2, dxfattribs={"layer": "细实线"})
        # 连接带
        msp.add_lwpolyline([(pts[0][0], pts[0][1] + cw / 2),
                             (pts[-1][0], pts[-1][1] + cw / 2),
                             (pts[-1][0], pts[-1][1] - cw / 2),
                             (pts[0][0], pts[0][1] - cw / 2)],
                           close=False, dxfattribs={"layer": "细实线"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox, oy - 6 * s), align=TextEntityAlignment.MIDDLE_LEFT)
