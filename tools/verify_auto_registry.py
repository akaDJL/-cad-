# -*- coding: utf-8 -*-
"""端到端验证：模拟新增一个领域，验证自动注册全流程"""
import os, sys, tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

print("=" * 60)
print("  自动注册器 - 端到端验证")
print("=" * 60)

# 1. 验证自动发现所有领域
from envcad.auto_registry import load_domain_registry, list_domains, domain_count

registry = load_domain_registry()
print(f"\n1. 自动发现 {domain_count()} 个领域")
assert domain_count() == 32, f"期望32个，实际{domain_count()}"

# 2. 验证 knowledge 自动 import
from envcad.knowledge import materials, codes, env_data, mech_data
print(f"2. 知识模块自动 import 成功")
print(f"   - materials: 混凝土{len(materials.CONCRETE)}档")
print(f"   - codes: 规范{len(codes.GB_CODES)}本")
print(f"   - env_data: {env_data.env_summary()[:40]}...")

# 3. 模拟新增领域：创建一个临时 YAML 配置
domains_dir = os.path.join(BASE, "envcad", "domains")
test_yaml = os.path.join(domains_dir, "_test_domain.yaml")

with open(test_yaml, "w", encoding="utf-8") as f:
    f.write('''# 测试领域
name: "_test_domain"
module: "envcad.standards.custom"
description: "测试领域（验证自动注册）"
functions:
  outline: "draw_outline"
''')

# 4. 重新加载，验证新领域被发现
registry2 = load_domain_registry()
assert "_test_domain" in registry2, "新增领域未被自动发现！"
print(f"3. 新增领域 _test_domain 自动发现成功")

# 5. 清理测试文件
os.remove(test_yaml)
registry3 = load_domain_registry()
assert "_test_domain" not in registry3, "删除后领域仍存在！"
print(f"4. 删除配置后领域自动消失")

# 6. 验证 CLI 可用
from envcad.cli import DOMAIN_REGISTRY
print(f"5. cli.py DOMAIN_REGISTRY 自动加载: {len(DOMAIN_REGISTRY)} 个领域")

# 7. 验证向后兼容
from envcad.knowledge import materials_summary, code_summary
ms = materials_summary()
cs = code_summary()
print(f"6. 向后兼容: materials_summary() = {ms}")
print(f"   code_summary() = {cs}")

print()
print("=" * 60)
print("  全部验证通过！自动注册器工作正常。")
print("=" * 60)
print()
print("  结论：多任务并行扩展不同领域，")
print("  每个任务只需创建自己的 domains/xxx.yaml + standards/xxx.py")
print("  + knowledge/xxx_data.py，零冲突。")
print("=" * 60)
