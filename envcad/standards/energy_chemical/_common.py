"""能源化工模块公共复用层。

设计原则
--------
1. **不重造框架**：图框 / 图层 / 文字样式 / 标注全部复用 envcad.standards.*，
   本文件只做「薄封装 + 化工专用几何件」。
2. **坐标约定**：modelspace 使用 *实物 mm*。图框按出图比例放大
   （A3 = 420x297 x scale），与 envcad.standards.frame 的约定完全一致。
   因此设备参数一律填 **真实尺寸 mm**（如 DN2000 筒体 diameter=2000）。
3. **图纸尺寸约定**：字高、法兰厚度等「与比例无关的制图要素」以
   *图纸 mm* 给出，内部乘以 scale 转换到模型空间，用 :func:`P` 完成。

依据标准
--------
* GB/T 14689—2008 图纸幅面和格式（经 envcad.standards.frame 实现）
* GB/T 17450—1998 技术制图 图线（经 envcad.standards.layers 实现）
* GB/T 50001—2017 制图统一标准 字体（仿宋 GB2312，经 envcad.standards.styles 实现）
* GB/T 25198—2023 压力容器封头（标准椭圆封头长短轴比 2:1）
"""
from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence, Tuple

from ezdxf.enums import TextEntityAlignment

# —— 复用 envcad 已验证组件 ——
from envcad.standards import frame as _frame
from envcad.standards.dim import draw_dimension as _draw_dimension

# ══════════════════════════════════════════════════════════
#  图层常量（全部取自 envcad.standards.layers.LAYER_DEFS，不新增图层）
# ══════════════════════════════════════════════════════════

L_THICK = "粗实线"        # 主轮廓：筒体、封头、设备外形
L_MID = "中实线"          # 次轮廓：法兰、塔板、折流板
L_THIN = "细实线"         # 辅助：填料、螺栓、剖面边界
L_DIM = "细实线-尺寸"     # 尺寸线
L_AUX = "细实线-辅助"     # 辅助构造线
L_DASH = "虚线"           # 不可见轮廓：夹套内壁、隐藏管束
L_CENTER = "点画线"       # 中心线 / 对称线
L_PHANTOM = "双点画线"    # 假想线：检修空间、极限位置
L_HATCH = "剖面线"        # 剖面填充
L_TEXT = "文字"
L_TITLE = "文字-标题"
L_EQUIP = "设备"
L_VALVE = "阀门"
L_ELEV = "标高"
L_PIPE_W = "管道-给水"
L_PIPE_S = "管道-污水"
L_FLOW = "流向"

#: 标准椭圆封头长短轴比（GB/T 25198）——曲面深度 h = D/4
ELLIPSOIDAL_HEAD_RATIO = 0.5


# ══════════════════════════════════════════════════════════
#  基础换算与文字
# ══════════════════════════════════════════════════════════

def P(value: float, scale: float) -> float:
    """图纸 mm -> 模型空间实物 mm。

    出图比例 1:scale 时，图纸上 1mm 对应模型空间 scale mm。
    """
    return value * scale


def text(msp, content: str, point: Tuple[float, float],
         height: float = 3.5, scale: float = 50.0,
         layer: str = L_TEXT, style: str = "HZ",
         align=TextEntityAlignment.MIDDLE_CENTER, rotation: float = 0.0):
    """写入单行文字。

    height 为 *图纸 mm* 字高，GB/T 50001—2017 规定汉字不小于 3.5mm。
    汉字用 ``HZ`` 样式（仿宋 GB2312 / simfang.ttf），
    字母数字用 ``ENG`` 样式（simplex.shx）——两者均由
    ``envcad.standards.styles.setup_text_styles`` 建立。
    """
    if not content:
        return None
    t = msp.add_text(str(content), dxfattribs={
        "layer": layer, "height": P(height, scale), "style": style,
        "rotation": rotation,
    })
    t.set_placement(point, align=align)
    return t


