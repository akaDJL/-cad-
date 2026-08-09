"""固体废物处理处置制图 v1.0。

引用标准（均为现行最新版）：
  GB 18598-2019     危险废物填埋污染控制标准（代替GB 18598-2001）
  GB 18485-2014     生活垃圾焚烧污染控制标准（含2019修改单）
  GB/T 50869-2013   生活垃圾卫生填埋处理技术规范（代替CJJ 113-2007，2025版已发布）
  GB 16889-2008     生活垃圾填埋场污染控制标准
  HJ 2035-2013      固体废物处理处置工程技术导则
  HJ 1164-2021      污染土壤修复工程技术规范 异位热脱附
  HJ 276-2007       医疗废物高温蒸汽集中处理工程技术规范

卫生填埋场防渗剖面、渗滤液收集导排、焚烧炉工艺术、
好氧堆肥发酵仓、厌氧消化罐、分选转运车间。

纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri  # v1.5: 统一工具函数


# ══════════════════════════════════════════════════════════
#  卫生填埋场
# ══════════════════════════════════════════════════════════

def draw_landfill_section(msp, origin, length=50.0, depth=12.0,
                          base_width=20.0, liner_type="composite",
                          scale=100.0, label="", params=None,
                          layer="填埋场", tracker=None):
    """卫生填埋场剖面图。

    参数:
        length: 填埋场底部长度 m
        depth: 填埋深度 m
        base_width: 底宽 m
        liner_type: "clay"黏土防渗 / "geomembrane"HDPE膜 / "composite"复合防渗 / "gcl"GCL
        params: {"capacity":"50万m³","area":"5万m²","slope":"1:3",
                  "liner_thickness":"2mm HDPE+600mm黏土","leachate":"120m³/d",...}
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; D = depth * s; BW = base_width * s

    left_toe = (ox, oy)
    left_top = (ox - D * 3, oy + D)
    right_toe = (ox + BW, oy)
    right_top = (ox + BW + D * 3, oy + D)

    msp.add_lwpolyline(
        [left_top, (ox + BW + D * 3, oy + D),
         right_top, right_toe, left_toe, left_top],
        close=False, dxfattribs={"layer": layer})

    # 防渗层（底部）
    liner_y = oy - 1.5 * s
    msp.add_line((ox - 2 * s, liner_y), (ox + BW + 2 * s, liner_y),
                 dxfattribs={"layer": layer, "lineweight": 50})

    if liner_type == "composite":
        msp.add_line((ox - 2 * s, liner_y - 1 * s),
                     (ox + BW + 2 * s, liner_y - 1 * s),
                     dxfattribs={"layer": "细实线"})
        msp.add_line((ox - 2 * s, liner_y - 2 * s),
                     (ox + BW + 2 * s, liner_y - 2 * s),
                     dxfattribs={"layer": "细实线"})
    elif liner_type == "geomembrane":
        msp.add_line((ox - 2 * s, liner_y - 1 * s),
                     (ox + BW + 2 * s, liner_y - 1 * s),
                     dxfattribs={"layer": "细实线"})

    # 渗滤液导排管
    pipe_y = oy + 0.5 * s
    msp.add_line((ox + 2 * s, pipe_y), (ox + BW - 2 * s, pipe_y),
                 dxfattribs={"layer": "管道-污水", "lineweight": 35})
    msp.add_lwpolyline(
        [(ox + 2 * s, pipe_y - 1 * s),
         (ox + BW - 2 * s, pipe_y - 1 * s),
         (ox + BW - 2 * s, pipe_y + 2 * s),
         (ox + 2 * s, pipe_y + 2 * s)],
        close=True, dxfattribs={"layer": "细实线", "linetype": "DASHED"})

    # 导气井
    well_x = ox + BW / 2
    msp.add_line((well_x, pipe_y), (well_x, oy + D - 2 * s),
                 dxfattribs={"layer": "管道-加药", "lineweight": 35})
    msp.add_circle((well_x, oy + D - 2 * s), 2 * s,
                   dxfattribs={"layer": "设备"})

    # 覆盖土层
    cover_y = oy + D
    msp.add_line((left_top[0], cover_y + 1 * s),
                 (right_top[0], cover_y + 1 * s),
                 dxfattribs={"layer": layer})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + BW / 2, oy + D + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + D + 6 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + BW / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + BW + D * 3, oy + D)


