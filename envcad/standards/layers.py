"""国标图层定义（GB/T 17450 图线 + 环保工程常用图层）。

线宽约定（出图 mm）：粗 0.5 / 中 0.35 / 细 0.18。
ezdxf lineweight 单位为 1/100 mm。
"""
from __future__ import annotations

import ezdxf

# (图层名, ACI颜色, 线型, 线宽1/100mm)
LAYER_DEFS = [
    # —— 基本图线 ——
    ("粗实线",        7, "CONTINUOUS", 50),   # 主轮廓
    ("中实线",        7, "CONTINUOUS", 35),   # 次轮廓
    ("细实线",        7, "CONTINUOUS", 18),   # 辅助、表格
    ("细实线-尺寸",   3, "CONTINUOUS", 18),   # 尺寸线（绿）
    ("细实线-辅助",   8, "CONTINUOUS", 18),
    ("虚线",          2, "DASHED",    35),    # 不可见轮廓（黄）
    ("点画线",        1, "CENTER",    18),    # 中心线/对称线（红）
    ("双点画线",      6, "PHANTOM",   18),    # 假想线
    # —— 工程图专用 ——
    ("图框",          7, "CONTINUOUS", 18),  # 0.18mm细实线，GB/T 14689
    ("文字",          7, "CONTINUOUS", 18),
    ("文字-标题",     7, "CONTINUOUS", 35),
    ("剖面线",        7, "CONTINUOUS", 18),
    ("网格",          8, "CONTINUOUS", 9),
    # —— 环保工艺 ——
    ("管道-污水",     4, "CONTINUOUS", 50),   # 青
    ("管道-给水",     5, "CONTINUOUS", 50),   # 蓝
    ("管道-加药",     6, "CONTINUOUS", 35),
    ("池体-壁",       7, "CONTINUOUS", 50),
    ("池体-水",       4, "CONTINUOUS", 18),
    ("设备",          2, "CONTINUOUS", 35),
    ("阀门",          1, "CONTINUOUS", 35),
    ("标高",          3, "CONTINUOUS", 18),
    ("图例",          7, "CONTINUOUS", 18),
    ("流向",          1, "CONTINUOUS", 35),
]

# 标准线型定义（dash-gap 序列，单位 mm）
LINETYPE_DEFS = {
    "DASHED":  ([2.0, -1.0], "__ __ __"),
    "CENTER":  ([4.0, -1.0, 0.5, -1.0], "____ . ____"),
    "PHANTOM": ([4.0, -1.0, 0.5, -1.0, 0.5, -1.0], "____ . ____ . ____"),
}


def _ensure_linetype(doc, name: str) -> None:
    """确保线型存在，失败回退 CONTINUOUS。"""
    if name == "CONTINUOUS":
        return
    # 修复：使用正确的 API 检查线型是否存在
    try:
        if doc.linetypes.has_entry(name):
            return
    except Exception as _e:
        # 兼容旧版 ezdxf
        try:
            if name in doc.linetypes:
                return
        except Exception as _e:
            print(f'[WARNING] layers.py: {_e}')
    if name not in LINETYPE_DEFS:
        return
    pattern, desc = LINETYPE_DEFS[name]
    try:
        doc.linetypes.add(name, pattern, desc)
    except Exception as _e:
        # ezdxf 不同版本 API 差异，二次尝试
        try:
            doc.linetypes.add(name, pattern=pattern, description=desc)
        except Exception as _e:
            # 最终兜底
            try:
                doc.linetypes.add(name, [2.5, -1.0], desc)
            except Exception as _e:
                print(f'[WARNING] layers.py: {_e}')


def setup_layers(doc: ezdxf.document.Drawing) -> None:
    """创建全部国标图层与线型。"""
    # 先建线型
    for lt in ("DASHED", "CENTER", "PHANTOM"):
        _ensure_linetype(doc, lt)
    # 再建图层
    for name, color, ltype, lw in LAYER_DEFS:
        if name in doc.layers:
            continue
        try:
            layer = doc.layers.add(name)
            layer.dxf.color = color
            # 修复：正确验证线型可用性
            if ltype == "CONTINUOUS":
                layer.dxf.linetype = "CONTINUOUS"
            else:
                # 检查线型是否真正可用
                try:
                    if doc.linetypes.has_entry(ltype):
                        layer.dxf.linetype = ltype
                    else:
                        # 尝试强制添加
                        _ensure_linetype(doc, ltype)
                        if doc.linetypes.has_entry(ltype):
                            layer.dxf.linetype = ltype
                        else:
                            layer.dxf.linetype = "CONTINUOUS"
                except Exception as _e:
                    # 兼容旧版
                    layer.dxf.linetype = "CONTINUOUS"
            layer.dxf.lineweight = lw
        except Exception as _e:
            print(f'[WARNING] layers.py: {_e}')


def layer_of(doc, name: str) -> str:
    """安全取图层名：不存在则回退到 细实线。"""
    return name if name in doc.layers else "细实线"
