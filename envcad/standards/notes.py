"""技术说明与施工要求 v1.0。

生成通用技术说明块、材料规格表、施工/安装要求、自动换行文本。
所有说明内容由用户或 Agent 提供，代码只负责排版和绘制。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ══════════════════════════════════════════════════════════
#  技术说明块
# ══════════════════════════════════════════════════════════

def draw_notes_block(msp, origin, notes: List[str],
                      title: str = "技术要求",
                      width: float = 80.0,
                      scale: float = 100.0,
                      numbered: bool = True,
                      layer_box: str = "粗实线",
                      layer_text: str = "文字",
                      tracker=None) -> Tuple[float, float]:
    """绘制技术说明块（编号列表 + 外框）。

    参数:
        origin: 左上角 (x, y)
        notes: 说明条目列表 ["所有焊缝须经无损检测", "螺栓预紧力矩 120N·m", ...]
        width: 块宽度（图纸 mm）
        numbered: 是否加序号
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    txt_h = 2.8 * s
    title_h = 4.0 * s
    line_sp = txt_h * 1.8
    pad = 3.0 * s

    cur_y = oy

    # ── 标题 ──
    t = msp.add_text(title, dxfattribs={
        "layer": "文字-标题", "height": title_h, "style": "HZ",
    })
    t.set_placement((ox + pad, cur_y - pad - title_h * 0.3),
                    align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= title_h + line_sp * 0.5

    # ── 内容 ──
    content_y = cur_y
    for i, note in enumerate(notes):
        prefix = f"{i + 1}. " if numbered else "· "
        full_text = prefix + note

        # 换行处理（根据宽度粗略估算）
        est_chars = int(w / (txt_h * 0.6))  # 每行约字符数
        if len(full_text) > est_chars and est_chars > 10:
            lines = _wrap_text(full_text, est_chars)
        else:
            lines = [full_text]

        for line in lines:
            t = msp.add_text(line, dxfattribs={
                "layer": layer_text, "height": txt_h, "style": "HZ",
            })
            t.set_placement((ox + pad, cur_y),
                            align=TextEntityAlignment.MIDDLE_LEFT)
            cur_y -= line_sp

    content_h = content_y - cur_y

    # ── 外框 ──
    box_h = content_h + pad * 2 + title_h + line_sp * 0.5
    msp.add_lwpolyline(
        [(ox, oy), (ox + w, oy),
         (ox + w, oy - box_h), (ox, oy - box_h)],
        close=True, dxfattribs={"layer": layer_box}
    )

    if tracker:
        tracker.register(ox, oy - box_h, ox + w, oy, margin=20)

    return (ox + w, oy - box_h)


# ══════════════════════════════════════════════════════════
#  材料规格表
# ══════════════════════════════════════════════════════════

def draw_material_spec_table(msp, origin, specs: List[dict],
                              title: str = "材料规格",
                              scale: float = 100.0,
                              layer_grid: str = "细实线",
                              layer_text: str = "文字",
                              layer_header: str = "粗实线",
                              tracker=None):
    """绘制材料规格说明表。

    参数:
        specs: [{"item":"管道","material":"Q235B","standard":"GB/T 3091",
                  "note":"热镀锌"}, ...]
    """
    s = scale
    ox, oy = _r(*origin)

    cols = [
        ("项目", 16.0, "left"),
        ("材质/牌号", 20.0, "center"),
        ("执行标准", 22.0, "center"),
        ("备注", 22.0, "left"),
    ]

    col_w = [c[1] * s for c in cols]
    total_w = sum(col_w)
    row_h = 7.0 * s
    txt_h = 2.5 * s
    hdr_h = 3.0 * s

    # 标题
    title_h = 5.0 * s
    _tbl_cell(msp, ox, oy - title_h, total_w, title_h, title,
              "center", 3.5 * s, layer_grid, layer_text)
    cur_y = oy - title_h

    # 表头
    cx = ox
    for i, (name, _, align) in enumerate(cols):
        _tbl_cell(msp, cx, cur_y - row_h, col_w[i], row_h, name,
                  "center", hdr_h, layer_grid, layer_text,
                  bold_layer=layer_header)
        cx += col_w[i]
    cur_y -= row_h

    # 数据
    for spec in specs:
        vals = [
            str(spec.get("item", "")),
            str(spec.get("material", "")),
            str(spec.get("standard", "")),
            str(spec.get("note", "")),
        ]
        cx = ox
        for i, val in enumerate(vals):
            _tbl_cell(msp, cx, cur_y - row_h, col_w[i], row_h, val,
                      cols[i][2], txt_h, layer_grid, layer_text)
            cx += col_w[i]
        cur_y -= row_h

    msp.add_lwpolyline(
        [(ox, oy - title_h), (ox + total_w, oy - title_h),
         (ox + total_w, cur_y), (ox, cur_y)],
        close=True, dxfattribs={"layer": layer_header}
    )

    if tracker:
        tracker.register(ox, cur_y, ox + total_w, oy, margin=30)

    return (ox + total_w, cur_y)


# ══════════════════════════════════════════════════════════
#  施工/安装要求
# ══════════════════════════════════════════════════════════

def draw_construction_notes(msp, origin, sections: List[dict],
                              scale: float = 100.0,
                              tracker=None):
    """绘制施工安装要求（多段说明）。

    参数:
        sections: [{"title":"焊接要求","items":["焊前预热至150°C",...]},
                   {"title":"安装要求","items":[...]}, ...]
    """
    s = scale
    ox, oy = _r(*origin)
    cur_y = oy

    for sec in sections:
        title = sec.get("title", "")
        items = sec.get("items", [])
        if title or items:
            end = draw_notes_block(
                msp, (ox, cur_y), items,
                title=title, width=80, scale=scale,
                numbered=True, tracker=tracker)
            cur_y = end[1] - 5 * s

    return cur_y


# ══════════════════════════════════════════════════════════
#  自动换行文字块
# ══════════════════════════════════════════════════════════

def draw_text_block(msp, origin, text: str,
                     width: float = 80.0,
                     scale: float = 100.0,
                     txt_height: float = 3.0,
                     layer: str = "文字",
                     align: str = "left",
                     tracker=None) -> Tuple[float, float]:
    """绘制自动换行文字块。

    参数:
        text: 长文本内容（含 \n 手动换行）
        width: 文字块宽度（图纸 mm）
        txt_height: 字高（图纸 mm，未乘 scale）
    """
    s = scale
    ox, oy = _r(*origin)
    w = width * s
    txt_h = txt_height * s
    line_sp = txt_h * 1.6

    # 预估每行字符数（中文字宽 ≈ 字高，英文 ≈ 0.6×字高）
    est_chars = int(w / (txt_h * 0.75))

    # 先按 \n 分段
    paragraphs = text.split("\\n")

    cur_y = oy
    max_line_y = oy

    for para in paragraphs:
        if not para.strip():
            cur_y -= line_sp
            continue

        # 按宽度自动换行
        wrapped = _wrap_text(para, est_chars)

        for line in wrapped:
            if align == "center":
                px = ox + w / 2
                a = TextEntityAlignment.MIDDLE_CENTER
            elif align == "right":
                px = ox + w - 2 * s
                a = TextEntityAlignment.MIDDLE_RIGHT
            else:
                px = ox + 2 * s
                a = TextEntityAlignment.MIDDLE_LEFT

            t = msp.add_text(line, dxfattribs={
                "layer": layer, "height": txt_h, "style": "HZ",
            })
            t.set_placement((px, cur_y), align=a)
            cur_y -= line_sp

        max_line_y = cur_y

    if tracker:
        tracker.register(ox, cur_y, ox + w, oy, margin=20)

    return (ox + w, cur_y)


def _wrap_text(text: str, max_chars: int) -> List[str]:
    """中英混排自动换行。"""
    lines = []
    current = ""
    current_len = 0.0

    for ch in text:
        # 中文字符宽度 ≈ 1，英文/数字 ≈ 0.5
        is_cjk = ord(ch) > 0x2000
        ch_width = 1.0 if is_cjk else 0.6

        if current_len + ch_width > max_chars and current:
            lines.append(current)
            current = ch
            current_len = ch_width
        else:
            current += ch
            current_len += ch_width

    if current:
        lines.append(current)

    return lines if lines else [text]


def _tbl_cell(msp, x0, y0, w, h, text, align, txt_h,
              layer_grid, layer_text, bold_layer=None):
    """表格单元格。"""
    layer = bold_layer if bold_layer else layer_grid
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)],
        close=True, dxfattribs={"layer": layer})
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
