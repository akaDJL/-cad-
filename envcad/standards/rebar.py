"""土木结构工程制图 v1.0（GB 50010—2010、GB 50017—2017）。

基于 ezdxf 实现钢筋表、梁柱配筋、钢结构节点等结构工程图纸。
所有标准数值（配筋率、锚固长度、保护层厚度、焊缝尺寸等）由 Agent 搜索后
显式传入绘图函数，代码只负责绘图框架。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

def _fmt_mm(val: float, decimals: int = 0) -> str:
    """格式化 mm 值，去多余小数。"""
    if decimals == 0:
        return f"{val:.0f}"
    return f"{val:.{decimals}f}"


# ══════════════════════════════════════════════════════════
#  钢筋表（Rebar Schedule）
# ══════════════════════════════════════════════════════════

def draw_rebar_schedule(msp, origin, bars: List[dict],
                         scale: float = 100.0,
                         title: str = "钢筋表",
                         layer_grid: str = "细实线",
                         layer_text: str = "文字",
                         layer_header: str = "粗实线",
                         tracker=None) -> Tuple[float, float]:
    """绘制钢筋材料表。

    参数:
        origin: 表格左上角 (x, y)
        bars: 钢筋列表，每项为 dict:
            {
                "pos": "1",        # 编号
                "dia": 16,         # 直径 mm
                "shape": "直筋",    # 形状描述（或形状代号）
                "length": 1200,    # 单根长度 mm（或 "3200" 字符串）
                "qty": 4,          # 根数
                "total_len": 4800, # 总长 m（可选，自动计算）
                "weight": 0,       # 总重 kg（可选，自动计算）
                "grade": "HRB400", # 牌号（可选）
                "note": "",        # 备注
            }
        scale: 出图比例倒数

    返回: 表格右下角坐标
    """
    s = scale
    ox, oy = _r(*origin)

    # 列定义（全部参数化，无预设值限制）
    cols = [
        ("编号",  8.0, "center"),
        ("直径", 10.0, "center"),
        ("形状", 15.0, "left"),
        ("长度", 14.0, "right"),
        ("根数",  8.0, "center"),
        ("总长", 14.0, "right"),
        ("总重", 12.0, "right"),
        ("备注", 16.0, "left"),
    ]

    col_w = [c[1] * s for c in cols]
    total_w = sum(col_w)
    row_h = 7.0 * s
    txt_h = 2.5 * s
    hdr_h = 3.0 * s

    # ── 标题行 ──
    title_h = 5.0 * s
    _cell(msp, ox, oy - title_h, total_w, title_h, title,
          "center", 3.5 * s, layer_grid, layer_text)
    cur_y = oy - title_h

    # ── 表头 ──
    cx = ox
    for i, (name, _, align) in enumerate(cols):
        _cell(msp, cx, cur_y - row_h, col_w[i], row_h, name,
              "center", hdr_h, layer_grid, layer_text, bold_layer=layer_header)
        cx += col_w[i]
    cur_y -= row_h

    # ── 数据行 ──
    for bar in bars:
        dia = bar.get("dia", 0)
        length = bar.get("length", 0)
        qty = bar.get("qty", 0)

        # 计算总长和总重（如果未提供）
        total_len = bar.get("total_len")
        if total_len is None:
            total_len = float(length) * qty / 1000.0  # mm → m

        weight = bar.get("weight")
        if weight is None and dia > 0 and total_len:
            weight = total_len * (dia ** 2) * 0.00617  # 经验公式

        vals = [
            str(bar.get("pos", "")),
            f"Φ{dia}" if dia else str(bar.get("grade", "")),
            str(bar.get("shape", "")),
            f"{float(length):.0f}" if length else "",
            str(qty),
            f"{float(total_len):.1f}" if total_len is not None else "",
            f"{float(weight):.1f}" if weight is not None else "",
            str(bar.get("note", "")),
        ]

        cx = ox
        for i, val in enumerate(vals):
            _cell(msp, cx, cur_y - row_h, col_w[i], row_h, val,
                  cols[i][2], txt_h, layer_grid, layer_text)
            cx += col_w[i]
        cur_y -= row_h

    # 外框加粗
    msp.add_lwpolyline(
        [(ox, oy - title_h), (ox + total_w, oy - title_h),
         (ox + total_w, cur_y), (ox, cur_y)],
        close=True, dxfattribs={"layer": layer_header}
    )

    if tracker:
        tracker.register(ox, cur_y, ox + total_w, oy, margin=40)

    return (ox + total_w, cur_y)


def _cell(msp, x0, y0, w, h, text, align, txt_h,
          layer_grid, layer_text, bold_layer=None):
    """绘制表格单元格。"""
    layer = bold_layer if bold_layer else layer_grid
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True, dxfattribs={"layer": layer}
    )
    if not text:
        return
    alignment = {
        "left": TextEntityAlignment.MIDDLE_LEFT,
        "center": TextEntityAlignment.MIDDLE_CENTER,
        "right": TextEntityAlignment.MIDDLE_RIGHT,
    }.get(align, TextEntityAlignment.MIDDLE_CENTER)
    if align == "left":
        px = x0 + 1.0 * txt_h
    elif align == "right":
        px = x0 + w - 1.0 * txt_h
    else:
        px = x0 + w / 2
    py = y0 + h / 2
    t = msp.add_text(str(text), dxfattribs={
        "layer": layer_text, "height": txt_h, "style": "HZ",
    })
    t.set_placement((px, py), align=alignment)


# ══════════════════════════════════════════════════════════
#  梁配筋断面
# ══════════════════════════════════════════════════════════

def draw_beam_section(msp, origin, width: float, height: float,
                       top_bars: List[dict] = None,
                       bottom_bars: List[dict] = None,
                       stirrup: dict = None,
                       cover: float = 25.0,
                       scale: float = 100.0,
                       label: str = "",
                       layer: str = "粗实线",
                       tracker=None):
    """绘制梁配筋断面图。

    参数:
        origin: 断面中心或左下角 (x, y)
        width: 梁宽 (mm)
        height: 梁高 (mm)
        top_bars: 上部钢筋 [{"count":3,"dia":16}, ...]
        bottom_bars: 下部钢筋 [{"count":4,"dia":20}, ...]
        stirrup: 箍筋 {"dia":8,"spacing":200} 或 {"dia":8,"spacing":"100/200"}
        cover: 保护层厚度 mm（Agent 搜索 GB 50010 后传入）
        label: 梁编号（如 "KL1 300×600"）
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    h = height * s
    c = cover * s

    # ── 梁轮廓 ──
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h)],
        close=True, dxfattribs={"layer": layer}
    )

    # ── 上部钢筋 ──
    if top_bars:
        bar_y = oy + h - c
        _draw_bar_row(msp, ox + c, bar_y, w - 2 * c, top_bars,
                       s, side="top", layer=layer)

    # ── 下部钢筋 ──
    if bottom_bars:
        bar_y = oy + c
        _draw_bar_row(msp, ox + c, bar_y, w - 2 * c, bottom_bars,
                       s, side="bottom", layer=layer)

    # ── 箍筋 ──
    if stirrup:
        stir_dia = stirrup.get("dia", 8)
        stir_spacing = stirrup.get("spacing", 200)
        # 箍筋矩形（缩进保护层）
        sx0, sy0 = ox + c - 2 * s, oy + c - 2 * s
        sx1, sy1 = ox + w - c + 2 * s, oy + h - c + 2 * s
        msp.add_lwpolyline(
            [(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)],
            close=True, dxfattribs={"layer": "细实线"}
        )
        # 箍筋间距标注
        sp_str = f"Φ{stir_dia}@{stir_spacing}" if isinstance(stir_spacing, (int, float)) else f"Φ{stir_dia}@{stir_spacing}"
        txt_h = 2.5 * s
        t = msp.add_text(sp_str, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((ox + w / 2, oy + h / 2),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 梁编号 ──
    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + h + 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(ox - 5 * s, oy - 5 * s,
                         ox + w + 5 * s, oy + h + 10 * s, margin=30)

    return (ox + w, oy + h)


def _draw_bar_row(msp, x0, y0, width, bars: List[dict],
                   s: float, side: str, layer: str):
    """在梁断面中画一排钢筋点。"""
    total_count = sum(b.get("count", 0) for b in bars)
    if total_count == 0:
        return

    spacing = width / (total_count + 1) if total_count > 1 else width / 2
    i = 0
    for bar in bars:
        count = bar.get("count", 0)
        dia = bar.get("dia", 0)
        for _ in range(count):
            i += 1
            bx = x0 + spacing * i
            r = dia * s / 2
            try:
                msp.add_circle((bx, y0), r,
                               dxfattribs={"layer": layer, "lineweight": 30})
                # 实心填充（小圆点）
                msp.add_solid(
                    [(bx - r * 0.7, y0 - r * 0.7),
                     (bx + r * 0.7, y0 - r * 0.7),
                     (bx + r * 0.7, y0 + r * 0.7),
                     (bx - r * 0.7, y0 + r * 0.7)],
                    dxfattribs={"layer": layer})
            except Exception as _e:
                print(f'[WARNING] rebar.py: {_e}')


# ══════════════════════════════════════════════════════════
#  柱配筋断面
# ══════════════════════════════════════════════════════════

def draw_column_section(msp, origin, width: float, depth: float,
                         bars: List[dict] = None,
                         stirrup: dict = None,
                         cover: float = 25.0,
                         scale: float = 100.0,
                         label: str = "",
                         layer: str = "粗实线",
                         tracker=None):
    """绘制柱配筋断面图。

    参数:
        origin: 柱中心或左下角 (x, y)
        width: 柱宽 (mm)  — X方向
        depth: 柱深 (mm)  — Y方向
        bars: 纵筋分布 [{"side":"corner","dia":20,"count":4},
                         {"side":"x","dia":16,"count":2}, ...]
              或简单数量 {"total":8, "dia":20}
        stirrup: 箍筋 {"dia":8, "spacing":"100/200", "legs":3}
                 多肢箍时 legs=肢数
        cover: 保护层厚度 mm
        label: 柱编号（如 "KZ1 400×400"）
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    d = depth * s
    c = cover * s

    # ── 柱轮廓 ──
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy), (ox + w, oy + d), (ox, oy + d)],
        close=True, dxfattribs={"layer": layer}
    )

    # ── 纵筋 ──
    if bars:
        if isinstance(bars, dict) and "total" in bars:
            # 简化模式：平均分布四角 + 中间
            total = bars["total"]
            dia = bars["dia"]
            corners = min(4, total)
            sides = total - corners
            _draw_bars_at_corners(msp, ox, oy, w, d, c, dia, s, layer,
                                  corners)
            if sides > 0:
                _draw_bars_on_sides(msp, ox, oy, w, d, c, dia, s, layer,
                                    sides)
        elif isinstance(bars, list):
            for bar_spec in bars:
                side = bar_spec.get("side", "corner")
                dia = bar_spec.get("dia", 16)
                count = bar_spec.get("count", 4)
                if side == "corner":
                    _draw_bars_at_corners(msp, ox, oy, w, d, c, dia, s,
                                          layer, min(count, 4))
                elif side == "x":
                    _draw_bars_along(msp, ox + c, oy + d - c,
                                      w - 2 * c, count, dia, s, layer)
                elif side == "y":
                    _draw_bars_along(msp, ox + c, oy + c, d - 2 * c,
                                      count, dia, s, layer, vertical=True)

    # ── 箍筋 ──
    if stirrup:
        stir_dia = stirrup.get("dia", 8)
        legs = stirrup.get("legs", 2)
        sx0, sy0 = ox + c - 2 * s, oy + c - 2 * s
        sx1, sy1 = ox + w - c + 2 * s, oy + d - c + 2 * s
        # 外箍
        msp.add_lwpolyline(
            [(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)],
            close=True, dxfattribs={"layer": "细实线"}
        )
        # 内箍（拉筋 / 多肢箍）
        if legs >= 3:
            leg_spacing = (sx1 - sx0) / (legs - 0.5)
            for li in range(1, legs - 1):
                lx = sx0 + leg_spacing * (li + 0.25)
                msp.add_line((lx, sy0), (lx, sy1),
                             dxfattribs={"layer": "细实线"})

        sp_str = f"Φ{stir_dia}@{stirrup.get('spacing','')}"
        txt_h = 2.5 * s
        t = msp.add_text(sp_str, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((ox + w / 2, oy + d / 2),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 柱编号 ──
    if label:
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + w / 2, oy + d + 3 * s),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker:
        tracker.register(ox - 5 * s, oy - 5 * s,
                         ox + w + 5 * s, oy + d + 10 * s, margin=30)

    return (ox + w, oy + d)


def _draw_bars_at_corners(msp, ox, oy, w, d, c, dia, s, layer, count):
    """在矩形四角画纵筋。"""
    corners = [(ox + c, oy + c), (ox + w - c, oy + c),
               (ox + c, oy + d - c), (ox + w - c, oy + d - c)]
    for i in range(min(count, 4)):
        bx, by = corners[i]
        r = dia * s / 2
        try:
            msp.add_circle((bx, by), r, dxfattribs={"layer": layer})
            msp.add_solid([(bx - r * 0.7, by - r * 0.7),
                           (bx + r * 0.7, by - r * 0.7),
                           (bx + r * 0.7, by + r * 0.7),
                           (bx - r * 0.7, by + r * 0.7)],
                          dxfattribs={"layer": layer})
        except Exception as _e:
            print(f'[WARNING] rebar.py: {_e}')


def _draw_bars_on_sides(msp, ox, oy, w, d, c, dia, s, layer, count):
    """在矩形四边均匀分布剩余纵筋。"""
    # 四条边：底、右、顶、左（去角）
    edges = [
        (ox + c, oy + c, ox + w - c, oy + c),     # 底边
        (ox + w - c, oy + c, ox + w - c, oy + d - c),  # 右边
        (ox + c, oy + d - c, ox + w - c, oy + d - c),  # 顶边
        (ox + c, oy + c, ox + c, oy + d - c),    # 左边
    ]
    per_side = max(1, count // 4)
    rem = count % 4
    idx = 0
    for ei, (sx, sy, ex, ey) in enumerate(edges):
        n = per_side + (1 if ei < rem else 0)
        r = dia * s / 2
        for j in range(n):
            frac = (j + 1) / (n + 1)
            bx = sx + (ex - sx) * frac
            by = sy + (ey - sy) * frac
            try:
                msp.add_circle((bx, by), r, dxfattribs={"layer": layer})
                msp.add_solid([(bx - r * 0.7, by - r * 0.7),
                               (bx + r * 0.7, by - r * 0.7),
                               (bx + r * 0.7, by + r * 0.7),
                               (bx - r * 0.7, by + r * 0.7)],
                              dxfattribs={"layer": layer})
            except Exception as _e:
                print(f'[WARNING] rebar.py: {_e}')
            idx += 1


def _draw_bars_along(msp, x0, y0, length, count, dia, s, layer,
                      vertical=False):
    """沿一条边均匀画纵筋。"""
    r = dia * s / 2
    for i in range(count):
        frac = (i + 1) / (count + 1)
        if vertical:
            bx, by = x0, y0 + length * frac
        else:
            bx, by = x0 + length * frac, y0
        try:
            msp.add_circle((bx, by), r, dxfattribs={"layer": layer})
            msp.add_solid([(bx - r * 0.7, by - r * 0.7),
                           (bx + r * 0.7, by - r * 0.7),
                           (bx + r * 0.7, by + r * 0.7),
                           (bx - r * 0.7, by + r * 0.7)],
                          dxfattribs={"layer": layer})
        except Exception as _e:
            print(f'[WARNING] rebar.py: {_e}')


# ══════════════════════════════════════════════════════════
#  钢结构节点
# ══════════════════════════════════════════════════════════

def draw_steel_connection(msp, origin, members: List[dict],
                           bolts: List[dict] = None,
                           welds: List[dict] = None,
                           plates: List[dict] = None,
                           scale: float = 100.0,
                           label: str = "",
                           layer: str = "粗实线",
                           tracker=None):
    """绘制钢结构连接节点详图。

    参数:
        origin: 节点参考点 (x, y)
        members: 构件列表
            [{"type":"beam","profile":"H300×200×8×12",
              "start":(x1,y1), "end":(x2,y2)}, ...]
        bolts: 螺栓列表（全部由 Agent 搜索 GB 50017 后决定）
            [{"dia":20, "grade":"10.9S", "center":(x,y),
              "rows":2, "cols":3, "row_sp":80, "col_sp":80}, ...]
        welds: 焊缝列表
            [{"type":"角焊缝", "leg":8, "length":200,
              "start":(x1,y1), "end":(x2,y2), "side":"arrow"}, ...]
        plates: 加劲板/端板列表
            [{"thk":12, "width":300, "height":400,
              "origin":(x,y)}, ...]
        label: 节点编号
    """
    s = scale
    ox, oy = _r(*origin)

    # ── 构件轮廓 ──
    for member in members:
        mtype = member.get("type", "beam")
        profile = member.get("profile", "")
        sx, sy = _r(*member["start"])
        ex, ey = _r(*member["end"])

        if mtype in ("beam", "column", "brace"):
            # H型钢简化画法：双线翼缘
            _draw_steel_member(msp, sx, sy, ex, ey, profile, s,
                               mtype, layer)

    # ── 节点板 ──
    if plates:
        for plate in plates:
            px, py = _r(*plate["origin"])
            pw = plate["width"] * s
            ph = plate["height"] * s
            msp.add_lwpolyline(
                [(px, py), (px + pw, py), (px + pw, py + ph),
                 (px, py + ph)],
                close=True, dxfattribs={"layer": layer}
            )
            # 板厚标注
            txt_h = 2.2 * s
            t = msp.add_text(f"t={plate['thk']}", dxfattribs={
                "layer": "文字", "height": txt_h, "style": "ENG",
            })
            t.set_placement((px + pw / 2, py + ph + 1.5 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 螺栓 ──
    if bolts:
        for bolt in bolts:
            cx, cy = bolt["center"]
            dia = bolt.get("dia", 20)
            rows = bolt.get("rows", 2)
            cols = bolt.get("cols", 2)
            rs = bolt.get("row_sp", 80) * s
            cs = bolt.get("col_sp", 80) * s

            for ri in range(rows):
                for ci in range(cols):
                    bx = cx + (ci - (cols - 1) / 2) * cs
                    by = cy + (ri - (rows - 1) / 2) * rs
                    r = dia * s / 2
                    msp.add_circle((bx, by), r,
                                   dxfattribs={"layer": layer})

            # 螺栓标注
            if bolt.get("grade"):
                txt_h = 2.0 * s
                t = msp.add_text(
                    f"M{bolt['dia']}-{bolt['grade']}", dxfattribs={
                        "layer": "文字", "height": txt_h, "style": "ENG",
                    })
                t.set_placement(
                    (cx, cy - rs * (rows / 2 + 1)),
                    align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 焊缝 ──
    if welds:
        from .symbols import draw_weld_symbol
        for weld in welds:
            draw_weld_symbol(
                msp, weld["start"],
                weld_type=weld.get("type", "角焊缝"),
                leg=str(weld.get("leg", 6)),
                length=str(weld.get("length", "")),
                arrow_side=(weld.get("side", "arrow") == "arrow"),
                scale=scale,
                layer=layer,
                tracker=tracker,
            )

    # ── 节点编号 ──
    if label:
        txt_h = 3.5 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + 5 * s, oy + 5 * s),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if tracker:
        tracker.register(ox - 20 * s, oy - 20 * s,
                         ox + 50 * s, oy + 50 * s, margin=50)

    return (ox, oy)


def _draw_steel_member(msp, sx, sy, ex, ey, profile, s, mtype, layer):
    """简化钢构件轮廓（H型钢双线表示）。"""
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length == 0:
        return

    # 翼缘宽度（简化，实际应从 profile 解析）
    bf = 30 * s  # 默认翼缘宽
    try:
        parts = profile.replace("H", "").replace("×", "x").split("x")
        if len(parts) >= 3:
            bf = float(parts[1]) * s / 2
    except (ValueError, IndexError):
        pass

    ux, uy = dx / length, dy / length
    px, py = -uy, ux  # 垂直方向

    # 双线翼缘
    msp.add_line((sx + px * bf, sy + py * bf),
                 (ex + px * bf, ey + py * bf),
                 dxfattribs={"layer": layer})
    msp.add_line((sx - px * bf, sy - py * bf),
                 (ex - px * bf, ey - py * bf),
                 dxfattribs={"layer": layer})
    # 中心线
    msp.add_line((sx, sy), (ex, ey),
                 dxfattribs={"layer": "中心线"})


# ══════════════════════════════════════════════════════════
#  弯起钢筋大样
# ══════════════════════════════════════════════════════════

def draw_rebar_bend(msp, origin, bend_points: List[Tuple[float, float]],
                     dia: float, scale: float = 100.0,
                     dims: List[str] = None,
                     label: str = "",
                     layer: str = "粗实线",
                     tracker=None):
    """绘制弯起钢筋大样。

    参数:
        origin: 起点 (x, y)
        bend_points: 弯折点列表（包括起终点），相对于 origin（单位 mm）
                     如 [(0,0), (200,0), (200,100), (400,100)]
        dia: 钢筋直径 mm
        dims: 各段长度标注 ["200","100","200"]
        label: 钢筋编号
    """
    s = scale
    ox, oy = _r(*origin)
    r = dia * s / 2  # 钢筋粗细

    # ── 绘线 ──
    if len(bend_points) < 2:
        return (ox, oy)

    prev_pt = None
    for px, py in bend_points:
        bx = ox + px * s
        by = oy + py * s
        if prev_pt:
            msp.add_line(prev_pt, (bx, by),
                         dxfattribs={"layer": layer, "lineweight": int(dia * 3)})
        # 端点小圆（表示钢筋断面）
        msp.add_circle((bx, by), r, dxfattribs={"layer": layer})
        prev_pt = (bx, by)

    # ── 尺寸标注 ──
    if dims:
        txt_h = 2.2 * s
        for i, d in enumerate(dims):
            if i < len(bend_points) - 1:
                mx = (bend_points[i][0] + bend_points[i + 1][0]) / 2
                my = (bend_points[i][1] + bend_points[i + 1][1]) / 2
                bx = ox + mx * s
                by = oy + my * s - 5 * s  # 偏下放置
                t = msp.add_text(d, dxfattribs={
                    "layer": "文字", "height": txt_h, "style": "ENG",
                })
                t.set_placement((bx, by),
                                align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 编号 ──
    if label:
        last_pt = bend_points[-1]
        txt_h = 3.0 * s
        t = msp.add_text(label, dxfattribs={
            "layer": "文字-标题", "height": txt_h, "style": "HZ",
        })
        t.set_placement((ox + last_pt[0] * s + 5 * s,
                         oy + last_pt[1] * s),
                        align=TextEntityAlignment.MIDDLE_LEFT)

    if tracker:
        xs = [p[0] * s + ox for p in bend_points]
        ys = [p[1] * s + oy for p in bend_points]
        tracker.register(min(xs) - 5 * s, min(ys) - 5 * s,
                         max(xs) + 15 * s, max(ys) + 5 * s, margin=20)

    return (ox + bend_points[-1][0] * s, oy + bend_points[-1][1] * s)
