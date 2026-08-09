"""图纸空间 / 布局 / 视口 / 打印配置（GB/T 14689—2008, GB/T 50001—2017）

在 ezdxf 中，R2000+ 的图纸空间通过 Layout 实现。
本模块提供施工图交付必备的布局创建、视口管理、打印配置。
"""
from __future__ import annotations

import ezdxf
from ezdxf.enums import TextEntityAlignment
from ..utils import _r

# ─── 标准纸张幅面 (mm) ──────────────────────────────────
PAPER_SIZES = {
    "A0": (1189, 841), "A1": (841, 594), "A2": (594, 420),
    "A3": (420, 297),  "A4": (297, 210),
    "A0_L": (1189, 841), "A1_L": (594, 841),
}


def create_layout(doc, name="布局1", paper="A3", landscape=True):
    """创建图纸空间布局（等同 AutoCAD 的 Layout 页签）。

    Args:
        doc: ezdxf 文档
        name: 布局名称
        paper: 纸张尺寸（A0/A1/A2/A3/A4）
        landscape: True=横幅, False=竖幅
    Returns:
        layout 对象
    """
    layout = doc.layouts.new(name)
    pw, ph = PAPER_SIZES.get(paper, PAPER_SIZES["A3"])
    if not landscape:
        pw, ph = ph, pw

    # 画纸张边界（虚线标注裁切范围）
    layout.add_lwpolyline(
        [(0, 0), (pw, 0), (pw, ph), (0, ph)],
        close=True,
        dxfattribs={"layer": "细实线", "linetype": "DASHED"},
    )

    # 图框（细实线，按 GB/T 14689，10mm 留边）
    frame = layout.add_lwpolyline(
        [(5, 5), (pw - 5, 5), (pw - 5, ph - 5), (5, ph - 5)],
        close=True,
        dxfattribs={"layer": "图框"},
    )
    return layout


def add_viewport(layout, center, width, height, scale=100.0, layer="0"):
    """在布局中添加视口，将模型空间内容按比例映射。

    Args:
        layout: 布局对象
        center: (x, y) 视口中心 (mm, 纸上坐标)
        width: 视口宽度 (mm)
        height: 视口高度 (mm)
        scale: 模型单位→图纸单位的缩放比例
        layer: 图层

    Returns:
        viewport 实体
    """
    cx, cy = _r(*center)
    hw, hh = width / 2, height / 2

    vp = layout.add_viewport(
        center=(cx, cy),
        size=(width, height),
        view_center_point=(cx, cy),
        view_height=height * scale,
        dxfattribs={"layer": layer},
    )
    # 设置视口比例
    try:
        vp.dxf.view_target_point = (cx, cy)
        vp.dxf.view_height = height * scale
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')

    return vp


def setup_print_config(layout, ctb=None, paper="A3", landscape=True):
    """配置打印样式（标注性，DPI等由 CAD 打开后设置）。"""
    if ctb:
        try:
            layout.dxf.current_style_sheet = ctb
        except Exception as _e:
            print(f'[WARNING] paperspace.py: {_e}')


def add_title_block(layout, origin, width, height,
                    project="", drawing_no="", rev="A", scale_str="1:100",
                    industry="general"):
    """在布局中绘制标题栏（右下角）。

    Args:
        layout: 布局对象
        origin: (x, y) 标题栏左上角
        width: 标题栏总宽
        height: 标题栏总高
        project: 项目名
        drawing_no: 图号
        rev: 版次
        scale_str: 比例文字
        industry: 行业标识
    """
    ox, oy = _r(*origin)
    msp = layout  # 布局本身可用作 modelspace 来画图

    # 标题栏外框（粗实线）
    msp.add_lwpolyline(
        [(ox, oy), (ox + width, oy),
         (ox + width, oy - height), (ox, oy - height)],
        close=True,
        dxfattribs={"layer": "粗实线"},
    )

    # 内隔线（细实线）
    h = height
    rows = 4
    rh = h / rows
    for i in range(1, rows):
        y = oy - i * rh
        msp.add_line((ox, y), (ox + width, y),
                     dxfattribs={"layer": "细实线"})

    # 列分隔
    cols = [(0.6, "项目名称"), (0.25, "图号"), (0.15, "版次")]
    x = ox
    for frac, label in cols:
        cw = width * frac
        msp.add_line((x + cw, oy), (x + cw, oy - h),
                     dxfattribs={"layer": "细实线"})
        x += cw

    # 标题文字
    txt_h = 3.5
    data = [
        (ox + 2, oy - rh + 2, f"项目: {project}"),
        (ox + 2, oy - 2 * rh + 2, f"比例: {scale_str}"),
        (ox + width * 0.6 + 2, oy - rh + 2, f"图号: {drawing_no}"),
        (ox + width * 0.6 + 2, oy - 2 * rh + 2, f"版次: {rev}"),
    ]
    for dx, dy, txt in data:
        t = msp.add_text(txt, dxfattribs={
            "layer": "文字", "height": txt_h, "style": "HZ",
        })
        t.set_placement((dx, dy), align=TextEntityAlignment.BOTTOM_LEFT)

    return (ox + width, oy - height)


def quick_sheet(doc, paper="A3", project="", drawing_no="",
                vp_center=(210, 148), vp_size=(380, 270), scale=100.0):
    """一键创建标准图纸（布局 + 视口 + 标题栏）。

    Args:
        doc: ezdxf 文档
        paper: 纸张尺寸
        project: 项目名
        drawing_no: 图号
        vp_center: 视口中心 (纸上坐标 mm)
        vp_size: 视口大小 (宽, 高 mm)
        scale: 绘图比例

    Returns:
        layout 对象
    """
    layout = create_layout(doc, name="Sheet1", paper=paper)
    setup_print_config(layout, paper=paper)
    add_viewport(layout, vp_center, vp_size[0], vp_size[1], scale=scale)
    pw, ph = PAPER_SIZES.get(paper, PAPER_SIZES["A3"])
    tw, th = 180, 20  # 标题栏尺寸
    add_title_block(layout, (pw - 10 - tw, ph - 10), tw, th,
                    project=project, drawing_no=drawing_no, scale_str=f"1:{int(scale)}")
    return layout
