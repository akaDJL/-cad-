"""参数化桥接 v1.0 —— 自然语言意图 → 改参 → 重出图。

核心场景：
  工程师说"絮凝池水深改 5m"、"层高改 3.6"、"桩径加到 800"
  → 桥接层定位到对应 draw_* 函数 → 更新参数 → 重新生成 DXF。

架构：PARAM_REGISTRY（参数映射表） + resolve_intent（意图解析） + apply_and_redraw（重出图）
"""
from __future__ import annotations
import importlib
import json
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

# ══════════════════════════════════════════════════════════
#  参数注册表 — 每个 draw_* 函数的可调参数
#  格式: { "domain": { "func_alias": { "param_name": (type, "中文描述", default) } } }
# ══════════════════════════════════════════════════════════

PARAM_REGISTRY: Dict[str, Dict[str, Dict[str, Tuple[str, str, Any]]]] = {
    # ── 建筑 ──
    "building": {
        "floor_section": {
            "n_floors":        ("int",    "楼层数",          3),
            "floor_height":    ("float",  "层高(m)",          3.0),
            "width":           ("float",  "建筑宽度(m)",      12.0),
            "wall_thickness":  ("float",  "墙厚(m)",          0.24),
            "slab_thickness":  ("float",  "楼板厚(m)",        0.12),
            "basement":        ("int",    "地下室层数",       0),
        },
        "floor_plan": {
            "width":           ("float",  "进深(m)",          12.0),
            "length":          ("float",  "面宽(m)",          18.0),
            "wall_thickness":  ("float",  "墙厚(m)",          0.24),
            "column_spacing":  ("float",  "柱网间距(m)",      6.0),
        },
        "wall": {
            "length":          ("float",  "墙长(m)",          6.0),
            "height":          ("float",  "墙高(m)",          3.0),
            "thickness":       ("float",  "墙厚(m)",          0.24),
        },
        "column": {
            "width":           ("float",  "柱宽(m)",          0.5),
            "depth":           ("float",  "柱深(m)",          0.5),
            "height":          ("float",  "柱高(m)",          3.0),
            "column_type":     ("str",    "柱类型",           "rect"),
        },
        "beam": {
            "span":            ("float",  "跨度(m)",          6.0),
            "width":           ("float",  "梁宽(m)",          0.3),
            "depth":           ("float",  "梁高(m)",          0.6),
        },
        "door": {
            "width":           ("float",  "门宽(m)",          1.0),
            "height":          ("float",  "门高(m)",          2.1),
        },
        "window": {
            "width":           ("float",  "窗宽(m)",          1.5),
            "height":          ("float",  "窗高(m)",          1.5),
            "sill_height":     ("float",  "窗台高(m)",        0.9),
        },
        "staircase": {
            "width":           ("float",  "梯段宽(m)",        2.4),
            "floor_height":    ("float",  "层高(m)",          3.0),
            "n_steps":         ("int",    "踏步数",           18),
        },
    },
    # ── 暖通 HVAC ──
    "hvac": {
        "duct_plan": {
            "length":          ("float",  "主管长(m)",        8.0),
            "width":           ("float",  "主管宽(m)",        0.6),
        },
        "duct_section": {
            "diameter":        ("float",  "风管直径(mm)",     500),
            "insulation":      ("float",  "保温层厚(mm)",     30),
        },
        "air_outlet": {
            "width":           ("float",  "风口宽(mm)",       400),
            "height":          ("float",  "风口高(mm)",       200),
            "outlet_type":     ("str",    "风口类型",         "grille"),
        },
        "ahu": {
            "length":          ("float",  "机组长(m)",        4.0),
            "width":           ("float",  "机组宽(m)",        1.5),
            "height":          ("float",  "机组高(m)",        2.0),
        },
        "fan_coil": {
            "length":          ("float",  "外形长(m)",        1.0),
            "width":           ("float",  "外形宽(m)",        0.6),
        },
        "cooling_tower": {
            "diameter":        ("float",  "塔径(m)",          3.0),
            "height":          ("float",  "塔高(m)",          4.0),
            "n_cells":         ("int",    "隔间数",           2),
        },
        "chiller": {
            "length":          ("float",  "外形长(m)",        3.5),
            "capacity":        ("int",    "制冷量(kW)",       500),
            "chiller_type":    ("str",    "类型",             "螺杆式"),
        },
        "boiler": {
            "diameter":        ("float",  "炉径(m)",          2.0),
            "length":          ("float",  "炉长(m)",          5.0),
            "capacity":        ("float",  "容量(MW)",         2.8),
            "boiler_type":     ("str",    "类型",             "燃气热水"),
        },
    },
    # ── 机械零件 ──
    "mechanical": {
        "spur_gear": {
            "m":               ("float",  "模数 mm",          5.0),
            "z":               ("int",    "齿数",             20),
            "b":               ("float",  "齿宽 mm",          25.0),
        },
        "shaft": {
            "diameter":        ("float",  "轴径 mm",          30.0),
            "length":          ("float",  "轴长 mm",          150.0),
            "n_steps":         ("int",    "台阶数",           3),
            "keyway_width":    ("float",  "键槽宽 mm",        8.0),
            "keyway_depth":    ("float",  "键槽深 mm",        4.0),
        },
        "key": {
            "width":           ("float",  "键宽 mm",          10.0),
            "height":          ("float",  "键高 mm",          8.0),
            "length":          ("float",  "键长 mm",          40.0),
            "key_type":        ("str",    "键型 A/B/C",       "A"),
        },
        "bearing": {
            "inner_d":         ("float",  "内径 mm",          30.0),
            "outer_d":         ("float",  "外径 mm",          72.0),
            "width":           ("float",  "宽度 mm",          19.0),
            "bearing_type":    ("str",    "轴承类型",          "deep_groove"),
        },
        "pulley": {
            "diameter":        ("float",  "节圆直径 mm",      200.0),
            "width":           ("float",  "轮宽 mm",          50.0),
            "n_grooves":       ("int",    "槽数",             3),
            "shaft_diameter":  ("float",  "轴孔 mm",          40.0),
            "groove_angle":    ("float",  "槽角 (°)",         38.0),
        },
    },
    # ── 土木结构 ──
    "structural": {
        "prestressed_beam": {
            "span":            ("float",  "跨度(m)",          12.0),
            "depth":           ("float",  "梁高(m)",          0.8),
            "width":           ("float",  "梁宽(m)",          0.3),
        },
        "masonry_wall": {
            "width":           ("float",  "墙宽(m)",          3.0),
            "height":          ("float",  "墙高(m)",          3.0),
            "thickness":       ("float",  "墙厚(m)",          0.24),
        },
    },
    # ── 基础 ──
    "foundation": {
        "foundation_detail": {
            "width":           ("float",  "基础宽(m)",        2.0),
            "depth":           ("float",  "基础埋深(m)",      1.5),
            "thickness":       ("float",  "底板厚(m)",        0.5),
        },
    },
    # ── 水处理 ──
    "water_treatment": {
        "aeration_tank": {
            "length":          ("float",  "池长(m)",          10.0),
            "width":           ("float",  "池宽(m)",          5.0),
            "depth":           ("float",  "水深(m)",          4.0),
            "n_zones":         ("int",    "分区数",           3),
        },
    },
    "advanced_wtp": {
        "a2o_flow": {
            "q_in":            ("float",  "进水流量(m3/d)",   5000),
            "hr_anaerobic":    ("float",  "厌氧HRT(h)",       2.0),
            "hr_anoxic":       ("float",  "缺氧HRT(h)",       4.0),
            "hr_oxic":         ("float",  "好氧HRT(h)",       8.0),
        },
    },
    # ── 固废 ──
    "solid_waste": {
        "landfill_section": {
            "length":          ("float",  "填埋场长(m)",      60.0),
            "depth":           ("float",  "填埋深度(m)",      15.0),
            "liner_type":      ("str",    "衬层类型",         "composite"),
        },
        "anaerobic_digester": {
            "diameter":        ("float",  "罐直径(m)",        10.0),
            "height":          ("float",  "罐高(m)",          12.0),
            "volume":          ("float",  "有效容积(m3)",     800),
        },
    },
    # ── 土壤修复 ──
    "soil_remediation": {
        "injection_well_grid": {
            "n_rows":          ("int",    "行数",             3),
            "n_cols":          ("int",    "列数",             5),
            "well_spacing":    ("float",  "井间距(m)",        3.0),
            "oxidant":         ("str",    "氧化剂",           "persulfate"),
        },
    },
    # ── 给排水 ──
    "plumbing": {
        "valve": {
            "diameter":        ("float",  "管径(mm)",         100),
            "valve_type":      ("str",    "阀门类型",         "gate"),
        },
    },
    # ── 电气 ──
    "electrical": {
        "breaker": {
            "rated_current":   ("float",  "额定电流(A)",     63),
            "poles":           ("int",    "极数",             3),
        },
    },
    # ── 液压 ──
    "hydraulic": {
        "pump": {
            "flow_rate":       ("float",  "流量(L/min)",     40),
            "pressure":        ("float",  "压力(MPa)",        21),
        },
        "cylinder": {
            "bore":            ("float",  "缸径(mm)",         50),
            "stroke":          ("float",  "行程(mm)",         300),
        },
    },
}

