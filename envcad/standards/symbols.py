"""焊接符号与表面粗糙度标注 v1.0。

焊接符号按 GB/T 324—2008，使用 Leader + MText 组合。
表面粗糙度按 GB/T 131—2006，绘制基本符号 + Ra 数值。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

def _arrow_line(msp, start, end, scale: float, layer="尺寸标注"):
    """带实心箭头的指引线。"""
    sx, sy = start
    ex, ey = end
    msp.add_line((sx, sy), (ex, ey), dxfattribs={"layer": layer})
    a = math.atan2(ey - sy, ex - sx)
    h = 2.5 * scale
    try:
        p1 = (ex, ey)
        p2 = (ex + h * math.cos(a + math.radians(150)),
              ey + h * math.sin(a + math.radians(150)))
        p3 = (ex + h * math.cos(a - math.radians(150)),
              ey + h * math.sin(a - math.radians(150)))
        msp.add_solid([p1, p2, p3, p3], dxfattribs={"layer": layer})
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')


# ══════════════════════════════════════════════════════════
#  焊接符号 (GB/T 324—2008)
# ══════════════════════════════════════════════════════════

# 焊缝基本符号映射
WELD_BASIC_SYMBOLS = {
    # 对接焊缝
    "I形焊缝":    "‖",      # 或直接画线
    "V形焊缝":    "V",
    "单边V形焊缝": "√",
    "U形焊缝":    "U",
    "J形焊缝":    "J",
    # 角焊缝
    "角焊缝":     "▽",      # 角焊缝符号 (三角形)
    "塞焊缝":     "□",
    "点焊缝":     "⊙",
    "缝焊缝":     "●",
    "槽焊缝":     "⊏",
    # 组合
    "喇叭形焊缝": "⌒",
    "单边喇叭形": "⌐",
    # 通用
    "卷边焊缝":   "∫",
}

# 补充符号
WELD_SUPP_SYMBOLS = {
    "周围焊缝":   "○",     # 圆圈（环绕焊接）
    "现场焊接":   "⮕",    # 旗标
    "平整":       "—",     # 水平线
    "凹面":       "⌣",     # 下弧线
    "凸面":       "⌢",     # 上弧线
    "打磨":       "G",
    "修整":       "F",
    "凿平":       "C",
    "锤平":       "M",
}


def draw_weld_symbol(msp, target, weld_type: str,
                     leg: str = "", throat: str = "",
                     length: str = "", pitch: str = "",
                     arrow_side: bool = True,
                     other_side: str = "",
                     supp_symbols: str = "",
                     site_weld: bool = False,
                     all_around: bool = False,
                     scale: float = 100.0,
                     leader_dir: Tuple[float, float] = (1, 0),
                     layer: str = "尺寸标注",
                     tracker=None):
    """绘制焊接符号。

    参数:
        target: 焊缝附着的点 (x, y)
        weld_type: 焊缝类型（中文名，如"角焊缝"、"V形焊缝"）
        leg: 焊脚尺寸（如 "5" 表示 5mm）
        throat: 熔深（如 "3" 表示 3mm）
        length: 焊缝长度（如 "50"）
        pitch: 焊缝节距（如 "100" 表示间断焊间距）
        arrow_side: True = 箭头侧，False = 非箭头侧
        other_side: 另一侧焊缝类型（如有对称焊缝）
        supp_symbols: 补充符号字符串
        site_weld: 是否现场焊接
        all_around: 是否周围焊缝
        leader_dir: 引出方向
    """
    s = scale
    tx, ty = _r(*target)

    # ── 引出线 + 箭头 ──
    L = 14 * s
    lx = tx + leader_dir[0] * L
    ly = ty + leader_dir[1] * L
    _arrow_line(msp, (tx, ty), (lx, ly), s, layer=layer)

    # ── 水平基准线（引出线末端 → 右延伸） ──
    hline_len = 20 * s
    hx0, hy0 = _r(lx, ly)
    hx1 = hx0 + hline_len if leader_dir[0] >= 0 else hx0 - hline_len
    msp.add_line((hx0, hy0), (hx1, hy0), dxfattribs={"layer": layer})

    # 方向因子
    dir_factor = 1 if leader_dir[0] >= 0 else -1

    # ── 箭头侧焊缝符号（基准线上方） ──
    sym = WELD_BASIC_SYMBOLS.get(weld_type, weld_type)
    txt_h = 3.0 * s

    if arrow_side:
        # 箭头侧 → 基准线下方 (GB/T 324 规定)
        sym_y = hy0 - 2.5 * s
    else:
        sym_y = hy0 + 2.5 * s

    sym_x = hx0 + dir_factor * 4 * s

    # 画焊缝符号
    if sym == "▽":  # 角焊缝特殊处理——画三角形
        tri_h = 3.5 * s
        tri_w = 4.0 * s
        if arrow_side:
            # 实心三角在基准线下
            tri_pts = [(sym_x, sym_y), (sym_x - tri_w / 2, sym_y - tri_h),
                       (sym_x + tri_w / 2, sym_y - tri_h)]
        else:
            tri_pts = [(sym_x, sym_y), (sym_x - tri_w / 2, sym_y + tri_h),
                       (sym_x + tri_w / 2, sym_y + tri_h)]
        try:
            msp.add_solid(tri_pts + [tri_pts[0]], dxfattribs={"layer": layer})
        except Exception as _e:
            msp.add_lwpolyline(tri_pts, close=True, dxfattribs={"layer": layer})
    else:
        # 文字符号
        t = msp.add_text(sym, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((sym_x, sym_y), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 焊脚尺寸（基准线左侧） ──
    if leg:
        leg_x = hx0 + dir_factor * (-2 * s)
        leg_txt = f"a{leg}" if throat else f"z{leg}"
        t = msp.add_text(leg_txt, dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((leg_x, sym_y), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 焊缝长度 / 节距（符号后） ──
    len_str = ""
    if length:
        len_str = f"{length}"
        if pitch:
            len_str += f"-{pitch}"
    if len_str:
        len_x = sym_x + dir_factor * (5 * s if sym == "▽" else 3 * s)
        t = msp.add_text(len_str, dxfattribs={
            "layer": "文字", "height": 2.5 * s, "style": "ENG",
        })
        t.set_placement((len_x, sym_y), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 周围焊缝 ○ ──
    if all_around:
        circle_r = 2.0 * s
        circle_cx = hx0 - dir_factor * 2 * s
        circle_cy = sym_y
        # 圆圈在引出线与基准线交点处
        msp.add_circle((hx0 - dir_factor * circle_r, hy0), circle_r,
                       dxfattribs={"layer": layer})

    # ── 现场焊接旗标 ──
    if site_weld:
        flag_x = hx1 + dir_factor * 3 * s
        flag_y = hy0 + 3 * s
        msp.add_line((flag_x, hy0), (flag_x, flag_y), dxfattribs={"layer": layer})
        # 小三角旗标
        flag_w = 3 * s
        msp.add_line((flag_x, flag_y), (flag_x + dir_factor * flag_w, flag_y - 1.5 * s),
                     dxfattribs={"layer": layer})

    # ── 另一侧焊缝 ──
    if other_side:
        other_sym = WELD_BASIC_SYMBOLS.get(other_side, other_side)
        other_y = hy0 + 2.5 * s if arrow_side else hy0 - 2.5 * s
        t = msp.add_text(other_sym, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        })
        t.set_placement((sym_x, other_y), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── 补充符号（基准线末端） ──
    if supp_symbols:
        supp_x = hx1 + dir_factor * 1.5 * s
        for i, ch in enumerate(supp_symbols):
            sx = supp_x + dir_factor * i * 3 * s
            t = msp.add_text(ch, dxfattribs={
                "layer": "文字", "height": 2.5 * s, "style": "ENG",
            })
            t.set_placement((sx, hy0 + 2 * s),
                            align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker is not None:
        tracker.register(min(hx0 - 10 * s, hx1), hy0 - 8 * s,
                         max(hx0 + 10 * s, hx1 + 10 * s), hy0 + 8 * s, margin=30)

    return (hx1, hy0)


# ══════════════════════════════════════════════════════════
#  表面粗糙度 (GB/T 131—2006)
# ══════════════════════════════════════════════════════════

def draw_surface_roughness(msp, target, ra_value: str = "6.3",
                            method: str = "removal",
                            sampling_length: str = "",
                            machining_allowance: str = "",
                            direction: str = "right",
                            scale: float = 100.0,
                            layer: str = "尺寸标注",
                            tracker=None):
    """绘制表面粗糙度符号。

    参数:
        target: 标注点 (x, y)，符号尖端对准此处
        ra_value: Ra 值（如 "3.2", "6.3", "12.5"）
        method: "any"=任意方法 / "removal"=去除材料(默认) / "noremoval"=不去除材料
        sampling_length: 取样长度（如 "0.8"）
        machining_allowance: 加工余量（如 "0.2"）
        direction: 符号朝向 "right" / "left" / "up" / "down"
    """
    s = scale
    tx, ty = _r(*target)

    # 基本符号尺寸（图纸 mm）
    h1 = 3.5 * s   # 长边
    h2 = 7.0 * s   # 短边（总宽）

    dir_factor = 1 if direction in ("right", "up") else -1

    # 符号尖端（下方的点）
    apex_x, apex_y = tx, ty

    if direction in ("right", "left"):
        # 水平朝向
        left_x = apex_x - h1 * dir_factor
        top_y = apex_y + h2
        pts = [(apex_x, apex_y), (left_x, top_y), (apex_x + h1 * dir_factor * 0.3, top_y)]
    else:
        # 竖直朝向
        top_x = apex_x + h2
        bottom_y = apex_y - h1 * dir_factor
        pts = [(apex_x, apex_y), (top_x, bottom_y), (apex_x + h1 * 0.3 * dir_factor, bottom_y)]

    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    # 不去除材料符号：加小圆
    if method == "noremoval":
        circle_r = 2.0 * s
        circ_x = pts[1][0] + (pts[2][0] - pts[1][0]) * 0.8
        circ_y = pts[1][1] + (pts[2][1] - pts[1][1]) * 0.8
        msp.add_circle((circ_x, circ_y), circle_r, dxfattribs={"layer": layer})

    # 去除材料额外横线
    if method == "removal":
        extension = 4.0 * s
        if direction in ("right", "left"):
            ext_x1 = pts[1][0] - extension * dir_factor
            ext_x2 = pts[2][0] + extension * dir_factor * 0.5
            ext_y = pts[1][1]
            msp.add_line((ext_x1, ext_y), (ext_x2, ext_y),
                         dxfattribs={"layer": layer})
        else:
            ext_x = pts[1][0]
            ext_y1 = pts[1][1] - extension * dir_factor
            ext_y2 = pts[2][1] + extension * dir_factor * 0.5
            msp.add_line((ext_x, ext_y1), (ext_x, ext_y2),
                         dxfattribs={"layer": layer})

    # Ra 数值在符号上方
    txt_h = 2.8 * s
    if direction in ("right", "left"):
        txt_x = (pts[1][0] + pts[2][0]) / 2
        txt_y = pts[1][1] + 2.8 * s
    else:
        txt_x = pts[1][0] + 5 * s
        txt_y = (pts[1][1] + pts[2][1]) / 2

    ra_str = f"Ra {ra_value}"
    t = msp.add_text(ra_str, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((txt_x, txt_y), align=TextEntityAlignment.MIDDLE_CENTER)

    # 取样长度（Ra 下方）
    if sampling_length:
        sample_y = txt_y - 3.0 * s if direction in ("right", "left") else txt_y
        sample_x = txt_x if direction in ("right", "left") else txt_x + 4 * s
        t = msp.add_text(f"l={sampling_length}", dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((sample_x, sample_y), align=TextEntityAlignment.MIDDLE_CENTER)

    # 加工余量（Ra 右侧）
    if machining_allowance:
        allow_x = txt_x + 8 * s
        allow_y = txt_y
        t = msp.add_text(machining_allowance, dxfattribs={
            "layer": "文字", "height": 2.0 * s, "style": "ENG",
        })
        t.set_placement((allow_x, allow_y), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker is not None:
        tracker.register(apex_x - 5 * s, apex_y - 5 * s,
                         apex_x + 15 * s, apex_y + 12 * s, margin=20)

    return (txt_x + 10 * s, txt_y)


def draw_roughness_on_surface(msp, start, end, ra_value: str = "6.3",
                               scale: float = 100.0,
                               side: str = "above",
                               spacing: float = 20.0,
                               layer: str = "尺寸标注",
                               tracker=None):
    """在轮廓线上批量标注表面粗糙度（沿线段均布）。

    参数:
        start/end: 线段端点
        side: 符号放置侧 "above" / "below"
        spacing: 符号间距（图纸 mm）
    """
    s = scale
    sx, sy = _r(*start)
    ex, ey = _r(*end)

    dx, dy = ex - sx, ey - sy
    seg_len = math.hypot(dx, dy)
    if seg_len == 0:
        return

    ux, uy = dx / seg_len, dy / seg_len
    # 法向量（侧向偏移）
    if side == "above":
        nx, ny = -uy, ux
    else:
        nx, ny = uy, -ux

    step = spacing * s
    n_symbols = max(1, int(seg_len / step))
    results = []

    # 从起点均匀分布到终点
    for i in range(n_symbols):
        t = (i + 0.5) / n_symbols  # 每个符号在相邻步长中点
        px = sx + dx * t + nx * 6 * s
        py = sy + dy * t + ny * 6 * s
        end_pt = draw_surface_roughness(
            msp, (px, py), ra_value,
            method="removal",
            direction="up" if side == "above" else "down",
            scale=scale, layer=layer, tracker=tracker)
        results.append(end_pt)

    return results


# ══════════════════════════════════════════════════════════
#  批量标注 ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════

def draw_weld_table(msp, origin, welds: list, scale: float = 100.0,
                    title: str = "焊接要求",
                    layer: str = "尺寸标注",
                    tracker=None):
    """批量标注多个焊缝。

    welds: 列表，每项为 draw_weld_symbol 的参数字典。
    """
    s = scale
    ox, oy = _r(*origin)

    if title:
        from .annotate import _t
        _t(msp, title, (ox, oy), 4.0 * s,
           align=TextEntityAlignment.LEFT, layer="文字-标题",
           tracker=tracker)

    cur_y = oy - 6 * s
    for w in welds:
        draw_weld_symbol(
            msp, w["target"], w["weld_type"],
            leg=w.get("leg", ""),
            throat=w.get("throat", ""),
            length=w.get("length", ""),
            pitch=w.get("pitch", ""),
            arrow_side=w.get("arrow_side", True),
            other_side=w.get("other_side", ""),
            supp_symbols=w.get("supp_symbols", ""),
            site_weld=w.get("site_weld", False),
            all_around=w.get("all_around", False),
            scale=scale, leader_dir=w.get("leader_dir", (1, 0)),
            layer=layer, tracker=tracker,
        )
        cur_y -= 10 * s

    return cur_y
