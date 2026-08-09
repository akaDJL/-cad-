"""模块 19 —— 悬挂式谷物条播机（种箱 + 排种行 + 机架）。

出两个视图，均为参数化：
  * ``draw_seeder``       —— 后视图（正视）：种箱全宽、机架横梁、n 行开沟器；
  * ``draw_seeder_side``  —— 侧视图：种箱剖面、排种器、开沟器、镇压轮、悬挂架。

复用 envcad：GB/T 17450 图层、仿宋 GB2312 文字样式、``standards.dim`` 标注、
``standards.annotate.draw_leader`` 指引线、``_common.wheel`` 轮子画法。

标准依据：
  * GB/T 14689—2008 图纸幅面 / GB/T 4457.4—2002 图线
  * GB/T 9478—2005 谷物条播机 试验方法  # TODO: verify against GB/T 9478
    （行距、播种深度、排种均匀性变异系数等；envcad standards_kb.json
     未覆盖农机行业，默认行距 150mm 仅为常用值，需按作物核定）
  * GB/T 6973—2005 单粒（精密）播种机试验方法  # TODO: verify against GB/T 6973（2005版现行）
"""
from __future__ import annotations

from typing import Dict

from ._common import (
    L_CENTER, L_HIDDEN, L_MED, L_THICK, L_THIN,
    cross_center, dim_h, dim_v, ground_line, hatch_solid, label, leader,
    poly, rect, wheel,
)

#: 24 行悬挂式谷物条播机默认参数（实物 mm）
DEFAULTS: Dict[str, float] = {
    "n_rows": 12.0,             # 排种行数
    "row_spacing": 150.0,       # 行距（GB/T 9478 试验按名义行距核定）
    "hopper_h": 620.0,          # 种箱高度
    "hopper_top_w": 520.0,      # 种箱上口宽（侧视）
    "hopper_bot_w": 180.0,      # 种箱下口宽（侧视）
    "frame_h": 140.0,           # 机架方管高
    "frame_y": 780.0,           # 机架下平面离地高
    "opener_h": 520.0,          # 开沟器立柱高
    "opener_w": 130.0,          # 开沟器铧宽
    "sow_depth": 40.0,          # 播种深度
    "wheel_d": 620.0,           # 地轮/镇压轮直径
    "hitch_h": 900.0,           # 悬挂上拉杆点高
    "seed_fill": 0.65,          # 种箱装种高度比（示意剖面）
}


def _machine_width(p) -> float:
    """按行数与行距计算工作幅宽（mm）。"""
    return (p["n_rows"] - 1) * p["row_spacing"] + p["row_spacing"]


def _draw_opener_front(msp, cx, y_ground, p):
    """后视图中的单个开沟器：立柱 + 双圆盘/铧式尖（细中实线）。"""
    y_top = y_ground + p["frame_y"]
    msp.add_line((cx, y_top), (cx, y_ground + p["sow_depth"]),
                 dxfattribs={"layer": L_MED})
    w = p["opener_w"] / 2
    poly(msp, [(cx - w, y_ground + p["sow_depth"] + 160),
               (cx + w, y_ground + p["sow_depth"] + 160),
               (cx, y_ground - p["sow_depth"])],
         layer=L_THICK, closed=True)


