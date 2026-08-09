# -*- coding: utf-8 -*-
"""5 个新行业（电气/给排水/暖通/液压/化工）知识+设计+文档 回归测试。

覆盖：
  - 知识层：规范清单、经济选型序列、概览摘要
  - 设计层：负荷/电缆/照度(电气)、用水量/管径/排水(给排水)、
            冷热负荷/风量/风管(暖通)、缸/泵/管(液压)、
            经济管径/泵/换热器(化工)
  - 文档自动化：DOCX 说明书 + XLSX 清单（各 5 行业）
  - CLI：envcad doc <type> 与 envcad design <kind> 全绿
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from envcad.knowledge import elec_data, plumb_data, hvac_data, hyd_data, proc_data
from envcad.design import electrical, plumbing, hvac, hydraulic, process


# ────────────────────────────────────────────────────────────
# 知识层
# ────────────────────────────────────────────────────────────
def test_elec_knowledge():
    assert len(elec_data.ELEC_CODES) >= 7
    s = elec_data.elec_summary()
    assert isinstance(s, str) and len(s) > 10


def test_plumb_knowledge():
    assert len(plumb_data.PLUMB_CODES) >= 6
    assert len(plumb_data.plumb_summary()) > 0
    # 公称直径 -> 外径 查表 & 上取公称直径
    assert plumb_data.pipe_di(50) > 0
    assert plumb_data.next_dn(57) >= 50


def test_hvac_knowledge():
    assert len(hvac_data.HVAC_CODES) >= 6
    assert len(hvac_data.hvac_summary()) > 0


def test_hyd_knowledge():
    assert len(hyd_data.HYD_CODES) >= 6
    assert len(hyd_data.hyd_summary()) > 0


def test_proc_knowledge():
    assert len(proc_data.PROC_CODES) >= 6
    assert len(proc_data.DN_SERIES) >= 10
    assert len(proc_data.ECON_VELOCITY) >= 3
    assert isinstance(proc_data.proc_summary(), str) and len(proc_data.proc_summary()) > 0


# ────────────────────────────────────────────────────────────
# 设计层
# ────────────────────────────────────────────────────────────
def test_elec_design():
    load = electrical.design_power_load(100, kind="办公照明")
    cable = electrical.select_cable(load["Ijs"], cos=load["cos"], length=50)
    illum = electrical.design_illumination(800, place="办公室")
    sc = electrical.estimate_short_circuit(630)
    assert isinstance(load, dict) and load["Ijs"] > 0
    assert isinstance(cable, dict) and cable["section"] > 0
    assert isinstance(illum, dict) and illum.get("E_actual", 0) > 0
    assert isinstance(sc, dict) and sc.get("Ik", 0) > 0


def test_plumb_design():
    demand = plumbing.design_water_demand(500, kind="办公楼")
    flow = plumbing.design_supply_flow(100)
    pipe = plumbing.size_supply_pipe(flow["qg"])
    drain = plumbing.design_drainage(80)
    pump = plumbing.design_pump_head(20)
    assert demand["Qs"] > 0 and pipe["dn"] > 0
    assert isinstance(drain, dict) and drain.get("qp", 0) > 0
    assert isinstance(pump, dict) and pump.get("H", 0) > 0


def test_hvac_design():
    hload = hvac.design_load(800, place="办公室")
    air = hvac.design_air_volume(800, 3.0, place="办公室")
    fresh = hvac.design_fresh_air(80, place="办公室")
    duct = hvac.size_duct(air["L"])
    assert hload["Qc"] > 0 and duct["w"] > 0
    assert isinstance(fresh, dict) and fresh.get("Lf", 0) > 0


def test_hydraulic_design():
    cyl = hydraulic.design_cylinder(50, p=16, v=0.1)
    hpump = hydraulic.select_pump(cyl["Q"], p=16)
    hpipe = hydraulic.size_hyd_pipe(cyl["Q"], p=16)
    assert cyl["D"] > 0 and hpump["P"] > 0 and hpipe.get("d", 0) > 0


def test_process_design():
    ppipe = process.size_econ_pipe(30, medium="水_一般")
    ppump = process.design_pump(30, 32)
    hx = process.design_heat_exchanger(500)
    assert ppipe["dn"] > 0 and hx["A_design"] > 0
    assert isinstance(ppump, dict) and ppump.get("Pm", 0) > 0


# ────────────────────────────────────────────────────────────
# 文档自动化（DOCX + XLSX）
# ────────────────────────────────────────────────────────────
def test_elec_doc(tmp_path):
    from envcad.docgen.elec_doc import generate_elec_spec, generate_load_xlsx
    load = electrical.design_power_load(100, kind="办公照明")
    cable = electrical.select_cable(load["Ijs"], cos=load["cos"], length=50)
    illum = electrical.design_illumination(800, place="办公室")
    sc = electrical.estimate_short_circuit(630)
    p1 = os.path.join(tmp_path, "电气设计说明书.docx")
    p2 = os.path.join(tmp_path, "负荷计算表.xlsx")
    generate_elec_spec(p1, project="阳泉配电工程", load=load, cable=cable,
                       illum=illum, sc=sc)
    generate_load_xlsx(p2)
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


def test_plumb_doc(tmp_path):
    from envcad.docgen.plumb_doc import generate_plumb_spec, generate_water_xlsx
    demand = plumbing.design_water_demand(500, kind="办公楼")
    flow = plumbing.design_supply_flow(100)
    pipe = plumbing.size_supply_pipe(flow["qg"])
    drain = plumbing.design_drainage(80)
    pump = plumbing.design_pump_head(20)
    p1 = os.path.join(tmp_path, "给排水设计说明书.docx")
    p2 = os.path.join(tmp_path, "用水量计算表.xlsx")
    generate_plumb_spec(p1, project="阳泉给排水工程", demand=demand, flow=flow,
                        pipe=pipe, drain=drain, pump=pump)
    generate_water_xlsx(p2)
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


def test_hvac_doc(tmp_path):
    from envcad.docgen.hvac_doc import generate_hvac_spec, generate_hvac_xlsx
    hload = hvac.design_load(800, place="办公室")
    air = hvac.design_air_volume(800, 3.0, place="办公室")
    fresh = hvac.design_fresh_air(80, place="办公室")
    duct = hvac.size_duct(air["L"])
    p1 = os.path.join(tmp_path, "暖通空调设计说明书.docx")
    p2 = os.path.join(tmp_path, "分区负荷设备表.xlsx")
    generate_hvac_spec(p1, project="阳泉空调工程", load=hload, air=air,
                       fresh=fresh, duct=duct)
    generate_hvac_xlsx(p2)
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


def test_hydraulic_doc(tmp_path):
    from envcad.docgen.hyd_doc import generate_hyd_calc, generate_hyd_bom
    cyl = hydraulic.design_cylinder(50, p=16, v=0.1)
    hpump = hydraulic.select_pump(cyl["Q"], p=16)
    hpipe = hydraulic.size_hyd_pipe(cyl["Q"], p=16)
    p1 = os.path.join(tmp_path, "液压系统设计计算书.docx")
    p2 = os.path.join(tmp_path, "液压元件清单.xlsx")
    generate_hyd_calc(p1, project="阳泉液压站", cyl=cyl, pump=hpump, pipe=hpipe)
    generate_hyd_bom(p2)
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


def test_proc_doc(tmp_path):
    from envcad.docgen.proc_doc import generate_proc_spec, generate_proc_bom
    ppipe = process.size_econ_pipe(30, medium="水_一般")
    ppump = process.design_pump(30, 32)
    hx = process.design_heat_exchanger(500)
    p1 = os.path.join(tmp_path, "化工工艺设计说明书.docx")
    p2 = os.path.join(tmp_path, "设备管道清单.xlsx")
    generate_proc_spec(p1, project="阳泉化工装置", pipe=ppipe, pump=ppump, hx=hx)
    generate_proc_bom(p2)
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


# ────────────────────────────────────────────────────────────
# CLI 验收（doc 10 类 + 代表性 design 类）
# ────────────────────────────────────────────────────────────
DOC_CASES = [
    ("elec", "电气设计说明书.docx"),
    ("elec-bom", "负荷计算表.xlsx"),
    ("plumb", "给排水设计说明书.docx"),
    ("plumb-bom", "用水量计算表.xlsx"),
    ("hvac", "暖通空调设计说明书.docx"),
    ("hvac-bom", "分区负荷设备表.xlsx"),
    ("hyd", "液压系统设计计算书.docx"),
    ("hyd-bom", "液压元件清单.xlsx"),
    ("proc", "化工工艺设计说明书.docx"),
    ("proc-bom", "设备管道清单.xlsx"),
]


@pytest.mark.parametrize("dtype,expected", DOC_CASES)
def test_cli_doc(tmp_path, dtype, expected):
    from envcad import cli
    rc = cli.main(["doc", dtype, "--out", str(tmp_path), "--project", "测试"])
    assert rc == 0
    assert os.path.exists(os.path.join(tmp_path, expected))


def test_cli_design_new_kinds():
    from envcad import cli
    # 设计类（仅打印，不落地文件），覆盖 5 行业代表 kind
    for kind in ("load", "cable", "illum",
                 "water", "supply", "drain",
                 "cooling", "duct",
                 "cylinder", "pump",
                 "pipe", "hx"):
        rc = cli.main(["design", kind])
        assert rc == 0, f"design {kind} 返回非零"
