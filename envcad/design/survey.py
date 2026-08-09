# -*- coding: utf-8 -*-
"""测绘GIS设计验算：坐标转换 / 精度评定 / 管线探测埋深校核。

从 knowledge.survey_data 取坐标系参数、精度等级等，完成高斯投影
正反算、控制网精度评定与管线最小埋深校核。
"""
from __future__ import annotations

import math
from ..knowledge import survey_data as sv


# ══════════════════════════════════════════════════════════
#  高斯投影正算（CGCS2000 6°带）
#  B: 纬度(度) L: 经度(度) → x(N), y(E), 带号
# ══════════════════════════════════════════════════════════
def gauss_forward(B: float, L: float) -> dict:
    """高斯-克吕格投影正算（CGCS2000）。

    参数：
        B  纬度 度
        L  经度 度
    返回：自然值 x(m), y(m), 带号, 中央子午线。
    """
    a = sv.CGCS2000["a"]
    e2 = sv.CGCS2000["e2"]
    zone, L0 = sv.gauss_zone(L)

    B_rad = math.radians(B)
    l_rad = math.radians(L - L0)               # 经差 rad

    sinB = math.sin(B_rad)
    cosB = math.cos(B_rad)
    tanB = math.tan(B_rad)

    N = a / math.sqrt(1 - e2 * sinB * sinB)     # 卯酉圈曲率半径
    eta2 = e2 / (1 - e2) * cosB * cosB

    # 子午线弧长（简化：克拉索夫斯基公式近似）
    X = 111134.861 * B - 16036.48 * math.sin(2 * B_rad) + 16.828 * math.sin(4 * B_rad) - 0.022 * math.sin(6 * B_rad)
    X *= 1000                                   # 转为米

    t = tanB
    x = X + N / 2 * sinB * cosB * l_rad**2 \
        + N / 24 * sinB * cosB**3 * (5 - t**2 + 9 * eta2 + 4 * eta2**2) * l_rad**4 \
        + N / 720 * sinB * cosB**5 * (61 - 58 * t**2 + t**4) * l_rad**6

    y = N * cosB * l_rad \
        + N / 6 * cosB**3 * (1 - t**2 + eta2) * l_rad**3 \
        + N / 120 * cosB**5 * (5 - 18 * t**2 + t**4 + 14 * eta2 - 58 * eta2 * t**2) * l_rad**5

    # 加 500km 偏移和带号
    y_nat = y + 500000
    if y_nat < 0:
        y_nat = 0  # 极罕见

    return dict(
        B=B, L=L, zone=zone, L0=L0,
        x=round(x, 3), y_nat=round(y_nat, 3),
        note=f"CGCS2000 {zone}°带 L0={L0}°，x={x:.3f}m y={y_nat:.3f}m",
    )


# ══════════════════════════════════════════════════════════
#  控制网精度评定
# ══════════════════════════════════════════════════════════
def control_accuracy_check(grade: str = "四等",
                           h_err_mm: float = 5.0,
                           v_err_mm: float = 3.0) -> dict:
    """控制点精度达标判定。

    参数：
        grade       控制等级
        h_err_mm    实测平面中误差 mm
        v_err_mm    实测高程中误差 mm
    返回：达标判定。
    """
    std = sv.control_accuracy(grade)
    h_ok = h_err_mm <= std["h"]
    v_ok = v_err_mm <= std["v"]
    return dict(
        grade=grade, standard_h=std["h"], standard_v=std["v"],
        measured_h=h_err_mm, measured_v=v_err_mm,
        h_ok=h_ok, v_ok=v_ok, all_ok=(h_ok and v_ok),
        use=std["use"],
        note=(f"{grade}控制：平面 {h_err_mm}≤{std['h']}mm {'√' if h_ok else '×'}，"
              f"高程 {v_err_mm}≤{std['v']}mm {'√' if v_ok else '×'}"),
    )


# ══════════════════════════════════════════════════════════
#  管线最小埋深校核
# ══════════════════════════════════════════════════════════
def pipe_depth_check(pipe_type: str = "给水", actual_depth: float = 0.6) -> dict:
    """管线埋深-最小埋深校核。

    参数：
        pipe_type     管线类别
        actual_depth  实际埋深 m
    返回：达标判定。
    """
    min_d = sv.pipe_min_depth(pipe_type)
    ok = actual_depth >= min_d
    return dict(
        pipe_type=pipe_type, min_depth=min_d,
        actual_depth=actual_depth, ok=ok,
        note=f"{pipe_type}管线 最小埋深{min_d}m，实际{actual_depth}m {'√' if ok else '× 不足'}",
    )


# ══════════════════════════════════════════════════════════
#  地图比例尺精度校核
# ══════════════════════════════════════════════════════════
def map_scale_check(scale: str = "1:500",
                    feature_spacing: float = 10) -> dict:
    """地形图地物间距-比例尺精度校核。

    参数：
        scale           比例尺
        feature_spacing 地物间距 m
    返回：该间距在图上的距离 mm 与能否分辨。
    """
    prop = sv.map_scale_prop(scale)
    # 图上 0.2mm 对应实地距离
    map_resolution = 0.2 * int(scale.split(":")[1]) / 1000  # m
    on_map_mm = feature_spacing / int(scale.split(":")[1]) * 1000

    ok = feature_spacing >= map_resolution
    return dict(
        scale=scale, feature_spacing=feature_spacing,
        map_resolution=round(map_resolution, 2),
        on_map_mm=round(on_map_mm, 2),
        ok=ok,
        contor_interval=prop["contour"],
        note=(f"{scale} 比例尺，图上分辨率 {map_resolution:.2f}m(0.2mm)，"
              f"地物间距 {feature_spacing}m → 图上 {on_map_mm:.2f}mm "
              f"{'可分辨' if ok else '不可分辨'}"),
    )
