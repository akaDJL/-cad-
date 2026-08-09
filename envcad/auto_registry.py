# -*- coding: utf-8 -*-
"""自动注册器：扫描 domains/ 和 knowledge/ 目录，自动发现并加载所有领域。

设计目标：
  - 新增领域只需要：丢一个 domains/xxx.yaml + standards/xxx.py + knowledge/xxx_data.py
  - 零修改 cli.py、knowledge/__init__.py
  - 多任务并行扩展时互不冲突

用法：
  from envcad.auto_registry import load_domain_registry, auto_import_knowledge

  DOMAIN_REGISTRY = load_domain_registry()        # 自动加载所有领域
  auto_import_knowledge()                          # 自动 import 所有知识模块
"""
from __future__ import annotations

import os
import importlib
import glob

# 本包目录
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_DOMAINS_DIR = os.path.join(_PKG_DIR, "domains")
_KNOWLEDGE_DIR = os.path.join(_PKG_DIR, "knowledge")


# ══════════════════════════════════════════════════════════
#  YAML 解析（不依赖 PyYAML，用简易解析器）
# ══════════════════════════════════════════════════════════

def _parse_simple_yaml(text: str) -> dict:
    """简易 YAML 解析器，支持本插件 domains/*.yaml 的格式。

    支持的语法：
      key: "value"        字符串
      key: value          裸值
      key:                子字典
        subkey: "value"
    """
    result = {}
    current_key = None
    in_functions = False

    for line in text.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        # 缩进判断
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # 顶层 key: value
        if indent == 0 and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            if not value:
                # 可能是子字典
                current_key = key
                if key == "functions":
                    in_functions = True
                    result[key] = {}
                else:
                    in_functions = False
                    result[key] = {}
            else:
                in_functions = False
                # 去掉引号
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                result[key] = value

        elif in_functions and indent >= 2 and ":" in stripped:
            # functions 子项: func_name: "real_name"
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if "functions" not in result:
                result["functions"] = {}
            result["functions"][key] = value

    return result


# ══════════════════════════════════════════════════════════
#  领域注册：扫描 domains/*.yaml
# ══════════════════════════════════════════════════════════

def load_domain_registry(domains_dir: str = None) -> dict:
    """扫描 domains/ 目录，自动加载所有领域配置。

    返回与 cli.py 中 DOMAIN_REGISTRY 相同结构的字典。
    """
    if domains_dir is None:
        domains_dir = _DOMAINS_DIR

    registry = {}
    if not os.path.isdir(domains_dir):
        return registry

    for yaml_path in sorted(glob.glob(os.path.join(domains_dir, "*.yaml"))):
        with open(yaml_path, "r", encoding="utf-8") as f:
            text = f.read()
        config = _parse_simple_yaml(text)

        name = config.get("name")
        if not name:
            # 用文件名作为领域名
            name = os.path.splitext(os.path.basename(yaml_path))[0]
            config["name"] = name

        registry[name] = config

    return registry


# ══════════════════════════════════════════════════════════
#  知识模块自动 import：扫描 knowledge/*_data.py
# ══════════════════════════════════════════════════════════

# 固定模块（必须先加载，其他模块可能依赖它们）
_CORE_KNOWLEDGE = [
    "materials", "codes", "theory", "formulas", "user_data",
]


def auto_import_knowledge(knowledge_pkg: str = "envcad.knowledge") -> dict:
    """自动 import knowledge/ 目录下所有 *_data.py 和 civil.py 模块。

    返回 {模块名: 模块对象} 字典。
    """
    import sys
    parent_pkg = importlib.import_module(knowledge_pkg)

    loaded = {}

    # 1. 先加载核心模块
    for mod_name in _CORE_KNOWLEDGE:
        full_name = f"{knowledge_pkg}.{mod_name}"
        try:
            mod = importlib.import_module(full_name)
            setattr(parent_pkg, mod_name, mod)
            loaded[mod_name] = mod
        except ImportError as e:
            print(f"[auto_registry] 跳过 {mod_name}: {e}", file=sys.stderr)

    # 2. 扫描 knowledge/ 目录，加载所有 *_data.py 和 civil.py
    if os.path.isdir(_KNOWLEDGE_DIR):
        for py_file in sorted(os.listdir(_KNOWLEDGE_DIR)):
            if not py_file.endswith(".py") or py_file.startswith("__"):
                continue
            mod_name = py_file[:-3]  # 去掉 .py

            # 跳过已加载的核心模块
            if mod_name in loaded:
                continue

            # 只加载 *_data 和 civil
            if not (mod_name.endswith("_data") or mod_name == "civil"):
                continue

            full_name = f"{knowledge_pkg}.{mod_name}"
            try:
                mod = importlib.import_module(full_name)
                setattr(parent_pkg, mod_name, mod)
                loaded[mod_name] = mod
            except ImportError as e:
                print(f"[auto_registry] 跳过 {mod_name}: {e}", file=sys.stderr)

    return loaded


# ══════════════════════════════════════════════════════════
#  便捷函数
# ══════════════════════════════════════════════════════════

def list_domains() -> list:
    """列出所有已注册的领域名。"""
    return sorted(load_domain_registry().keys())


def domain_info(name: str) -> dict:
    """查询单个领域信息。"""
    return load_domain_registry().get(name, {})


def domain_count() -> int:
    """已注册领域数量。"""
    return len(load_domain_registry())


# ══════════════════════════════════════════════════════════
#  自测
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== 自动注册器自测 ===")
    print()

    registry = load_domain_registry()
    print(f"已发现 {len(registry)} 个领域:")
    for name in sorted(registry.keys()):
        desc = registry[name].get("description", "")
        n_funcs = len(registry[name].get("functions", {}))
        print(f"  {name:25s} ({n_funcs:2d} 函数) {desc[:40]}")
