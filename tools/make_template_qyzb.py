# -*- coding: utf-8 -*-
"""生成企业级 CAD 制图标准模板 QYZB-STD-V1.0.dxf。

遵循 envcad 引擎约定（ezdxf R2018 + MM 单位 + GB/T 14689 图框）。
按企业《制图标准 V1.0》配置：
  * 7 个深蓝系分级图层（true color + 线型 + 线宽）
  * 文字样式 QY-SONG-35（宋体 SimSun + 大字体，字高3.5，宽0.7）
  * 标注样式 QY-DIM-STD（实心闭合箭头、整数精度、ISO 对齐）
  * A3(420x297) 图框 + 右下角 180x56 异形（右上切角）标题栏

用法:
    python make_template_qyzb.py
输出:
    <Desktop>/envcad-output/QYZB-STD-V1.0.dxf
"""
from __future__ import annotations

import os
import sys

import ezdxf
from ezdxf import units, colors
from ezdxf.enums import TextEntityAlignment

# ─── 输出路径 ────────────────────────────────────────────
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
OUT_DIR = os.path.join(DESKTOP, "envcad-output")
OUT_NAME = "QYZB-STD-V1.0.dxf"

# ─── 企业标准配置 ────────────────────────────────────────
# (图层名, 颜色#RRGGBB, ACI回退, 线型, 线宽1/100mm)
LAYERS = [
    ("粗实线", "#003366", 5, "CONTINUOUS", 50),   # 0.50mm 可见轮廓
    ("细实线", "#1a5276", 5, "CONTINUOUS", 25),   # 0.25mm 尺寸线/剖面线
    ("虚线",   "#2980b9", 4, "DASHED",     25),   # 0.25mm 不可见轮廓
    ("中心线", "#5dade2", 4, "CENTER",     25),   # 0.25mm 轴线/对称线
    ("标注",   "#1b4f72", 5, "CONTINUOUS", 25),   # 0.25mm 尺寸标注
    ("文字",   "#0e2f44", 5, "CONTINUOUS", 25),   # 0.25mm 技术要求/注释
    ("标题栏", "#001f3f", 5, "CONTINUOUS", 50),   # 0.50mm 标题栏框线
]

# 标注文字样式
TEXT_STYLE_NAME = "QY-SONG-35"
TEXT_FONT = "simsun.ttf"        # 宋体 SimSun
TEXT_BIGFONT = "gbcbig.shx"    # 启用大字体
TEXT_HEIGHT = 3.5              # 字高 mm（1:1）
TEXT_WIDTH = 0.7               # 宽度因子
TEXT_OBLIQUE = 0.0             # 倾斜角

# 标注样式
DIM_STYLE_NAME = "QY-DIM-STD"

# A3 横式幅面（GB/T 14689-2008）
A3_W, A3_H = 420.0, 297.0
MARGIN_L = 25.0    # 装订边
MARGIN_O = 5.0     # 其余边

# 标题栏尺寸（GB/T 10609.1）
TITLE_W, TITLE_H = 180.0, 56.0
TITLE_CORNER_CUT = 20.0  # 异形：右上角 45° 切角边长


def hex2rgb(h: str):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _safe_set(obj, key, val):
    try:
        obj.dxf.__setattr__(key, val)
        return True
    except Exception:
        return False


def _has_linetype(doc, name: str) -> bool:
    try:
        return doc.linetypes.has_entry(name)
    except Exception:
        return name in doc.linetypes


def _set_linetype(doc, name: str, pattern, desc: str):
    """确保线型存在并使用给定 metric 图案（acadiso 风格）。"""
    if _has_linetype(doc, name):
        try:
            doc.linetypes.discard(name)
        except Exception:
            try:
                del doc.linetypes[name]
            except Exception:
                return  # 已存在且无法删除，保留
    for attempt in (
        lambda: doc.linetypes.add(name, pattern=pattern, description=desc),
        lambda: doc.linetypes.add(name, pattern, description=desc),
        lambda: doc.linetypes.add(name, pattern),
    ):
        try:
            attempt()
            return
        except Exception:
            continue
    print(f"[WARN] 线型 {name} 创建失败")


