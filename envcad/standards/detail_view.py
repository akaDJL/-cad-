"""节点详图自动放大——选定区域自动生成放大视口+标注。

施工图深度第3项：detail circle → magnified viewport in paper space。
"""
from __future__ import annotations
from typing import Tuple, Optional
from ..utils import _r


def create_detail_view(doc, msp_center: Tuple[float, float],
                       radius: float, label: str = "I",
                       scale: float = 100.0, zoom_factor: float = 5.0,
                       paper="A2", layout_name="详图",
                       vp_center=(210, 148), vp_size=(350, 250),
                       tracker=None):
    """在主图画详图圈，在纸空间创建放大视口。

    Args:
        doc: ezdxf 文档
        msp_center: 主图中详图中心点 (模型空间坐标)
        radius: 详图圈半径 (模型单位 mm)
        label: 详图编号
        scale: 主图比例
        zoom_factor: 放大倍数（详图 = 主图 × zoom_factor）
        paper: 纸张尺寸
        layout_name: 布局名
        vp_center: 放大视口位置 (纸上坐标)
        vp_size: 放大视口大小

    Returns:
        layout 对象
    """
    from .views import draw_detail_circle, draw_detail_label
    from .paperspace import create_layout, add_viewport, setup_print_config

    s = scale; r = radius * s; zf = zoom_factor
    cx, cy = _r(*msp_center)
    msp = doc.modelspace()

    # 主图：画详图圈 + 标签
    draw_detail_circle(msp, (cx, cy), radius, label=label, view_scale=s)
    draw_detail_label(msp, (cx + r + 5 * s, cy), label=label, view_scale=s)

    # 纸空间：创建放大视口
    layout = create_layout(doc, f"{layout_name} {label}", paper)
    setup_print_config(layout, paper=paper)

    # 视口中心对准主图详图中心，放大
    vp_cx, vp_cy = _r(*vp_center)
    vw, vh = vp_size
    vp = add_viewport(layout, (vp_cx, vp_cy), vw, vh, scale=s / zf)

    try:
        vp.dxf.view_target_point = (cx, cy)
        vp.dxf.view_height = radius * 2.5 * s / zf
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')

    return layout


def add_detail_callout(msp, center: Tuple[float, float],
                       radius: float, label: str = "I",
                       view_direction: str = "right",
                       scale: float = 100.0, layer="详图标注",
                       tracker=None):
    """加详图引出线+标注。会画圈+引线+标签文字。

    与 create_detail_view 配合使用：
    1. 在主图画调用 add_detail_callout
    2. 在纸空间调用 create_detail_view

    view_direction: "right" / "left" / "up" / "down" — 引线方向
    """
    from .views import draw_detail_circle
    s = scale; r = radius * s
    cx, cy = _r(*center)
    msp_local = msp

    draw_detail_circle(msp_local, (cx, cy), radius, label=label, view_scale=s)

    # 引线
    directions = {"right": (1, 0), "left": (-1, 0), "up": (0, 1), "down": (0, -1)}
    dx, dy = directions.get(view_direction, (1, 0))
    ex = cx + r * dx + 5 * s * dx
    ey = cy + r * dy + 5 * s * dy
    msp_local.add_line((cx + r * dx, cy + r * dy), (ex, ey),
                       dxfattribs={"layer": layer})

    # 标签
    from ezdxf.enums import TextEntityAlignment
    t = msp_local.add_text(f"详图 {label}\n{int(radius)}mm 范围",
                           dxfattribs={"layer": "文字", "height": 2.5 * s, "style": "HZ"})
    t.set_placement((ex + 2 * s * dx, ey + 2 * s * dy),
                    align=TextEntityAlignment.MIDDLE_LEFT if dx > 0 else
                           TextEntityAlignment.MIDDLE_RIGHT if dx < 0 else
                           TextEntityAlignment.MIDDLE_CENTER)
    return (ex, ey)
