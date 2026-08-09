# -*- coding: utf-8 -*-
"""标准型钢选用（知识驱动）。

给定所需截面积，自动从 materials 型钢库里挑最小满足的截面，
对标探索者「截面选用」功能：输入需求 → 输出标准型号与参数。
"""
from __future__ import annotations

from ..knowledge import materials


def select_section(catalog: str, required_area_mm2: float) -> dict:
    """从指定目录挑截面积不小于需求的最小型钢。

    catalog ∈ {"I" 工字钢, "C" 槽钢, "L" 等边角钢, "H" H型钢}
    返回: {"name", "Ax", "W", ...截面参数, "margin"}，未满足返回最接近者。
    """
    tbl = {
        "I": materials.I_BEAM, "C": materials.CHANNEL,
        "L": materials.ANGLE_L, "H": materials.H_BEAM,
    }.get(catalog)
    if tbl is None:
        raise KeyError(f"未知型钢目录: {catalog}")

    best = None
    for name, p in tbl.items():
        cand = dict(name=name, **p, margin=p["Ax"] - required_area_mm2)
        if best is None:
            best = cand
        else:
            # 优先满足需求；都满足时取余量最小
            if (best["margin"] < 0) and (cand["margin"] >= 0):
                best = cand
            elif (best["margin"] >= 0) == (cand["margin"] >= 0):
                if cand["margin"] < best["margin"]:
                    best = cand
            # 若 best 已满足而 cand 不满足，保留 best
    return best


def select_i_beam(required_area_mm2: float) -> dict:
    """工字钢选用快捷接口。"""
    return select_section("I", required_area_mm2)


def select_h_beam(required_area_mm2: float) -> dict:
    """H 型钢选用快捷接口。"""
    return select_section("H", required_area_mm2)


def format_section_choice(ch: dict) -> str:
    ok = ch["margin"] >= 0
    return (f"选用 {ch['name']}（A={ch['Ax']:.0f} mm², {ch['W']} kg/m）"
            f"，需求 {ch['Ax']-ch['margin']:.0f} mm² → {'满足' if ok else '不足'}")