def setup_layers(doc):
    """创建全部线型与图层（true color + 线宽 + 线型）。"""
    # 先建/覆盖 metric 线型
    _set_linetype(doc, "DASHED",  [12.7, -6.35],                       "Dashed __ __ __")
    _set_linetype(doc, "CENTER",  [31.75, -6.35, 6.35, -6.35],         "Center ____ . ____")
    _set_linetype(doc, "PHANTOM", [31.75, -6.35, 6.35, -6.35, 6.35, -6.35], "Phantom")

    for name, hexc, aci, lt, lw in LAYERS:
        if name in doc.layers:
            layer = doc.layers.get(name)
        else:
            layer = doc.layers.add(name)
        layer.dxf.color = aci
        if lt == "CONTINUOUS":
            layer.dxf.linetype = "CONTINUOUS"
        else:
            layer.dxf.linetype = lt if _has_linetype(doc, lt) else "CONTINUOUS"
        layer.dxf.lineweight = lw
        layer.dxf.plot = 1
        # true color（深蓝系分级配色）
        layer.rgb = hex2rgb(hexc)


def setup_text_style(doc):
    """创建标注文字样式 QY-SONG-35（宋体 + 大字体，3.5mm，宽0.7）。"""
    if TEXT_STYLE_NAME in doc.styles:
        st = doc.styles.get(TEXT_STYLE_NAME)
    else:
        st = doc.styles.add(TEXT_STYLE_NAME, font=TEXT_FONT)
    _safe_set(st, "font", TEXT_FONT)
    _safe_set(st, "bigfont", TEXT_BIGFONT)
    _safe_set(st, "height", TEXT_HEIGHT)
    _safe_set(st, "width", TEXT_WIDTH)
    _safe_set(st, "oblique", TEXT_OBLIQUE)
    # flags: 不置 vertical；大字体由 bigfont 字段非空启用


def _create_arrow_block(doc):
    """创建实心闭合箭头块 _CLOSEDFILLED（以(0,0)为尖端，向 -X 延伸 1 单位）。"""
    name = "_CLOSEDFILLED"
    if name in doc.blocks:
        return name
    blk = doc.blocks.new(name)
    # SOLID 三角形：尖端(0,0) -> (-1,-1/3) -> (-1,+1/3)
    blk.add_solid([(0.0, 0.0), (-1.0, -0.3333), (-1.0, 0.3333), (-1.0, 0.3333)])
    return name


