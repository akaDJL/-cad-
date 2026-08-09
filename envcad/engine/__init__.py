"""engine — 二集集成内核。

  * dxf_base       — text-to-cad 的 ezdxf 生成内核（DXF）
  * multicad_bridge — multiCAD-mcp 的 COM 桥接（DXF→AutoCAD/ZWCAD）

惰性导出（PEP 562）：collision_fix / batch_layout 仅在首次访问时导入，
避免 `import envcad` 就拉起 ezdxf + standards + components 整棵子图。
"""

# 碰撞检测增强 / 批量出图引擎 —— 按需加载
_LAZY_EXPORTS = {
    "TrackedMSpace": "envcad.engine.collision_fix",
    "post_process_overlaps": "envcad.engine.collision_fix",
    "batch_fasteners": "envcad.engine.batch_layout",
    "batch_mixed": "envcad.engine.batch_layout",
}


def __getattr__(name: str):
    mod_name = _LAZY_EXPORTS.get(name)
    if mod_name is not None:
        import importlib
        value = getattr(importlib.import_module(mod_name), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


__all__ = list(_LAZY_EXPORTS)