def eng_text(msp, content, point, height=2.5, scale=50.0,
             layer=L_TEXT, align=TextEntityAlignment.MIDDLE_CENTER):
    """写入拉丁字母/数字文字（位号、DN 规格等），使用 ENG 样式。"""
    return text(msp, content, point, height, scale, layer, "ENG", align)


# ══════════════════════════════════════════════════════════
#  图框（薄封装 —— envcad 中真实函数名为 frame.draw_frame）
# ══════════════════════════════════════════════════════════

def add_a3_frame(doc, scale: float = 50.0, title: str = "未命名图纸",
                 drawing_no: str = "EC-00", project: str = "能源化工工程",
                 designer: str = "", checker: str = "", auditor: str = "",
                 unit: str = "设计单位", date: str = "2026.07",
                 tracker=None) -> Tuple[float, float, float, float]:
    """绘制 A3 横式图框 + 标题栏，返回内框范围 ``(x0, y0, x1, y1)``。

    这是对 :func:`envcad.standards.frame.draw_frame` 的薄封装
    （envcad 中并不存在 ``add_a3_frame`` 这一名字，此处提供该别名以便调用）。

    依据标准：GB/T 14689—2008 图纸幅面；GB/T 50001—2017 标题栏。
    """
    info = _frame.FrameInfo(
        title=title, drawing_no=drawing_no,
        scale_str=f"1:{int(scale)}", designer=designer, checker=checker,
        auditor=auditor, project=project, unit=unit, date=date,
    )
    return _frame.draw_frame(doc, scale, info, tracker=tracker)


def frame_center(extents: Tuple[float, float, float, float]
                 ) -> Tuple[float, float]:
    """返回图框内框中心点，便于把设备摆到图面正中。"""
    x0, y0, x1, y1 = extents
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


# ══════════════════════════════════════════════════════════
#  通用图线辅助
# ══════════════════════════════════════════════════════════

def centerline(msp, p1: Tuple[float, float], p2: Tuple[float, float],
               extend: float = 0.0):
    """中心线 / 对称轴（点画线，GB/T 17450）。extend 为两端伸出量（实物 mm）。"""
    (x1, y1), (x2, y2) = p1, p2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L > 1e-9 and extend:
        ux, uy = dx / L, dy / L
        x1 -= ux * extend
        y1 -= uy * extend
        x2 += ux * extend
        y2 += uy * extend
    return msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": L_CENTER})


def rect(msp, x0: float, y0: float, x1: float, y1: float,
         layer: str = L_THICK, closed: bool = True):
    """轴对齐矩形。"""
    return msp.add_lwpolyline(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        close=closed, dxfattribs={"layer": layer})


def hatch_area(msp, points: Sequence[Tuple[float, float]],
               pattern: str = "ANSI31", scale: float = 50.0,
               pattern_scale: float = 1.0, layer: str = L_HATCH):
    """剖面填充。失败时静默跳过（保证 DXF 仍可生成）。

    依据 GB/T 17453—2005《技术制图 图样画法 剖面区域的表示法》：
    金属材料剖面线为 45 度细实线。
    """
    try:
        h = msp.add_hatch(dxfattribs={"layer": layer})
        h.paths.add_polyline_path(list(points), is_closed=True)
        h.set_pattern_fill(pattern, scale=P(2.0, scale) * pattern_scale,
                           angle=45.0)
        return h
    except Exception as _e:
        return None


