# -*- coding: utf-8 -*-
"""恢复 materials.py 中被误删的辅助函数和数据"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# 先看看 section_db.py 需要什么
path = os.path.join(BASE, 'envcad', 'design', 'section_db.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有 materials.xxx 引用
import re
refs = re.findall(r'materials\.(\w+)', content)
print('section_db.py 引用的 materials 属性:')
for r in sorted(set(refs)):
    print(f'  {r}')

print()

# 看看 rc_beam.py 需要什么
path2 = os.path.join(BASE, 'envcad', 'design', 'rc_beam.py')
with open(path2, 'r', encoding='utf-8') as f:
    content2 = f.read()
refs2 = re.findall(r'materials\.(\w+)', content2)
print('rc_beam.py 引用的 materials 属性:')
for r in sorted(set(refs2)):
    print(f'  {r}')

print()

# 看看 bom_xlsx.py 需要什么
path3 = os.path.join(BASE, 'envcad', 'docgen', 'bom_xlsx.py')
with open(path3, 'r', encoding='utf-8') as f:
    content3 = f.read()
refs3 = re.findall(r'materials\.(\w+)', content3)
print('bom_xlsx.py 引用的 materials 属性:')
for r in sorted(set(refs3)):
    print(f'  {r}')
