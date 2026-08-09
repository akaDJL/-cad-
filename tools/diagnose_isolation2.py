# -*- coding: utf-8 -*-
"""精确诊断：运行时 import 每个 standards 模块，看它真实依赖哪些 knowledge 子模块"""
import os, sys, importlib, traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# 先 import knowledge 基础包，让它的模块可用
import envcad.knowledge as kb_pkg

# 获取所有 knowledge 子模块名
kb_names = set()
kb_dir = os.path.join(BASE, "envcad", "knowledge")
for f in os.listdir(kb_dir):
    if f.endswith(".py") and not f.startswith("__"):
        kb_names.add(f[:-3])

print("knowledge 子模块:", sorted(kb_names))
print()

# 扫描 standards/ 每个模块
std_dir = os.path.join(BASE, "envcad", "standards")
results = []

for f in sorted(os.listdir(std_dir)):
    if not f.endswith(".py") or f.startswith("__"):
        continue
    mod_name = f[:-3]
    full_name = f"envcad.standards.{mod_name}"

    # 记录 import 前的 knowledge 属性
    before = set(name for name in dir(kb_pkg) if not name.startswith("_"))

    try:
        mod = importlib.import_module(full_name)
    except Exception as e:
        results.append((mod_name, [], f"IMPORT_FAIL: {e}"))
        continue

    # 看模块源码里 import 了哪些 knowledge
    src_path = os.path.join(std_dir, f)
    with open(src_path, "r", encoding="utf-8", errors="ignore") as fh:
        src = fh.read()

    deps = []
    for kn in kb_names:
        # 匹配 patterns: knowledge.kn, knowledge import kn, import kn
        if f"knowledge.{kn}" in src or f"import {kn}" in src:
            deps.append(kn)

    results.append((mod_name, deps, "OK"))

# 输出矩阵
print("=" * 70)
print("  standards 模块 -> knowledge 依赖矩阵")
print("=" * 70)
print(f"  {'standards 模块':<30} {'knowledge 依赖'}")
print("-" * 70)

has_dep_count = 0
no_dep_count = 0
for mod_name, deps, status in results:
    if "IMPORT_FAIL" in status:
        print(f"  {mod_name:<30} [FAIL] {status.split(':',1)[1].strip()[:40]}")
        continue
    if deps:
        has_dep_count += 1
        print(f"  {mod_name:<30} {', '.join(deps)}")
    else:
        no_dep_count += 1

print("-" * 70)
print(f"  有 knowledge 依赖: {has_dep_count} 个")
print(f"  无 knowledge 依赖: {no_dep_count} 个 (完全独立)")
print()

# 统计被依赖最多的 knowledge 模块
import collections
dep_cnt = collections.Counter()
for _, deps, status in results:
    if "IMPORT_FAIL" in status:
        continue
    for d in deps:
        dep_cnt[d] += 1

print("=" * 70)
print("  共享 knowledge 模块被引用排行（真正的并行瓶颈）")
print("=" * 70)
print(f"  {'knowledge 模块':<25} {'被standards引用次数':>15}  风险")
print("-" * 70)
for mod, cnt in dep_cnt.most_common():
    risk = "[HIGH]" if cnt >= 3 else ("[MID]" if cnt >= 2 else "[LOW]")
    print(f"  {mod:<25} {cnt:>12}  {risk}")

# 真正零依赖（完全独立）的 standards 模块
print()
print("=" * 70)
print("  完全独立的 standards 模块（零 knowledge 依赖，可任意并行）")
print("=" * 70)
for mod_name, deps, status in results:
    if "IMPORT_FAIL" in status:
        continue
    if not deps:
        print(f"  {mod_name}")