# 中文参数名 → 英文参数名映射（用于自然语言解析）
_CN_PARAM_ALIASES = {
    "层高":    "floor_height",  "楼层高度": "floor_height",  "楼高": "floor_height",
    "层数":    "n_floors",      "楼层数":   "n_floors",
    "墙厚":    "wall_thickness", "墙体厚度": "wall_thickness",
    "墙高":    "height",        "墙体高度": "height",
    "墙长":    "length",        "墙体长度": "length",
    "柱宽":    "width",         "柱子宽度": "width",
    "柱高":    "height",        "柱子高度": "height",
    "梁高":    "depth",         "梁截面高": "depth",
    "梁宽":    "width",         "梁截面宽": "width",
    "跨度":    "span",          "梁跨度":   "span",
    "门宽":    "width",         "门洞宽度": "width",
    "门高":    "height",        "门洞高度": "height",
    "窗宽":    "width",         "窗洞宽度": "width",
    "窗高":    "height",        "窗洞高度": "height",
    "窗台高":  "sill_height",   "窗台高度": "sill_height",
    "池长":    "length",        "水池长度": "length",
    "池宽":    "width",         "水池宽度": "width",
    "水深":    "depth",         "池深":     "depth",
    "埋深":    "depth",         "基础埋深": "depth",
    "桩径":    "diameter",      "桩直径":   "diameter",
    "管径":    "diameter",      "管道直径": "diameter",
    "流量":    "flow_rate",     "进水量":   "q_in",
    "容积":    "volume",        "有效容积": "volume",
    "压力":    "pressure",      "工作压力": "pressure",
    "行程":    "stroke",        "活塞行程": "stroke",
    "缸径":    "bore",          "油缸内径": "bore",
    "电流":    "rated_current", "额定电流": "rated_current",
    "极数":    "poles",         "开关极数": "poles",
    # ── 机械 ──
    "模数":    "m",              "齿轮模数": "m",
    "齿数":    "z",              "齿轮齿数": "z",
    "齿宽":    "b",              "齿轮齿宽": "b",
    "压力角":  "pressure_angle","啮合角":   "pressure_angle",
    "齿宽":    "face_width",    "齿轮宽度": "face_width",
    "轴孔":    "shaft_diameter","轴孔直径": "shaft_diameter",
    "轴径":    "diameter",      "轴直径":   "diameter",
    "轴长":    "length",        "轴长度":   "length",
    "键槽宽":  "keyway_width",  "键槽宽度": "keyway_width",
    "键槽深":  "keyway_depth",  "键槽深度": "keyway_depth",
    "内径":    "inner_d",       "轴承内径": "inner_d",
    "外径":    "outer_d",       "轴承外径": "outer_d",
    "槽数":    "n_grooves",     "带轮槽数": "n_grooves",
    "节圆":    "diameter",      "节圆直径": "diameter",
    # ── EN aliases ──
    "teeth":         "z",           "teeth number":      "z",
    "tooth count":   "z",           "gear teeth":        "z",
    "module":        "m",           "gear module":       "m",
    "diameter":      "diameter",    "bore":              "diameter",
    "od":            "outer_d",     "outer diameter":    "outer_d",
    "id":            "inner_d",     "inner diameter":    "inner_d",
    "length":        "length",      "width":             "width",
    "height":        "height",      "thickness":         "wall_thickness",
    "span":          "span",        "floor height":      "floor_height",
    "floors":        "n_floors",    "n floors":          "n_floors",
    "pressure angle":"pressure_angle",
    "face width":    "b",           "gear width":        "b",
    "shaft diameter":"diameter",    "shaft length":      "length",
    "key width":     "keyway_width","key height":        "keyway_depth",
    "key length":    "length",      "keyway":            "keyway_width",
    "grooves":       "n_grooves",   "pulley grooves":    "n_grooves",
    "pitch diameter": "diameter",   "pitch":             "diameter",
    "stroke":        "stroke",      "flow":              "flow_rate",
    "flow rate":     "flow_rate",   "pressure":          "pressure",
    "bore size":     "bore",        "cylinder bore":     "bore",
    "wall":          "wall_thickness",
    "duct diameter": "diameter",    "duct length":       "length",
    "insulation":    "insulation",  "AHU length":        "length",
    "current":       "rated_current","amps":             "rated_current",
    "poles":         "poles",       "depth":             "depth",
}