def setup_dim_style(doc):
    """创建标注样式 QY-DIM-STD。"""
    _create_arrow_block(doc)
    if DIM_STYLE_NAME in doc.dimstyles:
        dim = doc.dimstyles.get(DIM_STYLE_NAME)
    else:
        dim = doc.dimstyles.add(DIM_STYLE_NAME)

    _safe_set(dim, "dimtxsty", TEXT_STYLE_NAME)   # 关联文字样式
    _safe_set(dim, "dimblk", "_CLOSEDFILLED")     # 实心闭合箭头
    _safe_set(dim, "dimblk1", "_CLOSEDFILLED")
    _safe_set(dim, "dimblk2", "_CLOSEDFILLED")
    _safe_set(dim, "dimtsz", 0.0)                  # 不用斜线标记
    _safe_set(dim, "dimasz", 3.5)                  # 箭头大小 3.5mm
    _safe_set(dim, "dimdle", 0.0)                  # 尺寸线超出标记 0
    _safe_set(dim, "dimdli", 7.0)                  # 基线间距 7mm
    _safe_set(dim, "dimexe", 2.0)                  # 界线超出尺寸线 2mm
    _safe_set(dim, "dimexo", 1.0)                  # 界线起点偏移 1mm
    _safe_set(dim, "dimdec", 0)                    # 精度：整数
    _safe_set(dim, "dimrnd", 0.0)
    _safe_set(dim, "dimtdec", 0)
    _safe_set(dim, "dimzin", 0)
    _safe_set(dim, "dimtih", 0)                    # 界内文字与尺寸线对齐
    _safe_set(dim, "dimtoh", 1)                    # 界外文字水平 -> ISO 标准
    _safe_set(dim, "dimtad", 1)                    # 文字置于尺寸线上方
    _safe_set(dim, "dimgap", 1.0)                  # 文字与尺寸线间隙
    _safe_set(dim, "dimclrt", 256)                 # 文字色 BYLAYER
    _safe_set(dim, "dimclrd", 256)                 # 尺寸线色 BYLAYER
    _safe_set(dim, "dimclre", 256)                 # 界线色 BYLAYER
    _safe_set(dim, "dimlwd", -2)                   # 尺寸线线宽 BYLAYER
    _safe_set(dim, "dimlwe", -2)                   # 界线线宽 BYLAYER
    _safe_set(dim, "dimtofl", 1)                   # 界线间画尺寸线
    _safe_set(dim, "dimsah", 0)                    # 两端同箭头


def _center_marks(msp, x0, y0, x1, y1):
    mid_w = (x0 + x1) / 2
    mid_h = (y0 + y1) / 2
    L = 5.0
    for cx, cy, dx, dy in [
        (mid_w, y1, L, L), (mid_w, y0, L, -L),
        (x0, mid_h, -L, L), (x1, mid_h, L, L),
    ]:
        msp.add_line((cx - dx / 2, cy), (cx + dx / 2, cy), dxfattribs={"layer": "细实线"})
        msp.add_line((cx, cy - dy / 2), (cx, cy + dy / 2), dxfattribs={"layer": "细实线"})


def _label(msp, txt, cx, cy):
    t = msp.add_text(txt, dxfattribs={
        "layer": "文字", "style": TEXT_STYLE_NAME, "height": TEXT_HEIGHT})
    t.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)


def _title_block(msp, rx, by):
    """右下角(rx,by)向左上展开 180x56 异形（右上切角）标题栏。"""
    lx = rx - TITLE_W
    ty = by + TITLE_H
    cut = TITLE_CORNER_CUT

    # 外框：异形多段线（右上角 45° 切角）
    pts = [
        (lx, by),        # 左下
        (rx, by),        # 右下
        (rx, ty - cut),  # 右侧上段
        (rx - cut, ty),  # 切角斜边
        (lx, ty),        # 左上
    ]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "标题栏"})

    THIN = {"layer": "细实线"}

    # 水平分格线
    for dy in (14.0, 28.0, 42.0):
        msp.add_line((lx, by + dy), (rx, by + dy), dxfattribs=THIN)

    # 底签名行（0..14）垂直线：设计|签|校对|签|审核|签|批准|签
    for dx in (15, 45, 60, 90, 105, 135, 150):
        msp.add_line((lx + dx, by), (lx + dx, by + 14), dxfattribs=THIN)

    # 标记行（14..28）垂直线：标记|处数|更改文件号|签名|年、月、日
    for dx in (20, 40, 80, 120):
        msp.add_line((lx + dx, by + 14), (lx + dx, by + 28), dxfattribs=THIN)

    # 中部行（28..42）垂直线：图名 | 材料 | 比例
    for dx in (110, 145):
        msp.add_line((lx + dx, by + 28), (lx + dx, by + 42), dxfattribs=THIN)

    # 顶部行（42..56）垂直线：单位名称 | 图样代号
    msp.add_line((lx + 110, by + 42), (lx + 110, ty), dxfattribs=THIN)

    # 文字标签
    for dx, lab in zip((0, 45, 90, 135), ("设计", "校对", "审核", "批准")):
        _label(msp, lab, lx + dx + 7.5, by + 7)
    for cx, lab in ((10, "标记"), (30, "处数"), (60, "更改文件号"),
                    (100, "签名"), (150, "年、月、日")):
        _label(msp, lab, lx + cx, by + 21)
    _label(msp, "（图样名称）", lx + 55, by + 35)
    _label(msp, "材料标记", lx + 127.5, by + 35)
    _label(msp, "比例", lx + 162.5, by + 35)
    _label(msp, "（单位名称）", lx + 55, by + 49)
    _label(msp, "图样代号", lx + 145, by + 49)


