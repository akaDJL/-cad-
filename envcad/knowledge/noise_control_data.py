# -*- coding: utf-8 -*-
"""噪声与振动治理设计数据速查 — GB 12348、HJ 2034、HJ/T 90、GB/T 19887。

数值为行业常用区间/典型默认，供绘图默认参数与 AI 取数参考；
实际工程应由源强/敏感点声级/插入损失目标计算确定。
"""

NOISE_DEFAULTS = {
    # 声屏障（mm）
    "barrier_H": 3000.0,        # 屏体高度（路面以上，常规 2.5~4.0m）
    "post_pitch": 2000.0,       # 立柱间距
    "post_type": "HW150×150",   # H 钢立柱
    "panel_t": 100.0,           # 吸声屏体厚（常规 80~120）
    "base_W": 500.0,            # 基础宽
    "base_H": 800.0,            # 基础高
    "base_embed": 1200.0,       # 基础埋深
    "top_arc": 500.0,           # 顶部弧形挑臂（可选）
    # 消声器
    "muffler_L": 1500.0,        # 消声器长（常规 1000~2000）
    "muffler_W": 800.0,         # 断面宽
    "muffler_H": 800.0,         # 断面高
    "n_splitter": 4,            # 阻性消声片数
    "splitter_t": 100.0,        # 消声片厚
    "splitter_gap": 100.0,      # 片间气流通道
    # 隔声罩
    "hood_L": 3000.0,           # 隔声罩长
    "hood_W": 2000.0,           # 罩宽
    "hood_H": 2200.0,           # 罩高
    "hood_t": 100.0,            # 罩板厚（钢板+吸声层）
    "window_W": 600.0,          # 观察窗宽
    "window_H": 800.0,          # 观察窗高
    "door_W": 800.0,            # 检修门宽
    "door_H": 1800.0,           # 检修门高
    # 消声百叶
    "louver_L": 1200.0,         # 百叶长度（进深）
    "louver_W": 1500.0,         # 百叶宽
    "louver_H": 1000.0,         # 百叶高
    "blade_pitch": 150.0,       # 叶片间距
    "blade_t": 80.0,            # 叶片厚
}

NOISE_NOTES = [
    "声屏障插入损失常规 5~15 dB(A)，顶端绕射为控制因素。",
    "阻性消声器消声量 15~25 dB(A)/m，流速≤8~12 m/s 防再生噪声。",
    "隔声罩内衬 50~100mm 吸声棉，罩体计权隔声量≥25 dB。",
    "厂界执行 GB 12348 相应声环境功能区限值。",
]

NOISE_CODES = ["GB 12348", "HJ 2034", "HJ/T 90", "GB/T 19887", "GB 3096"]


def noise_summary() -> str:
    return f"噪声治理数据：屏障高 {NOISE_DEFAULTS['barrier_H']:.0f}，消声器 {NOISE_DEFAULTS['muffler_L']:.0f} 长，规范 {len(NOISE_CODES)} 本"
