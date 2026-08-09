# 并行开发指南

> 改造完成后，新增行业领域**零冲突**。每个任务只碰自己的新文件，公共注册点完全不用动。

## 架构变更

### 改造前（手动注册，3个必撞点）

```
新增领域需要修改：
  1. cli.py              ← DOMAIN_REGISTRY 追加     🔴 冲突
  2. knowledge/__init__.py ← import 追加             🔴 冲突
  3. standards/xxx.py     ← 独立                    ✅
  4. knowledge/xxx_data.py ← 独立                   ✅
```

### 改造后（自动注册，零冲突）

```
新增领域只需要创建：
  1. domains/xxx.yaml     ← 领域配置（自动发现）    ✅
  2. standards/xxx.py     ← 绘图函数               ✅
  3. knowledge/xxx_data.py ← 知识数据               ✅
```

`cli.py` 和 `knowledge/__init__.py` **不再需要修改**。

## 新增领域的完整步骤

### 第1步：创建领域配置 `domains/xxx.yaml`

```yaml
# 领域配置: my_domain
name: "my_domain"
module: "envcad.standards.my_domain"
description: "我的领域（功能1/功能2/功能3）"
functions:
  func_a: "draw_func_a"
  func_b: "draw_func_b"
```

### 第2步：创建绘图模块 `standards/my_domain.py`

```python
def draw_func_a(msp, origin=(0, 0), scale=100, **kw):
    """功能A的绘图函数"""
    # msp: ezdxf modelspace
    # origin: 插入点
    # scale: 比例
    ...

def draw_func_b(msp, origin=(0, 0), scale=100, **kw):
    """功能B的绘图函数"""
    ...
```

### 第3步（可选）：创建知识模块 `knowledge/my_domain_data.py`

```python
# -*- coding: utf-8 -*-
"""我的领域知识库"""

MY_DATA = {
    "param_a": 100,
    "param_b": "说明文字",
}

def my_summary() -> str:
    return f"我的领域数据 {len(MY_DATA)} 项"
```

### 完成！

运行 `envcad domain my_domain --function func_a --out out/` 即可出图。

## 并行任务冲突矩阵

| 任务A操作 | 任务B操作 | 是否冲突 |
|-----------|-----------|----------|
| 创建 `domains/A.yaml` | 创建 `domains/B.yaml` | ✅ 不冲突 |
| 创建 `standards/A.py` | 创建 `standards/B.py` | ✅ 不冲突 |
| 创建 `knowledge/A_data.py` | 创建 `knowledge/B_data.py` | ✅ 不冲突 |
| 修改 `knowledge/materials.py` | 修改 `knowledge/materials.py` | 🔴 冲突 |
| 修改 `knowledge/codes.py` | 修改 `knowledge/codes.py` | 🔴 冲突 |
| 修改 `knowledge/formulas.py` | 修改 `knowledge/formulas.py` | 🔴 冲突 |
| 修改 `engine/dxf_base.py` | 创建 `standards/B.py` | ✅ 不冲突 |

**规则：每个任务只创建自己的新文件，不要碰共享数据文件（materials/codes/formulas）。**

如果多个任务都需要往 `codes.py` 加规范，建议：
- 各自创建独立的 `knowledge/xxx_data.py`
- 或者在任务分配时，把"规范扩充"作为一个单独任务

## 自动注册器 API

```python
from envcad.auto_registry import (
    load_domain_registry,  # 加载所有领域配置
    auto_import_knowledge,  # 自动 import 知识模块
    list_domains,          # 列出所有领域名
    domain_info,           # 查询单个领域信息
    domain_count,          # 已注册领域数量
)

# 查看所有领域
print(list_domains())        # ['building', 'electrical', 'hvac', ...]

# 查询某个领域
info = domain_info("hvac")
print(info["description"])    # "暖通空调（风管/风口/...）"
print(info["functions"])      # {"duct_plan": "draw_duct_plan", ...}
```

## 验证

改造后运行测试：
```
pytest tests/ -v
# 57 passed, 6 skipped
```

## 文件结构

```
envcad/
├── auto_registry.py      ← 自动注册器（核心）
├── domains/              ← 领域配置目录（每个文件独立）
│   ├── building.yaml
│   ├── mechanical.yaml
│   ├── hvac.yaml
│   └── ... (32个)
├── cli.py                ← 改造：用 _load_domains() 替代硬编码
├── knowledge/
│   ├── __init__.py       ← 改造：用 auto_import 替代手动 import
│   ├── materials.py      ← 共享（需协调）
│   ├── codes.py          ← 共享（需协调）
│   └── ... (*_data.py 自动发现)
├── standards/            ← 绘图标准（每个文件独立）
└── ...
```
