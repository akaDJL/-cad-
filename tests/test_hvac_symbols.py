# -*- coding: utf-8 -*-
"""GB/T 50114 暖通空调制图 风道阀门/风口/附件 符号库测试。"""
import os
import ezdxf
from envcad.standards.hvac import (
    draw_hvac_valve, draw_hvac_outlet, draw_hvac_accessory, draw_hvac_legend,
)

SCALE = 100.0


def _entities(path):
    doc = ezdxf.readfile(path)
    return list(doc.modelspace())


def _draw(fn, *args, **kw):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    fn(msp, (5000, 5000), scale=SCALE, *args, **kw)
    path = "tmp_hvac_test.dxf"
    doc.saveas(path)
    ents = _entities(path)
    os.remove(path)
    return ents


def test_hvac_valve_all_types():
    for vt in ["butterfly", "multileaf", "multileaf_electric", "check",
               "three_way", "slide", "fire", "smoke", "electric"]:
        ents = _draw(draw_hvac_valve, valve_type=vt)
        assert len(ents) >= 1, f"valve {vt} 未生成实体"
        # 阀门应至少含一段风管中线(线)或阀体(多段线)
        assert any(e.dxftype() in ("LINE", "LWPOLYLINE") for e in ents), vt


def test_hvac_outlet_all_types():
    for ot in ["general", "grille_single", "grille_double", "diffuser_rect",
               "diffuser_round", "slot", "swirl", "louver", "louver_rain", "nozzle"]:
        ents = _draw(draw_hvac_outlet, outlet_type=ot)
        assert len(ents) >= 1, f"outlet {ot} 未生成实体"


def test_hvac_accessory_all_types():
    for at in ["transition", "flexible", "silencer", "elbow_arc",
               "elbow_guide", "up", "down"]:
        ents = _draw(draw_hvac_accessory, acc_type=at)
        assert len(ents) >= 1, f"accessory {at} 未生成实体"


def test_hvac_legend_generates_grid():
    ents = _draw(draw_hvac_legend)
    # 图例应包含标题文字 + 各符号 + 名称标注
    texts = [e.dxftype() for e in ents if e.dxftype() == "TEXT"]
    assert any("GB/T 50114" in (e.dxfattribs().get("text", "")) for e in ents
               if e.dxftype() == "TEXT"), "图例缺少标准标题"
    # 阀门/风口/附件符号 + 代号表 + 名称标注，实体数应足够多
    assert len(ents) > 40, f"图例实体过少: {len(ents)}"


def test_unknown_type_raises():
    import pytest
    with pytest.raises(ValueError):
        _draw(draw_hvac_valve, valve_type="___nope")
