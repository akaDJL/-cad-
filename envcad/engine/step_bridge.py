"""
STEP 3D 模型输出桥接模块（v1.5.1 新增）。

依赖 build123d（>=0.8）。为 envcad 补齐「输出 STEP」能力缺口，
与 2D DXF 引擎（dxf_base）对应，提供 3D 参数化建模 + STEP 导出。

用法：
    from envcad.engine.step_bridge import StepAssembly, make_spur_gear_3d

    asm = StepAssembly("减速器")
    asm.add_box("底板", 200, 300, 20, pos=(100, 150, 10))
    gear = make_spur_gear_3d(m=4, z=20, b=25)
    asm.add(gear, pos=(0, 0, 30))
    asm.save("output.step")

依赖安装：pip install build123d
"""
from __future__ import annotations

import math
import os
from typing import List, Optional, Tuple


def _bd():
    """惰性导入 build123d，未安装时给出明确提示。"""
    try:
        import build123d
        return build123d
    except ImportError as e:
        raise ImportError(
            "STEP 输出需要 build123d，请先安装：pip install build123d"
        ) from e


class StepAssembly:
    """3D 装配体容器：收集零件，统一导出 STEP。

    坐标约定与 build123d 一致：Box/Cylinder 等基本体默认居中于原点，
    Cylinder 轴沿 Z。pos 为移动量（mm）。
    """

    def __init__(self, label: str = "Assembly"):
        self.bd = _bd()
        self.parts: List = []
        self.label = label

    def add(self, shape, pos: Tuple[float, float, float] = (0, 0, 0)):
        """添加一个已定位的 build123d 形状。"""
        if pos != (0, 0, 0):
            shape = shape.moved(self.bd.Pos(*pos))
        self.parts.append(shape)
        return shape

    def add_box(self, l: float, w: float, h: float,
                pos: Tuple[float, float, float] = (0, 0, 0),
                label: str = "box"):
        shape = self.bd.Box(l, w, h)
        shape.label = label
        return self.add(shape, pos)

    def add_cylinder(self, r: float, h: float,
                     pos: Tuple[float, float, float] = (0, 0, 0),
                     label: str = "cylinder"):
        shape = self.bd.Cylinder(r, h)
        shape.label = label
        return self.add(shape, pos)

    def add_sphere(self, r: float,
                   pos: Tuple[float, float, float] = (0, 0, 0),
                   label: str = "sphere"):
        shape = self.bd.Sphere(r)
        shape.label = label
        return self.add(shape, pos)

    def add_cone(self, r: float, h: float,
                 pos: Tuple[float, float, float] = (0, 0, 0),
                 label: str = "cone"):
        shape = self.bd.Cone(r, h, r * 0.5)
        shape.label = label
        return self.add(shape, pos)

    def save(self, path: str) -> str:
        """合并所有零件并导出 STEP，返回绝对路径。"""
        path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        comp = self.bd.Compound(label=self.label, children=self.parts)
        self.bd.export_step(comp, path)
        return path


def save_step(parts: List, path: str, label: str = "Assembly") -> str:
    """快速导出：直接给一堆 build123d 形状，输出一个 STEP。"""
    bd = _bd()
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    comp = bd.Compound(label=label, children=parts)
    bd.export_step(comp, path)
    return path


# ═══════════════════════════════════════════
# 常用机械零件 3D 生成（对应 2D mechanical 模块）
# ═══════════════════════════════════════════