def solid_tri(msp, pts: Sequence[Tuple[float, float]], layer: str = L_THICK):
    """实心三角（箭头/标高符号），失败回退为闭合多段线。"""
    pts = list(pts)
    try:
        return msp.add_solid(pts + [pts[0]], dxfattribs={"layer": layer})
    except Exception as _e:
        return msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def arrow(msp, tip: Tuple[float, float], direction: Tuple[float, float],
          scale: float = 50.0, size: float = 3.0, layer: str = L_FLOW):
    """实心箭头，size 为 *图纸 mm* 箭头长度（GB/T 4458.4 推荐 2.5~4mm）。"""
    tx, ty = tip
    dx, dy = direction
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    h = P(size, scale)
    w = h / 3.0
    base = (tx - ux * h, ty - uy * h)
    px, py = -uy * w, ux * w
    solid_tri(msp, [tip, (base[0] + px, base[1] + py),
                    (base[0] - px, base[1] - py)], layer=layer)


# ══════════════════════════════════════════════════════════
#  标注（复用 envcad.standards.dim.draw_dimension）
# ══════════════════════════════════════════════════════════

def dim_linear(msp, p1, p2, offset: float = 12.0, scale: float = 50.0,
               label: str = "", dimstyle: str = "Standard"):
    """线性尺寸标注。offset 为 *图纸 mm* 偏移，label 为空则自动取实测值。

    直接复用 :func:`envcad.standards.dim.draw_dimension`，
    尺寸线落在 envcad 已定义的「细实线-尺寸」图层。
    """
    return _draw_dimension(msp, p1, p2, offset=offset, scale=scale,
                           dimstyle=dimstyle, text=label, layer=L_DIM)


def leader_note(msp, target: Tuple[float, float], content: str,
                scale: float = 50.0, dx: float = 18.0, dy: float = 12.0,
                height: float = 3.0, layer_text: str = L_TEXT):
    """折线引出标注（GB/T 4458.2）：圆点起始 + 斜线 + 水平线 + 文字。

    dx/dy 为 *图纸 mm* 偏移量，正负决定引出方向。
    """
    tx, ty = target
    bx, by = tx + P(dx, scale), ty + P(dy, scale)
    ex = bx + P(8.0 if dx >= 0 else -8.0, scale)
    msp.add_line((tx, ty), (bx, by), dxfattribs={"layer": L_DIM})
    msp.add_line((bx, by), (ex, by), dxfattribs={"layer": L_DIM})
    msp.add_circle((tx, ty), P(0.6, scale), dxfattribs={"layer": L_DIM})
    align = (TextEntityAlignment.MIDDLE_LEFT if dx >= 0
             else TextEntityAlignment.MIDDLE_RIGHT)
    off = P(1.5 if dx >= 0 else -1.5, scale)
    text(msp, content, (ex + off, by + P(1.6, scale)), height, scale,
         layer=layer_text, align=align)
    return (ex, by)


def elevation_mark(msp, point: Tuple[float, float], value: str,
                   scale: float = 50.0, height: float = 3.0):
    """标高符号（GB/T 50001—2017 §7.4：等腰直角三角形，高约 3mm）。"""
    px, py = point
    h = P(height, scale)
    msp.add_lwpolyline([(px, py), (px - h, py + h), (px + h, py + h)],
                       close=True, dxfattribs={"layer": L_ELEV})
    msp.add_line((px - h, py + h), (px + P(14, scale), py + h),
                 dxfattribs={"layer": L_ELEV})
    eng_text(msp, value, (px + P(2.0, scale), py + h + P(1.6, scale)),
             2.5, scale, layer=L_ELEV, align=TextEntityAlignment.MIDDLE_LEFT)


def note_block(msp, origin: Tuple[float, float], lines: Iterable[str],
               scale: float = 50.0, title: str = "技术要求",
               height: float = 3.0, line_gap: float = 1.8):
    """技术要求文字块（左对齐，自上而下）。返回块底部 y 坐标。"""
    ox, oy = origin
    if title:
        text(msp, title, (ox, oy), height + 0.5, scale, layer=L_TITLE,
             align=TextEntityAlignment.MIDDLE_LEFT)
        oy -= P(height * line_gap, scale)
    for ln in lines:
        text(msp, ln, (ox, oy), height, scale, layer=L_TEXT,
             align=TextEntityAlignment.MIDDLE_LEFT)
        oy -= P(height * line_gap, scale)
    return oy


