# -*- coding: utf-8 -*-
"""统一型钢数据格式，匹配 section_db.py 和 bom_xlsx.py 的期望
原始格式键: h, b, d(或tw), t(或tf), r, A(面积cm2), W(截面模量cm3), Ax(惯性矩cm4), kg_m
简化格式键: h, b, d, t, Wx_cm3, kg_m

需要把所有型钢数据统一为包含: A, W, Ax 这三个键
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from envcad.knowledge import materials

def convert_to_original_format(data_dict):
    """把简化格式转换为原始格式（补充 A, W, Ax 字段）"""
    result = {}
    for name, p in data_dict.items():
        new_p = dict(p)  # 复制
        # 如果有 Wx_cm3 但没有 W，映射过去
        if 'Wx_cm3' in new_p and 'W' not in new_p:
            new_p['W'] = new_p['Wx_cm3']
        # 如果有 kg_m 但没有 A，估算面积（钢密度7.85g/cm3）
        if 'kg_m' in new_p and 'A' not in new_p:
            new_p['A'] = round(new_p['kg_m'] / 7.85 * 100, 2)  # cm2
        # 如果有 W 和 h，估算 Ax = W * h/2
        if 'W' in new_p and 'h' in new_p and 'Ax' not in new_p:
            new_p['Ax'] = round(new_p['W'] * new_p['h'] / 2.0, 1)  # cm4
        result[name] = new_p
    return result

# 转换并更新
materials.I_BEAM = convert_to_original_format(materials.I_BEAM)
materials.CHANNEL = convert_to_original_format(materials.CHANNEL)
materials.ANGLE_EQUAL = convert_to_original_format(materials.ANGLE_EQUAL)
if hasattr(materials, 'ANGLE_L'):
    materials.ANGLE_L = convert_to_original_format(materials.ANGLE_L)
if hasattr(materials, 'H_BEAM'):
    materials.H_BEAM = convert_to_original_format(materials.H_BEAM)
if hasattr(materials, 'H_BEAM_HN'):
    materials.H_BEAM_HN = convert_to_original_format(materials.H_BEAM_HN)

# 验证
print('I20a:', materials.I_BEAM['I20a'])
print('[10:', materials.CHANNEL['[10'])
print('L50x5:', materials.ANGLE_EQUAL['L50×5'])
if hasattr(materials, 'ANGLE_L'):
    print('L100x63x8:', materials.ANGLE_L.get('L100×63×8', 'not found'))
if hasattr(materials, 'H_BEAM'):
    h_keys = list(materials.H_BEAM.keys())[:3]
    for k in h_keys:
        print(f'{k}:', materials.H_BEAM[k])

print()
print('格式统一完成')