# 构件/设备中文名 → (domain, func_alias)
_CN_DOMAIN_ALIASES = {
    # 机械
    "齿轮":      ("mechanical",  "spur_gear"),
    "轴":        ("mechanical",  "shaft"),
    "阶梯轴":    ("mechanical",  "shaft"),
    "平键":      ("mechanical",  "key"),
    "键":        ("mechanical",  "key"),
    "轴承":      ("mechanical",  "bearing"),
    "滚动轴承":  ("mechanical",  "bearing"),
    "皮带轮":    ("mechanical",  "pulley"),
    "带轮":      ("mechanical",  "pulley"),
    "V带轮":     ("mechanical",  "pulley"),
    # 暖通
    "风管":      ("hvac",        "duct_plan"),
    "风管剖面":  ("hvac",        "duct_section"),
    "风口":      ("hvac",        "air_outlet"),
    "空调机组":  ("hvac",        "ahu"),
    "空调箱":    ("hvac",        "ahu"),
    "风机盘管":  ("hvac",        "fan_coil"),
    "冷却塔":    ("hvac",        "cooling_tower"),
    "冷水机组":  ("hvac",        "chiller"),
    "锅炉":      ("hvac",        "boiler"),
    # 建筑
    "楼层剖面":  ("building",    "floor_section"),
    "楼层":      ("building",    "floor_section"),
    "剖面":      ("building",    "floor_section"),
    "平面图":    ("building",    "floor_plan"),
    "墙":        ("building",    "wall"),
    "墙体":      ("building",    "wall"),
    "柱":        ("building",    "column"),
    "柱子":      ("building",    "column"),
    "梁":        ("building",    "beam"),
    "门":        ("building",    "door"),
    "窗":        ("building",    "window"),
    "窗户":      ("building",    "window"),
    "楼梯":      ("building",    "staircase"),
    # 土木
    "预应力梁":  ("structural",  "prestressed_beam"),
    "砌体墙":    ("structural",  "masonry_wall"),
    # 基础
    "基础":      ("foundation",  "foundation_detail"),
    "独立基础":  ("foundation",  "foundation_detail"),
    # 水处理
    "曝气池":    ("water_treatment", "aeration_tank"),
    "好氧池":    ("water_treatment", "aeration_tank"),
    "絮凝池":    ("water_treatment", "aeration_tank"),
    "A2O":       ("advanced_wtp",     "a2o_flow"),
    # 固废
    "填埋场":    ("solid_waste",  "landfill_section"),
    "厌氧罐":    ("solid_waste",  "anaerobic_digester"),
    "消化罐":    ("solid_waste",  "anaerobic_digester"),
    # 土壤
    "注入井":    ("soil_remediation", "injection_well_grid"),
    # 给排水
    "阀门":      ("plumbing",     "valve"),
    # 电气
    "断路器":    ("electrical",   "breaker"),
    # ── EN domain aliases ──
    "gear":        ("mechanical",  "spur_gear"),
    "spur gear":   ("mechanical",  "spur_gear"),
    "helical gear":("mechanical",  "helical_gear"),
    "shaft":       ("mechanical",  "shaft"),
    "stepped shaft":("mechanical", "shaft"),
    "key":         ("mechanical",  "key"),
    "woodruff key":("mechanical",  "key"),
    "bearing":     ("mechanical",  "bearing"),
    "roller bearing":("mechanical","bearing"),
    "pulley":      ("mechanical",  "pulley"),
    "belt pulley": ("mechanical",  "pulley"),
    "duct":        ("hvac",        "duct_plan"),
    "air duct":    ("hvac",        "duct_plan"),
    "ahu":         ("hvac",        "ahu"),
    "air handler": ("hvac",        "ahu"),
    "fan coil":    ("hvac",        "fan_coil"),
    "fcu":         ("hvac",        "fan_coil"),
    "cooling tower":("hvac",       "cooling_tower"),
    "chiller":     ("hvac",        "chiller"),
    "boiler":      ("hvac",        "boiler"),
    "floor section":("building",   "floor_section"),
    "floor plan":  ("building",    "floor_plan"),
    "wall":        ("building",    "wall"),
    "column":      ("building",    "column"),
    "beam":        ("building",    "beam"),
    "door":        ("building",    "door"),
    "window":      ("building",    "window"),
    "staircase":   ("building",    "staircase"),
    "stairs":      ("building",    "staircase"),
    "foundation":  ("foundation",  "foundation_detail"),
    "pile":        ("foundation",  "pile_foundation"),
    "valve":       ("plumbing",    "valve"),
    "breaker":     ("electrical",  "breaker"),
    "circuit breaker":("electrical","breaker"),
    "aeration tank":("water_treatment","aeration_tank"),
    "tank":        ("water_treatment","aeration_tank"),
    "landfill":    ("solid_waste", "landfill_section"),
    "digester":    ("solid_waste", "anaerobic_digester"),
    "injection well":("soil_remediation","injection_well_grid"),
    "pump":        ("hydraulic",   "pump"),
    "cylinder":    ("hydraulic",   "cylinder"),
    # 液压
    "液压泵":    ("hydraulic",    "pump"),
    "油缸":      ("hydraulic",    "cylinder"),
}


