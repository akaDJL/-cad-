# -*- coding: utf-8 -*-
"""分析 cli.py 的注册机制和依赖关系"""
import re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

with open(os.path.join(BASE, 'envcad', 'cli.py'), 'r', encoding='utf-8') as f:
    content = f.read()

# 1. DOMAIN_REGISTRY 结构
start = content.find('DOMAIN_REGISTRY = {')
# 找到匹配的结束括号
depth = 0
end = start
for i, ch in enumerate(content[start:], start):
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
registry_block = content[start:end]
domains = re.findall(r'"(\w+)":\s*\{', registry_block)
print('DOMAIN_REGISTRY 中的领域数:', len(domains))
for d in domains:
    print(f'  - {d}')

# 2. 检查每个领域引用了哪个 knowledge 模块
print()
print('=== 领域 -> knowledge 依赖关系 ===')
for d in domains:
    pattern = f'"{d}":'.replace('$','\\$')
    block_start = registry_block.find(f'"{d}":')
    if block_start < 0:
        continue
    # 找这个 domain 的 block
    block_end = registry_block.find('"', block_start + len(d) + 4)
    block = registry_block[block_start:block_start+500]
    module_match = re.search(r'"module":\s*"(envcad\.\w+\.\w+)"', block)
    if module_match:
        print(f'  {d:25s} -> {module_match.group(1)}')

# 3. 检查 __init__.py 的注册
print()
print('=== knowledge/__init__.py 注册的模块 ===')
with open(os.path.join(BASE, 'envcad', 'knowledge', '__init__.py'), 'r', encoding='utf-8') as f:
    init_content = f.read()
imports = re.findall(r'(\w+)(?:,|\s)', init_content[init_content.find('from . import'):init_content.find(')]')])
print('已注册:', ', '.join(imports[:30]))

# 4. 找出哪些文件是"公共注册点"
print()
print('=== 冲突风险分析 ===')
print('高风险文件（每个新领域都要修改）:')
print('  1. envcad/cli.py          - DOMAIN_REGISTRY 必须追加新领域')
print('  2. envcad/knowledge/__init__.py - 新 knowledge 模块必须 import')
print('  3. envcad/__init__.py     - 可能需要导出')
print()
print('低风险文件（每个领域独立一个文件）:')
print('  - envcad/knowledge/xxx_data.py   (知识数据，互不影响)')
print('  - envcad/standards/xxx.py        (绘图标准，互不影响)')
print('  - envcad/design/xxx.py            (设计逻辑，互不影响)')
print('  - envcad/docgen/xxx_doc.py        (文档生成，互不影响)')
print('  - envcad/drawings/txx.py          (图纸模板，互不影响)')