def draw_frame(doc):
    """绘制 A3 图框 + 对中标志 + 异形标题栏。"""
    msp = doc.modelspace()
    # 外图幅边界（细实线）
    msp.add_lwpolyline([(0, 0), (A3_W, 0), (A3_W, A3_H), (0, A3_H)],
                       close=True, dxfattribs={"layer": "细实线"})
    # 内框图框线（粗实线）
    x0, y0 = MARGIN_L, MARGIN_O
    x1, y1 = A3_W - MARGIN_O, A3_H - MARGIN_O
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": "粗实线"})
    _center_marks(msp, x0, y0, x1, y1)
    _title_block(msp, x1, y0)


def setup_header(doc):
    """设置单位、当前图层/文字/标注样式等头变量。"""
    h = doc.header
    h["$MEASUREMENT"] = 1            # 1=公制
    h["$INSUNITS"] = units.MM        # 毫米
    h["$LUNITS"] = 2                # 十进制
    h["$LUPREC"] = 0                 # 整数显示
    h["$AUNITS"] = 0                # 十进制度
    h["$AUPREC"] = 0
    h["$LTSCALE"] = 1.0
    h["$CELTSCALE"] = 1.0
    h["$DIMSCALE"] = 1.0
    h["$DIMZIN"] = 0
    h["$CLAYER"] = "细实线"
    h["$TEXTSTYLE"] = TEXT_STYLE_NAME
    h["$DIMSTYLE"] = DIM_STYLE_NAME
    h["$TEXTSIZE"] = TEXT_HEIGHT
    h["$ELEVATION"] = 0.0
    h["$INSBASE"] = (0.0, 0.0, 0.0)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, OUT_NAME)

    doc = ezdxf.new("R2018", setup=True)
    doc.units = units.MM

    setup_layers(doc)
    setup_text_style(doc)
    setup_dim_style(doc)
    setup_header(doc)
    draw_frame(doc)

    # 审计
    auditor = doc.audit()
    n_err = len(auditor.errors)
    n_fix = len(auditor.fixes)

    doc.saveas(out_path)

    print("=" * 60)
    print("企业级 CAD 制图标准模板生成完成")
    print("=" * 60)
    print(f"输出文件 : {out_path}")
    print(f"DXF 版本 : R2018 (AC1024)")
    print(f"单位     : 毫米 (MM)")
    print(f"图层     : {len(LAYERS)} 个（深蓝系分级）")
    print(f"文字样式 : {TEXT_STYLE_NAME}（{TEXT_FONT} + {TEXT_BIGFONT}）")
    print(f"标注样式 : {DIM_STYLE_NAME}")
    print(f"图框     : A3 横式 {A3_W:.0f}x{A3_H:.0f}mm（GB/T 14689）")
    print(f"标题栏   : {TITLE_W:.0f}x{TITLE_H:.0f}mm 异形（右上切角{TITLE_CORNER_CUT:.0f}mm）")
    print(f"审计     : 错误 {n_err}，修复 {n_fix}")
    print("-" * 60)
    print("下一步：在 AutoCAD/ZWCAD 中打开该 DXF，")
    print("        执行 SAVEAS -> *.dwt 保存为模板文件 QYZB-STD-V1.0.dwt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