def draw_seeder(msp, x: float, y: float, scale: float = 25.0,
                with_dims: bool = True, with_labels: bool = True,
                tracker=None, **params) -> Dict[str, object]:
    """绘制条播机**后视图**（种箱 + 机架 + n 行开沟器）。

    Args:
        msp: ezdxf modelspace
        x, y: 插入基点 —— 机具左端与**地平线**的交点（实物 mm）
        scale: 出图比例倒数
        **params: 覆盖 :data:`DEFAULTS`，如 n_rows=16, row_spacing=125

    Returns:
        dict：``bbox``、``width``（幅宽）、``row_x``（各行开沟器 X 坐标）
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})
    n = int(p["n_rows"])
    width = _machine_width(p)

    ground_line(msp, x - 400, x + width + 400, y, scale, n_ticks=28)

    # ── 机架横梁（方管）──
    fy0 = y + p["frame_y"]
    rect(msp, x, fy0, x + width, fy0 + p["frame_h"], layer=L_THICK)
    msp.add_line((x, fy0 + p["frame_h"] * 0.5), (x + width, fy0 + p["frame_h"] * 0.5),
                 dxfattribs={"layer": L_THIN})

    # ── 种箱（全宽，上宽下窄）──
    hy0 = fy0 + p["frame_h"]
    hy1 = hy0 + p["hopper_h"]
    poly(msp, [(x + 60, hy0), (x + width - 60, hy0),
               (x + width, hy1), (x, hy1)], layer=L_THICK, closed=True)
    # 种子料位线（细实线）
    msp.add_line((x + 40, hy0 + p["hopper_h"] * p["seed_fill"]),
                 (x + width - 40, hy0 + p["hopper_h"] * p["seed_fill"]),
                 dxfattribs={"layer": L_THIN})
    # 箱盖
    rect(msp, x - 40, hy1, x + width + 40, hy1 + 60, layer=L_MED)

    # ── 排种行 ──
    row_x = [x + p["row_spacing"] * (0.5 + i) for i in range(n)]
    for cx in row_x:
        # 输种管（虚线，箱后不可见）
        msp.add_line((cx, hy0), (cx, fy0 + p["frame_h"]),
                     dxfattribs={"layer": L_HIDDEN})
        _draw_opener_front(msp, cx, y, p)

    # ── 两端地轮 ──
    for wx in (x + 120, x + width - 120):
        wheel(msp, wx, y + p["wheel_d"] / 2, p["wheel_d"], scale, n_lugs=10)

    # ── 三点悬挂架（中部）──
    mid = x + width / 2
    poly(msp, [(mid - 320, fy0 + p["frame_h"]), (mid, y + p["hitch_h"] + 420),
               (mid + 320, fy0 + p["frame_h"])], layer=L_MED)

    # ── 尺寸 ──
    if with_dims:
        dim_h(msp, (x, y), (x + width, y), scale, offset=24,
              text=f"{width:.0f}", tracker=tracker)
        dim_h(msp, (row_x[0], y), (row_x[1], y), scale, offset=14,
              text=f"{p['row_spacing']:.0f}", tracker=tracker)
        dim_v(msp, (x, hy0), (x, hy1), scale, offset=10,
              text=f"{p['hopper_h']:.0f}", tracker=tracker)
        dim_v(msp, (x + width, y), (x + width, fy0), scale, offset=-10,
              text=f"{p['frame_y']:.0f}", tracker=tracker)

    if with_labels:
        leader(msp, (mid, hy1), f"种箱（{n}行）", scale, bend=(6, 7),
               tracker=tracker)
        leader(msp, (row_x[0], y + p["sow_depth"] + 80), "铧式开沟器", scale,
               bend=(-6, -7), text_dir="left", tracker=tracker)
        leader(msp, (mid, fy0 + p["frame_h"] / 2), "机架横梁", scale,
               bend=(7, -6), tracker=tracker)
        leader(msp, (x + 120, y + p["wheel_d"]), "地轮（排种传动）", scale,
               bend=(-7, 6), text_dir="left", tracker=tracker)
        label(msp, f"行距 {p['row_spacing']:.0f}×{n}行  播深 {p['sow_depth']:.0f}",
              (mid, y - 9 * scale), scale, height=3.0, tracker=tracker)

    return {
        "bbox": (x - 200, y, x + width + 200, hy1 + 60),
        "width": width,
        "row_x": row_x,
        "params": p,
    }


def draw_seeder_side(msp, x: float, y: float, scale: float = 25.0,
                     with_labels: bool = True, tracker=None,
                     **params) -> Dict[str, object]:
    """绘制条播机**侧视图**（种箱剖面 + 排种器 + 开沟器 + 镇压轮）。

    Args:
        x, y: 插入基点 —— 机具最前端（悬挂侧）与地平线的交点
    """
    p = dict(DEFAULTS)
    p.update({k: float(v) for k, v in params.items() if k in DEFAULTS})

    depth = p["hopper_top_w"] + 900.0     # 侧视总长
    ground_line(msp, x - 300, x + depth + 500, y, scale, n_ticks=16)

    # 机架纵梁
    fy0 = y + p["frame_y"]
    rect(msp, x + 200, fy0, x + depth, fy0 + p["frame_h"], layer=L_THICK)

    # 种箱剖面（梯形）
    hx0 = x + 380
    hy0 = fy0 + p["frame_h"]
    hy1 = hy0 + p["hopper_h"]
    top_w, bot_w = p["hopper_top_w"], p["hopper_bot_w"]
    pts = [(hx0 + (top_w - bot_w) / 2, hy0), (hx0 + (top_w + bot_w) / 2, hy0),
           (hx0 + top_w, hy1), (hx0, hy1)]
    poly(msp, pts, layer=L_THICK, closed=True)
    hatch_solid(msp, [(hx0 + 20, hy0 + 30),
                      (hx0 + top_w - 20, hy0 + 30),
                      (hx0 + top_w - 30, hy0 + p["hopper_h"] * p["seed_fill"]),
                      (hx0 + 30, hy0 + p["hopper_h"] * p["seed_fill"])],
                 layer=L_THIN, pattern="AR-SAND", pattern_scale=8.0)

    # 外槽轮排种器（箱底小圆）
    mx, my = hx0 + top_w / 2, hy0 - 60
    msp.add_circle((mx, my), 90, dxfattribs={"layer": L_MED})
    cross_center(msp, mx, my, 90, scale)

    # 输种管（点画线走向 → 开沟器）
    ox = x + depth - 260
    poly(msp, [(mx, my - 90), (mx + 80, fy0 - 100), (ox, y + p["sow_depth"] + 200)],
         layer=L_THIN)

    # 开沟器 + 覆土器
    poly(msp, [(ox - 60, fy0), (ox + 60, fy0),
               (ox + 60, y + p["sow_depth"] + 150),
               (ox, y - p["sow_depth"]),
               (ox - 60, y + p["sow_depth"] + 150)],
         layer=L_THICK, closed=True)

    # 镇压轮
    wcx = x + depth + 260
    wheel(msp, wcx, y + p["wheel_d"] / 2, p["wheel_d"], scale, n_lugs=10)
    poly(msp, [(x + depth, fy0 + p["frame_h"] / 2), (wcx, y + p["wheel_d"] / 2)],
         layer=L_MED)

    # 三点悬挂
    poly(msp, [(x + 200, fy0 + p["frame_h"]), (x, y + p["hitch_h"] + 380),
               (x + 200, fy0)], layer=L_MED)
    msp.add_line((x, y + p["hitch_h"] + 380), (x - 260, y + p["hitch_h"] + 380),
                 dxfattribs={"layer": L_MED})
    msp.add_line((x + 200, fy0), (x - 260, fy0 - 220),
                 dxfattribs={"layer": L_MED})

    # 播深标注
    msp.add_line((ox - 500, y - p["sow_depth"]), (ox + 500, y - p["sow_depth"]),
                 dxfattribs={"layer": L_CENTER})
    dim_v(msp, (ox + 420, y - p["sow_depth"]), (ox + 420, y), scale,
          offset=-4, text=f"播深{p['sow_depth']:.0f}", tracker=tracker)

    if with_labels:
        leader(msp, (mx, my), "外槽轮排种器", scale, bend=(-7, -7),
               text_dir="left", tracker=tracker)
        leader(msp, (wcx, y + p["wheel_d"]), "镇压轮", scale, bend=(6, 6),
               tracker=tracker)

    return {"bbox": (x - 300, y - p["sow_depth"], x + depth + 600, hy1),
            "params": p}
