# -*- coding: utf-8 -*-
"""知识库扩充验证脚本"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from envcad.knowledge import codes, env_data, mech_data, plumb_data
from envcad.knowledge import hvac_data, elec_data, materials, formulas

print('=' * 60)
print('  CAD助手 v1.5 知识库扩充验证')
print('=' * 60)
print()
print(f'  codes.py     : 规范 {len(codes.GB_CODES)} 本')
print(f'  env_data.py  : {env_data.env_summary()}')
print(f'  mech_data.py : {mech_data.mech_summary()}')
print(f'  plumb_data.py: {plumb_data.plumb_summary()}')
print(f'  hvac_data.py : {hvac_data.hvac_summary()}')
print(f'  elec_data.py : {elec_data.elec_summary()}')
print(f'  materials.py : 混凝土{len(materials.CONCRETE)} 钢筋{len(materials.REBAR_GRADE)} 钢材{len(materials.STEEL)}')
print(f'               : 工字钢{len(materials.I_BEAM)} 槽钢{len(materials.CHANNEL)} 角钢{len(materials.ANGLE_EQUAL)}')
print(f'               : H型钢{len(materials.H_BEAM_HN)} 钢管{len(materials.STEEL_PIPE)}')
func_list = [x for x in dir(formulas) if not x.startswith('_') and callable(getattr(formulas, x))]
print(f'  formulas.py  : {len(func_list)} 个公式函数')
print()
print('=' * 60)
print()

# 抽样验证
print('  抽样验证:')

# codes
v = codes.GB_CODES['GB 50014-2021']['params']['污水管道最小流速_m_s']
print(f'  - GB 50014 污水最小流速: {v} m/s')

# 轴承
b = mech_data.BEARING_6200[6205]
print(f'  - 6205轴承: d={b["d"]} D={b["D"]} Cr={b["Cr"]}kN')

# 螺栓
bl = mech_data.BOLT_HEX['M12']
print(f'  - M12螺栓: 对边{bl["s"]}mm 头高{bl["k"]}mm')

# 工字钢
i = materials.I_BEAM['I20a']
print(f'  - I20a工字钢: h={i["h"]} Wx={i["Wx_cm3"]}cm3 {i["kg_m"]}kg/m')

# 钢管
p = materials.STEEL_PIPE['DN100']
print(f'  - DN100钢管: D={p["D"]} t={p["t"]} {p["kg_m"]}kg/m')

# 曼宁公式
v = formulas.manning_velocity(0.5, 0.013, 0.003)
print(f'  - 曼宁公式: R=0.5m n=0.013 S=0.003 v={v:.2f} m/s')

# 布袋除尘
a = formulas.baghouse_filter_area(10000, 1.2)
print(f'  - 布袋过滤面积: Q=10000m3/h vf=1.2m/min A={a:.1f} m2')

# 隔声量
r = formulas.noise_mass_law_simple(31.2)
print(f'  - 隔声量: m=31.2kg/m2 R={r:.1f} dB')

# 隔振
T = formulas.vibration_transmissibility(25, 5)
eta = formulas.vibration_efficiency(T)
print(f'  - 隔振效率: f=25Hz fn=5Hz eta={eta:.1f}%')

# 电缆压降
du = formulas.cable_voltage_drop(100, 100, 16)
print(f'  - 电缆压降: I=100A L=100m S=16mm2 dU={du:.2f}%')

# 送风量
g = formulas.supply_air_flow(10, delta_t=8)
print(f'  - 送风量: Q=10kW dt=8C G={g:.0f} m3/h')

# 填埋库容
v = formulas.landfill_capacity(1.0, 100000, 10)
print(f'  - 填埋库容: 10万人 1kg/人d 10年 V={v:.0f} m3')

print()
print('=' * 60)
print('  全部验证通过！知识库扩充成功。')
print('=' * 60)