# ── 通用几何 / 物理量同义词（范围感知：仅当目标参数确实存在于该函数时生效）──
# 解决原全局别名表覆盖过窄的问题（如"直径/半径/深度/压力/流量"等缺失）。
# 这些词是多义的，所以必须限定到已识别函数实际拥有的参数上，避免错配。
GENERIC_SYNONYMS: Dict[str, str] = {
    # 几何尺寸
    "直径":   "diameter",   "半径":   "radius",
    "内径":   "inner_d",    "外径":   "outer_d",
    "深度":   "depth",      "间距":   "spacing",
    "角度":   "angle",
    # 物理 / 工艺量
    "压力":   "pressure",   "压强":   "pressure",
    "流量":   "flow_rate",  "风量":   "flow_rate",
    "温度":   "temp",       "浓度":   "conc",
    "功率":   "power",      "转速":   "rpm",
    "风速":   "speed",      "流速":   "speed",
    "容积":   "volume",     "体积":   "volume",
    "面积":   "area",
    # 单字几何同义词（口语常见：长/宽/高/深/厚），范围感知避免误伤
    "长":     "length",    "宽":     "width",
    "高":     "height",    "深":     "depth",
    "厚":     "thickness",
    # 数量类（限定到具体参数名）
    "行数":   "n_rows",     "列数":   "n_cols",
    "分区数": "n_zones",    "数量":   "n_zones",
    "个数":   "n_zones",
}


