"""param 自然语言解析增强回归测试。

锁定范围感知 + 最长匹配优先的行为，防止后续重构回归。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from envcad.engine.parametric_bridge import resolve_intent


def _norm(text):
    r = resolve_intent(text)
    return (r["domain"], r["function"], r["param"], r["value"]) if r else None


@pytest.mark.parametrize("text,expected", [
    # 既有用例（必须保持）
    ("齿轮齿数 19", ("mechanical", "spur_gear", "z", 19.0)),
    # 通用几何词 / 物理量（范围感知，仅当函数拥有对应参数）
    ("齿轮模数4", ("mechanical", "spur_gear", "m", 4.0)),
    ("齿轮齿宽25", ("mechanical", "spur_gear", "b", 25.0)),
    ("厌氧罐直径12米", ("solid_waste", "anaerobic_digester", "diameter", 12.0)),
    ("填埋场深度18米", ("solid_waste", "landfill_section", "depth", 18.0)),
    ("填埋场长60米", ("solid_waste", "landfill_section", "length", 60.0)),
    ("曝气池池长20米", ("water_treatment", "aeration_tank", "length", 20.0)),
    ("墙高3米", ("building", "wall", "height", 3.0)),
    ("轴承内径30mm", ("mechanical", "bearing", "inner_d", 30.0)),
    ("注入井行数4列数6", ("soil_remediation", "injection_well_grid", "n_rows", 4.0)),
])
def test_resolve_intent_ok(text, expected):
    assert _norm(text) == expected


@pytest.mark.parametrize("text", [
    "随便说点什么",          # 无领域
    "沉淀池直径6米",         # 沉淀池未注册到参数表（领域误配防护）
])
def test_resolve_intent_none(text):
    assert resolve_intent(text) is None
