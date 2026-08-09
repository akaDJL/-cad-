# -*- coding: utf-8 -*-
"""结构设计计算公式库（钢筋混凝土常用验算，简化工程算法）。

供 design 层与 docgen 计算书直接调用，公式依据 GB 50010 常规表达式。
所有内力单位 N_mm（力矩 N_mm，剪力 N，尺寸 mm），返回量为常用工程单位。
"""
from __future__ import annotations


def xi_b(fy: float, Es: float = 200000.0, ecu: float = 0.0033,
         beta1: float = 0.8) -> float:
    """界限相对受压区高度 ξb（受拉钢筋屈服与混凝土压碎同时发生）。"""
    return beta1 / (1.0 + fy / (Es * ecu))


def rc_flexure(b: float, h0: float, M: float, fc: float, fy: float,
               alpha1: float = 1.0) -> dict:
    """单筋矩形截面正截面受弯承载力。

    返回: As(计算配筋 mm2)、ξ、x、Mu(抗弯承载力 N_mm)、ok(ξ小于等于ξb)
    """
    xb = xi_b(fy) * h0
    alphas = M / (alpha1 * fc * b * h0 * h0)
    if alphas > 1.0:
        return dict(As=None, xi=None, x=None, Mu=0.0, ok=False, note="alpha_s>1 超筋，需加大截面或改双筋")
    xi = 1.0 - (1.0 - 2.0 * alphas) ** 0.5
    x = xi * h0
    As = alpha1 * fc * b * x / fy
    Mu = alpha1 * fc * b * x * (h0 - x / 2.0)
    ok = x <= xb
    return dict(As=As, xi=xi, x=x, Mu=Mu, ok=ok,
                note="" if ok else "超筋，ξ>ξb，应提高混凝土等级或改用双筋截面")


def rc_shear(b: float, h0: float, V: float, ft: float, fc: float,
             fyv: float = 360.0, beta_c: float = 1.0) -> dict:
    """斜截面受剪（仅箍筋）验算。

    返回: Asv_s(箍筋面积/间距 mm2/mm)、Vc(混凝土抗剪)、Vmax(截面限制)、
          ok_section、ok_stirrup
    """
    Vc = 0.7 * ft * b * h0
    Vmax = 0.25 * beta_c * fc * b * h0
    ok_section = V <= Vmax
    need = max(0.0, V - Vc)
    Asv_s = need / (fyv * h0) if h0 > 0 else 0.0
    ok_stirrup = V <= Vc or Asv_s > 0.0
    return dict(Asv_s=Asv_s, Vc=Vc, Vmax=Vmax,
                ok_section=ok_section, ok_stirrup=ok_stirrup,
                note="" if ok_section else "截面抗剪不足，需加大截面或提高混凝土等级")


def rc_crack(Mk: float, As: float, b: float, h: float, h0: float,
             ftk: float, c: float = 20.0, d_eq: float = 25.0,
             Es: float = 200000.0, alpha_cr: float = 2.1,
             limit: float = 0.30) -> dict:
    """受弯构件最大裂缝宽度(mm)，GB 50010 简化式。"""
    rho_te = max(As / (0.5 * b * h), 0.01)
    if As <= 0:
        return dict(wmax=0.0, psi=1.0, rho_te=rho_te, ok=True, note="无受拉筋")
    sigma_sk = Mk / (0.87 * As * h0)
    psi = max(0.2, min(1.0, 1.1 - 0.65 * ftk / (rho_te * sigma_sk)))
    wmax = alpha_cr * psi * sigma_sk / Es * (1.9 * c + 0.08 * d_eq / rho_te)
    return dict(wmax=wmax, psi=psi, rho_te=rho_te, ok=wmax <= limit,
                note="" if wmax <= limit else f"裂缝超限(>{limit}mm)")


