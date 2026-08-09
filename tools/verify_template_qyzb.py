# -*- coding: utf-8 -*-
"""复核 QYZB-STD-V1.0.dxf 是否符合企业制图标准 V1.0 全部要求。"""
from __future__ import annotations

import os
import sys

import ezdxf
from ezdxf import colors

PATH = os.path.join(os.path.expanduser("~"), "Desktop",
                    "envcad-output", "QYZB-STD-V1.0.dxf")

# 期望值
EXPECT_LAYERS = [
    ("粗实线", "#003366", "CONTINUOUS", 50),
    ("细实线", "#1a5276", "CONTINUOUS", 25),
    ("虚线",   "#2980b9", "DASHED",     25),
    ("中心线", "#5dade2", "CENTER",     25),
    ("标注",   "#1b4f72", "CONTINUOUS", 25),
    ("文字",   "#0e2f44", "CONTINUOUS", 25),
    ("标题栏", "#001f3f", "CONTINUOUS", 50),
]


def hex2rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb2hex(rgb):
    return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])


results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" -- {detail}" if detail and not ok else ""))


def main():
    if not os.path.exists(PATH):
        print(f"[FAIL] 文件不存在: {PATH}")
        return 1
    doc = ezdxf.readfile(PATH)
    msp = doc.modelspace()

    # 1) 图层
    print("\n── 图层 ──")
    for nm, hexc, lt, lw in EXPECT_LAYERS:
        if nm not in doc.layers:
            check(f"图层 {nm}", False, "缺失")
            continue
        ly = doc.layers.get(nm)
        # true color (rgb property)
        rgb = ly.rgb
        hex_got = rgb2hex(rgb).lower() if rgb else None
        check(f"{nm} 颜色={hexc}", hex_got == hexc.lower(),
              f"实际 {hex_got}")
        check(f"{nm} 线型={lt}", ly.dxf.linetype == lt,
              f"实际 {ly.dxf.linetype}")
        check(f"{nm} 线宽={lw}", ly.dxf.lineweight == lw,
              f"实际 {ly.dxf.lineweight}")

    # 2) 文字样式
    print("\n── 文字样式 ──")
    sty_name = "QY-SONG-35"
    if sty_name not in doc.styles:
        check(f"文字样式 {sty_name}", False, "缺失")
    else:
        st = doc.styles.get(sty_name)
        check(f"{sty_name} 字体=simsun.ttf",
              (st.dxf.font or "").lower() == "simsun.ttf", f"实际 {st.dxf.font}")
        check(f"{sty_name} 大字体=gbcbig.shx",
              (st.dxf.bigfont or "").lower() == "gbcbig.shx", f"实际 {st.dxf.bigfont}")
        check(f"{sty_name} 字高=3.5",
              abs(st.dxf.height - 3.5) < 1e-6, f"实际 {st.dxf.height}")
        check(f"{sty_name} 宽度=0.7",
              abs(st.dxf.width - 0.7) < 1e-6, f"实际 {st.dxf.width}")
        check(f"{sty_name} 倾斜=0",
              abs(st.dxf.oblique) < 1e-6, f"实际 {st.dxf.oblique}")

    # 3) 标注样式
    print("\n── 标注样式 ──")
    dim_name = "QY-DIM-STD"
    if dim_name not in doc.dimstyles:
        check(f"标注样式 {dim_name}", False, "缺失")
    else:
        dim = doc.dimstyles.get(dim_name)
        checks = [
            ("dimtxsty=QY-SONG-35", dim.dxf.dimtxsty, "QY-SONG-35"),
            ("dimblk 实心闭合",      dim.dxf.dimblk,   "_CLOSEDFILLED"),
            ("dimasz 箭头=3.5",      dim.dxf.dimasz,   3.5),
            ("dimdle 超出标记=0",     dim.dxf.dimdle,   0.0),
            ("dimdli 基线间距=7",     dim.dxf.dimdli,   7.0),
            ("dimexe 界线超出=2",     dim.dxf.dimexe,   2.0),
            ("dimexo 起点偏移=1",     dim.dxf.dimexo,   1.0),
            ("dimdec 整数精度=0",     dim.dxf.dimdec,   0),
            ("dimtih 界内对齐=0",     dim.dxf.dimtih,   0),
            ("dimtoh 界外水平=1",     dim.dxf.dimtoh,   1),
        ]
        for desc, got, exp in checks:
            ok = got == exp
            if isinstance(exp, float):
                ok = abs(got - exp) < 1e-6
            check(f"{dim_name} {desc}", ok, f"实际 {got}")
        # 箭头块存在
        check("箭头块 _CLOSEDFILLED",
              "_CLOSEDFILLED" in doc.blocks, "缺失")

    # 4) 头变量
    print("\n── 头变量 / 当前样式 ──")
    h = doc.header
    check("MEASUREMENT 公制", h.get("$MEASUREMENT") == 1, f"实际 {h.get('$MEASUREMENT')}")
    check("INSUNITS 毫米",    h.get("$INSUNITS") == 4,    f"实际 {h.get('$INSUNITS')}")
    check("CLAYER=细实线",    h.get("$CLAYER") == "细实线", f"实际 {h.get('$CLAYER')}")
    check("TEXTSTYLE=QY-SONG-35", h.get("$TEXTSTYLE") == "QY-SONG-35",
          f"实际 {h.get('$TEXTSTYLE')}")
    check("DIMSTYLE=QY-DIM-STD",   h.get("$DIMSTYLE") == "QY-DIM-STD",
          f"实际 {h.get('$DIMSTYLE')}")

    # 5) 几何：A3 图框 + 异形标题栏
    print("\n── 几何 ──")
    polys = list(msp.query("LWPOLYLINE"))
    lines = list(msp.query("LINE"))
    # A3 外幅 420x297
    a3_outer = [p for p in polys if len(p) >= 4 and
                abs(max(pt[0] for pt in p) - 420) < 0.1 and
                abs(max(pt[1] for pt in p) - 297) < 0.1]
    check("A3 图幅 420x297", len(a3_outer) >= 1, "未找到")
    # 内框 25..415, 5..292
    a3_inner = [p for p in polys if
                abs(min(pt[0] for pt in p) - 25) < 0.1 and
                abs(max(pt[0] for pt in p) - 415) < 0.1 and
                abs(min(pt[1] for pt in p) - 5) < 0.1 and
                abs(max(pt[1] for pt in p) - 292) < 0.1]
    check("A3 内框 25,5-415,292", len(a3_inner) >= 1, "未找到")
    # 标题栏异形外框（5顶点，含切角）
    tb = [p for p in polys if
          abs(min(pt[0] for pt in p) - 235) < 0.1 and
          abs(max(pt[0] for pt in p) - 415) < 0.1 and
          abs(min(pt[1] for pt in p) - 5) < 0.1 and
          abs(max(pt[1] for pt in p) - 61) < 0.1 and
          len(p) == 5]
    check("标题栏 180x56 异形(5顶点)", len(tb) >= 1, "未找到")
    # 标题栏文字
    texts = [t.dxf.text for t in msp.query("TEXT")]
    need = ["设计", "校对", "审核", "批准", "标记", "处数", "更改文件号",
            "签名", "年、月、日", "材料标记", "比例", "图样代号"]
    miss = [k for k in need if not any(k in t for t in texts)]
    check("标题栏标签齐全", len(miss) == 0, f"缺失 {miss}")

    # 6) audit
    print("\n── 审计 ──")
    aud = doc.audit()
    check("ezdxf audit 无错误", len(aud.errors) == 0,
          f"{len(aud.errors)} 错误")

    # 总结
    n_pass = sum(1 for _, ok, _ in results if ok)
    n_fail = len(results) - n_pass
    print("\n" + "=" * 60)
    print(f"总计 {len(results)} 项：PASS {n_pass} / FAIL {n_fail}")
    print("=" * 60)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
