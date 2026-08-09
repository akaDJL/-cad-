# -*- coding: utf-8 -*-
"""删除 cli.py 中旧的硬编码 DOMAIN_REGISTRY 内容"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(BASE, "envcad", "cli.py")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 找到旧内容起始
old_start = content.find("    # ── P1 新增")
if old_start < 0:
    print("未找到旧内容起始标记，可能已删除")
    sys.exit(0)

# 找到 auto_section 块的结束
auto_idx = content.find('"auto_section"', old_start)
if auto_idx < 0:
    print("未找到 auto_section")
    sys.exit(1)

# 从 auto_section 往后找顶层的 }
end_marker = content.find("\n}\n", auto_idx)
if end_marker < 0:
    print("未找到结束标记")
    sys.exit(1)

end_pos = end_marker + 2  # 包含 }\n

# 删除旧内容
old_block = content[old_start:end_pos]
content = content[:old_start] + content[end_pos:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"已删除旧 DOMAIN_REGISTRY 内容 ({len(old_block)} 字符)")