def spec_table(msp, origin: Tuple[float, float], rows: Sequence[Sequence[str]],
               scale: float = 50.0, col_w: Sequence[float] = (30.0, 34.0),
               row_h: float = 7.0, title: str = "", height: float = 2.6):
    """设备数据表（左上角定位，向右下展开）。col_w/row_h 单位为图纸 mm。"""
    ox, oy = origin
    widths = [P(w, scale) for w in col_w]
    total_w = sum(widths)
    rh = P(row_h, scale)
    cur_y = oy
    if title:
        rect(msp, ox, cur_y - rh, ox + total_w, cur_y, layer=L_MID)
        text(msp, title, (ox + total_w / 2, cur_y - rh / 2), height + 0.6,
             scale, layer=L_TITLE)
        cur_y -= rh
    for row in rows:
        cx = ox
        for i, cell in enumerate(row[:len(widths)]):
            w = widths[i]
            rect(msp, cx, cur_y - rh, cx + w, cur_y, layer=L_THIN)
            style = "HZ" if i == 0 else "ENG"
            text(msp, cell, (cx + w / 2, cur_y - rh / 2), height, scale,
                 layer=L_TEXT, style=style)
            cx += w
        cur_y -= rh
    rect(msp, ox, cur_y, ox + total_w, oy, layer=L_MID)
    return (ox + total_w, cur_y)


# ══════════════════════════════════════════════════════════
#  化工专用几何件（跨模块复用）
# ══════════════════════════════════════════════════════════

def ellipsoidal_head(msp, cx: float, cy: float, D: float,
                     direction: str = "up", straight: float = 0.0,
                     layer: str = L_THICK):
    """标准椭圆封头（GB/T 25198—2023，长短轴比 2:1，曲面深度 h = D/4）。

    参数
    ----
    cx, cy : 封头与筒体的连接截面中心（直边段起点）
    D      : 筒体内直径 mm
    direction : ``up`` / ``down`` / ``left`` / ``right`` 封头凸出方向
    straight  : 直边段高度 mm（GB/T 25198 按壁厚取 25/40/50mm）

    返回封头最外端点坐标。
    """
    R = D / 2.0
    # 直边段
    if direction in ("up", "down"):
        sgn = 1.0 if direction == "up" else -1.0
        jy = cy + sgn * straight
        if straight:
            msp.add_line((cx - R, cy), (cx - R, jy), dxfattribs={"layer": layer})
            msp.add_line((cx + R, cy), (cx + R, jy), dxfattribs={"layer": layer})
        msp.add_ellipse((cx, jy), major_axis=(R, 0),
                        ratio=ELLIPSOIDAL_HEAD_RATIO,
                        start_param=0 if direction == "up" else math.pi,
                        end_param=math.pi if direction == "up" else 2 * math.pi,
                        dxfattribs={"layer": layer})
        return (cx, jy + sgn * R * ELLIPSOIDAL_HEAD_RATIO)
    else:
        sgn = 1.0 if direction == "right" else -1.0
        jx = cx + sgn * straight
        if straight:
            msp.add_line((cx, cy - R), (jx, cy - R), dxfattribs={"layer": layer})
            msp.add_line((cx, cy + R), (jx, cy + R), dxfattribs={"layer": layer})
        msp.add_ellipse((jx, cy), major_axis=(0, R),
                        ratio=ELLIPSOIDAL_HEAD_RATIO,
                        start_param=math.pi if direction == "right" else 0,
                        end_param=2 * math.pi if direction == "right" else math.pi,
                        dxfattribs={"layer": layer})
        return (jx + sgn * R * ELLIPSOIDAL_HEAD_RATIO, cy)


