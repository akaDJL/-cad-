# -*- coding: utf-8 -*-
"""从现有 cli.py 的 DOMAIN_REGISTRY 提取领域配置，生成 domains/*.yaml。

每个领域一个独立 YAML 文件，以后新增领域只需要丢一个文件进去，
不需要改 cli.py 和 knowledge/__init__.py。
"""
import os, sys, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# 导入现有的 DOMAIN_REGISTRY
from envcad.cli import DOMAIN_REGISTRY

# 创建 domains 目录
domains_dir = os.path.join(BASE, "envcad", "domains")
os.makedirs(domains_dir, exist_ok=True)

# 为每个领域生成一个 YAML 文件
count = 0
for domain_name, config in DOMAIN_REGISTRY.items():
    yaml_content = f"""# 领域配置: {domain_name}
# 此文件由 auto_registry 自动扫描加载，新增领域只需在此目录放入 YAML 文件
# 无需修改 cli.py 或 knowledge/__init__.py

name: "{domain_name}"
module: "{config['module']}"
description: "{config.get('description', '')}"
functions:
"""

    for func_name, real_name in config.get("functions", {}).items():
        yaml_content += f'  {func_name}: "{real_name}"\n'

    yaml_path = os.path.join(domains_dir, f"{domain_name}.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    count += 1

print(f"已生成 {count} 个领域配置文件到 envcad/domains/")
print(f"目录: {domains_dir}")

# 列出生成的文件
for f in sorted(os.listdir(domains_dir)):
    if f.endswith(".yaml"):
        print(f"  {f}")