# ══════════════════════════════════════════════════════════
#  意图解析
# ══════════════════════════════════════════════════════════

def resolve_intent(text: str) -> Optional[dict]:
    """解析自然语言参数修改意图。

    输入: "絮凝池水深改成 5m" / "层高 3.6" / "桩径加到 800"

    返回: {
        "domain": "water_treatment",
        "function": "aeration_tank",
        "param": "depth",
        "value": 5.0,
        "raw_text": "絮凝池水深改成 5m",
    }
        或 None（无法解析时）
    """
    result = {"raw_text": text}
    text_lower = text.lower().strip()

    # Step 1: 匹配构件/设备 → domain + function（最长匹配优先，杜绝子串抢匹配）
    best_domain = None
    best_len = 0
    for cn_name, (domain, func) in _CN_DOMAIN_ALIASES.items():
        if cn_name in text_lower and len(cn_name) > best_len:
            best_domain = (domain, func)
            best_len = len(cn_name)
    if best_domain is None:
        return None  # 无法识别构件
    result["domain"], result["function"] = best_domain

    # Step 2: 范围感知的参数匹配（最长匹配优先）
    # 先专属别名（仅当目标参数确实存在于该函数），再通用同义词（同样限定到本函数参数）。
    func_params = PARAM_REGISTRY.get(result["domain"], {}).get(result["function"], {})
    param = None
    best_len = 0
    for cn_param, en_param in _CN_PARAM_ALIASES.items():
        if cn_param in text_lower and en_param in func_params and len(cn_param) > best_len:
            param = en_param
            best_len = len(cn_param)
    if param is None:
        for term, en_param in GENERIC_SYNONYMS.items():
            if term in text_lower and en_param in func_params and len(term) > best_len:
                param = en_param
                best_len = len(term)
    if param is None:
        return None  # 无法识别参数
    result["param"] = param

    # Step 3: 提取数值（支持 5m / 3.6 / 800）
    import re
    # 匹配 "数字 + 可选单位(m/mm/cm/m3/L)"
    val_match = re.search(r'(\d+\.?\d*)\s*[mM厘毫微]?(?:m|米)?', text_lower)
    if not val_match:
        # 尝试纯数字
        val_match = re.search(r'(\d+\.?\d*)', text_lower)

    if val_match:
        raw_val = float(val_match.group(1))
        # 单位换算：如果原文本含 "mm" 或 "毫米"，单位是 mm
        if re.search(r'[mM]{2}|毫米|mm', text_lower) and result["param"] in (
            "bore", "stroke", "diameter"
        ):
            result["value"] = raw_val  # 保持 mm
        # 如果参数描述含 m，且数值 > 100 → 可能是 mm 转 m
        elif result["param"] in ("depth", "length", "width", "height", "span",
                                  "floor_height", "wall_thickness", "slab_thickness"):
            if raw_val > 100:
                result["value"] = raw_val / 1000.0  # mm→m
            else:
                result["value"] = raw_val
        else:
            result["value"] = raw_val
    else:
        return None  # 无法提取数值

    return result


