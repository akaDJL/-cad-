# -*- coding: utf-8 -*-
"""给型钢数据补充 A 和 Ax 字段，匹配 section_db.py 的期望"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

post_process = '''

# ══════════════════════════════════════════════════════════
#  数据后处理：统一型钢格式，补充 A(面积cm2) 和 Ax(惯性矩cm4)
# ══════════════════════════════════════════════════════════

def _normalize_section_data(data_dict):
    """统一型钢数据格式：补充 A、W、Ax 字段。"""
    result = {}
    for name, p in data_dict.items():
        new_p = dict(p)
        # 面积 A (cm2): 从 kg_m 推算 (钢密度7.85g/cm3)
        if 'kg_m' in new_p and 'A' not in new_p:
            new_p['A'] = round(new_p['kg_m'] / 7.85 * 100, 2)
        # 截面模量 W (cm3): 从 Wx_cm3 映射
        if 'Wx_cm3' in new_p and 'W' not in new_p:
            new_p['W'] = new_p['Wx_cm3']
        # 惯性矩 Ax (cm4): 近似 Ax = W * h/2
        if 'W' in new_p and 'h' in new_p and 'Ax' not in new_p:
            new_p['Ax'] = round(new_p['W'] * new_p['h'] / 2.0, 1)
        result[name] = new_p
    return result

I_BEAM = _normalize_section_data(I_BEAM)
CHANNEL = _normalize_section_data(CHANNEL)
ANGLE_EQUAL = _normalize_section_data(ANGLE_EQUAL)
if 'ANGLE_L' in dir():
    ANGLE_L = _normalize_section_data(ANGLE_L)
if 'H_BEAM' in dir():
    H_BEAM = _normalize_section_data(H_BEAM)
if 'H_BEAM_HN' in dir():
    H_BEAM_HN = _normalize_section_data(H_BEAM_HN)
'''

path = os.path.join(BASE, 'envcad', 'knowledge', 'materials.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 追加到文件末尾
content = content.rstrip() + '\n' + post_process

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('已追加型钢数据后处理函数')
