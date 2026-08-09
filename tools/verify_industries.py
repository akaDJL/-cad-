# -*- coding: utf-8 -*-
"""三行业（土木/环保/机械）知识+设计+文档端到端验证。

运行：
  python tools/verify_industries.py
生成样例文件到 out/industries/ 并断言全部成功。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join("out", "industries")
os.makedirs(OUT, exist_ok=True)


def _ok(path):
    assert os.path.exists(path) and os.path.getsize(path) > 0, f"文件未生成: {path}"
    print(f"  ✓ {os.path.basename(path)}  ({os.path.getsize(path)} bytes)")


print("=" * 60)
print("【知识层概览】")
from envcad.knowledge import civil, env_data, mech_data
print("  土木:", civil.civil_summary() if hasattr(civil, "civil_summary")
      else f"土层 {len(civil.SOIL)} 种 | 规范 {len(civil.CIVIL_CODES)} 本")
print("  环保:", env_data.env_summary() if hasattr(env_data, "env_summary")
      else f"水/气/噪声限值 + 规范 {len(env_data.ENV_CODES)} 本")
print("  机械:", mech_data.mech_summary())

# ── 土木 ──────────────────────────────────────────────
print("=" * 60)
print("【土木：地基/基础/挡土墙】")
from envcad.design.foundation import (design_spread_footing,
                                      design_retaining_wall,
                                      format_footing_result,
                                      format_retaining_result)
from envcad.docgen.geotech_doc import generate_geotech_spec

footing = design_spread_footing(1200.0, soil="粉质粘土", d=1.5)
retaining = design_retaining_wall(4.5)   # 回填默认中砂(无粘性透水料)
print(format_footing_result(footing))
print(format_retaining_result(retaining))
p = os.path.join(OUT, "地基与基础设计说明.docx")
generate_geotech_spec(p, project="阳泉某厂房", footing=footing,
                      retaining=retaining)
_ok(p)

# ── 环保 ──────────────────────────────────────────────
print("=" * 60)
print("【环保：污水/除尘工艺】")
from envcad.design.env_process import (design_aeration_tank, design_sed_tank,
                                       design_dust_collector,
                                       format_wwtp_result, format_dust_result)
from envcad.docgen.env_report import (generate_env_spec,
                                      generate_discharge_xlsx)

aer = design_aeration_tank(10000.0, 200.0, Se=10.0)
sed = design_sed_tank(10000.0)
dust = design_dust_collector(50000.0, kind="baghouse")
print(format_wwtp_result(aer, sed))
print(format_dust_result(dust))
p1 = os.path.join(OUT, "环保工艺设计说明书.docx")
generate_env_spec(p1, project="XX污水处理厂", discharge_std="一级A",
                  aeration=aer, sed=sed, dust=dust)
_ok(p1)
p2 = os.path.join(OUT, "污染物排放达标清单.xlsx")
generate_discharge_xlsx(p2, standard="一级A")
_ok(p2)

# ── 机械 ──────────────────────────────────────────────
print("=" * 60)
print("【机械：齿轮/轴校核】")
from envcad.design.gear import check_spur_gear, format_gear_result
from envcad.design.shaft import design_shaft, format_shaft_result
from envcad.docgen.mech_calc import generate_mech_calc, generate_parts_xlsx

gear = check_spur_gear(5.0, 960.0, z1=20, z2=60, material="40Cr")
shaft = design_shaft(5.0, 960.0, material="45钢")
print(format_gear_result(gear))
print(format_shaft_result(shaft))
p3 = os.path.join(OUT, "机械设计计算说明书.docx")
generate_mech_calc(p3, project="单级圆柱齿轮减速器", gear=gear, shaft=shaft)
_ok(p3)
p4 = os.path.join(OUT, "零件明细表.xlsx")
generate_parts_xlsx(p4, project="单级圆柱齿轮减速器")
_ok(p4)

print("=" * 60)
print("全部三行业端到端验证通过 ✓  样例目录：", os.path.abspath(OUT))