# ══════════════════════════════════════════════════════════
#  改参 + 重出图
# ══════════════════════════════════════════════════════════

def get_params(domain: str, func_alias: str) -> Optional[Dict[str, Any]]:
    """获取某函数的参数默认值字典。"""
    domain_params = PARAM_REGISTRY.get(domain, {})
    func_params = domain_params.get(func_alias)
    if not func_params:
        return None
    return {k: v[2] for k, v in func_params.items()}


def list_params(domain: str, func_alias: str) -> List[dict]:
    """列出某函数所有可调参数，含类型和描述。"""
    domain_params = PARAM_REGISTRY.get(domain, {})
    func_params = domain_params.get(func_alias)
    if not func_params:
        return []
    return [
        {"name": k, "type": v[0], "desc": v[1], "default": v[2]}
        for k, v in func_params.items()
    ]


def apply_and_redraw(intent: dict, out_dir: str, scale: float = 100.0
                      ) -> Optional[str]:
    """根据解析结果改参并重出图。

    返回: 生成的 DXF 路径，或 None
    """
    domain = intent.get("domain")
    func_name = intent.get("function")
    param = intent.get("param")
    value = intent.get("value")

    if not all([domain, func_name, param, value is not None]):
        print(f"  [参数化] 意图解析不完整: {intent}")
        return None

    # 获取默认参数
    params = get_params(domain, func_name)
    if params is None:
        print(f"  [参数化] 未找到参数定义: {domain}.{func_name}")
        return None

    # 改参
    if param in params:
        old_val = params[param]
        params[param] = value
        print(f"  [参数化] {domain}.{func_name} {param}: {old_val} → {value}")
    else:
        print(f"  [参数化] 函数 {domain}.{func_name} 无此参数: {param}")
        print(f"    可用参数: {list(params.keys())}")
        return None

    # 调用绘图引擎
    try:
        from ..cli import _run_domain_drawing
        path = _run_domain_drawing(domain, func_name, params, out_dir, scale=scale)
        if path:
            print(f"  [参数化] 重新生成: {path}")
        return path
    except ImportError:
        # 降级：直接调模块
        try:
            import importlib
            dom = _CN_DOMAIN_ALIASES.get(domain)
            # Fallback: 从 PARAM_REGISTRY 获取模块名
            mod_name = f"envcad.standards.{domain}"
            mod = importlib.import_module(mod_name)
            func_alias_map = PARAM_REGISTRY.get(domain, {})
            if func_name in func_alias_map:
                from ..engine.dxf_base import new_drawing, save_dxf
                from ..cli import DOMAIN_REGISTRY
                dom_info = DOMAIN_REGISTRY.get(domain, {})
                real_func = dom_info.get("functions", {}).get(func_name)
                if real_func:
                    draw_fn = getattr(mod, real_func)
                    doc, _, tracker = new_drawing(scale, return_tracker=True)
                    msp = doc.modelspace()
                    os.makedirs(out_dir, exist_ok=True)
                    filename = f"{domain}_{func_name}_parametric.dxf"
                    path = os.path.join(out_dir, filename)
                    draw_fn(msp, (5000, 5000), **params)
                    save_dxf(doc, path)
                    print(f"  [参数化] 重新生成: {path}")
                    return path
        except Exception as e:
            print(f"  [参数化] 降级重绘失败: {e}")
            import traceback
            traceback.print_exc()
            return None


# ══════════════════════════════════════════════════════════
#  CLI 入口（envcad parametric <自然语言>）
# ══════════════════════════════════════════════════════════

def parametric_cli(text: str, out_dir: str = None, scale: float = 100.0):
    """从 CLI 调用参数化桥接。"""
    if out_dir is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Desktop", "envcad-output")

    print(f"\n[参数化桥接] 解析: \"{text}\"")
    intent = resolve_intent(text)

    if not intent:
        print("  [参数化] 无法解析意图。支持的格式：\"构件名 + 参数名 + 数值\"")
        print("  例如: \"层高 3.6\" / \"絮凝池水深 5m\" / \"柱宽 600\"")
        return None

    print(f"  定位: {intent['domain']}.{intent['function']}")
    print(f"  参数: {intent['param']} → {intent['value']}")

    return apply_and_redraw(intent, out_dir, scale)