def draw_leachate_collection(msp, origin, n_wells=3, well_spacing=30.0,
                              scale=100.0, label="", params=None,
                              layer="渗滤液", tracker=None):
    """渗滤液收集导排系统平面图。

    参数:
        n_wells: 导排井数量
        well_spacing: 井间距 m
        params: {"pipe_dn":"DN200 HDPE","slope":"2%","tank":"500m³",...}
    """
    s = scale; ox, oy = _r(*origin)
    sp = well_spacing * s

    main_y = oy
    total_w = sp * (n_wells - 1)
    msp.add_line((ox, main_y), (ox + total_w, main_y),
                 dxfattribs={"layer": "管道-污水", "lineweight": 50})

    for i in range(n_wells):
        wx = ox + sp * i
        msp.add_circle((wx, main_y), 3 * s, dxfattribs={"layer": layer})
        msp.add_line((wx, main_y - 3 * s), (wx, main_y + 3 * s),
                     dxfattribs={"layer": layer})
        t = msp.add_text(f"W{i+1}", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "ENG"})
        t.set_placement((wx, main_y + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        if i < n_wells - 1:
            branch_y = main_y - 8 * s
            msp.add_line((wx, main_y - 3 * s), (wx, branch_y),
                         dxfattribs={"layer": "管道-污水", "lineweight": 35})
            msp.add_line((wx, branch_y), (wx + sp, branch_y),
                         dxfattribs={"layer": "管道-污水", "lineweight": 35})
            msp.add_line((wx + sp, branch_y), (wx + sp, main_y - 3 * s),
                         dxfattribs={"layer": "管道-污水", "lineweight": 35})

    tank_x = ox + total_w + 10 * s
    tank_w, tank_h = 12 * s, 8 * s
    msp.add_lwpolyline(
        [(tank_x, main_y - tank_h / 2),
         (tank_x + tank_w, main_y - tank_h / 2),
         (tank_x + tank_w, main_y + tank_h / 2),
         (tank_x, main_y + tank_h / 2)],
        close=True, dxfattribs={"layer": layer})
    t = msp.add_text("调节池", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((tank_x + tank_w / 2, main_y),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    msp.add_line((ox + total_w, main_y), (tank_x, main_y),
                 dxfattribs={"layer": "管道-污水", "lineweight": 50})
    _tri(msp, (tank_x, main_y), (1, 0), s, "管道-污水")

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + total_w / 2, main_y + 10 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = main_y + 10 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + total_w / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (tank_x + tank_w, main_y)


# ══════════════════════════════════════════════════════════
#  垃圾焚烧
# ══════════════════════════════════════════════════════════

def draw_incinerator_flow(msp, origin, f_type="grate",
                           scale=100.0, label="", params=None,
                           layer="工艺", tracker=None):
    """垃圾焚烧工艺流程图。

    参数:
        f_type: "grate"炉排炉 / "fluidized"流化床 / "rotary"回转窑
        params: {"capacity":"500t/d","temp":"850℃","residence":">2s",...}
    """
    s = scale; ox, oy = _r(*origin); spacing = 28 * s

    stages = [
        ("垃圾坑", "P-101"),
        ("给料", "F-201"),
        ("焚烧炉", "I-301"),
        ("余热锅炉", "B-401"),
        ("烟气净化", "APC-501"),
        ("烟囱", "S-601"),
    ]

    bh = 14 * s; bw = 20 * s

    for i, (name, tag) in enumerate(stages):
        cx = ox + spacing * i

        if i == 2 and f_type == "grate":
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2 - 3 * s, oy + bh / 2),
                 (cx - bw / 2 + 3 * s, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})
            for j in range(4):
                lx = cx - bw / 2 + 3 * s + (bw - 6 * s) * (j + 0.5) / 4
                msp.add_line((lx, oy - bh / 2 + 1 * s),
                             (lx, oy + bh / 2 - 1 * s),
                             dxfattribs={"layer": "细实线"})
        elif i == 2 and f_type == "fluidized":
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2),
                 (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})
            for j in range(5):
                fx = cx - bw / 2 + bw * (j + 0.5) / 5
                msp.add_line((fx, oy - bh / 2 + 2 * s),
                             (fx, oy + bh / 2 - 2 * s),
                             dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        elif i == 2 and f_type == "rotary":
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2 + 2 * s),
                 (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2),
                 (cx - bw / 2, oy + bh / 2 - 2 * s)],
                close=True, dxfattribs={"layer": layer})
        elif i == 5:
            msp.add_lwpolyline(
                [(cx, oy + bh / 2),
                 (cx - 4 * s, oy - bh / 2),
                 (cx + 4 * s, oy - bh / 2)],
                close=True, dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2),
                 (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})

        t = msp.add_text(name, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((cx, oy + 1.5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)
        t2 = msp.add_text(tag, dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "ENG"})
        t2.set_placement((cx, oy - 2 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)

        if i < len(stages) - 1:
            nx = ox + spacing * (i + 1)
            msp.add_line((cx + bw / 2, oy), (nx - bw / 2, oy),
                         dxfattribs={"layer": layer})
            _tri(msp, (nx - bw / 2, oy), (1, 0), s, layer)

    # 渗滤液回喷
    ret_y = oy + bh / 2 + 6 * s
    msp.add_line((ox + bw / 2, ret_y),
                 (ox + spacing * 4 + bw / 2, ret_y),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    msp.add_line((ox + spacing * 4 + bw / 2, ret_y),
                 (ox + spacing * 4 + bw / 2, oy + bh / 2),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})
    t = msp.add_text("渗滤液回喷", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + spacing * 2, ret_y + 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + spacing * 2.5, oy + bh / 2 + 12 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy - bh / 2 - 5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + spacing * 2.5, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + spacing * len(stages), oy)


def draw_incinerator_section(msp, origin, capacity=500, scale=100.0,
                              label="", params=None,
                              layer="焚烧炉", tracker=None):
    """焚烧炉断面图。

    参数:
        capacity: 处理量 t/d
        params: {"temp":"850℃","residence":">2s","grate_type":"往复式",...}
    """
    s = scale; ox, oy = _r(*origin)
    fw = 30 * s; fh = 20 * s

    msp.add_lwpolyline(
        [(ox, oy), (ox + fw, oy),
         (ox + fw - 3 * s, oy + fh),
         (ox + 3 * s, oy + fh)],
        close=True, dxfattribs={"layer": layer})

    grate_y = oy + fh * 0.3
    n_grates = 5
    for i in range(n_grates):
        gx1 = ox + 3 * s + (fw - 6 * s) * i / n_grates
        gx2 = ox + 3 * s + (fw - 6 * s) * (i + 1) / n_grates
        gy1 = grate_y + (fh * 0.4) * i / n_grates
        gy2 = grate_y + (fh * 0.4) * (i + 1) / n_grates
        msp.add_line((gx1, gy1), (gx2, gy2),
                     dxfattribs={"layer": layer, "lineweight": 35})
        msp.add_line((gx1, gy1), (gx1, gy1 - 2 * s),
                     dxfattribs={"layer": "细实线"})

    t = msp.add_text("850℃+", dxfattribs={
        "layer": "文字", "height": 2.5 * s, "style": "ENG"})
    t.set_placement((ox + fw / 2, oy + fh * 0.7),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    for side in [(-3 * s, 1), (fw + 3 * s, -1)]:
        ax = ox + fw / 2 + side[0]
        ay = oy + fh * 0.6
        msp.add_line((ax, ay), (ax + side[1] * 3 * s, ay),
                     dxfattribs={"layer": layer})
        _tri(msp, (ax, ay), (side[1] * -1, 0), s, layer)
        t = msp.add_text("二次风", dxfattribs={
            "layer": "文字", "height": 1.8 * s, "style": "HZ"})
        t.set_placement((ax + side[1] * 5 * s, ay + 2 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    msp.add_line((ox + fw - 3 * s, oy),
                 (ox + fw + 5 * s, oy - 3 * s),
                 dxfattribs={"layer": layer})
    t = msp.add_text("炉渣", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + fw + 6 * s, oy - 1.5 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    msp.add_line((ox + fw / 2, oy + fh),
                 (ox + fw / 2, oy + fh + 5 * s),
                 dxfattribs={"layer": layer})
    t = msp.add_text("烟气→", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + fw / 2 + 4 * s, oy + fh + 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + fw / 2, oy + fh + 10 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy - 6 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + fw / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + fw + 8 * s, oy + fh)


# ══════════════════════════════════════════════════════════
#  好氧堆肥
# ══════════════════════════════════════════════════════════

def draw_composting(msp, origin, c_type="windrow",
                     length=30.0, width=5.0,
                     scale=100.0, label="", params=None,
                     layer="堆肥", tracker=None):
    """好氧堆肥设施图。

    参数:
        c_type: "windrow"条垛式 / "static"静态曝气 / "vessel"仓式 / "tunnel"隧道式
        params: {"volume":"500m³","period":"21d","temp":"55℃",
                  "aeration":"0.2m³/min·m³","moisture":"55%",...}
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; W = width * s

    if c_type == "windrow":
        msp.add_lwpolyline(
            [(ox, oy), (ox + L, oy), (ox + L / 2, oy + W * 0.7)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((ox - 2 * s, oy + W * 0.7 + 3 * s),
                     (ox + L + 2 * s, oy + W * 0.7 + 3 * s),
                     dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        t = msp.add_text("翻堆机", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + W * 0.7 + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    elif c_type == "static":
        msp.add_lwpolyline(
            [(ox, oy), (ox + L, oy), (ox + L, oy + W * 0.6),
             (ox, oy + W * 0.6)],
            close=True, dxfattribs={"layer": layer})
        msp.add_line((ox + 2 * s, oy - 1 * s),
                     (ox + L - 2 * s, oy - 1 * s),
                     dxfattribs={"layer": "管道-加药", "lineweight": 35})
        for i in range(int(L / (5 * s)) + 1):
            vx = ox + 5 * s * i
            msp.add_line((vx, oy - 1 * s), (vx, oy - 3 * s),
                         dxfattribs={"layer": "管道-加药"})
            _tri(msp, (vx, oy), (0, 1), s, "管道-加药")

    elif c_type == "vessel":
        r = W * 0.5
        msp.add_circle((ox + r, oy + r), r, dxfattribs={"layer": layer})
        msp.add_line((ox + r, oy + r - r), (ox + r, oy + r + r),
                     dxfattribs={"layer": layer, "lineweight": 35})
        msp.add_line((ox - 3 * s, oy + r),
                     (ox, oy + r), dxfattribs={"layer": layer})
        _tri(msp, (ox, oy + r), (1, 0), s, layer)
        msp.add_line((ox + 2 * r, oy + r),
                     (ox + 2 * r + 3 * s, oy + r),
                     dxfattribs={"layer": layer})
        _tri(msp, (ox + 2 * r + 3 * s, oy + r), (1, 0), s, layer)
        t1 = msp.add_text("进料", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t1.set_placement((ox - 5 * s, oy + r + 2 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)
        t2 = msp.add_text("出料", dxfattribs={
            "layer": "文字", "height": 2 * s, "style": "HZ"})
        t2.set_placement((ox + 2 * r + 6 * s, oy + r + 2 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)

    elif c_type == "tunnel":
        msp.add_lwpolyline(
            [(ox, oy), (ox + L, oy), (ox + L, oy + W),
             (ox, oy + W)],
            close=True, dxfattribs={"layer": layer})
        for i in range(1, 4):
            mx = ox + L * i / 4
            msp.add_line((mx, oy), (mx, oy + W),
                         dxfattribs={"layer": "细实线", "linetype": "DASHED"})
        phases = ["升温期", "高温期", "降温期", "腐熟期"]
        for i, ph in enumerate(phases):
            t = msp.add_text(ph, dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + L * (i + 0.5) / 4, oy + W / 2),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + W + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + W + 6 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + L / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + L, oy + W)


def draw_anaerobic_digester(msp, center, dia=10.0, height=15.0,
                             scale=100.0, label="", params=None,
                             layer="设备", tracker=None):
    """厌氧消化罐。

    参数:
        dia: 罐体直径 m
        height: 罐体高度 m
        params: {"volume":"800m³","HRT":"20d","temp":"35℃(中温)",
                  "biogas":"500m³/d","ts":"8%",...}
    """
    s = scale; cx, cy = _r(*center)
    r = dia * s / 2; H = height * s

    msp.add_lwpolyline(
        [(cx - r, cy), (cx - r, cy + H),
         (cx + r, cy + H), (cx + r, cy)],
        close=False, dxfattribs={"layer": layer})

    msp.add_ellipse((cx, cy), major_axis=(r, 0, 0), ratio=0.2,
                     dxfattribs={"layer": layer})

    msp.add_arc((cx, cy + H), radius=r, start_angle=0, end_angle=180,
                dxfattribs={"layer": layer})

    msp.add_line((cx, cy + H), (cx, cy + H * 0.3),
                 dxfattribs={"layer": layer, "lineweight": 35})
    msp.add_line((cx - r * 0.6, cy + H * 0.3),
                 (cx + r * 0.6, cy + H * 0.3),
                 dxfattribs={"layer": layer, "lineweight": 35})

    msp.add_line((cx - r - 4 * s, cy + H * 0.7),
                 (cx - r, cy + H * 0.7),
                 dxfattribs={"layer": "管道-污水"})
    _tri(msp, (cx - r, cy + H * 0.7), (1, 0), s, "管道-污水")

    msp.add_line((cx + r, cy + H * 0.2),
                 (cx + r + 4 * s, cy + H * 0.2),
                 dxfattribs={"layer": "管道-污水"})

    msp.add_line((cx, cy + H + r * 0.3),
                 (cx, cy + H + r * 0.3 + 5 * s),
                 dxfattribs={"layer": "管道-加药"})
    t = msp.add_text("沼气→", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((cx + 5 * s, cy + H + r * 0.3 + 4 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    msp.add_line((cx - r + 1 * s, cy + H * 0.5),
                 (cx + r - 1 * s, cy + H * 0.5),
                 dxfattribs={"layer": "细实线", "linetype": "DASHED"})

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3 * s, "style": "HZ"})
        t.set_placement((cx, cy + H + r * 0.3 + 10 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = cy - r * 0.2 - 4 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((cx, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (cx + r + 5 * s, cy + H + r * 0.3)


# ══════════════════════════════════════════════════════════
#  分选转运
# ══════════════════════════════════════════════════════════

def draw_sorting_line(msp, origin, stages, scale=100.0,
                       label="", layer="工艺", tracker=None):
    """垃圾分选工艺术流程图。

    stages: [{"label":"破袋","type":"bag_breaker"},
             {"label":"滚筒筛","type":"trommel"},
             {"label":"风选","type":"air_separator"},
             {"label":"磁选","type":"magnetic"},
             {"label":"涡电流","type":"eddy_current"},
             {"label":"人工分选","type":"manual"}]
    """
    s = scale; ox, oy = _r(*origin); spacing = 26 * s
    bw = 18 * s; bh = 12 * s

    for i, st in enumerate(stages):
        cx = ox + spacing * i
        stype = st.get("type", "")
        slabel = st.get("label", "")

        if stype == "trommel":
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2 + 2 * s),
                 (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2),
                 (cx - bw / 2, oy + bh / 2 - 2 * s)],
                close=True, dxfattribs={"layer": layer})
            msp.add_arc((cx, oy), radius=bw * 0.3,
                        start_angle=20, end_angle=160,
                        dxfattribs={"layer": "细实线"})
        elif stype == "magnetic":
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})
            msp.add_line((cx - 3 * s, oy + bh / 2),
                         (cx + 3 * s, oy + bh / 2),
                         dxfattribs={"layer": layer, "lineweight": 50})
            t = msp.add_text("N", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "ENG"})
            t.set_placement((cx, oy + bh / 2 + 2 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)
        elif stype == "air_separator":
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})
            for j in range(3):
                ay = oy - bh / 2 + bh * (j + 0.5) / 3
                msp.add_line((cx - bw / 2 - 3 * s, ay),
                             (cx - bw / 2, ay),
                             dxfattribs={"layer": layer})
                _tri(msp, (cx - bw / 2, ay), (1, 0), s, layer)
        elif stype == "manual":
            for j in range(3):
                bx = cx - bw / 2 + j * bw / 3
                msp.add_lwpolyline(
                    [(bx, oy - bh / 2),
                     (bx + bw / 3, oy - bh / 2),
                     (bx + bw / 3, oy + bh / 2),
                     (bx, oy + bh / 2)],
                    close=True, dxfattribs={"layer": layer})
        else:
            msp.add_lwpolyline(
                [(cx - bw / 2, oy - bh / 2), (cx + bw / 2, oy - bh / 2),
                 (cx + bw / 2, oy + bh / 2), (cx - bw / 2, oy + bh / 2)],
                close=True, dxfattribs={"layer": layer})

        t = msp.add_text(slabel, dxfattribs={
            "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
        t.set_placement((cx, oy),
                        align=TextEntityAlignment.MIDDLE_CENTER)

        if i < len(stages) - 1:
            nx = ox + spacing * (i + 1)
            msp.add_line((cx + bw / 2, oy), (nx - bw / 2, oy),
                         dxfattribs={"layer": layer})
            _tri(msp, (nx - bw / 2, oy), (1, 0), s, layer)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + spacing * (len(stages) - 1) / 2, oy + bh / 2 + 6 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    return (ox + spacing * len(stages), oy)


def draw_transfer_station(msp, origin, length=30.0, width=15.0,
                           scale=100.0, label="", params=None,
                           layer="转运站", tracker=None):
    """垃圾转运站平面图。

    参数:
        params: {"capacity":"300t/d","vehicles":"15辆/d",
                  "compress_type":"水平压缩","box":"20m³",...}
    """
    s = scale; ox, oy = _r(*origin)
    L = length * s; W = width * s

    msp.add_lwpolyline(
        [(ox, oy), (ox + L, oy), (ox + L, oy + W), (ox, oy + W)],
        close=True, dxfattribs={"layer": layer, "lineweight": 50})

    unload_w = L * 0.35
    msp.add_line((ox + unload_w, oy), (ox + unload_w, oy + W),
                 dxfattribs={"layer": layer})
    t = msp.add_text("卸料区", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ox + unload_w / 2, oy + W / 2),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    compress_w = L * 0.3
    msp.add_line((ox + unload_w + compress_w, oy),
                 (ox + unload_w + compress_w, oy + W),
                 dxfattribs={"layer": layer})
    cx = ox + unload_w + compress_w / 2
    msp.add_lwpolyline(
        [(cx - 4 * s, oy + W / 2 - 3 * s),
         (cx + 4 * s, oy + W / 2 - 3 * s),
         (cx + 4 * s, oy + W / 2 + 3 * s),
         (cx - 4 * s, oy + W / 2 + 3 * s)],
        close=True, dxfattribs={"layer": "设备"})
    t = msp.add_text("压缩机", dxfattribs={
        "layer": "文字-标题", "height": 2 * s, "style": "HZ"})
    t.set_placement((cx, oy + W / 2),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    t = msp.add_text("装车区", dxfattribs={
        "layer": "文字-标题", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ox + unload_w + compress_w + (L - unload_w - compress_w) / 2, oy + W / 2),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    gate_w = 6 * s
    msp.add_line((ox + L / 2 - gate_w / 2, oy),
                 (ox + L / 2 - gate_w / 2, oy - 3 * s),
                 dxfattribs={"layer": layer})
    msp.add_line((ox + L / 2 + gate_w / 2, oy),
                 (ox + L / 2 + gate_w / 2, oy - 3 * s),
                 dxfattribs={"layer": layer})
    t = msp.add_text("大门", dxfattribs={
        "layer": "文字", "height": 2 * s, "style": "HZ"})
    t.set_placement((ox + L / 2, oy - 2 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    msp.add_circle((ox + 3 * s, oy + W - 3 * s), 2 * s,
                   dxfattribs={"layer": "设备"})
    t = msp.add_text("除臭", dxfattribs={
        "layer": "文字", "height": 1.8 * s, "style": "HZ"})
    t.set_placement((ox + 3 * s, oy + W - 3 * s),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    if label:
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": 3.5 * s, "style": "HZ"})
        t.set_placement((ox + L / 2, oy + W + 5 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if params:
        py = oy + W + 5 * s + 3.5 * s
        for k, v in params.items():
            t = msp.add_text(f"{k}:{v}", dxfattribs={
                "layer": "文字", "height": 2 * s, "style": "HZ"})
            t.set_placement((ox + L / 2, py),
                            align=TextEntityAlignment.MIDDLE_CENTER)
            py -= 2.5 * s

    return (ox + L, oy + W)


def draw_incinerator(msp, origin, d=2.0, H=5.0, scale=100.0,
                     label="焚烧炉", layer="固废", tracker=None):
    s=scale;ox,oy=_r(*origin);ds=d*s;hs=H*s;cx,cy=ox+ds/2,oy-hs/2
    msp.add_lwpolyline([(ox,oy),(ox+ds,oy),(ox+ds,oy-hs),(ox,oy-hs)],close=True,dxfattribs={"layer":layer})
    tw=ds*0.6;msp.add_lwpolyline([(cx-tw/2,oy),(cx+tw/2,oy),(cx+ds*0.15,oy+hs*0.15),(cx-ds*0.15,oy+hs*0.15)],close=True,dxfattribs={"layer":layer})
    sw=ds*0.2;sh=hs*0.4;msp.add_lwpolyline([(cx+ds*0.2,oy-hs),(cx+ds*0.2+sw,oy-hs),(cx+ds*0.2+sw,oy-hs-sh),(cx+ds*0.2,oy-hs-sh)],close=True,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(cx+ds*0.2,oy-hs-sh),(cx+ds*0.2+sw,oy-hs-sh),(cx+ds*0.2+sw,oy-hs-sh-2*s),(cx+ds*0.2,oy-hs-sh-2*s)],close=True,dxfattribs={"layer":"细实线"})
    msp.add_line((ox+ds*0.1,oy-hs),(ox+ds*0.1,oy-hs-3*s),dxfattribs={"layer":layer});msp.add_line((ox+ds*0.3,oy-hs),(ox+ds*0.3,oy-hs-3*s),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.8*s,"style":"HZ"});t.set_placement((cx,oy-hs-sh-5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+ds+5*s,oy)