def make_spur_gear_3d(m: float = 4.0, z: int = 20, b: float = 25.0,
                      bore: Optional[float] = None, bd=None):
    """直齿圆柱齿轮 3D（简化齿形：齿顶圆盘 + 等间距矩形齿槽 + 中心孔）。

    m=模数(mm), z=齿数, b=齿宽(mm), bore=中心孔径(默认 da*0.15)。
    齿轮轴沿 Z，中心在原点。
    """
    bd = bd or _bd()
    da = m * (z + 2)          # 齿顶圆直径
    df = m * (z - 2.5)        # 齿根圆直径
    ra, rf = da / 2, df / 2
    bore = bore if bore is not None else da * 0.15

    gear = bd.Cylinder(ra, b)

    # 齿槽（径向矩形，等间距分布）
    slot_w = m * 0.65          # 齿槽宽（近似）
    slot_depth = ra - rf + 1   # 齿槽深度
    for i in range(z):
        angle = i * 360.0 / z
        slot = bd.Box(slot_w, b + 2, slot_depth)
        slot = slot.moved(bd.Pos(rf + slot_depth / 2, 0, 0))
        slot = slot.moved(bd.Rot(0, 0, angle))
        gear -= slot

    # 中心孔
    gear -= bd.Cylinder(bore / 2, b + 2)

    gear.label = f"直齿轮 m={m} z={z}"
    return gear


def make_stepped_shaft_3d(diameters: List[float], lengths: List[float],
                          bd=None):
    """阶梯轴 3D（多段圆柱，轴沿 X，从左到右）。

    diameters=[40,55,40,30](mm), lengths=[60,35,45,25](mm)。
    """
    bd = bd or _bd()
    segments = []
    x = 0.0
    for dia, length in zip(diameters, lengths):
        seg = bd.Cylinder(dia / 2, length, rotation=(0, 90, 0))  # 轴沿 X
        seg = seg.moved(bd.Pos(x + length / 2, 0, 0))
        segments.append(seg)
        x += length

    shaft = segments[0]
    for seg in segments[1:]:
        shaft += seg
    shaft.label = "阶梯轴"
    return shaft


def make_cyl_tank_3d(d: float, h: float, wall: float = 6.0,
                     bd=None):
    """立式圆筒罐/池体 3D（含底板+顶板，壁厚 wall）。

    d=内径, h=高度, wall=壁厚。轴沿 Z。
    """
    bd = bd or _bd()
    r_in, r_out = d / 2, d / 2 + wall

    shell = bd.Cylinder(r_out, h) - bd.Cylinder(r_in, h + 2)
    bottom = bd.Cylinder(r_out, wall)
    top = bd.Cylinder(r_out, wall).moved(bd.Pos(0, 0, h))

    tank = shell + bottom + top
    tank.label = f"圆筒罐 D{d} H{h}"
    return tank


def make_rect_tube_frame_3d(l: float, w: float, tube: float = 50.0,
                            wall: float = 4.0, bd=None):
    """矩形管车架 3D（两条纵梁 + 两条端梁，矩形管截面 tube×tube）。

    l=长度, w=宽度, tube=管截面边长, wall=壁厚。
    """
    bd = bd or _bd()
    half = tube / 2
    inner = tube / 2 - wall

    def beam(length):
        # 矩形管（沿 X 方向）
        outer = bd.Box(length, tube, tube)
        inner_box = bd.Box(length + 2, tube - 2 * wall, tube - 2 * wall)
        return outer - inner_box

    b1 = beam(l).moved(bd.Pos(l / 2, w / 2 - half, 0))
    b2 = beam(l).moved(bd.Pos(l / 2, -w / 2 + half, 0))
    # 端梁沿 Y 方向
    b3 = bd.Box(tube, w, tube) - bd.Box(tube - 2 * wall, w + 2, tube - 2 * wall)
    b3 = b3.moved(bd.Pos(half, 0, 0))
    b4 = b3.moved(bd.Pos(l - tube, 0, 0))

    frame = b1 + b2 + b3 + b4
    frame.label = f"矩形管车架 {l}x{w}"
    return frame


# 便捷：常用零件的统一入口（便于 CLI/Agent 调用）
PART_MAKERS = {
    "spur_gear": make_spur_gear_3d,
    "stepped_shaft": make_stepped_shaft_3d,
    "cyl_tank": make_cyl_tank_3d,
    "rect_frame": make_rect_tube_frame_3d,
}


def make_part(kind: str, **kwargs):
    """按名称生成零件 3D，如 make_part("spur_gear", m=4, z=20, b=25)。"""
    if kind not in PART_MAKERS:
        raise ValueError(f"未知零件类型 {kind}，可用：{list(PART_MAKERS)}")
    return PART_MAKERS[kind](**kwargs)
