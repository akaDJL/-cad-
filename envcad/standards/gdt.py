"""GD&T 形位公差标注 v1.0（GB/T 1182—2018）。

基于 ezdxf Tolerance 实体实现特征控制框，同时用 Leader + MText 做备用渲染。

支持:
  * 特征控制框：形状公差（直线度/平面度/圆度/圆柱度/线轮廓度/面轮廓度）
                 方向公差（平行度/垂直度/倾斜度）
                 位置公差（位置度/同轴度/对称度/圆跳动/全跳动）
  * 基准标注（Datum Feature Symbol）
  * 基准目标标注（Datum Target）

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ─── 公差符号字典 ────────────────────────────────────────

TOLERANCE_SYMBOLS = {
    # 形状公差
    "直线度":    "0",  # ezdxf 字符映射 (Tolerance 实体用文本)
    "平面度":    "1",
    "圆度":      "2",
    "圆柱度":    "3",
    "线轮廓度":  "4",
    "面轮廓度":  "5",
    # 方向公差
    "平行度":    "A",
    "垂直度":    "B",
    "倾斜度":    "C",
    # 位置公差
    "位置度":    "D",
    "同轴度":    "E",
    "对称度":    "F",
    "圆跳动":    "G",
    "全跳动":    "H",
}

# ezdxf 中 Tolerance 实体描述符（数字索引对应具体符号）
TOL_SYMBOL_MAP = {
    "直线度":    "\\U+23E4",   # ⏤
    "平面度":    "\\U+23E5",   # ⏥  (替代: ▱)
    "圆度":      "\\U+25CB",   # ○
    "圆柱度":    "\\U+232D",   # ⌭
    "线轮廓度":  "\\U+2324",   # ⌒  (实际用弧线符号)
    "面轮廓度":  "\\U+2313",   # ⌓  (封闭弧线)
    "平行度":    "//",
    "垂直度":    "\\U+22A5",   # ⊥
    "倾斜度":    "\\U+2220",   # ∠
    "位置度":    "\\U+2295",   # ⊕
    "同轴度":    "\\U+25CE",   # ◎
    "对称度":    "\\U+21D4",   # ⇔
    "圆跳动":    "\\U+2197",   # ↗
    "全跳动":    "\\U+2197\\U+2197",  # ↗↗
}

# 基准特征符号（φ 表示公差带为圆形/圆柱形，Ⓜ 表示最大实体要求）
MATERIAL_MODIFIERS = {
    "MMC": "\\U+24C2",  # Ⓜ 最大实体要求
    "LMC": "\\U+24C7",  # Ⓛ 最小实体要求
    "RFS": "",           # 不考虑特征尺寸（默认，不标）
}


def _arrow_line(msp, start, end, scale: float, layer="尺寸标注"):
    """带箭头的指引线。"""
    sx, sy = start
    ex, ey = end
    msp.add_line((sx, sy), (ex, ey), dxfattribs={"layer": layer})
    # 实心箭头
    a = math.atan2(ey - sy, ex - sx)
    h = 2.5 * scale
    p1 = (ex, ey)
    p2 = (ex + h * math.cos(a + math.radians(150)),
          ey + h * math.sin(a + math.radians(150)))
    p3 = (ex + h * math.cos(a - math.radians(150)),
          ey + h * math.sin(a - math.radians(150)))
    try:
        msp.add_solid([p1, p2, p3, p3], dxfattribs={"layer": layer})
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')


# ─── 特征控制框 ─────────────────────────────────────────

def draw_feature_control_frame(msp, target, tol_type: str,
                                value: str, datum: str = "",
                                datum2: str = "", datum3: str = "",
                                scale: float = 100.0,
                                material: str = "",
                                diametric: bool = False,
                                leader_dir: Tuple[float, float] = (0, 1),
                                layer: str = "尺寸标注",
                                tracker=None):
    """绘制形位公差特征控制框。

    参数:
        target: 目标点 (x, y) 或配合 leader_dir 的引出点
        tol_type: 公差类型（中文名，如"垂直度"、"同轴度"）
        value: 公差值（如 "0.05" 或 "φ0.02"；diametric=True 时自动加 φ）
        datum: 第一基准（如 "A"）
        datum2: 第二基准（如 "B"）
        datum3: 第三基准（如 "C"）
        scale: 出图比例倒数
        material: 实体条件修饰符 "MMC" / "LMC" / ""
        diametric: 公差带为圆形/圆柱形时设为 True
        leader_dir: 引出线方向 (dx, dy)，相对于 target
        tracker: BBoxTracker 实例（可选碰撞检测）
    """
    s = scale
    tx, ty = _r(*target)

    # 构建框内文字
    sym = TOL_SYMBOL_MAP.get(tol_type, tol_type)
    if diametric and not value.startswith("φ"):
        disp_value = f"φ{value}"
    else:
        disp_value = value

    # 框格文本行
    row1 = f"{sym}{disp_value}"  # 符号 + 公差值
    if material:
        row1 += f" {MATERIAL_MODIFIERS.get(material, '')}"

    rows = [row1]
    if datum:
        rows.append(f"{datum}" if not datum.startswith(("\\U", "φ")) else datum)
    if datum2:
        rows.append(f"{datum2}" if not datum2.startswith(("\\U", "φ")) else datum2)
    if datum3:
        rows.append(f"{datum3}" if not datum3.startswith(("\\U", "φ")) else datum3)

    # 框格尺寸（图纸 mm）
    cell_h = 3.5 * s   # 每格高度
    cell_w = 8.0 * s   # 每格宽度（增大以容纳 Unicode 符号）
    frame_w = cell_w
    frame_h = cell_h * len(rows)

    # 引出线目标
    leader_end = _r(tx + leader_dir[0] * 12 * s,
                     ty + leader_dir[1] * 12 * s)

    # 带箭头引出线
    if leader_dir != (0, 0):
        _arrow_line(msp, (tx, ty), leader_end, s, layer=layer)

    # 框格左下角
    bx = leader_end[0] + (cell_w * 1.5 if leader_dir[0] >= 0 else -cell_w * 0.5)
    by = leader_end[1] + cell_h * 0.5

    # 绘制框格外框
    msp.add_lwpolyline(
        [(bx, by), (bx + frame_w, by),
         (bx + frame_w, by + frame_h), (bx, by + frame_h)],
        close=True, dxfattribs={"layer": layer}
    )

    # 分隔线
    for i in range(1, len(rows)):
        sep_y = by + cell_h * i
        msp.add_line((bx, sep_y), (bx + frame_w, sep_y),
                     dxfattribs={"layer": layer})

    # 写入文字
    txt_height = 2.8 * s
    for i, text in enumerate(rows):
        ty_center = by + cell_h * (len(rows) - i - 1) + cell_h / 2
        t = msp.add_mtext(text, dxfattribs={
            "layer": "文字",
            "style": "ENG",
            "char_height": txt_height,
        })
        t.set_location(insert=(bx + 1.0 * s, ty_center),
                       attachment_point=4)  # 4 = MC (middle center)
        t.dxf.width = frame_w - 2.0 * s

    # 注册碰撞区域
    if tracker is not None:
        tracker.register(bx, by, bx + frame_w, by + frame_h, margin=40)

    return (bx + frame_w, by + frame_h)


# ─── 基准标注 ───────────────────────────────────────────

def draw_datum_symbol(msp, target, datum_id: str, scale: float = 100.0,
                      direction: str = "down",
                      leader_len: float = 10.0,
                      layer: str = "尺寸标注",
                      tracker=None):
    """绘制基准符号（Datum Feature Symbol）。

    GB/T 1182 样式：带引出线和实心/空心三角，基准字母在方框内。
    参数:
        target: 附着点 (x, y)
        datum_id: 基准标识字母（如 "A", "B"）
        direction: 引出方向 "up" / "down" / "left" / "right"
        leader_len: 引出线图纸长度
    """
    s = scale
    tx, ty = _r(*target)

    dirs = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
    dx, dy = dirs.get(direction, (0, -1))
    L = leader_len * s

    # 引出线端点
    ex = tx + dx * L
    ey = ty + dy * L

    # 基准三角（实心，边长 3.5*s）
    tri_h = 3.5 * s
    tri_w = 3.5 * s
    if direction == "up":
        tri_pts = [(ex, ey), (ex - tri_w / 2, ey + tri_h), (ex + tri_w / 2, ey + tri_h)]
    elif direction == "down":
        tri_pts = [(ex, ey), (ex - tri_w / 2, ey - tri_h), (ex + tri_w / 2, ey - tri_h)]
    elif direction == "right":
        tri_pts = [(ex, ey), (ex + tri_h, ey - tri_w / 2), (ex + tri_h, ey + tri_w / 2)]
    else:  # left
        tri_pts = [(ex, ey), (ex - tri_h, ey - tri_w / 2), (ex - tri_h, ey + tri_w / 2)]

    # 引出线
    msp.add_line((tx, ty), (ex, ey), dxfattribs={"layer": layer})

    # 填充三角
    try:
        msp.add_solid(tri_pts + [tri_pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        # 降级为线框三角
        msp.add_lwpolyline(tri_pts, close=True, dxfattribs={"layer": layer})

    # 基准方框（字母框）
    box_s = 4.5 * s  # 方框边长
    if direction == "up":
        box_x = ex - box_s / 2
        box_y = ey + tri_h + 1.5 * s
    elif direction == "down":
        box_x = ex - box_s / 2
        box_y = ey - tri_h - box_s - 1.5 * s
    elif direction == "right":
        box_x = ex + tri_h + 1.5 * s
        box_y = ey - box_s / 2
    else:  # left
        box_x = ex - tri_h - box_s - 1.5 * s
        box_y = ey - box_s / 2

    msp.add_lwpolyline(
        [(box_x, box_y), (box_x + box_s, box_y),
         (box_x + box_s, box_y + box_s), (box_x, box_y + box_s)],
        close=True, dxfattribs={"layer": layer}
    )

    # 基准字母
    txt_h = 3.0 * s
    txt_cx = box_x + box_s / 2
    txt_cy = box_y + box_s / 2
    t = msp.add_text(datum_id, dxfattribs={
        "layer": "文字", "height": txt_h, "style": "ENG",
    })
    t.set_placement((txt_cx, txt_cy), align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker is not None:
        # 框住整个区域
        all_x = sorted([tx, ex, box_x, box_x + box_s])
        all_y = sorted([ty, ey, box_y, box_y + box_s])
        tracker.register(all_x[0], all_y[0], all_x[-1], all_y[-1], margin=30)

    return (box_x + box_s, box_y + box_s)


# ─── 基准目标 ───────────────────────────────────────────

def draw_datum_target(msp, target, datum_id: str, area_label: str = "",
                       target_type: str = "point",
                       size: float = 0,
                       scale: float = 100.0,
                       layer: str = "尺寸标注",
                       tracker=None):
    """基准目标标注（Datum Target）。

    参数:
        target_type: "point" / "line" / "area"
        size: 目标区域直径（type="area" 时）
        area_label: 区域编号（如 "A1", "A2"）
    """
    s = scale
    tx, ty = _r(*target)

    # 上半圆（基准目标符号标准样式：分上下两部分）
    r = 4.0 * s  # 圆半径
    cx, cy = tx, ty

    # 画圆
    msp.add_circle((cx, cy), r, dxfattribs={"layer": layer})

    # 水平分割线
    msp.add_line((cx - r, cy), (cx + r, cy), dxfattribs={"layer": layer})

    # 上半：目标区域标记
    txt_h = 2.5 * s
    if area_label:
        msp.add_text(area_label, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        }).set_placement((cx, cy + r * 0.5),
                         align=TextEntityAlignment.MIDDLE_CENTER)

    if target_type == "area" and size > 0:
        # 下半：尺寸标注
        size_str = f"φ{size:.0f}" if size >= 1 else f"φ{size:.2f}"
        msp.add_text(size_str, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "ENG",
        }).set_placement((cx, cy - r * 0.5),
                         align=TextEntityAlignment.MIDDLE_CENTER)

    # 引出线（从圆右边缘出发）
    lx = cx + r
    msp.add_line((lx, cy), (lx + 6 * s, cy), dxfattribs={"layer": layer})

    # 基准字母在横线上方
    if datum_id:
        msp.add_text(datum_id, dxfattribs={
            "layer": "文字", "height": 2.8 * s, "style": "ENG",
        }).set_placement((lx + 3 * s, cy + 3 * s),
                         align=TextEntityAlignment.MIDDLE_CENTER)

    if tracker is not None:
        tracker.register(cx - r, cy - r, cx + r + 8 * s, cy + r + 4 * s, margin=20)

    return (cx + r + 6 * s, cy + r)


# ─── 批量 GD&T ──────────────────────────────────────────

def draw_gdt_table(msp, origin, items: list, scale: float = 100.0,
                   label: str = "形位公差要求",
                   layer: str = "尺寸标注",
                   tracker=None):
    """批量生成 GD&T 表格。

    items: 列表，每项为字典 {
        "target": (x, y), "type": 公差类型, "value": 公差值,
        "datum": 基准 (可选), "datum2": 基准2 (可选), "datum3": 基准3 (可选),
        "direction": "up"|"down"|"left"|"right" (可选),
    }
    """
    s = scale
    ox, oy = _r(*origin)

    if label:
        from .annotate import _t
        _t(msp, label, (ox, oy + 2 * s), 4.0 * s,
           align=TextEntityAlignment.LEFT, layer="文字-标题",
           tracker=tracker)

    cur_y = oy
    for i, item in enumerate(items):
        target_pt = item["target"]
        dr = item.get("direction", "up")
        ldr = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
        leader = ldr.get(dr, (0, 1))

        end = draw_feature_control_frame(
            msp, target_pt,
            tol_type=item["type"],
            value=item["value"],
            datum=item.get("datum", ""),
            datum2=item.get("datum2", ""),
            datum3=item.get("datum3", ""),
            scale=scale,
            material=item.get("material", ""),
            diametric=item.get("diametric", False),
            leader_dir=leader,
            layer=layer,
            tracker=tracker,
        )
        cur_y = min(cur_y, end[1])

    return cur_y
