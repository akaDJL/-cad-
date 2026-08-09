"""多领域配置：每个工程领域一套图层扩展 + 技术要求模板 + 标注提示。

设计原则：
  - 基础国标图层（粗实线/细实线/点画线…）由 layers.py 的 setup_layers() 统一建立，
    所有领域共享，不在此重复定义。
  - 每个领域只定义【额外】需要的专用图层 + 行业技术要求模板 + 标注提示。
  - 新增领域只需在此文件加一个字典，不改引擎代码。
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# 领域专用图层定义：(图层名, ACI颜色, 线型, 线宽1/100mm)
DOMAIN_LAYERS: Dict[str, List[Tuple]] = {
    "environmental": [
        ("管道-污水",   4, "CONTINUOUS", 50),
        ("管道-给水",   5, "CONTINUOUS", 50),
        ("管道-加药",   6, "CONTINUOUS", 35),
        ("管道-污泥",   2, "CONTINUOUS", 50),
        ("池体-壁",     7, "CONTINUOUS", 50),
        ("池体-水",     4, "CONTINUOUS", 18),
        ("设备",        2, "CONTINUOUS", 35),
        ("阀门",        1, "CONTINUOUS", 35),
        ("标高",        3, "CONTINUOUS", 18),
        ("图例",        7, "CONTINUOUS", 18),
        ("流向",        1, "CONTINUOUS", 35),
    ],
    "mechanical": [
        ("轮廓-粗",     7, "CONTINUOUS", 50),
        ("轮廓-中",     7, "CONTINUOUS", 35),
        ("螺纹",        4, "CONTINUOUS", 18),
        ("粗糙度",      3, "CONTINUOUS", 18),
        ("公差",        2, "CONTINUOUS", 18),
        ("剖面线",      7, "CONTINUOUS", 18),
        ("中心孔",      1, "CENTER",     18),
    ],
    "architecture": [
        ("墙体",        7, "CONTINUOUS", 50),
        ("门窗",        4, "CONTINUOUS", 35),
        ("家具",        8, "CONTINUOUS", 18),
        ("标注-轴线",   1, "CENTER",     18),
        ("标注-标高",   3, "CONTINUOUS", 18),
        ("填充",        8, "CONTINUOUS", 9),
        ("楼梯",        7, "CONTINUOUS", 35),
    ],
    "electrical": [
        ("导线-动力",   1, "CONTINUOUS", 25),
        ("导线-控制",   4, "CONTINUOUS", 18),
        ("导线-信号",   6, "DASHED",     18),
        ("接地",        2, "PHANTOM",    18),
        ("设备-强电",   7, "CONTINUOUS", 35),
        ("设备-弱电",   6, "CONTINUOUS", 25),
        ("桥架",        8, "CONTINUOUS", 35),
        ("标注-线号",   3, "CONTINUOUS", 18),
    ],
    "water": [
        ("管道-给水",   1, "CONTINUOUS", 50),
        ("管道-排水",   5, "CONTINUOUS", 50),
        ("管道-消防",   1, "CONTINUOUS", 50),
        ("管道-热水",   6, "CONTINUOUS", 35),
        ("阀门",        1, "CONTINUOUS", 35),
        ("水泵",        2, "CONTINUOUS", 35),
        ("标高",        3, "CONTINUOUS", 18),
        ("坡度",        3, "CONTINUOUS", 18),
    ],
    "general": [],
}

# 领域技术要求模板
DOMAIN_TECH_NOTES: Dict[str, List[str]] = {
    "environmental": [
        "技术要求:",
        "1. 池体采用C30防水混凝土，抗渗等级P8",
        "2. 管道材质：污水管HDPE，污泥管不锈钢",
        "3. 进出水管坡度 i>=0.004",
        "4. 设备防腐：环氧树脂涂料两道",
    ],
    "mechanical": [
        "技术要求:",
        "1. 未注尺寸公差按 GB/T 1804-m",
        "2. 未注形位公差按 GB/T 1184-K",
        "3. 锐边倒钝 R0.5",
        "4. 表面处理：发黑",
    ],
    "architecture": [
        "技术要求:",
        "1. 墙体厚度240mm，材料为MU10烧结砖",
        "2. 门窗尺寸详门窗表",
        "3. 室内地坪标高+/-0.000，室外-0.450",
        "4. 楼层净高2800mm",
    ],
    "electrical": [
        "技术要求:",
        "1. 所有元器件型号详见材料表",
        "2. 导线截面详见导线表",
        "3. 接地电阻不大于4欧姆",
        "4. 防护等级IP54",
    ],
    "water": [
        "技术要求:",
        "1. 给水管采用PPR管，热熔连接",
        "2. 排水管采用UPVC管，粘接",
        "3. 给水试验压力0.6MPa",
        "4. 排水管坡度：DN100 i=0.02, DN150 i=0.01",
    ],
    "general": [
        "技术要求:",
        "1. 未注尺寸单位为mm",
        "2. 未注公差按GB/T 1804-m",
    ],
}

# 领域标注提示（给 agent 参考，该领域还需要补什么标注）
DOMAIN_HINTS: Dict[str, Dict[str, str]] = {
    "environmental": {
        "pipe_diameter": "标注管道管径（DN350 等）",
        "elevation":     "标注构筑物标高（+/-0.000 等）",
        "flow_rate":     "标注设计流量（Q=50m3/d 等）",
        "equipment":     "标注设备型号及参数",
    },
    "mechanical": {
        "surface_roughness": "标注表面粗糙度 Ra 值",
        "tolerance":         "标注配合公差（H7/g6 等）",
        "thread":            "标注螺纹规格（M10-7H 等）",
        "chamfer":           "标注倒角及圆角",
    },
    "architecture": {
        "elevation":  "标注各房间地坪标高",
        "axis":       "标注轴线编号",
        "room_name":  "标注各房间名称及面积",
        "door_window":"标注门窗尺寸及编号",
    },
    "electrical": {
        "device_code":  "标注元器件位号（KM1/KA1/FR1 等）",
        "wire_cross":   "标注导线线号及截面",
        "voltage":      "标注电压等级",
        "terminal":     "标注端子排编号",
    },
    "water": {
        "pipe_diameter": "标注管径及材质（DN100 PPR 等）",
        "slope":         "标注管道坡度及坡向",
        "valve":         "标注阀门型号",
        "elevation":     "标注管道标高",
    },
    "general": {},
}

# 领域默认 FrameInfo 字段
DOMAIN_FRAME_DEFAULTS: Dict[str, Dict] = {
    "environmental": {"project": "环保工程"},
    "mechanical":    {"project": "机械设计"},
    "architecture":  {"project": "建筑工程"},
    "electrical":    {"project": "电气工程"},
    "water":         {"project": "给排水工程"},
    "general":       {"project": "工程设计"},
}


def get_domain_layers(domain: str = "environmental") -> list:
    """返回领域专用图层定义列表，不存在则返回空。"""
    return DOMAIN_LAYERS.get(domain, [])


def get_domain_tech_notes(domain: str = "environmental") -> list:
    """返回领域技术要求模板，不存在则返回通用模板。"""
    return DOMAIN_TECH_NOTES.get(domain, DOMAIN_TECH_NOTES["general"])


def get_domain_hints(domain: str = "environmental") -> dict:
    """返回领域标注提示，不存在则返回空字典。"""
    return DOMAIN_HINTS.get(domain, {})


def get_domain_frame_defaults(domain: str = "environmental") -> dict:
    """返回领域 FrameInfo 默认值。"""
    return DOMAIN_FRAME_DEFAULTS.get(domain, {"project": "工程设计"})


def supported_domains() -> list:
    """返回所有支持的领域列表。"""
    return list(DOMAIN_LAYERS.keys())


# ─── 兼容别名（供 ezdxf_annotator 使用）─────────────────────
def get_profile(domain: str = "environmental") -> dict:
    """兼容 ezdxf_annotator 的旧接口，等价于 get_domain_frame_defaults。"""
    return get_domain_frame_defaults(domain)


def list_domains() -> list:
    """兼容 ezdxf_annotator 的旧接口，等价于 supported_domains。"""
    return supported_domains()
