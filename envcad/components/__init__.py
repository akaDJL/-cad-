"""环保专业组件库 v1.5：管道 / 管件 / 池体 / 阀门 / 环保设备。

组件按 1:1 实物尺寸（mm）绘制到 modelspace，所有尺寸乘 scale（出图比例倒数）。
平面图用单线+符号，剖面图用双线+剖面线，符合制图规范。
"""


# 管件组件（原有 + v1.5 扩展）
from .fittings import (
    draw_valve, draw_soft_joint, draw_flow_meter,
    draw_flange, draw_check_valve, draw_wall_sleeve,
    # v1.5 新增阀门
    draw_butterfly_valve, draw_diaphragm_valve,
    draw_globe_valve, draw_ball_valve,
    draw_sampling_valve, draw_regulating_valve,
    draw_plug_valve, draw_any_valve, VALVE_DRAWERS,
    # v1.5 新增管件
    draw_elbow, draw_tee, draw_reducer,
    draw_flange_pair, draw_cross, draw_pipe_cap,
    # v1.5 仪表符号
    draw_instrument_symbol,
)

# 环保专用设备（v1.5 新增）
from .env_equipment import (
    draw_self_priming_pump, draw_vertical_multistage_pump,
    draw_submersible_pump, draw_mixer,
    draw_dosing_system, draw_clo2_generator,
    draw_gate_valve, draw_bar_screen,
    ENV_EQUIPMENT_LEGEND,
)

# 紧固件组件（螺栓/螺母/螺钉/垫圈）
from .fasteners import (
    draw_hex_bolt, draw_hex_nut, draw_screw,
    draw_washer, draw_spring_washer, draw_bolt_assembly,
    list_specs,
    GB_BOLTS, GB_NUTS, GB_SCREWS_HEX_SOCKET, GB_SCREWS_PAN,
    GB_WASHERS, GB_SPRING_WASHERS,
    get_bolt_params, get_nut_params, get_screw_params, get_washer_params,
)
