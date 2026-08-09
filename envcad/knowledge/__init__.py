# -*- coding: utf-8 -*-
"""知识层：国标材料库 / 规范表 / 设计理论 / 计算公式 / 用户数据。

设计目标——把「数据、规范、理论」作为第一类公民沉淀进插件，
让绘图、设计、文档三处从同一数据源取数，对标天正/探索者的「规范内置」。

子模块：
  materials          混凝土/钢筋/钢材/型钢国标数据库 + 查询函数
  codes              GB 系列规范注册表与关键参数
  theory             结构设计理论要点（文本知识）
  formulas           钢筋混凝土常用验算公式
  user_data          用户订阅/自有数据的 drop-in 接入点
  civil              土层参数/地基承载力修正/岩土桥梁道路规范（土木）
  env_data           水/气/噪声/焚烧排放限值 + 工艺参数 + 环保规范（环保）
  mech_data          材料许用应力/标准模数/优先数/螺纹/公差 + 机械规范（机械）
  elec_data          电缆载流量/需要系数/照度/短路 + 电气规范（电气）
  plumb_data         用水定额/器具当量/管材流速/排水坡度 + 给排水规范（给排水）
  hvac_data          设计温湿度/负荷指标/换气次数/风管规格 + 暖通规范（暖通）
  hyd_data           液压油/标准缸径/压力等级/管路流速 + 液压规范（液压）
  proc_data          管道规格/经济流速/介质物性/换热系数 + 工艺规范（化工）
  energy_chem_data   容器材料/腐蚀裕量/换热K/填料塔/储罐/新能源基础（能化）
  electronics_data   PCB参数/IC封装/连接器/IP等级/散热器/机箱（电子）
  agri_data          灌溉参数/螺旋输送机/包装机/拖拉机/收割机/播种机（农食）
  survey_data        坐标系参数/精度等级/图式/管线探测/竣工测量（测绘GIS）
  bridge_data        荷载等级/抗震设防/支座/伸缩缝/箱梁（桥梁）
  remediation_data   土壤筛选值/注入抽提井/热脱附/水泥窑（土壤修复）
  emergency_data     风险物质阈值/应急池/围堰/扩散参数（环境应急）
  eia_data           评价等级判定/敏感区/防护距离/总量控制（环评）
"""
from __future__ import annotations

import os as _os
import importlib as _importlib

# ── 惰性自动注册：扫描 knowledge/ 目录，但仅在首次访问时才 import ──
# 新增知识模块只需在 knowledge/ 目录放入 *_data.py 文件，
# 无需修改本文件。多任务并行扩展互不冲突。
# 与急切版区别：不再于包导入时一次性加载全部模块（20+ 文件），
# `from envcad.knowledge import xxx_data` 只加载被引用的那一个。
_CORE_KNOWLEDGE = ("materials", "codes", "theory", "formulas", "user_data")


def _discover_modules() -> frozenset:
    """扫描目录名（不 import），得到可惰性加载的知识模块集合。"""
    names = set(_CORE_KNOWLEDGE)
    here = _os.path.dirname(_os.path.abspath(__file__))
    for fname in _os.listdir(here):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        mod_name = fname[:-3]
        if mod_name.endswith("_data") or mod_name == "civil":
            names.add(mod_name)
    return frozenset(names)


_LAZY_MODULES = _discover_modules()


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = _importlib.import_module(f"{__name__}.{name}")
        globals()[name] = mod  # 缓存
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_LAZY_MODULES))


__all__ = sorted(_LAZY_MODULES) + ["materials_summary", "code_summary"]


def materials_summary() -> str:
    """材料库概览，供 CLI/文档引用。"""
    from . import materials
    n_section = sum(len(t) for t in (materials.I_BEAM, materials.CHANNEL,
                                     materials.ANGLE_L, materials.H_BEAM))
    return (f"混凝土 {len(materials.CONCRETE)} 级 | "
            f"钢筋 {len(materials.REBAR_GRADE)} 种 | "
            f"直径 {len(materials.REBAR_D)} 档 | "
            f"钢材 {len(materials.STEEL)} 种 | "
            f"型钢 {n_section} 个")


def code_summary() -> str:
    """规范库概览。"""
    from . import codes
    n = len(codes.GB_CODES)
    return f"内置 GB 规范 {n} 本，覆盖可靠度/荷载/抗震/混凝土/钢结构/地基/制图"
