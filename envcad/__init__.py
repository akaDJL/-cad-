"""envcad — 环保工程全领域制图集成插件 v1.5。

集成两个开源项目：
  * text-to-cad  —— ezdxf 几何生成内核（DXF）
  * multiCAD-mcp —— COM 桥接，把图纸推送到 AutoCAD/ZWCAD

核心是参数化的国标二维工程图引擎，覆盖环保全领域10个细分方向。

环保全领域模块：
  水处理 / 高级水处理 / 废气治理 / 固废处理 / 土壤修复
  物理污染防治 / 环境应急 / 环境工程通用 / 生态环境 / 环评
  + custom 非标兜底模块

命令行：
  envcad list                              # 查看所有领域和函数
  envcad batch --config tasks.json --out . # JSON批量出图
  envcad domain solid_waste --out .        # 按领域出图
  envcad test all --out .                  # 运行验收测试
"""
from __future__ import annotations

__version__ = "1.5"

# ── 惰性导出（PEP 562）────────────────────────────────────
# 不再在包导入时急切加载 engine.dxf_base（会连带 ezdxf ≈1.6s），
# 首次访问 new_drawing/save_dxf 时才真正导入，纯计算/文档命令零 DXF 开销。
_LAZY_EXPORTS = {
    "new_drawing": "envcad.engine.dxf_base",
    "save_dxf": "envcad.engine.dxf_base",
}


def __getattr__(name: str):
    mod_name = _LAZY_EXPORTS.get(name)
    if mod_name is not None:
        import importlib
        value = getattr(importlib.import_module(mod_name), name)
        globals()[name] = value  # 缓存，后续访问走正常全局查找
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


__all__ = ["new_drawing", "save_dxf"]
