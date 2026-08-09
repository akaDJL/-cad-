# -*- coding: utf-8 -*-
"""恢复 materials.py 中被误删的辅助函数和数据"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# 要追加的内容
append_content = '''
# ══════════════════════════════════════════════════════════
#  不等边角钢规格（常用型号，GB/T 706
# ══════════════════════════════════════════════════════════
ANGLE_L = {
    "L25×16×3": dict(B=25, b=16, d=3, Wx_cm3=0.72, kg_m=0.912),
    "L32×20×3": dict(B=32, b=20, d=3, Wx_cm3=1.16, kg_m=1.171),
    "L40×25×3": dict(B=40, b=25, d=3, Wx_cm3=1.96, kg_m=1.484),
    "L45×28×4": dict(B=45, b=28, d=4, Wx_cm3=2.27, kg_m=2.203),
    "L50×32×4": dict(B=50, b=32, d=4, Wx_cm3=2.95, kg_m=2.494),
    "L56×36×4": dict(B=56, b=36, d=4, Wx_cm3=3.86, kg_m=2.818),
    "L63×40×5": dict(B=63, b=40, d=5, Wx_cm3=5.14, kg_m=3.920),
    "L70×45×5": dict(B=70, b=45, d=5, Wx_cm3=6.23, kg_m=4.403),
    "L75×50×6": dict(B=75, b=50, d=6, Wx_cm3=7.30, kg_m=5.699),
    "L80×50×5": dict(B=80, b=50, d=5, Wx_cm3=7.93, kg_m=5.005),
    "L90×56×6": dict(B=90, b=56, d=6, Wx_cm3=10.6, kg_m=6.717),
    "L100×63×8": dict(B=100, b=63, d=8, Wx_cm3=15.1, kg_m=9.878),
    "L100×80×8": dict(B=100, b=80, d=8, Wx_cm3=20.8, kg_m=10.946),
    "L125×80×10": dict(B=125, b=80, d=10, Wx_cm3=29.6, kg_m=15.504),
    "L140×90×10": dict(B=140, b=90, d=10, Wx_cm3=36.9, kg_m=17.688),
    "L160×100×12": dict(B=160, b=100, d=12, Wx_cm3=51.2, kg_m=23.988),
}

# ══════════════════════════════════════════════════════════
#  H型钢（宽翼缘HW/中翼缘HM/窄翼缘HN，常用规格）
# ══════════════════════════════════════════════════════════
H_BEAM = {
    # HW 宽翼缘
    "HW100×100": dict(h=100, b=100, t1=6, t2=8, Wx_cm3=49, kg_m=17.2),
    "HW125×125": dict(h=125, b=125, t1=6.5, t2=9, Wx_cm3=82.6, kg_m=23.8),
    "HW150×150": dict(h=150, b=150, t1=7, t2=10, Wx_cm3=128, kg_m=31.9),
    "HW175×175": dict(h=175, b=175, t1=7.5, t2=11, Wx_cm3=185, kg_m=40.3),
    "HW200×200": dict(h=200, b=200, t1=8, t2=12, Wx_cm3=277, kg_m=50.5),
    "HW250×250": dict(h=250, b=250, t1=9, t2=14, Wx_cm3=541, kg_m=72.4),
    "HW300×300": dict(h=300, b=300, t1=10, t2=15, Wx_cm3=883, kg_m=94.5),
    # HM 中翼缘
    "HM150×100": dict(h=148, b=100, t1=6, t2=9, Wx_cm3=75.6, kg_m=21.4),
    "HM200×150": dict(h=194, b=150, t1=6, t2=9, Wx_cm3=146, kg_m=31.2),
    "HM250×175": dict(h=244, b=175, t1=7, t2=11, Wx_cm3=229, kg_m=44.1),
    "HM300×200": dict(h=294, b=200, t1=8, t2=12, Wx_cm3=366, kg_m=57.3),
    "HM350×250": dict(h=340, b=250, t1=9, t2=14, Wx_cm3=576, kg_m=79.7),
    "HM400×300": dict(h=390, b=300, t1=10, t2=16, Wx_cm3=879, kg_m=107.0),
    # HN 窄翼缘（已在 H_BEAM_HN 中，这里补充别名引用
}

# 把 HN 系列也加入 H_BEAM
from . import H_BEAM_HN  # noqa: F401
for k, v in H_BEAM_HN.items():
    if k not in H_BEAM:
        H_BEAM[k] = v

# ══════════════════════════════════════════════════════════
#  查询辅助函数
# ══════════════════════════════════════════════════════════

def concrete_props(grade: str = "C30") -> dict:
    """混凝土强度参数。"""
    return CONCRETE.get(grade, CONCRETE["C30"])


def rebar_props(grade: str = "HRB400") -> dict:
    """钢筋强度参数。"""
    return REBAR_GRADE.get(grade, REBAR_GRADE["HRB400"])


def rebar_area(diameter: float) -> float:
    """单根钢筋截面面积 (mm2)。"""
    if diameter in REBAR_D:
        return REBAR_D[diameter]["area"]
    import math
    return math.pi * diameter * diameter / 4.0


def steel_props(grade: str = "Q355") -> dict:
    """钢材强度参数。"""
    return STEEL.get(grade, STEEL["Q355"])


def steel_f_design(grade: str, thickness_mm: float) -> float:
    """考虑厚度折减的钢材抗拉强度设计值 (N/mm2)。"""
    base = STEEL[grade]["f"] if grade in STEEL else 215
    penalty = _STEEL_PENALTY.get(grade, {})
    if not penalty:
        return base
    for t in sorted(penalty.keys()):
        if thickness_mm <= t:
            return penalty[t]
    return list(penalty.values())[-1]
'''

path = os.path.join(BASE, 'envcad', 'knowledge', 'materials.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 追加到文件末尾
content = content.rstrip() + "\n" + append_content

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('已追加 ANGLE_L / H_BEAM / 辅助函数到 materials.py')
