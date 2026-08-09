"""测试2：竖流斜管沉淀池平剖面图。

直径 6m，总高 5.5m，污泥斗 1.5m，斜管区 1.2m；
中心进水管、周边出水堰、DN150 排泥管；标注各部位标高、管径；
A3 图幅标题栏与安装技术要求，比例 1:50。
"""
from __future__ import annotations

import os

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame
from ..standards.annotate import _t
from ..components.pool import draw_circular_pool_plan, draw_circular_pool_section
from . import draw_tech_notes
from ezdxf.enums import TextEntityAlignment


def gen_t2(out_dir: str, scale: float = 50.0,
           diameter: float = 6000.0, total_h: float = 5.5,
           hopper_h: float = 1.5, tube_h: float = 1.2,
           inlet_dn: float = 300, sludge_dn: float = 150) -> str:
    doc, dim, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    info = FrameInfo(
        title="竖流斜管沉淀池平剖面图",
        drawing_no="T2-01",
        scale_str=f"1:{int(scale)}",
        project="单体构筑物测试",
        unit="环保工程",
        designer="envcad",
        date="2026.07",
    )
    x0, y0, x1, y1 = draw_frame(doc, scale, info, tracker=tracker)

    # 平面图（左）
    plan_cx = x0 + 3500
    plan_cy = y0 + (y1 - y0) * 0.58
    draw_circular_pool_plan(msp, (plan_cx, plan_cy), diameter, 250, scale,
                            name="竖流斜管沉淀池", inlet_dn=inlet_dn, sludge_dn=sludge_dn,
                            tracker=tracker)
    _t(msp, "平面图", (plan_cx, y0 + 9 * scale), 3.5 * scale,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
       tracker=tracker)

    # 剖面图（右）
    sec_x = x0 + 11000
    sec_y = y0 + (y1 - y0) * 0.78  # 池顶图上 y
    draw_circular_pool_section(msp, sec_x, sec_y, diameter, total_h, hopper_h, tube_h,
                               250, scale, top_elev=0.300,
                               name="竖流斜管沉淀池", inlet_dn=inlet_dn, sludge_dn=sludge_dn,
                               tracker=tracker)
    _t(msp, "1-1 剖面图", (sec_x + diameter / 2, y0 + 9 * scale), 3.5 * scale,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字-标题",
       tracker=tracker)

    # 安装技术要求
    draw_tech_notes(msp, (x1 - 95 * scale, y1 - 32 * scale), scale,
                    "安装技术要求",
                    ["池体采用 C30 钢筋混凝土，抗渗等级 P6，壁厚 250mm。",
                     "斜管采用蜂窝斜管填料，管径 Φ80，安装倾角 60°。",
                     f"中心进水管 DN{int(inlet_dn)}，排泥管 DN{int(sludge_dn)}，管材 UPVC。",
                     "周边出水堰采用三角堰，堰口高程一致，高差≤2mm。",
                     "池体内壁做环氧树脂玻璃钢防腐（两布三油）。",
                     "施工及验收执行 GB 50141—2008。"],
                    tracker=tracker)

    return save_dxf(doc, os.path.join(out_dir, "T2_竖流斜管沉淀池平剖面图.dxf"))
