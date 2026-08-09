"""25. pipe_detection —— 地下管线探测成果图。

制图依据：
  CJJ 61—2017《城市地下管线探测技术规程》（管线图图式、管线代码、
  #       管点符号与注记格式；现行城市地下管线探测主体标准）
  # TODO: verify 标准号 —— CJJ/T 158 实为《城建档案业务管理规范》，非管线探测标准；
  #       若任务书指定 CJJ/T 158，请以任务书为准。
  GB/T 20257.1—2017 4.5 管线（地形图上管线要素的表示方法）
  GB/T 50106—2010 给水排水制图标准（管道线型与代号，envcad 已内建）

复用 envcad 既有实现（不重复造轮子）：
  · envcad.standards.plumbing.draw_plumbing_pipe —— 给水/排水/消防管段
  · envcad.standards.pid.draw_process_line       —— 燃气/工业/电力管块
  · envcad.standards.pid.draw_instrument         —— 管点（井）圆形符号
  · envcad.standards.annotate.draw_leader        —— 埋深/规格引出标注
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from envcad.standards.pid import draw_instrument, draw_process_line
from envcad.standards.plumbing import draw_plumbing_pipe

from ._common import (TextEntityAlignment, circle, draw_leader,
                      ensure_doc_ready, line, polyline, solid_fill, text)

# ── 管线代码与图层（探测成果通用代号）────────────────────
# code: (中文名, 图层, 复用函数, plumbing/pid 类型参数)
PIPE_KINDS: Dict[str, Tuple[str, str, str, str]] = {
    "JS": ("给水", "给水管", "plumbing", "cold"),
    "WS": ("污水", "排水管", "plumbing", "drain"),
    "YS": ("雨水", "排水管", "plumbing", "rain"),
    "XF": ("消防", "消防管", "plumbing", "fire"),
    "RQ": ("燃气", "燃气管", "pid", "main"),
    "DL": ("电力", "电力管", "pid", "electrical"),
    "TX": ("通信", "通信管", "pid", "instrument"),
    "RL": ("热力", "热力管", "pid", "jacket"),
    "GY": ("工业", "工艺管道", "pid", "secondary"),
}

# ── 图上尺寸默认值 (mm) ───────────────────────────────────
D_NODE = 1.6        # 管点（明显点）符号直径
H_NOTE = 2.5        # 管线注记字高
H_NODE_TAG = 2.0    # 管点编号字高
LEADER_BEND = (6.0, 6.0)


def draw_pipe(msp, pts: Sequence[Tuple[float, float]], scale: float = 50.0,
              code: str = "JS", dn: int = 300, material: str = "",
              depth: float | None = None,
              label: str | None = None,
              **params):
    """绘制一条探测管线（折线），逐段复用 envcad 管道函数。

    标注格式（探测成果常用）："JS DN300 PE 1.20"，即
    管线代码 + 管径 + 材质 + 管顶（或中心）埋深 m。
    """
    ensure_doc_ready(msp)
    name_cn, layer, engine, sub = PIPE_KINDS.get(code, PIPE_KINDS["JS"])
    if label is None:
        parts = [code, f"DN{dn}" if dn else "", material,
                 f"{depth:.2f}" if depth is not None else ""]
        label = " ".join(p for p in parts if p)
    pts = list(pts)
    for i in range(len(pts) - 1):
        seg_label = label if i == (len(pts) - 1) // 2 else ""
        if engine == "plumbing":
            draw_plumbing_pipe(msp, pts[i], pts[i + 1], pipe_type=sub,
                               dn=dn, scale=scale, label=seg_label)
        else:
            draw_process_line(msp, pts[i], pts[i + 1], line_type=sub,
                              scale=scale, label=seg_label, layer=layer)
    return pts[-1]


def draw_pipe_node(msp, x: float, y: float, scale: float = 50.0,
                   node_type: str = "井",
                   tag: str = "",
                   depth: float | None = None,
                   dia: float = D_NODE,
                   tag_h: float = H_NODE_TAG,
                   layer: str = "管点",
                   **params):
    """管点符号（探测明显点/隐蔽点）。

    node_type: "井" 检修井（圆，复用 pid.draw_instrument 现场安装圆符号）/
               "阀" 阀门 / "变径" 变径点 / "转折" 转折点 / "探测" 隐蔽点。
    """
    ensure_doc_ready(msp)
    s = scale
    r = dia * s / 2
    if node_type == "井":
        # 复用 pid 现场仪表圆符号：其半径固定为 6.0*scale，故换算传入比例
        # 使成图直径等于 dia（图上 mm）。位号另行按 tag_h 注记，保证可读。
        draw_instrument(msp, (x, y), tag="", mounting="field",
                        scale=dia * s / 12.0, layer=layer)
    elif node_type == "阀":
        polyline(msp, [(x - r, y - r), (x + r, y + r)], layer)
        polyline(msp, [(x - r, y + r), (x + r, y - r)], layer)
        line(msp, (x - r, y - r), (x - r, y + r), layer)
        line(msp, (x + r, y - r), (x + r, y + r), layer)
    elif node_type == "变径":
        polyline(msp, [(x - r, y - r), (x + r, y - r * 0.4),
                       (x + r, y + r * 0.4), (x - r, y + r)], layer, close=True)
    elif node_type == "转折":
        circle(msp, (x, y), r * 0.5, layer)
    else:  # 探测隐蔽点：实心小圆
        solid_fill(msp, [(x + r * 0.5 * c, y + r * 0.5 * sn) for c, sn in
                         _unit_circle(10)], layer)
    if tag:
        text(msp, tag, (x + r * 1.4, y + r), tag_h * s,
             align=TextEntityAlignment.MIDDLE_LEFT, layer="控制点注记")
    if depth is not None:
        draw_leader(msp, (x, y), f"埋深 {depth:.2f}m", scale=s,
                    bend=LEADER_BEND)
    return (x, y)


def _unit_circle(n: int):
    import math
    return [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
            for i in range(n)]


def draw_pipe_detection(msp, x: float, y: float, scale: float = 50.0,
                        pipes: Sequence[dict] | None = None,
                        nodes: Sequence[dict] | None = None,
                        show_legend: bool = True,
                        legend_dx: float = 0.0,
                        legend_dy: float = 0.0,
                        legend_row_h: float = 8.0,
                        legend_w: float = 40.0,
                        note_h: float = H_NOTE,
                        **params):
    """地下管线探测成果图总装。

    pipes: [{"pts":[(dx,dy)...], "code":"JS", "dn":300,
             "material":"PE", "depth":1.20}]  dx/dy 相对 (x,y) 的实物偏移。
    nodes: [{"dx","dy","type","tag","depth"}]
    show_legend: 绘制管线代码图例（图上 mm 尺寸参数化）。
    返回已绘管线条数与管点数 (n_pipe, n_node)。
    """
    ensure_doc_ready(msp)
    pipes = list(pipes or [])
    nodes = list(nodes or [])

    for p in pipes:
        pts = [(x + dx, y + dy) for dx, dy in p.get("pts", [])]
        if len(pts) < 2:
            continue
        draw_pipe(msp, pts, scale=scale, code=p.get("code", "JS"),
                  dn=p.get("dn", 300), material=p.get("material", ""),
                  depth=p.get("depth"), label=p.get("label"))

    for n in nodes:
        draw_pipe_node(msp, x + n.get("dx", 0.0), y + n.get("dy", 0.0),
                       scale=scale, node_type=n.get("type", "井"),
                       tag=n.get("tag", ""), depth=n.get("depth"))

    if show_legend:
        codes = []
        for p in pipes:
            c = p.get("code", "JS")
            if c not in codes:
                codes.append(c)
        lx = x + legend_dx
        ly = y + legend_dy
        text(msp, "管线图例", (lx, ly + legend_row_h * scale), note_h * scale * 1.2,
             align=TextEntityAlignment.MIDDLE_LEFT, layer="文字-标题")
        for i, c in enumerate(codes):
            cy = ly - i * legend_row_h * scale
            name_cn, layer, engine, sub = PIPE_KINDS[c]
            line(msp, (lx, cy), (lx + legend_w * scale * 0.4, cy), layer)
            text(msp, f"{c} {name_cn}管线",
                 (lx + legend_w * scale * 0.5, cy), note_h * scale,
                 align=TextEntityAlignment.MIDDLE_LEFT, layer="图例")

    return (len(pipes), len(nodes))