def flat_head(msp, cx: float, cy: float, D: float, thickness: float,
              direction: str = "up", layer: str = L_THICK):
    """平盖封头（用于低压设备/人孔盖）。返回外端面中心。"""
    R = D / 2.0
    if direction in ("up", "down"):
        sgn = 1.0 if direction == "up" else -1.0
        rect(msp, cx - R, cy, cx + R, cy + sgn * thickness, layer=layer)
        return (cx, cy + sgn * thickness)
    sgn = 1.0 if direction == "right" else -1.0
    rect(msp, cx, cy - R, cx + sgn * thickness, cy + R, layer=layer)
    return (cx + sgn * thickness, cy)


_DIRS = {"up": (0.0, 1.0), "down": (0.0, -1.0),
         "left": (-1.0, 0.0), "right": (1.0, 0.0)}


def nozzle(msp, base: Tuple[float, float], direction: str, dn: float,
           length: float, scale: float = 50.0, tag: str = "",
           flange: bool = True, layer: str = L_THICK,
           tag_offset: float = 4.0):
    """接管 + 突面法兰（HG/T 20592—2009 PN 系列法兰简化画法）。

    参数
    ----
    base   : 接管根部（壳体外壁上的点）
    direction : ``up``/``down``/``left``/``right``
    dn     : 公称通径 mm（此处按外径近似绘制）
    length : 接管伸出长度 mm
    tag    : 管口号（如 ``a`` / ``N1``），标注在法兰外侧

    返回法兰端面中心坐标。
    """
    bx, by = base
    ux, uy = _DIRS.get(direction, (0.0, 1.0))
    # 垂直于轴线的单位向量
    px, py = -uy, ux
    r = dn / 2.0
    ex, ey = bx + ux * length, by + uy * length

    # 接管两条素线
    msp.add_line((bx + px * r, by + py * r), (ex + px * r, ey + py * r),
                 dxfattribs={"layer": layer})
    msp.add_line((bx - px * r, by - py * r), (ex - px * r, ey - py * r),
                 dxfattribs={"layer": layer})

    if flange:
        # 法兰盘：外径约 1.9*DN，厚度约 0.16*DN（简化，实际查 HG/T 20592 表）
        # TODO: verify against HG/T 20592—2009 法兰外径/厚度系列表
        fr = max(r * 1.9, r + dn * 0.25)
        ft = max(dn * 0.16, P(1.2, scale))
        f0 = (ex - ux * ft, ey - uy * ft)
        msp.add_lwpolyline([
            (f0[0] + px * fr, f0[1] + py * fr),
            (ex + px * fr, ey + py * fr),
            (ex - px * fr, ey - py * fr),
            (f0[0] - px * fr, f0[1] - py * fr),
        ], close=True, dxfattribs={"layer": L_MID})

    if tag:
        tx = ex + ux * P(tag_offset, scale) + px * P(tag_offset * 0.6, scale)
        ty = ey + uy * P(tag_offset, scale) + py * P(tag_offset * 0.6, scale)
        eng_text(msp, tag, (tx, ty), 2.8, scale, layer=L_TITLE)

    return (ex, ey)


def manhole(msp, base: Tuple[float, float], direction: str, dn: float = 500.0,
            length: float = 250.0, scale: float = 50.0, tag: str = "M",
            layer: str = L_THICK):
    """人孔（HG/T 21514—2014 钢制人孔，常用 DN450/DN500/DN600）。

    在接管基础上加盲板盖与铰链短线。
    """
    end = nozzle(msp, base, direction, dn, length, scale, tag="",
                 flange=True, layer=layer)
    ux, uy = _DIRS.get(direction, (0.0, 1.0))
    px, py = -uy, ux
    fr = dn * 0.95
    # 盖板
    c0 = end
    c1 = (end[0] + ux * dn * 0.16, end[1] + uy * dn * 0.16)
    msp.add_lwpolyline([
        (c0[0] + px * fr, c0[1] + py * fr),
        (c1[0] + px * fr, c1[1] + py * fr),
        (c1[0] - px * fr, c1[1] - py * fr),
        (c0[0] - px * fr, c0[1] - py * fr),
    ], close=True, dxfattribs={"layer": L_MID})
    if tag:
        tx = c1[0] + ux * P(5, scale)
        ty = c1[1] + uy * P(5, scale)
        eng_text(msp, tag, (tx, ty), 2.8, scale, layer=L_TITLE)
    return c1


