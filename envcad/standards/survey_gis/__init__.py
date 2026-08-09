"""envcad.survey_gis —— 测绘与 GIS 行业模块。

模块清单：
  23. topo_symbols   地形图符号库      GB/T 20257.1—2017
  24. control_point  测量控制点        GB/T 20257.1 4.1 / GB/T 12898—2009
  25. pipe_detection 管线探测图        CJJ 61-2017（见模块内标准号核验说明）
  26. as_built_frame 竣工测绘图框      GB/T 50001—2017 / GB/T 14689—2008
  27. boundary       红线 / 用地图     GB/T 50001—2017 / GB/T 50103—2010

全部图层、文字样式（仿宋 GB2312 "HZ"）、图框与标注均复用 envcad 既有
已验证实现，本包不修改 envcad 源码。
"""
from ._common import (ENVCAD_ROOT, FrameInfo, ensure_survey_layers,  # noqa: F401
                      new_drawing, save_dxf)
from .as_built_frame import draw_as_built_frame  # noqa: F401
from .boundary import draw_boundary  # noqa: F401
from .control_point import draw_control_network, draw_control_point  # noqa: F401
from .pipe_detection import draw_pipe_detection  # noqa: F401
from .topo_symbols import draw_topo_symbols  # noqa: F401

__all__ = [
    "draw_topo_symbols", "draw_control_point", "draw_control_network",
    "draw_pipe_detection", "draw_as_built_frame", "draw_boundary",
    "new_drawing", "save_dxf", "FrameInfo", "ensure_survey_layers",
    "ENVCAD_ROOT",
]