def rc_deflect(Mk: float, As: float, b: float, h0: float, l: float,
               Ec: float = 30000.0, Es: float = 200000.0,
               limit_div: float = 200.0) -> dict:
    """受弯构件挠度(mm)，简支梁跨中简化（5/48_Mk_l2/Bs）。"""
    if As <= 0:
        return dict(f=0.0, Bs=0.0, ok=True, note="无配筋")
    rho = As / (b * h0)
    alpha_e = Es / Ec
    psi = 0.85  # 取常用中值
    Bs = Es * As * h0 * h0 / (1.15 * psi + 0.2 + 6.0 * alpha_e * rho)
    f = 5.0 / 48.0 * Mk * l * l / Bs if Bs > 0 else 0.0
    return dict(f=f, Bs=Bs, ok=f <= l / limit_div,
                note="" if f <= l / limit_div else f"挠度超限(l/{limit_div})")


# ══════════════════════════════════════════════════════════
#  水力学公式
# ══════════════════════════════════════════════════════════

def manning_velocity(R, n, S):
    """曼宁公式计算流速 v (m/s)。
    R-水力半径(m), n-粗糙系数, S-水力坡度。
    v = (1/n) * R^(2/3) * S^(1/2)
    """
    if n <= 0 or R <= 0 or S <= 0:
        return 0.0
    return (1.0 / n) * (R ** (2.0 / 3.0)) * (S ** 0.5)


def manning_flow(A, R, n, S):
    """曼宁公式计算流量 Q (m3/s)。
    A-过水断面面积(m2)。
    """
    return A * manning_velocity(R, n, S)


def darcy_weisbach(v, L, D, f=0.02, g=9.81):
    """达西-魏斯巴赫公式计算沿程水头损失 hf (m)。"""
    if D <= 0:
        return 0.0
    return f * (L / D) * (v * v) / (2.0 * g)


def hazen_williams(Q, D, L, Ch=120):
    """海曾-威廉公式计算给水管道水头损失 hf (m)。"""
    if D <= 0 or Ch <= 0:
        return 0.0
    return 10.67 * (Q ** 1.852) * L / ((Ch ** 1.852) * (D ** 4.8704))


def surface_load_area(Q, q):
    """表面负荷法计算沉淀池/滤池面积 A (m2)。
    Q-流量(m3/h), q-表面负荷(m3/m2*h)。
    """
    if q <= 0:
        return 0.0
    return Q / q


def retention_volume(Q, T):
    """停留时间法计算池容 V (m3)。
    Q-流量(m3/h), T-停留时间(h)。
    """
    return Q * T


# ══════════════════════════════════════════════════════════
#  大气治理公式
# ══════════════════════════════════════════════════════════

def baghouse_filter_area(Q, vf):
    """布袋除尘器过滤面积 A (m2)。
    Q-处理风量(m3/h), vf-过滤风速(m/min)。
    """
    if vf <= 0:
        return 0.0
    return Q / (60.0 * vf)


def baghouse_bag_count(A, d, L):
    """布袋除尘器滤袋数量 n。
    A-过滤面积(m2), d-滤袋直径(m), L-滤袋长度(m)。
    """
    import math
    if d <= 0 or L <= 0:
        return 0
    return math.ceil(A / (math.pi * d * L))


def scrubber_diameter(Q, v):
    """喷淋塔塔径 D (m)。
    Q-处理风量(m3/h), v-空塔流速(m/s)。
    """
    import math
    if v <= 0:
        return 0.0
    return math.sqrt(4.0 * Q / (math.pi * v * 3600.0))


def carbon_adsorption_mass(Q, Ci, q, t_hours):
    """活性炭吸附所需炭量 W (kg)。
    Q-风量(m3/h), Ci-入口浓度(kg/m3), q-工作吸附容量(kg/kg), t-吸附时间(h)。
    """
    if q <= 0:
        return 0.0
    return (Ci * Q * t_hours) / q


# ══════════════════════════════════════════════════════════
#  噪声与振动公式
# ══════════════════════════════════════════════════════════

def noise_mass_law(m, f=500):
    """隔声质量定律估算隔声量 R (dB)。
    m-面密度(kg/m2), f-频率(Hz)。
    """
    import math
    if m <= 0 or f <= 0:
        return 0.0
    return 20.0 * math.log10(m * f) - 42.5


def noise_mass_law_simple(m):
    """500Hz时隔声量简化估算 R (dB)。
    R ≈ 18*lg(m) + 8
    """
    import math
    if m <= 0:
        return 0.0
    return 18.0 * math.log10(m) + 8.0


