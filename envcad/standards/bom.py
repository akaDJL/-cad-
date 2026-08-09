"""材料明细表 / BOM 表生成 v1.0（GB/T 10609.2—2009）。

生成标题栏上方或独立放置的材料明细表，支持序号/名称/数量/材料/备注列，
自动计算行高和列宽。

纯 ezdxf，零新依赖。
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri


# ─── 内部辅助 ───────────────────────────────────────────

# ─── BOM 列定义 ──────────────────────────────────────────

# 预设列方案
BOM_COLUMNS = {
    "standard": [  # 标准机械
        ("序号",    10.0, "center"),
        ("名称",    30.0, "left"),
        ("数量",    10.0, "center"),
        ("材料",    20.0, "center"),
        ("备注",    15.0, "left"),
    ],
    "detail": [  # 详细
        ("序号",    8.0, "center"),
        ("代号",    18.0, "center"),
        ("名称",    25.0, "left"),
        ("数量",    8.0, "center"),
        ("材料",    18.0, "center"),
        ("单件重量", 10.0, "center"),
        ("总计",    10.0, "center"),
        ("备注",    12.0, "left"),
    ],
    "pipe": [  # 管道工程
        ("序号",    8.0, "center"),
        ("名称",    25.0, "left"),
        ("规格",    18.0, "center"),
        ("数量",    10.0, "center"),
        ("单位",    8.0, "center"),
        ("材料",    15.0, "center"),
        ("备注",    12.0, "left"),
    ],
    "env": [  # 环保工程
        ("序号",    8.0, "center"),
        ("设备名称", 25.0, "left"),
        ("型号/规格", 20.0, "center"),
        ("数量",    8.0, "center"),
        ("功率/参数", 15.0, "center"),
        ("材质",    12.0, "center"),
        ("备注",    12.0, "left"),
    ],
}


def _draw_table_cell(msp, x0: float, y0: float, w: float, h: float,
                     text: str, align: str, txt_h: float,
                     layer_grid: str, layer_text: str):
    """绘制单个表格单元格。"""
    x1, y1 = x0 + w, y0 + h

    # 边框
    msp.add_lwpolyline(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        close=True, dxfattribs={"layer": layer_grid}
    )

    if not text:
        return

    # 文字
    alignment = {
        "left": TextEntityAlignment.MIDDLE_LEFT,
        "center": TextEntityAlignment.MIDDLE_CENTER,
        "right": TextEntityAlignment.MIDDLE_RIGHT,
    }.get(align, TextEntityAlignment.MIDDLE_CENTER)

    if align == "left":
        px = x0 + 0.5 * txt_h  # 左侧留边距
    elif align == "right":
        px = x1 - 0.5 * txt_h
    else:
        px = x0 + w / 2

    py = y0 + h / 2

    t = msp.add_text(str(text), dxfattribs={
        "layer": layer_text,
        "height": txt_h,
        "style": "HZ",
    })
    t.set_placement((px, py), align=alignment)


def draw_bom(msp, origin, items: List[dict],
             columns: str = "standard",
             scale: float = 100.0,
             title: str = "",
             title_height: float = 5.0,
             row_height: float = 8.0,     # 行高
             header_row: bool = True,
             sort_nums: bool = True,
             layer_grid: str = "细实线",
             layer_text: str = "文字",
             layer_header: str = "粗实线",
             tracker=None) -> Tuple[float, float]:
    """绘制材料明细表。

    参数:
        origin: 表格左上角起点 (x, y)
        items: 物料列表，每项为与列对应的值列表（或字典）
        columns: 预设列方案名 或 自定义列定义列表
                 自定义格式: [(列名, 宽度mm, 对齐方式), ...]
        scale: 出图比例倒数
        title: 表格标题（显示在最上方行）
        sort_nums: 是否自动填充序号（1,2,3...）
        row_height: 行高（图纸 mm）

    返回: 表格右下角坐标 (x, y)
    """
    s = scale

    # 解析列定义
    if isinstance(columns, str):
        col_defs = BOM_COLUMNS.get(columns, BOM_COLUMNS["standard"])
    else:
        col_defs = columns

    col_names = [c[0] for c in col_defs]
    col_widths = [c[1] * s for c in col_defs]
    col_aligns = [c[2] for c in col_defs]

    total_width = sum(col_widths)
    row_h = row_height * s
    txt_h = 2.8 * s       # 数据行字高
    hdr_txt_h = 3.2 * s   # 表头字高

    ox, oy = _r(*origin)

    # ── 标题行 ──
    cur_y = oy
    if title:
        title_h = title_height * s
        # 标题跨整个表宽
        msp.add_lwpolyline(
            [(ox, cur_y), (ox + total_width, cur_y),
             (ox + total_width, cur_y - title_h), (ox, cur_y - title_h)],
            close=True, dxfattribs={"layer": layer_grid}
        )
        t = msp.add_text(title, dxfattribs={
            "layer": layer_text, "height": 4.0 * s, "style": "HZ",
        })
        t.set_placement((ox + total_width / 2, cur_y - title_h / 2),
                        align=TextEntityAlignment.MIDDLE_CENTER)
        cur_y -= title_h

    # ── 表头行 ──
    if header_row:
        cx = ox
        for i, col_name in enumerate(col_names):
            _draw_table_cell(msp, cx, cur_y - row_h, col_widths[i], row_h,
                             col_name, "center", hdr_txt_h,
                             layer_grid, layer_text)
            cx += col_widths[i]
        cur_y -= row_h

    # ── 数据行 ──
    for i, item in enumerate(items):
        # 将 item 转为值列表
        if isinstance(item, dict):
            values = [item.get(name, "") for name in col_names]
        elif isinstance(item, (list, tuple)):
            values = list(item)
        else:
            values = [str(item)]

        # 补全或截断
        while len(values) < len(col_names):
            values.append("")
        values = values[:len(col_names)]

        # 自动序号
        if sort_nums and col_names[0] in ("序号",):
            values[0] = str(i + 1)

        cx = ox
        for j, val in enumerate(values):
            _draw_table_cell(msp, cx, cur_y - row_h, col_widths[j], row_h,
                             str(val) if val else "",
                             col_aligns[j], txt_h,
                             layer_grid, layer_text)
            cx += col_widths[j]
        cur_y -= row_h

    # ── 表格外框加粗 ──
    # 重画粗外框（覆盖原有的细线，或用粗实线再画一遍）
    bottom_y = cur_y
    top_y = oy - (title_height * s if title else 0)

    msp.add_lwpolyline(
        [(ox, top_y), (ox + total_width, top_y),
         (ox + total_width, bottom_y), (ox, bottom_y)],
        close=True, dxfattribs={"layer": layer_header}
    )

    if tracker is not None:
        tracker.register(ox, bottom_y, ox + total_width, top_y, margin=50)

    return (ox + total_width, bottom_y)


def draw_bom_from_dict(msp, origin, bom_data: dict,
                       scale: float = 100.0,
                       tracker=None) -> Tuple[float, float]:
    """从字典结构绘制 BOM 表（简化接口）。

    bom_data: {
        "title": "材料明细表",
        "columns": "standard",  # 预设名或自定义
        "items": [
            {"序号": "1", "名称": "...", "数量": "2", ...},
            ...
        ]
    }
    """
    title = bom_data.get("title", "材料明细表")
    columns = bom_data.get("columns", "standard")
    items = bom_data.get("items", [])

    return draw_bom(msp, origin, items,
                    columns=columns, scale=scale,
                    title=title, tracker=tracker)


def estimate_bom_height(n_items: int, scale: float = 100.0,
                        has_title: bool = True,
                        title_height: float = 5.0,
                        row_height: float = 8.0,
                        has_header: bool = True) -> float:
    """预估 BOM 表总高度（mm，modelspace 坐标）。

    用于在布局时判断是否有足够空间放置表格。
    """
    s = scale
    h = 0
    if has_title:
        h += title_height * s
    if has_header:
        h += row_height * s
    h += n_items * row_height * s
    return h
