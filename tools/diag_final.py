# -*- coding: utf-8 -*-
import os, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kb_dir = os.path.join(BASE, "envcad", "knowledge")
kb_names = [f[:-3] for f in os.listdir(kb_dir) if f.endswith(".py") and not f.startswith("__")]

cnt = collections.Counter()
refs = collections.defaultdict(list)

for subdir in ["design", "docgen"]:
    d = os.path.join(BASE, "envcad", subdir)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith(".py") or f.startswith("__"):
            continue
        path = os.path.join(d, f)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            src = fh.read()
        for kn in kb_names:
            if "knowledge." + kn in src or "import " + kn in src:
                cnt[kn] += 1
                refs[kn].append(subdir + "/" + f)

print("=" * 80)
print("  共享 knowledge 模块被引用排行（真正的并行瓶颈）")
print("=" * 80)
header = "  knowledge模块           引用次数  风险     引用者"
print(header)
print("-" * 80)
for mod, c in cnt.most_common():
    risk = "[HIGH]" if c >= 3 else ("[MID]" if c >= 2 else "[LOW]")
    who = ", ".join(refs[mod][:3])
    if len(refs[mod]) > 3:
        who += "..."
    line = "  %-22s %8d  %-7s  %s" % (mod, c, risk, who)
    print(line)

print()
print("=" * 80)
print("  完全独立的领域知识模块（只被自己领域的 design+docgen 引用）")
print("=" * 80)
# 每个 *_data 模块只被同名的 design/docgen 引用 -> 独立
domain_specific = []
shared = []
for mod, c in cnt.most_common():
    referrers = refs[mod]
    # 看引用者是否都来自同一领域
    stem = mod.replace("_data", "")
    if all(stem in r for r in referrers):
        domain_specific.append(mod)
    else:
        shared.append(mod)

print("  领域专属（可安全并行）:")
for m in domain_specific:
    print("    " + m + " <- " + ", ".join(refs[m]))
print()
print("  共享（多领域交叉引用，并行需协调）:")
for m in shared:
    print("    " + m + " <- " + ", ".join(refs[m]))
