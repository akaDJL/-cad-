"""钢筋详图+配料表联动。梁/柱配筋一键出图+报表。"""
from __future__ import annotations
from typing import List, Tuple


def draw_beam_with_schedule(msp, origin, width=300.0, height=500.0,
                            top_bars=3, top_d=20, bottom_bars=3, bottom_d=20,
                            stirrup_d=8, stirrup_spacing=150,
                            cover=25, scale=100.0, label="梁配筋图",
                            layer="钢筋", tracker=None):
    """梁配筋剖面+钢筋表（联动）。"""
    from .rebar import draw_beam_section

    s = scale; ox, oy = origin
    w, h = width * s, height * s

    top_b = [{"count": top_bars, "diameter": top_d,
              "layer": "top", "depth": cover}]
    bot_b = [{"count": bottom_bars, "diameter": bottom_d,
              "layer": "bottom", "depth": cover}]
    stirrup = {"diameter": stirrup_d, "spacing": stirrup_spacing}

    draw_beam_section(msp, (ox, oy), width, height,
                      top_bars=top_b, bottom_bars=bot_b,
                      stirrup=stirrup, scale=s,
                      layer=layer)

    # 自动出钢筋表
    from ..standards.building import draw_schedule_table
    rows = [
        ["①", f"顶部主筋", f"{top_d}mm", str(top_bars), f"L≈{(width+height)*2/10:.0f}cm", "HRB400"],
        ["②", f"底部主筋", f"{bottom_d}mm", str(bottom_bars), f"L≈{(width+height)*2/10:.0f}cm", "HRB400"],
        ["③", f"箍筋", f"{stirrup_d}mm", f"@{stirrup_spacing}mm", f"L≈{(width+height-4*cover)*2/10:.0f}cm", "HPB300"],
    ]
    draw_schedule_table(msp, (ox, oy - h - 20 * s),
                        title="钢筋表",
                        headers=["编号","名称","直径","数量","长度","材质"],
                        rows=rows, col_widths=[20,28,24,20,35,24],
                        scale=scale, tracker=tracker)
    return (ox + w + 10 * s, oy)


def draw_column_with_schedule(msp, origin, bx=400.0, by=400.0,
                              corner_d=25, side_d=20,
                              n_corner=4, n_side=2,
                              stirrup_d=10, stirrup_spacing=100,
                              cover=30, scale=100.0, label="柱配筋图",
                              layer="钢筋", tracker=None):
    """柱配筋剖面+钢筋表（联动）。"""
    from .rebar import draw_column_section

    s = scale; ox, oy = origin
    w, h = bx * s, by * s

    draw_column_section(msp, (ox, oy), bx, by,
                        corner_d=corner_d, side_d=side_d,
                        n_corner=n_corner, n_side=n_side,
                        stirrup_d=stirrup_d,
                        stirrup_spacing=stirrup_spacing,
                        cover=cover, scale=s, layer=layer)

    total = n_corner + n_side * 4
    from ..standards.building import draw_schedule_table
    rows = [
        ["①", "角筋", f"{corner_d}mm", str(n_corner), "L=柱高", "HRB400"],
        ["②", "侧筋", f"{side_d}mm", str(n_side*4), "L=柱高", "HRB400"],
        ["③", "箍筋", f"{stirrup_d}mm", f"@{stirrup_spacing}mm", f"箍筋周长", "HPB300"],
    ]
    draw_schedule_table(msp, (ox, oy - h - 20 * s),
                        title="柱钢筋表",
                        headers=["编号","名称","直径","数量","长度","材质"],
                        rows=rows, col_widths=[20,24,22,20,34,24],
                        scale=scale, tracker=tracker)
    return (ox + w + 10 * s, oy)
