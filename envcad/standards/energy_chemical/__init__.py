"""能源化工行业 CAD 模块集（envcad 扩展）。

全部模块复用 envcad.standards 的图层（粗实线/中实线/细实线/虚线/点画线）、
仿宋 GB2312 文字样式、A3 图框与标注体系，不修改 envcad 源码。

模块一览
--------
==============================  ====================  ==========================
模块                            主函数                依据标准
==============================  ====================  ==========================
vertical_tank                   立式储罐              GB/T 150-2024, SH/T 3049
horizontal_tank                 卧式储罐              GB/T 150-2024, NB/T 47065.1
packed_column                   填料塔                GB/T 150-2024, HG/T 21514/21556
tray_column                     板式塔                HG/T 21514, NB/T 10557-2021
shell_tube_exchanger            列管换热器            GB/T 151
reactor_vessel                  反应釜                GB/T 150-2024, HG/T 20569
centrifugal_pump                离心泵                GB/T 5656
compressor                      压缩机                GB/T 3853, GB 50029
pipe_support                    管道支吊架            GB/T 17116, GB 50316
substation_pv_foundation        变电站/光伏/风机基础  GB 50059, GB 50797, NB/T 10311
==============================  ====================  ==========================

用法
----
>>> import sys
>>> sys.path.insert(0, r"C:/Users/lenovo/Desktop/凹凸cad小助手（二集）v1.5")
>>> from envcad.engine.dxf_base import new_drawing, save_dxf
>>> from envcad.standards.energy_chemical import add_a3_frame, draw_vertical_tank
>>> doc, dimstyle = new_drawing(scale=50)
>>> msp = doc.modelspace()
>>> ext = add_a3_frame(doc, 50, title="立式储罐装配图", drawing_no="EC-01")
>>> draw_vertical_tank(msp, 10875, 2000, scale=50, diameter=2400)
>>> save_dxf(doc, "out/tank.dxf")
"""
from __future__ import annotations

from ._common import (
    add_a3_frame, frame_center, P, text, eng_text,
    centerline, rect, hatch_area, arrow, dim_linear, leader_note,
    elevation_mark, note_block, spec_table,
    ellipsoidal_head, flat_head, nozzle, manhole,
    saddle_support, skirt_support, lug_support, support_legs, level_gauge,
)
from .vertical_tank import draw_vertical_tank, draw_vertical_tank_symbol
from .horizontal_tank import (draw_horizontal_tank,
                              draw_horizontal_tank_symbol)
from .packed_column import draw_packed_column, draw_packed_column_symbol
from .tray_column import draw_tray_column, draw_tray_column_symbol
from .shell_tube_exchanger import (draw_shell_tube_exchanger,
                                   draw_shell_tube_exchanger_symbol)
from .reactor_vessel import draw_reactor_vessel, draw_reactor_vessel_symbol
from .centrifugal_pump import (draw_centrifugal_pump,
                               draw_centrifugal_pump_symbol)
from .compressor import draw_compressor
from .pipe_support import draw_pipe_support
from .substation_pv_foundation import (draw_substation_pv_foundation,
                                       draw_substation_plan,
                                       draw_pv_array_foundation,
                                       draw_wtg_foundation)

__version__ = "1.5"

#: 模块注册表：名称 -> (绘制函数, 依据标准)
MODULE_REGISTRY = {
    "vertical_tank": (draw_vertical_tank, "GB/T 150-2024 / SH/T 3049"),
    "horizontal_tank": (draw_horizontal_tank, "GB/T 150-2024 / NB/T 47065.1"),
    "packed_column": (draw_packed_column, "GB/T 150-2024 / HG/T 21514"),
    "tray_column": (draw_tray_column, "HG/T 21514 / NB/T 10557-2021"),
    "shell_tube_exchanger": (draw_shell_tube_exchanger, "GB/T 151"),
    "reactor_vessel": (draw_reactor_vessel, "GB/T 150-2024 / HG/T 20569"),
    "centrifugal_pump": (draw_centrifugal_pump, "GB/T 5656"),
    "compressor": (draw_compressor, "GB/T 3853 / GB 50029"),
    "pipe_support": (draw_pipe_support, "GB/T 17116 / GB 50316"),
    "substation_pv_foundation": (draw_substation_pv_foundation,
                                 "GB 50059 / GB 50797 / NB/T 10311"),
}

__all__ = [
    "MODULE_REGISTRY",
    # 图框与公共件
    "add_a3_frame", "frame_center", "P", "text", "eng_text",
    "centerline", "rect", "hatch_area", "arrow", "dim_linear", "leader_note",
    "elevation_mark", "note_block", "spec_table",
    "ellipsoidal_head", "flat_head", "nozzle", "manhole",
    "saddle_support", "skirt_support", "lug_support", "support_legs",
    "level_gauge",
    # 行业模块
    "draw_vertical_tank", "draw_vertical_tank_symbol",
    "draw_horizontal_tank", "draw_horizontal_tank_symbol",
    "draw_packed_column", "draw_packed_column_symbol",
    "draw_tray_column", "draw_tray_column_symbol",
    "draw_shell_tube_exchanger", "draw_shell_tube_exchanger_symbol",
    "draw_reactor_vessel", "draw_reactor_vessel_symbol",
    "draw_centrifugal_pump", "draw_centrifugal_pump_symbol",
    "draw_compressor",
    "draw_pipe_support",
    "draw_substation_pv_foundation", "draw_substation_plan",
    "draw_pv_array_foundation", "draw_wtg_foundation",
]