def vibration_transmissibility(f, fn, damping_ratio=0.05):
    """隔振传递率 T（无量纲）。
    f-扰动频率(Hz), fn-系统固有频率(Hz)。
    """
    if fn <= 0:
        return 1.0
    r = f / fn
    zeta = damping_ratio
    numerator = 1.0 + (2.0 * zeta * r) ** 2
    denominator = (1.0 - r * r) ** 2 + (2.0 * zeta * r) ** 2
    if denominator <= 0:
        return 1.0
    return (numerator / denominator) ** 0.5


def vibration_efficiency(T):
    """隔振效率 η (%)。"""
    return max(0.0, (1.0 - T) * 100.0)


def natural_frequency(delta_st, g=9.81):
    """隔振系统固有频率 fn (Hz)。
    delta_st-静态压缩量(m)。
    """
    import math
    if delta_st <= 0:
        return 0.0
    return (1.0 / (2.0 * math.pi)) * (g / delta_st) ** 0.5


# ══════════════════════════════════════════════════════════
#  电气公式
# ══════════════════════════════════════════════════════════

def cable_voltage_drop(I, L, S, cos_phi=0.85, material="铜"):
    """电缆电压损失 ΔU (%) 简化估算。
    I-电流(A), L-长度(m), S-截面(mm2)。
    """
    rho = 0.0184 if material == "铜" else 0.031
    R = rho * L / S
    Un = 380
    dU = 1.732 * I * R * cos_phi / (Un * 10) * 100
    return dU


def short_circuit_section(Ik, t, k=171):
    """短路热稳定校验最小截面 S (mm2)。
    Ik-短路电流(kA), t-短路持续时间(s), k-热稳定系数。
    """
    return Ik * 1000 * (t ** 0.5) / k


def power_factor_correction(P_kW, cos1, cos2):
    """功率因数补偿所需电容容量 Qc (kvar)。"""
    import math
    if cos1 >= 1.0 or cos2 >= 1.0:
        return 0.0
    tan1 = math.tan(math.acos(cos1))
    tan2 = math.tan(math.acos(cos2))
    return P_kW * (tan1 - tan2)


# ══════════════════════════════════════════════════════════
#  暖通空调公式
# ══════════════════════════════════════════════════════════

def cooling_load(area, q):
    """面积指标法估算冷负荷 Q (W)。"""
    return area * q


def supply_air_flow(Q, rho=1.2, cp=1.01, delta_t=8.0):
    """送风量 G (m3/h)。
    Q-全热负荷(kW), delta_t-送风温差(度C)。
    """
    if delta_t <= 0:
        return 0.0
    return Q * 3600.0 / (rho * cp * delta_t)


def duct_velocity(Q, A):
    """风管内风速 v (m/s)。
    Q-风量(m3/h), A-截面积(m2)。
    """
    if A <= 0:
        return 0.0
    return Q / 3600.0 / A


def duct_pressure_loss(v, L, D_eq, lambda_=0.02):
    """风管沿程阻力 ΔP (Pa)。"""
    rho = 1.2
    if D_eq <= 0:
        return 0.0
    return lambda_ * (L / D_eq) * (rho * v * v) / 2.0


def water_pipe_flow(Q_kW, delta_t=5.0, cp=4.1868):
    """空调水管流量 G (m3/h)。
    Q_kW-冷热负荷(kW), delta_t-供回水温差(度C)。
    """
    if delta_t <= 0:
        return 0.0
    return Q_kW * 3600.0 / (1000.0 * cp * delta_t)


# ══════════════════════════════════════════════════════════
#  固废处理公式
# ══════════════════════════════════════════════════════════

def landfill_capacity(W, N, T, rho=0.9):
    """填埋场库容 V (m3)。
    W-人均垃圾产量(kg/人*d), N-服务人口(人), T-使用年限(a)。
    """
    if rho <= 0:
        return 0.0
    return W * N * T * 365.0 / (1000.0 * rho)


def leachate_flow(I, A, C=0.5):
    """渗滤液产量 Q (m3/d)。
    I-降雨量(mm/d), A-汇水面积(ha), C-渗流系数。
    """
    return I * A * C / 1000.0
