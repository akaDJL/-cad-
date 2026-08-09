"""envcad.agri_food —— 农业食品机械行业模块（清单 17~22）。

非破坏性扩展：不修改 envcad 主包，全部几何/图层/文字/标注均复用
``envcad.standards.*`` 与 ``envcad.engine.dxf_base`` 中已验证的国标实现。

模块清单：
    17 tractor         拖拉机侧视图
    18 combine         联合收割机
    19 seeder          播种机（后视 + 侧视）
    20 irrigation      滴灌/喷灌系统（GB/T 50485—2020）
    21 screw_conveyor  螺旋输送机（纵剖 + 横断面）
    22 packaging       包装封口机
"""
from __future__ import annotations

from .combine import draw_combine
from .irrigation import draw_emitter, draw_head_unit, draw_irrigation
from .packaging import draw_conveyor, draw_packaging
from .screw_conveyor import draw_screw_conveyor, draw_screw_section
from .seeder import draw_seeder, draw_seeder_side
from .tractor import draw_tractor

__all__ = [
    "draw_tractor", "draw_combine", "draw_seeder", "draw_seeder_side",
    "draw_irrigation", "draw_emitter", "draw_head_unit",
    "draw_screw_conveyor", "draw_screw_section",
    "draw_packaging", "draw_conveyor",
]