def saddle_support(msp, cx: float, cy: float, R: float, height: float,
                   width: float = 0.0, scale: float = 50.0,
                   wrap_deg: float = 120.0, layer: str = L_THICK):
    """卧式容器鞍座（NB/T 47065.1—2018，标准包角 120 度）。

    参数
    ----
    cx, cy : 筒体截面中心
    R      : 筒体外半径 mm
    height : 鞍座高度（筒体底部到底板面）mm
    width  : 底板宽度 mm，默认取 1.8R
    wrap_deg : 包角，标准值 120 度（重型可用 150 度）

    # TODO: verify against NB/T 47065.1—2018 鞍座尺寸系列表（腹板厚、筋板数）
    """
    if width <= 0:
        width = R * 1.8
    half = math.radians(wrap_deg / 2.0)
    base_y = cy - R - height
    # 包角圆弧（底部对称）
    a0 = 270.0 - wrap_deg / 2.0
    a1 = 270.0 + wrap_deg / 2.0
    msp.add_arc((cx, cy), R, start_angle=a0, end_angle=a1,
                dxfattribs={"layer": layer})
    # 腹板两侧
    lx = cx - R * math.sin(half)
    rx = cx + R * math.sin(half)
    ly = cy - R * math.cos(half)
    msp.add_line((lx, ly), (cx - width / 2, base_y), dxfattribs={"layer": layer})
    msp.add_line((rx, ly), (cx + width / 2, base_y), dxfattribs={"layer": layer})
    # 底板
    tb = max(height * 0.12, R * 0.05)
    rect(msp, cx - width / 2, base_y, cx + width / 2, base_y + tb, layer=layer)
    # 加强筋（细实线）
    for f in (-0.5, 0.0, 0.5):
        fx = cx + width * 0.35 * f * 2
        top_y = cy - math.sqrt(max(R * R - min(abs(fx - cx), R) ** 2, 0.0))
        msp.add_line((fx, base_y + tb), (fx, top_y), dxfattribs={"layer": L_THIN})
    return base_y


def skirt_support(msp, cx: float, cy: float, D: float, height: float,
                  scale: float = 50.0, thickness: float = 0.0,
                  layer: str = L_THICK, n_holes: int = 4):
    """立式容器裙座（JB/T 4712.3—2007 圆筒形裙座）。

    cy 为筒体下封头与裙座连接处标高，height 为裙座高度 mm。
    返回基础环底面 y 坐标。

    # TODO: verify against JB/T 4712.3—2007 裙座壁厚与基础环尺寸系列
    """
    R = D / 2.0
    if thickness <= 0:
        thickness = max(D * 0.006, 8.0)
    base_y = cy - height
    for sgn in (-1, 1):
        x_out = cx + sgn * R
        x_in = cx + sgn * (R - thickness)
        msp.add_line((x_out, cy), (x_out, base_y), dxfattribs={"layer": layer})
        msp.add_line((x_in, cy), (x_in, base_y), dxfattribs={"layer": L_MID})
    # 基础环 + 盖板
    ring_w = R * 0.30
    ring_t = max(D * 0.012, 16.0)
    rect(msp, cx - R - ring_w, base_y, cx + R + ring_w, base_y + ring_t,
         layer=layer)
    # 地脚螺栓（细实线示意）
    for i in range(n_holes):
        frac = (i + 0.5) / n_holes
        bx = cx - R - ring_w * 0.5 + (2 * R + ring_w) * frac
        msp.add_line((bx, base_y - ring_t * 0.8), (bx, base_y + ring_t * 1.8),
                     dxfattribs={"layer": L_THIN})
    # 裙座人孔/排气孔
    msp.add_arc((cx - R, base_y + height * 0.35), max(D * 0.08, 60.0),
                start_angle=-90, end_angle=90, dxfattribs={"layer": L_THIN})
    return base_y - ring_t * 0.8


