"""给排水/消防工程制图 v1.0（GB 50015—2019、GB 50974—2014）。

基于 ezdxf 实现给水平面图、排水系统图、消防栓布置、卫生器具符号。
所有标准数值（管径、流量、水压等）由 Agent 搜索后显式传入。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ══════════════════════════════════════════════════════════
#  管道绘制（给排水专用，与环保管道区分）
# ══════════════════════════════════════════════════════════

def draw_plumbing_pipe(msp, start, end, pipe_type: str = "cold",
                        dn: int = 25, scale: float = 100.0,
                        label: str = "",
                        layer: str = "给水管",
                        tracker=None):
    """绘制给排水管段。

    参数:
        pipe_type: "cold"冷水 / "hot"热水 / "drain"排水 / "vent"通气管 /
                   "fire"消防 / "rain"雨水 / "recycle"中水
        dn: 公称直径 mm
        label: 标注文字（如 "DN25"）
    """
    s = scale
    sx, sy = _r(*start)
    ex, ey = _r(*end)

    # 线型选择
    line_layer = {
        "cold": "给水管", "hot": "热水管", "drain": "排水管",
        "vent": "通气管", "fire": "消防管", "rain": "雨水管",
        "recycle": "中水管",
    }.get(pipe_type, "给水管")

    # Hot water: dash-dot
    linetype = None
    if pipe_type in ("hot", "fire"):
        linetype = "DASHDOT"

    msp.add_line((sx, sy), (ex, ey),
                 dxfattribs={"layer": line_layer,
                             "linetype": linetype} if linetype else
                 {"layer": line_layer})

    # 标注
    if label:
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        txt_h = 2.5 * s
        dx, dy = ex - sx, ey - sy
        lg = math.hypot(dx, dy)
        if lg > 0:
            px, py = -dy / lg, dx / lg
            tx = mx + px * 4 * s
            ty = my + py * 4 * s
        else:
            tx, ty = mx, my - 4 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((tx, ty), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(min(sx, ex) - 3 * s, min(sy, ey) - 3 * s,
                         max(sx, ex) + 10 * s, max(sy, ey) + 10 * s, margin=20)

    return (ex, ey)


# ══════════════════════════════════════════════════════════
#  卫生器具符号
# ══════════════════════════════════════════════════════════

def draw_fixture(msp, center, f_type: str,
                  scale: float = 100.0,
                  label: str = "",
                  layer: str = "设备",
                  tracker=None):
    """卫生器具平面符号。

    参数:
        f_type: "toilet"坐便器 / "squat"蹲便器 / "urinal"小便器 /
                "basin"洗脸盆 / "sink"洗涤槽 / "bathtub"浴缸 /
                "shower"淋浴 / "floor_drain"地漏 / "mop"拖布池
    """
    s = scale
    cx, cy = _r(*center)
    w, h = 12.0 * s, 16.0 * s

    if f_type == "toilet":
        # 坐便器：矩形 + 内椭圆
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        msp.add_ellipse((cx, cy + 2 * s), radius_x=w*0.35, radius_y=h*0.3,
                         dxfattribs={"layer": layer})
        # 水箱
        msp.add_lwpolyline(
            [(cx - w * 0.3, cy + h / 2),
             (cx + w * 0.3, cy + h / 2),
             (cx + w * 0.3, cy + h / 2 + 3 * s),
             (cx - w * 0.3, cy + h / 2 + 3 * s)],
            close=True, dxfattribs={"layer": layer})

    elif f_type == "squat":
        # 蹲便器：矩形 + 内窄长方形
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        msp.add_lwpolyline(
            [(cx - w * 0.25, cy - h * 0.35),
             (cx + w * 0.25, cy - h * 0.35),
             (cx + w * 0.25, cy + h * 0.35),
             (cx - w * 0.25, cy + h * 0.35)],
            close=True, dxfattribs={"layer": layer})

    elif f_type == "urinal":
        # 小便器：半圆 + 矩形
        msp.add_arc((cx, cy + 2 * s), radius=w / 2,
                     start_angle=180, end_angle=360,
                     dxfattribs={"layer": layer})
        msp.add_line((cx - w / 2, cy + 2 * s),
                     (cx - w / 2, cy - h / 2),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + w / 2, cy + 2 * s),
                     (cx + w / 2, cy - h / 2),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - w / 2, cy - h / 2),
                     (cx + w / 2, cy - h / 2),
                     dxfattribs={"layer": layer})

    elif f_type == "basin":
        # 洗脸盆：椭圆
        msp.add_ellipse((cx, cy), radius_x=w * 0.5, radius_y=h * 0.4,
                         dxfattribs={"layer": layer})
        # 龙头
        msp.add_circle((cx, cy + h * 0.3), 1.5 * s,
                       dxfattribs={"layer": layer})

    elif f_type == "sink":
        # 洗涤槽：双联矩形
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        # 中间隔板
        msp.add_line((cx, cy - h / 2), (cx, cy + h / 2),
                     dxfattribs={"layer": "细实线"})

    elif f_type == "bathtub":
        # 浴缸：大椭圆
        msp.add_ellipse((cx, cy), radius_x=w * 0.5, radius_y=h * 0.45,
                         dxfattribs={"layer": layer})
        # 内小椭圆
        msp.add_ellipse((cx, cy + 1 * s), radius_x=w * 0.3, radius_y=h * 0.25,
                         dxfattribs={"layer": "细实线"})

    elif f_type == "shower":
        # 淋浴：十字 + 圆
        r = 5.0 * s
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        msp.add_line((cx - r, cy), (cx + r, cy),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((cx, cy - r), (cx, cy + r),
                     dxfattribs={"layer": "细实线"})

    elif f_type == "floor_drain":
        # 地漏：小圆 + 网格
        r = 4.0 * s
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        for i in range(3):
            off = (i - 1) * 1.5 * s
            msp.add_line((cx - r, cy + off), (cx + r, cy + off),
                         dxfattribs={"layer": "细实线"})

    elif f_type == "mop":
        # 拖布池：小方框
        msp.add_lwpolyline(
            [(cx - 5 * s, cy - 5 * s), (cx + 5 * s, cy - 5 * s),
             (cx + 5 * s, cy + 5 * s), (cx - 5 * s, cy + 5 * s)],
            close=True, dxfattribs={"layer": layer})

    # 标注
    if label:
        txt_h = 2.2 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - h / 2 - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + w / 2, cy - h / 2 - 5 * s)


# ══════════════════════════════════════════════════════════
#  阀门 / 管件 / 水表
# ══════════════════════════════════════════════════════════

def draw_valve_plumbing(msp, center, v_type: str = "gate",
                         scale: float = 100.0,
                         label: str = "",
                         layer: str = "管件",
                         tracker=None):
    """给排水阀门符号。

    参数:
        v_type: "gate"闸阀 / "globe"截止阀 / "ball"球阀 /
                "butterfly"蝶阀 / "check"止回阀 / "strainer"过滤器 /
                "meter"水表 / "prv"减压阀
    """
    s = scale
    cx, cy = _r(*center)

    if v_type == "gate":
        # 闸阀：蝴蝶形（两个背对背三角）
        tri_w, tri_h = 5.0 * s, 4.0 * s
        pts = [(cx, cy - tri_h / 2), (cx, cy + tri_h / 2),
               (cx + tri_w, cy)]
        try:
            msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        msp.add_line((cx + tri_w, cy), (cx + tri_w + 4 * s, cy),
                     dxfattribs={"layer": layer})
        msp.add_line((cx - tri_w * 0.3, cy), (cx - 4 * s, cy),
                     dxfattribs={"layer": layer})

    elif v_type == "check":
        # 止回阀：箭头 + 横线
        msp.add_line((cx - 5 * s, cy), (cx + 5 * s, cy),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + 3 * s, cy - 2 * s), (cx + 5 * s, cy),
                     dxfattribs={"layer": layer})
        msp.add_line((cx + 3 * s, cy + 2 * s), (cx + 5 * s, cy),
                     dxfattribs={"layer": layer})

    elif v_type == "meter":
        # 水表：圆 + M
        r = 4.0 * s
        msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})
        t = msp.add_text("WM", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    elif v_type == "prv":
        # 减压阀：三角 + 横线
        tri = [(cx - 3 * s, cy - 3 * s), (cx + 3 * s, cy - 3 * s),
               (cx, cy + 3 * s)]
        msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - 6 * s, cy - 2 * s), (cx + 6 * s, cy - 2 * s),
                     dxfattribs={"layer": layer})

    else:
        # 通用符号：两三角
        tri_pts = [(cx - 4 * s, cy - 2.5 * s), (cx, cy),
                   (cx - 4 * s, cy + 2.5 * s)]
        msp.add_lwpolyline(tri_pts, close=True, dxfattribs={"layer": layer})
        tri_pts2 = [(cx + 4 * s, cy - 2.5 * s), (cx, cy),
                    (cx + 4 * s, cy + 2.5 * s)]
        msp.add_lwpolyline(tri_pts2, close=True, dxfattribs={"layer": layer})
        msp.add_line((cx - 6 * s, cy), (cx + 6 * s, cy),
                     dxfattribs={"layer": layer})

    if label:
        txt_h = 2.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + 6 * s, cy)


# ══════════════════════════════════════════════════════════
#  消防设施
# ══════════════════════════════════════════════════════════

def draw_fire_hydrant(msp, center, h_type: str = "indoor",
                       scale: float = 100.0,
                       label: str = "",
                       layer: str = "消防",
                       tracker=None):
    """消火栓符号。

    参数:
        h_type: "indoor"室内 / "outdoor"室外地上 / "underground"地下式
    """
    s = scale
    cx, cy = _r(*center)
    r = 6.0 * s

    if h_type == "indoor":
        # 室内：矩形 + 内三角
        w, h = 10.0 * s, 12.0 * s
        msp.add_lwpolyline(
            [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
             (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
            close=True, dxfattribs={"layer": layer})
        tri = [(cx, cy - 3 * s), (cx - 3 * s, cy + 3 * s),
               (cx + 3 * s, cy + 3 * s)]
        msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})
        # 水带弯曲线
        msp.add_line((cx - 2 * s, cy + 5 * s), (cx + 0, cy + 3 * s),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((cx + 0, cy + 3 * s), (cx + 2 * s, cy + 1 * s),
                     dxfattribs={"layer": "细实线"})

    elif h_type == "outdoor":
        # 室外地上：三角
        tri = [(cx, cy + r), (cx - r, cy - r), (cx + r, cy - r)]
        try:
            msp.add_solid(tri + [tri[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})

    elif h_type == "underground":
        # 地下式：半填充三角
        tri = [(cx, cy + r), (cx - r, cy - r), (cx + r, cy - r)]
        msp.add_lwpolyline(tri, close=True, dxfattribs={"layer": layer})
        msp.add_line((cx, cy + r * 0.3), (cx, cy - r * 0.5),
                     dxfattribs={"layer": layer})

    if label:
        txt_h = 2.2 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 4 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (cx + r, cy - r - 6 * s)


def draw_sprinkler(msp, center, sp_type: str = "pendant",
                    scale: float = 100.0,
                    label: str = "",
                    params: dict = None,
                    layer: str = "消防",
                    tracker=None):
    """喷淋头符号。

    参数:
        sp_type: "pendant"下垂型 / "upright"直立型 / "sidewall"边墙型 /
                 "concealed"隐蔽型
        params: {"K":"80","temp":"68°C","coverage":"12m²",...}
    """
    s = scale
    cx, cy = _r(*center)
    r = 3.5 * s

    # 圆
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    if sp_type == "pendant":
        # 下垂：中心点
        try:
            msp.add_solid([(cx - r * 0.5, cy - r * 0.5),
                           (cx + r * 0.5, cy - r * 0.5),
                           (cx + r * 0.5, cy + r * 0.5),
                           (cx - r * 0.5, cy + r * 0.5)],
                          dxfattribs={"layer": layer})
        except Exception as _e:
            print(f'[WARNING] plumbing.py: {_e}')

    if label:
        txt_h = 2.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((cx, cy - r - 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        cy_p = cy - r - 3 * s - 2.0 * s
        for key, val in params.items():
            t = msp.add_text(f"{key}:{val}", dxfattribs={
                "layer": "文字", "height": 1.8 * s, "style": "ENG",
            })
            t.set_placement((cx, cy_p),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            cy_p -= 2.2 * s

    return (cx + r, cy - r - 5 * s)


# ══════════════════════════════════════════════════════════
#  给排水系统图（轴测/展开）
# ══════════════════════════════════════════════════════════

def draw_plumbing_riser(msp, origin, floors: List[dict],
                         pipe_types: List[str] = None,
                         scale: float = 100.0,
                         label: str = "",
                         layer: str = "给水管",
                         tracker=None):
    """给排水立管系统图。

    参数:
        origin: 底部起点
        floors: 楼层列表 [{"name":"1F","el":0}, {"name":"2F","el":3.6}, ...]
        pipe_types: 立管类型 ["cold","hot","drain","vent","fire"]
    """
    s = scale
    ox, oy = _r(*origin)
    floor_h = 50.0 * s  # 层间高度（图纸 mm）
    pipe_sp = 15.0 * s  # 立管横向间距

    if pipe_types is None:
        pipe_types = ["cold", "drain"]

    # 各立管竖线
    pipe_x = {}
    for i, ptype in enumerate(pipe_types):
        px = ox + pipe_sp * i
        pipe_x[ptype] = px
        top_y = oy + floor_h * (len(floors) - 1)

        layer_name = {"cold": "给水管", "hot": "热水管",
                       "drain": "排水管", "vent": "通气管",
                       "fire": "消防管", "rain": "雨水管"}.get(ptype, "给水管")
        msp.add_line((px, oy), (px, top_y + 10 * s),
                     dxfattribs={"layer": layer_name})

        # 立管编号
        t = msp.add_text(ptype.upper(), dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((px, top_y + 13 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # 楼层标高 + 支管接口
    for fi, floor in enumerate(floors):
        fy = oy + floor_h * fi
        name = floor.get("name", f"{fi+1}F")
        el_val = floor.get("el", fi * 3.6)

        # 标高线
        msp.add_line((ox - 20 * s, fy), (ox + pipe_sp * len(pipe_types) + 5 * s, fy),
                     dxfattribs={"layer": "细实线-尺寸"})

        # 标高值
        t = msp.add_text(f"{el_val:.3f}", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((ox - 22 * s, fy + 1.5 * s),
                        align=TextEntityAlignment.MIDDLE_RIGHT)

        # 楼层标注
        t2 = msp.add_text(name, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ",
        })
        t2.set_placement((ox - 30 * s, fy),
                         align=TextEntityAlignment.MIDDLE_RIGHT)

        # 支管口（在立管上标记）
        for ptype in pipe_types:
            px = pipe_x[ptype]
            if ptype in ("cold", "hot", "fire"):
                # 冷水/热水/消防：横支管
                msp.add_line((px, fy), (px + 8 * s, fy),
                             dxfattribs={"layer": "给水管"})
            elif ptype in ("drain", "vent", "rain"):
                # 排水：Y形三通标记
                msp.add_line((px, fy), (px + 4 * s, fy + 3 * s),
                             dxfattribs={"layer": "排水管"})
                msp.add_line((px, fy), (px + 4 * s, fy - 3 * s),
                             dxfattribs={"layer": "排水管"})

    # 系统标注
    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ",
        })
        t.set_placement((ox + pipe_sp * (len(pipe_types) - 1) / 2, oy - 8 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(ox - 35 * s, oy - 10 * s,
                         ox + pipe_sp * len(pipe_types) + 15 * s,
                         oy + floor_h * len(floors) + 20 * s, margin=40)

    return (ox + pipe_sp * len(pipe_types), oy + floor_h * len(floors))

# ══════ v1.5+ 给排水增补：水泵/水箱/检查井/化粪池/雨水口/管道支架 ══════
def draw_water_pump(msp,origin,diameter=0.3,length=0.8,pump_type="离心",flow=50,head=30,scale=100.0,label="",layer="设备",tracker=None):
    s=scale*3;ox,oy=_r(*origin);D=diameter*s;L=length*s
    msp.add_lwpolyline([(ox,oy),(ox+L,oy),(ox+L,oy+D),(ox,oy+D)],close=True,dxfattribs={"layer":layer})
    msp.add_circle((ox+L*0.3,oy+D/2),D*0.3,dxfattribs={"layer":"细实线"})
    t=msp.add_text(f"Q={flow}m³/h H={head}m",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"});t.set_placement((ox+L/2,oy-3*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+L/2,oy+D+4*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_water_tank(msp,origin,width=4.0,length=6.0,height=3.0,capacity=72.0,scale=100.0,label="",layer="设备",tracker=None):
    s=scale;ox,oy=_r(*origin);w=width*s;l=length*s;H=height*s
    msp.add_lwpolyline([(ox,oy),(ox+w,oy),(ox+w,oy+l),(ox,oy+l)],close=True,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(ox+1*s,oy+1*s),(ox+w-1*s,oy+1*s),(ox+w-1*s,oy+l-1*s),(ox+1*s,oy+l-1*s)],close=True,dxfattribs={"layer":"细实线"})
    t=msp.add_text(f"V={capacity:.1f}m³",dxfattribs={"layer":"文字","height":3*s,"style":"HZ"});t.set_placement((ox+w/2,oy+l/2),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+w/2,oy+l+5*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_manhole(msp,origin,diameter=1.0,depth=2.5,pipe_in=0.3,pipe_out=0.3,scale=100.0,label="",layer="检查井",tracker=None):
    s=scale*2;ox,oy=_r(*origin);D=diameter*s;H=depth*s;di=pipe_in*s;do=pipe_out*s
    msp.add_circle((ox+D/2,oy+H),D/2,dxfattribs={"layer":layer})
    msp.add_line((ox,oy+H),(ox+D,oy+H),dxfattribs={"layer":layer})
    msp.add_line((ox,oy),(ox,oy+H+D/4),dxfattribs={"layer":layer})
    msp.add_line((ox+D,oy),(ox+D,oy+H+D/4),dxfattribs={"layer":layer})
    msp.add_line((ox-D/2-2*s,oy+H-D/4),(ox-1*s,oy+H-D/4),dxfattribs={"layer":"粗实线"})
    msp.add_line((ox+D+1*s,oy+H-D/4),(ox+D+D/2+2*s,oy+H-D/4),dxfattribs={"layer":"粗实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+D/2,oy+H+D+3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_septic_tank(msp,origin,length=6.0,width=2.5,depth=2.0,compartments=3,scale=100.0,label="",layer="设备",tracker=None):
    s=scale;ox,oy=_r(*origin);L=length*s;W=width*s;D=depth*s
    msp.add_lwpolyline([(ox,oy),(ox+L,oy),(ox+L,oy-W),(ox,oy-W)],close=True,dxfattribs={"layer":layer})
    for i in range(1,compartments):
        cx=ox+L*i/compartments;msp.add_line((cx,oy),(cx,oy-W),dxfattribs={"layer":"细实线"})
    for i in range(compartments):
        t=msp.add_text(f"{i+1}格",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"})
        t.set_placement((ox+L*(i+0.5)/compartments,oy-W/2),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+L/2,oy-W-5*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_rain_inlet(msp,origin,width=0.6,length=0.4,scale=100.0,label="",layer="雨水口",tracker=None):
    s=scale*5;ox,oy=_r(*origin);w=width*s;l=length*s
    msp.add_lwpolyline([(ox,oy),(ox+w,oy),(ox+w,oy+l),(ox,oy+l)],close=True,dxfattribs={"layer":layer})
    for i in range(3):msp.add_line((ox,oy+l*i/3),(ox+w,oy+l*i/3),dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2*s,"style":"HZ"});t.set_placement((ox+w/2,oy+l+3*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_pipe_support(msp,origin,pipe_d=0.3,support_w=0.2,support_h=0.5,scale=100.0,label="",layer="管支架",tracker=None):
    s=scale*3;ox,oy=_r(*origin);pd=pipe_d*s;sw=support_w*s;sh=support_h*s
    msp.add_line((ox,oy),(ox,oy-sh),dxfattribs={"layer":layer})
    msp.add_line((ox-sw,oy-sh),(ox+sw+pd,oy-sh),dxfattribs={"layer":layer})
    msp.add_circle((ox+pd/2,oy+pd/2+1*s),pd/2,dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"});t.set_placement((ox+pd/2,oy+pd+3*s),align=TextEntityAlignment.MIDDLE_CENTER)


def draw_water_supply_system(msp, origin, floors=3, floor_h=3.0, pipe_d=100,
                             scale=100.0, label="给水系统图", layer="给水", tracker=None):
    """给水系统轴侧示意图。竖管+各层支管+设备符号。"""
    s=scale;ox,oy=_r(*origin);fh=floor_h*s;pd=pipe_d*s
    rh=fh*floors;msp.add_line((ox,oy),(ox,oy+rh),dxfattribs={"layer":layer})
    for i in range(floors):
        ly=oy+(i+0.5)*fh;ex=ox+4*s+pd
        msp.add_line((ox,ly),(ex,ly),dxfattribs={"layer":layer})
        msp.add_circle((ex+pd,ly),pd/1.5,dxfattribs={"layer":"细实线"})
        t=msp.add_text(f"{i+1}F",dxfattribs={"layer":"文字","height":2.2*s,"style":"ENG"})
        t.set_placement((ox-2*s,ly),align=TextEntityAlignment.MIDDLE_RIGHT)
    msp.add_circle((ox,oy+rh+1*s),pd/1.2,dxfattribs={"layer":layer})
    msp.add_line((ox-2*s,oy+rh),(ox+2*s,oy+rh),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+5*s,oy+rh+3*s),align=TextEntityAlignment.MIDDLE_LEFT)
    return (ox+6*s+pd,oy+rh+5*s)


def draw_drainage_system(msp, origin, floors=3, floor_h=3.0, pipe_d=150,
                         scale=100.0, label="排水系统图", layer="排水", tracker=None):
    """排水系统轴侧示意图。通气管+竖管+各层支管。"""
    s=scale;ox,oy=_r(*origin);fh=floor_h*s;pd=pipe_d*s
    rh=fh*floors;vent_h=fh*0.8
    msp.add_line((ox,oy-1*s),(ox,oy+rh+vent_h),dxfattribs={"layer":layer})
    msp.add_line((ox+1*s,oy+rh+vent_h),(ox+1*s,oy+rh+vent_h+2*s),dxfattribs={"layer":"细实线"})
    for i in range(floors):
        ly=oy+(i+0.3)*fh;ex=ox+4*s+pd
        msp.add_line((ox,ly),(ex,ly),dxfattribs={"layer":layer})
        t=msp.add_text(f"{i+1}F",dxfattribs={"layer":"文字","height":2.2*s,"style":"ENG"})
        t.set_placement((ox-2*s,ly),align=TextEntityAlignment.MIDDLE_RIGHT)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+5*s,oy+rh+vent_h+4*s),align=TextEntityAlignment.MIDDLE_LEFT)
    return (ox+6*s+pd,oy+rh+vent_h+6*s)
