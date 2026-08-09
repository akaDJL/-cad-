"""envcad 扩展包 —— 电子与半导体（ELECTRONICS & SEMICONDUCTOR）行业模块。

本包不修改 envcad 原包，仅以只读方式复用其图层、文字样式、图框、标注、
明细表与技术要求等已验证的国标实现（见 _common.py）。

模块清单:
    11 board_outline  PCB 外形框            IPC-2221B / GB/T 4588.3
    12 ic_qfp         IC 封装 QFP           JEDEC MS-026 / JEP95
    13 ic_bga         IC 封装 BGA           JEDEC MO-192 / IPC-7095
    14 connector      连接器（板对板/排针） IEC 61076 / IEC 60603-2
    15 heatsink       散热器（翅片/针柱）   GB/T 1804 / GB/T 6892
    16 enclosure      机箱壳体 / 面板开孔   GB/T 1804 / IEC 60297-3-100
"""
from .board_outline import draw_board_outline
from .connector import draw_connector
from .enclosure import draw_enclosure
from .heatsink import draw_heatsink
from .ic_bga import draw_ic_bga
from .ic_qfp import draw_ic_qfp

__all__ = [
    "draw_board_outline", "draw_ic_qfp", "draw_ic_bga",
    "draw_connector", "draw_heatsink", "draw_enclosure",
]
