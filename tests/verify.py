"""五个测试的自动化校验：核对每张 DXF 的关键标注/内容是否齐全。"""
from __future__ import annotations

import os
import sys

import ezdxf


def texts(path):
    d = ezdxf.readfile(path)
    m = d.modelspace()
    return [t.dxf.text for t in m.query("TEXT")], d, m


def has(all_text, kw):
    return any(kw in t for t in all_text)


def check(name, path, kws):
    if not os.path.exists(path):
        print(f"[FAIL] {name}: 文件不存在 {path}")
        return False
    try:
        ts, d, m = texts(path)
    except Exception as e:
        print(f"[FAIL] {name}: 读取失败 {e}")
        return False
    n_line = len(list(m.query("LINE")))
    n_poly = len(list(m.query("LWPOLYLINE")))
    n_txt = len(ts)
    ok = True
    miss = []
    for kw in kws:
        if not has(ts, kw):
            miss.append(kw)
            ok = False
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: 文字{n_txt} 线{n_line} 多段线{n_poly}"
          + (f"  缺失:{miss}" if miss else ""))
    return ok


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "output"
    )
    all_ok = True
    # T1
    all_ok &= check("T1 污水管道标注", os.path.join(out, "T1_污水管道标注图.dxf"),
                    ["DN300", "1.200", "1.176", "0.4%", "水流方向", "技术要求"])
    # T2
    all_ok &= check("T2 竖流斜管沉淀池", os.path.join(out, "T2_竖流斜管沉淀池平剖面图.dxf"),
                    ["沉淀池", "5.5", "1.5", "1.2", "DN300", "DN150",
                     "出水堰", "安装技术要求"])
    # T3
    all_ok &= check("T3 污水自流管网", os.path.join(out, "T3_污水自流管网平面布置图.dxf"),
                    ["DN350", "0.3%", "闸阀", "软接头", "流量计", "防水套管",
                     "水流方向", "图  例"])
    # T4
    for no, title, kws in [
        ("01", "总平面布置图", ["总平面", "格栅", "调节池", "接触氧化池", "沉淀池", "消毒池", "提升泵"]),
        ("02", "调节池平剖面图", ["调节池", "C30", "防腐", "GB 50141"]),
        ("03", "接触氧化池平剖面图", ["接触氧化池", "填料", "曝气"]),
        ("04", "斜管沉淀池平剖面图", ["斜管沉淀池", "斜管", "DN150"]),
        ("05", "工艺管道平面图", ["工艺管道", "闸阀", "流量计", "水流方向"]),
        ("06", "设备材料表", ["设备材料表", "提升泵", "曝气器", "HDPE"]),
    ]:
        f = [f for f in os.listdir(out) if f.startswith(f"T4-{no}")]
        if not f:
            print(f"[FAIL] T4-{no} {title}: 文件不存在")
            all_ok = False
            continue
        all_ok &= check(f"T4-{no} {title}", os.path.join(out, f[0]), kws)
    # T5
    all_ok &= check("T5a 第一步 8x5", os.path.join(out, "T5a_调节池_第一步_8x5x4.dxf"),
                    ["8×5", "-0.500", "C30", "土建施工技术要求"])
    all_ok &= check("T5b 第二步 8x6 防腐", os.path.join(out, "T5b_调节池_第二步_8x6x4_防腐.dxf"),
                    ["8×6", "-0.800", "环氧树脂玻璃钢", "两布三油"])
    # T6
    all_ok &= check("T6 污水自流管网平面布置图", os.path.join(out, "T6_污水自流管网平面布置图.dxf"),
                    ["DN300", "DN200", "HFC-01", "HFC-02", "HFC-03",
                     "GS-01", "TJC-01", "检查井", "格栅井", "化粪池", "调节池",
                     "HDPE", "水流方向", "管底标高", "图  例",
                     "施工技术要求", "水力校验", "GB 50268"])

    print("\n==== 总结 ====")
    print("全部通过" if all_ok else "存在未通过项")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
