"""批量替换静默 except:pass → 警告（v3 精确匹配）。"""
import os, re, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "envcad"))
P = re.compile(r'except(?: Exception)?\s*:\s*\n\s+pass\b', re.MULTILINE)
FIXED = 0

for fpath in glob.glob(os.path.join(ROOT, "**/*.py"), recursive=True):
    with open(fpath, "r", encoding="utf-8") as f:
        orig = f.read()
    mod = orig
    while True:
        m = P.search(mod)
        if not m:
            break
        b = m.group()
        indent = b[:b.index("except")]
        # 保留有意义的注释：跳过旧版/不支持/跳过
        if "旧版" in b or "不支持" in b or "跳过" in b:
            mod = mod.replace(b, b + "", 1)  # 不再处理
            continue
        # 生成警告
        if "Exception" in b:
            new_b = b.replace("except Exception:", "except Exception as _e:", 1)
            new_b = new_b.replace("\n        pass", "\n        print(f'[警告] 操作失败：{_e}')", 1)
        else:
            new_b = b.replace("except:", "except Exception as _e:", 1)
            new_b = new_b.replace("\n        pass", "\n        print(f'[警告] 操作失败：{_e}')", 1)
        mod = mod.replace(b, new_b, 1)
    if mod != orig:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(mod)
        FIXED += 1
        print(f"  ✓ {os.path.relpath(fpath, ROOT)}")

print(f"\n修复完成：{FIXED} 个文件")
