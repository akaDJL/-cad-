# -*- coding: utf-8 -*-
"""端到端验证 5 个新行业（电气/给排水/暖通/液压/化工）知识+设计+文档三件套。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from envcad.knowledge import elec_data, plumb_data, hvac_data, hyd_data, proc_data
from envcad.design import electrical, plumbing, hvac, hydraulic, process
from envcad.docgen.elec_doc import generate_elec_spec, generate_load_xlsx
from envcad.docgen.plumb_doc import generate_plumb_spec, generate_water_xlsx
from envcad.docgen.hvac_doc import generate_hvac_spec, generate_hvac_xlsx
from envcad.docgen.hyd_doc import generate_hyd_calc, generate_hyd_bom
from envcad.docgen.proc_doc import generate_proc_spec, generate_proc_bom

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "out", "new_industries")
os.makedirs(OUT, exist_ok=True)


def p(name):
    return os.path.join(OUT, name)


print("=" * 60)
print("知识层概览")
print("  电气 :", elec_data.elec_summary())
print("  给排水:", plumb_data.plumb_summary())
print("  暖通 :", hvac_data.hvac_summary())
print("  液压 :", hyd_data.hyd_summary())
print("  化工 :", proc_data.proc_summary())

print("=" * 60)
print("【电气】")
load = electrical.design_power_load(100, kind="办公照明")
cable = electrical.select_cable(load["Ijs"], cos=load["cos"], length=50)
illum = electrical.design_illumination(800, place="办公室")
sc = electrical.estimate_short_circuit(630)
print(" ", load["note"])
print(" ", cable["note"])
assert load["Ijs"] > 0 and cable["section"] > 0
generate_elec_spec(p("电气设计说明书.docx"), project="阳泉配电工程",
                   load=load, cable=cable, illum=illum, sc=sc)
generate_load_xlsx(p("负荷计算表.xlsx"))

print("【给排水】")
demand = plumbing.design_water_demand(500, kind="办公楼")
flow = plumbing.design_supply_flow(100)
pipe = plumbing.size_supply_pipe(flow["qg"])
drain = plumbing.design_drainage(80)
pump = plumbing.design_pump_head(20)
print(" ", demand["note"])
print(" ", pipe["note"])
assert demand["Qs"] > 0 and pipe["dn"] > 0
generate_plumb_spec(p("给排水设计说明书.docx"), project="阳泉给排水工程",
                    demand=demand, flow=flow, pipe=pipe, drain=drain, pump=pump)
generate_water_xlsx(p("用水量计算表.xlsx"))

print("【暖通】")
hload = hvac.design_load(800, place="办公室")
air = hvac.design_air_volume(800, 3.0, place="办公室")
fresh = hvac.design_fresh_air(80, place="办公室")
duct = hvac.size_duct(air["L"])
print(" ", hload["note"])
print(" ", duct["note"])
assert hload["Qc"] > 0 and duct["w"] > 0
generate_hvac_spec(p("暖通空调设计说明书.docx"), project="阳泉空调工程",
                   load=hload, air=air, fresh=fresh, duct=duct)
generate_hvac_xlsx(p("分区负荷设备表.xlsx"))

print("【液压】")
cyl = hydraulic.design_cylinder(50, p=16, v=0.1)
hpump = hydraulic.select_pump(cyl["Q"], p=16)
hpipe = hydraulic.size_hyd_pipe(cyl["Q"], p=16)
print(" ", cyl["note"])
print(" ", hpump["note"])
assert cyl["D"] > 0 and hpump["P"] > 0
generate_hyd_calc(p("液压系统设计计算书.docx"), project="阳泉液压站",
                  cyl=cyl, pump=hpump, pipe=hpipe)
generate_hyd_bom(p("液压元件清单.xlsx"))

print("【化工】")
ppipe = process.size_econ_pipe(30, medium="水_一般")
ppump = process.design_pump(30, 32)
hx = process.design_heat_exchanger(500)
print(" ", ppipe["note"])
print(" ", ppump["note"])
print(" ", hx["note"])
assert ppipe["dn"] > 0 and hx["A_design"] > 0
generate_proc_spec(p("化工工艺设计说明书.docx"), project="阳泉化工装置",
                   pipe=ppipe, pump=ppump, hx=hx)
generate_proc_bom(p("设备管道清单.xlsx"))

print("=" * 60)
files = sorted(os.listdir(OUT))
print(f"✓ 全部通过，生成 {len(files)} 个样例文件：")
for f in files:
    print("   -", f)
