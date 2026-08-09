# -*- coding: utf-8 -*-
"""三行业（土木/环保/机械）知识+设计+文档 回归测试。"""
import os, sys, pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from envcad.knowledge import civil, env_data, mech_data


# ── 知识层 ────────────────────────────────────────────
def test_civil_knowledge():
    assert len(civil.SOIL) >= 12
    assert len(civil.CIVIL_CODES) >= 5
    assert civil.soil_props("中砂")["phi"] == 32
    assert 0 < civil.active_earth_coef(32) < 1


def test_env_knowledge():
    assert "一级A" in env_data.WATER_GB18918
    assert env_data.water_limit("一级A")["COD"] > 0
    assert len(env_data.ENV_CODES) >= 5


def test_mech_knowledge():
    assert len(mech_data.MECH_MATERIAL) >= 8
    assert mech_data.round_to_module(1.3) == 1.5
    assert mech_data.round_to_std_diameter(21) == 22


# ── 土木设计 ──────────────────────────────────────────
def test_foundation_footing():
    from envcad.design.foundation import design_spread_footing
    r = design_spread_footing(1200.0, soil="粉质粘土", d=1.5)
    assert r["A"] > 0
    assert r["ok"] is True, r["note"]


def test_retaining_wall():
    from envcad.design.foundation import design_retaining_wall
    r = design_retaining_wall(4.5)          # 默认中砂回填 + 0.75H 底宽
    assert r["all_ok"] is True, r["note"]


# ── 环保设计 ──────────────────────────────────────────
def test_aeration_and_sed():
    from envcad.design.env_process import design_aeration_tank, design_sed_tank
    aer = design_aeration_tank(10000.0, 200.0, Se=10.0)
    sed = design_sed_tank(10000.0)
    assert aer["V"] > 0 and aer["removal"] > 90
    assert sed["D"] > 0


def test_dust_collector():
    from envcad.design.env_process import design_dust_collector
    r = design_dust_collector(50000.0, kind="baghouse")
    assert r["ok"] is True, r["note"]


# ── 机械设计 ──────────────────────────────────────────
def test_gear_check():
    from envcad.design.gear import check_spur_gear
    r = check_spur_gear(5.0, 960.0, z1=20, z2=60, material="40Cr")
    assert r["mn"] > 0
    assert r["all_ok"] is True, r["note"]      # 软齿面接触控制选模数后应两者满足


def test_shaft_design():
    from envcad.design.shaft import design_shaft
    r = design_shaft(5.0, 960.0, material="45钢")
    assert r["d"] > 0
    assert r["all_ok"] is True, r["check"]["note"]


# ── 文档自动化 ────────────────────────────────────────
def test_geotech_doc(tmp_path):
    from envcad.design.foundation import design_spread_footing, design_retaining_wall
    from envcad.docgen.geotech_doc import generate_geotech_spec
    f = design_spread_footing(1200.0)
    w = design_retaining_wall(4.5)
    p = os.path.join(tmp_path, "基础说明.docx")
    generate_geotech_spec(p, project="测试", footing=f, retaining=w)
    assert os.path.getsize(p) > 0


def test_env_docs(tmp_path):
    from envcad.design.env_process import design_aeration_tank, design_sed_tank
    from envcad.docgen.env_report import generate_env_spec, generate_discharge_xlsx
    aer = design_aeration_tank(10000.0, 200.0)
    sed = design_sed_tank(10000.0)
    p1 = os.path.join(tmp_path, "工艺说明.docx")
    generate_env_spec(p1, project="测试厂", aeration=aer, sed=sed)
    p2 = os.path.join(tmp_path, "排放清单.xlsx")
    generate_discharge_xlsx(p2, standard="一级A")
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


def test_mech_docs(tmp_path):
    from envcad.design.gear import check_spur_gear
    from envcad.design.shaft import design_shaft
    from envcad.docgen.mech_calc import generate_mech_calc, generate_parts_xlsx
    g = check_spur_gear(5.0, 960.0, material="40Cr")
    s = design_shaft(5.0, 960.0)
    p1 = os.path.join(tmp_path, "计算说明书.docx")
    generate_mech_calc(p1, project="减速器", gear=g, shaft=s)
    p2 = os.path.join(tmp_path, "零件明细表.xlsx")
    generate_parts_xlsx(p2)
    assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0


# ── CLI ───────────────────────────────────────────────
def test_cli_doc_geotech(tmp_path):
    from envcad import cli
    rc = cli.main(["doc", "geotech", "--out", str(tmp_path), "--project", "测试"])
    assert rc == 0
    assert os.path.exists(os.path.join(tmp_path, "地基与基础设计说明.docx"))


def test_cli_doc_env(tmp_path):
    from envcad import cli
    rc = cli.main(["doc", "env", "--out", str(tmp_path), "--project", "测试厂"])
    assert rc == 0
    assert os.path.exists(os.path.join(tmp_path, "环保工艺设计说明书.docx"))


def test_cli_doc_mech(tmp_path):
    from envcad import cli
    rc = cli.main(["doc", "mech", "--out", str(tmp_path), "--project", "减速器"])
    assert rc == 0
    assert os.path.exists(os.path.join(tmp_path, "机械设计计算说明书.docx"))


def test_cli_design_gear():
    from envcad import cli
    rc = cli.main(["design", "gear", "--power", "5", "--rpm", "960"])
    assert rc == 0
