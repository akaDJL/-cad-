# -*- coding: utf-8 -*-
"""知识层 + 设计 + 文档自动化 冒烟验证（直接运行，无需 pytest）。"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from envcad.knowledge import materials, codes, theory, user_data
from envcad.knowledge import materials_summary, code_summary
from envcad.design.rc_beam import design_rc_beam, format_rc_beam_result
from envcad.design.section_db import select_section, format_section_choice
from envcad.docgen.spec_doc import generate_structure_spec
from envcad.docgen.calc_book import generate_calc_book
from envcad.docgen.bom_xlsx import generate_material_bom

out = os.path.abspath(os.path.join(ROOT, "out", "doc_demo"))
os.makedirs(out, exist_ok=True)

print("== 知识层 ==")
print(materials_summary())
print(code_summary())
print("规范:", codes.code_names())

print("\n== 设计验算 RC梁 (b=250,h=500,C30,HRB400,M=120kN·m,V=180kN,l=6000) ==")
r = design_rc_beam(250, 500, 20, "C30", "HRB400", M=120e6, V=180e3, l=6000)
print(format_rc_beam_result(r))
assert r["rebar"]["area"] > 0, "配筋计算异常"

print("\n== 型钢选用 (按纵筋面积) ==")
ch = select_section("I", r["rebar"]["area"])
print(format_section_choice(ch))

print("\n== 生成文档 ==")
p1 = generate_structure_spec(os.path.join(out, "结构设计总说明.docx"), project="阳泉某车间")
p2 = generate_calc_book(os.path.join(out, "结构计算书.docx"), r, project="KL1")
p3 = generate_material_bom(os.path.join(out, "材料表.xlsx"))
print("说明 :", p1)
print("计算书:", p2)
print("材料表:", p3)
assert os.path.getsize(p1) > 0 and os.path.getsize(p2) > 0 and os.path.getsize(p3) > 0

print("\nALL OK ->", out)