def lug_support(msp, cx: float, cy: float, R: float, scale: float = 50.0,
                lug_h: float = 0.0, layer: str = L_THICK):
    """耳式支座（JB/T 4712.3—2007 A 型），用于中小型立式容器。"""
    if lug_h <= 0:
        lug_h = R * 0.5
    w = R * 0.45
    for sgn in (-1, 1):
        x = cx + sgn * R
        msp.add_lwpolyline([
            (x, cy), (x + sgn * w, cy), (x + sgn * w, cy - lug_h * 0.25),
            (x, cy - lug_h),
        ], close=True, dxfattribs={"layer": layer})
    return cy - lug_h


def support_legs(msp, cx: float, cy: float, D: float, height: float,
                 n: int = 4, scale: float = 50.0, layer: str = L_THICK):
    """支腿（型钢支腿，正视图画 2 条），返回底板 y。"""
    R = D / 2.0
    base_y = cy - height
    t = max(D * 0.02, 30.0)
    for sgn in (-1, 1):
        x = cx + sgn * R * 0.78
        rect(msp, x - t / 2, base_y, x + t / 2, cy, layer=layer)
    rect(msp, cx - R, base_y - t * 0.6, cx + R, base_y, layer=layer)
    return base_y - t * 0.6


def level_gauge(msp, x: float, y_low: float, y_high: float, scale: float = 50.0,
                dn: float = 25.0, standoff: float = 0.0, tag: str = "LG"):
    """玻璃板液位计（HG 21592-1995）：上下两个引出管口 + 竖直表体。

    x 为壳体外壁 x 坐标，液位计装在其外侧 standoff 处。
    """
    if standoff <= 0:
        standoff = max(dn * 6, P(6, scale))
    gx = x + standoff
    for yy in (y_low, y_high):
        msp.add_line((x, yy), (gx, yy), dxfattribs={"layer": L_MID})
        msp.add_line((gx - dn * 0.6, yy - dn * 0.5),
                     (gx - dn * 0.6, yy + dn * 0.5),
                     dxfattribs={"layer": L_THIN})
    rect(msp, gx - dn * 0.7, y_low, gx + dn * 0.7, y_high, layer=L_MID)
    centerline(msp, (gx, y_low), (gx, y_high))
    if tag:
        eng_text(msp, tag, (gx + P(4, scale), (y_low + y_high) / 2),
                 2.5, scale, layer=L_TITLE,
                 align=TextEntityAlignment.MIDDLE_LEFT)
    return gx


def bolt_circle_note(msp, center, D: float, n: int, dia: float,
                     scale: float = 50.0):
    """螺栓孔布置引注（如 ``8-M20 均布``）。"""
    cx, cy = center
    leader_note(msp, (cx + D / 2 * 0.85, cy), f"{n}-M{int(dia)} 均布",
                scale=scale, dx=16, dy=10)


__all__ = [
    "P", "text", "eng_text", "add_a3_frame", "frame_center",
    "centerline", "rect", "hatch_area", "solid_tri", "arrow",
    "dim_linear", "leader_note", "elevation_mark", "note_block", "spec_table",
    "ellipsoidal_head", "flat_head", "nozzle", "manhole",
    "saddle_support", "skirt_support", "lug_support", "support_legs",
    "level_gauge", "bolt_circle_note",
    "L_THICK", "L_MID", "L_THIN", "L_DIM", "L_AUX", "L_DASH", "L_CENTER",
    "L_PHANTOM", "L_HATCH", "L_TEXT", "L_TITLE", "L_EQUIP", "L_VALVE",
    "L_ELEV", "L_FLOW",
]
