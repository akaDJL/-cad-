# -*- coding: utf-8 -*-
"""诊断：每个 standards/ 模块依赖哪些 knowledge 共享文件？
输出一张依赖矩阵，看清哪些文件是真正的并行瓶颈。
"""
import os, re, sys, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

STD_DIR = os.path.join(BASE, "envcad", "standards")
COMP_DIR = os.path.join(BASE, "envcad", "components")
DESIGN_DIR = os.path.join(BASE, "envcad", "design")
DOCGEN_DIR = os.path.join(BASE, "envcad", "docgen")

# 所有 knowledge 模块名（共享数据源）
KB_MODS = []
for f in os.listdir(os.path.join(BASE, "envcad", "knowledge")):
    if f.endswith(".py") and not f.startswith("__"):
        KB_MODS.append(f[:-3])

# 扫描 standards/ 下所有 .py，统计 import 依赖
results = []  # [(file, [依赖的kb模块...])]

def scan_dir(directory, label):
    out = []
    if not os.path.isdir(directory):
        return out
    for f in sorted(os.listdir(directory)):
        if not f.endswith(".py") or f.startswith("__"):
            continue
        path = os.path.join(directory, f)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        deps = []
        for mod in KB_MODS:
            # 匹配 from ..knowledge import xxx 或 from ..knowledge.xxx
            if f"knowledge.{mod}" in text or f"import {mod}" in text:
                deps.append(mod)
        out.append((f, deps))
    return out

std_deps = scan_dir(STD_DIR, "standards")
comp_deps = scan_dir(COMP_DIR, "components")
design_deps = scan_dir(DESIGN_DIR, "design")
docgen_deps = scan_dir(DOCGEN_DIR, "docgen")

# 统计：每个共享 knowledge 模块被多少个 standards 文件依赖
dep_count = collections.Counter()
for fname, deps in std_deps + comp_deps + design_deps + docgen_deps:
    for d in deps:
        dep_count[d] += 1

print("=" * 60)
print("  共享 knowledge 模块被引用次数（并行瓶颈排行）")
print("=" * 60)
print(f"{'knowledge 模块':<25} {'被引用次数':>10}  风险")
print("-" * 60)
for mod, cnt in dep_count.most_common():
    risk = "[HIGH]" if cnt >= 5 else ("[MID]" if cnt >= 2 else "[LOW]")
    print(f"  {mod:<23} {cnt:>8}  {risk}")

print()
print("=" * 60)
print("  standards/ 模块依赖详情（只列有依赖的）")
print("=" * 60)
for fname, deps in std_deps + comp_deps:
    if deps:
        print(f"  {fname:<30} -> {', '.join(deps)}")
