# -*- coding: utf-8 -*-
"""设计验算层：把知识层材料/规范/公式转化为可执行的工程验算。

子模块：
  rc_beam         钢筋混凝土梁正截面/斜截面配筋计算 + 裂缝/挠度验算
  section_db      标准型钢按需求面积自动选用
  foundation      地基承载力修正/独立基础底面积/挡土墙抗滑抗倾覆（土木）
  env_process     曝气池/二沉池/除尘器工艺计算 + 达标判定（环保）
  gear            直齿圆柱齿轮接触+弯曲疲劳强度校核（机械）
  shaft           轴扭转初估 + 弯扭合成强度校核（机械）
  electrical      需要系数法负荷/电缆选型/照度/短路（电气）
  plumbing        用水量/给水秒流量/管径水力/排水/泵扬程（给排水）
  hvac            冷热负荷/送风量/新风/风管尺寸（暖通）
  hydraulic       液压缸/泵功率/管径（液压）
  process         经济管径/泵扬程功率/换热面积（化工）
  energy_chemical 压力容器壁厚/换热器面积/填料塔流体力学（能化）
  electronics     PCB载流温升/散热器热阻/微带线阻抗（电子）
  agri            灌溉水力/螺旋输送机功率/包装节拍（农食）
  survey          坐标转换/精度评定/管线埋深/比例尺校核（测绘GIS）
  bridge          车道荷载/支座选型/伸缩缝/高跨比校核（桥梁）
  remediation     土壤达标判定/注入井间距/热脱附参数校核（土壤修复）
  emergency       风险Q值/应急池容积/围堰/烟团扩散（环境应急）
  eia             评价等级判定/防护距离/敏感区校核（环评）
"""
from __future__ import annotations

# ── 惰性导出（PEP 562）────────────────────────────────────
# 不再于包导入时急切加载全部 19 个验算模块，
# `from envcad.design import rc_beam` / `import envcad.design.rc_beam`
# 仅加载被引用的模块及其对应知识库，启动开销按需支付。
_LAZY_MODULES = frozenset({
    "rc_beam", "section_db", "foundation", "env_process", "gear", "shaft",
    "electrical", "plumbing", "hvac", "hydraulic", "process",
    "energy_chemical", "electronics", "agri", "survey",
    "bridge", "remediation", "emergency", "eia",
})


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        import importlib
        mod = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = mod  # 缓存
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_LAZY_MODULES))


__all__ = sorted(_LAZY_MODULES)
