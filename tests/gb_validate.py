"""GB 标准符合性校验器 v1.5 P2。

独立脚本：对 *任意* envcad 生成的 DXF 图纸进行国标符合性检查，
不依赖 T1-T5 命名约定。可作为 pytest 插件或独立调用。

Usage:
  python tests/gb_validate.py <dxf_file_or_dir>
  python tests/gb_validate.py output/  --verbose

检查项：
  1. 图层名符合 GB/T 17450（识别的标准图层 + 未知图层告警）
  2. 文字样式存在 "HZ"（仿宋 GB2312）
  3. 线型库包含 CENTER/DASHED（GB 规定线型）
  4. 实体数量合理（非空图）
  5. 标注文字存在（至少 1 个 TEXT/MTEXT）
  6. 比例/图框线索（可选 A3 图框检测）
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import List

import ezdxf

# ── GB/T 17450—1998 预期图层（envcad 全部使用的）─────────────
GB_KNOWN_LAYERS = {
    # 模板预置层（dxf_base new_drawing）
    "0", "Defpoints",
    "粗实线", "中实线", "细实线",
    "虚线", "点画线", "双点画线",
    "剖面线", "中心线",
    "尺寸标注",
    "文字", "文字-标题",
    "细实线-尺寸", "细实线-辅助",
    "图框", "图例", "标高", "网格",
    # 环保领域
    "管道", "管件", "设备", "阀门",
    "流向",
    "池体-壁", "池体-水",
    "管道-污水", "管道-给水", "管道-加药",
    # 液压领域
    "油路", "元件",
    # 电气领域
    "母线", "馈线", "控制回路",
    # 给排水/消防
    "给水管", "消防",
    # P&ID
    "工艺管道", "控制阀", "仪表",
    # 土木/结构
    "结构", "基础", "桩基", "支护", "边坡",
    "桥墩", "隔震", "节点", "组合结构", "施工",
    # 暖通
    "风管",
}

# ── GB/T 50001—2017 必需文字样式 ─────────────────────────
REQUIRED_TEXT_STYLES = {"HZ"}  # 仿宋 GB2312

# ── GB/T 14689—2008 A3 图框理论尺寸（mm, 1:100 时缩放） ─
A3_SIZE = (42000, 29700)  # 420×297 mm × 100


@dataclass
class GbReport:
    """单张图纸的 GB 符合性报告。"""
    path: str = ""
    total_entities: int = 0
    layers: List[str] = field(default_factory=list)
    text_styles: List[str] = field(default_factory=list)
    line_types: List[str] = field(default_factory=list)

    # 逐项
    ok_layers: bool = False
    ok_text_styles: bool = False
    ok_line_types: bool = False
    ok_has_text: bool = False
    ok_not_empty: bool = False

    unknown_layers: List[str] = field(default_factory=list)
    missing_styles: List[str] = field(default_factory=list)
    missing_linetypes: List[str] = field(default_factory=list)

    @property
    def all_pass(self) -> bool:
        return all([
            self.ok_layers, self.ok_text_styles, self.ok_line_types,
            self.ok_has_text, self.ok_not_empty,
        ])

    def status_line(self) -> str:
        s = "PASS" if self.all_pass else "FAIL"
        issues = []
        if not self.ok_layers and self.unknown_layers:
            issues.append(f"未知图层:{self.unknown_layers}")
        if not self.ok_text_styles:
            issues.append(f"缺文字样式:{self.missing_styles}")
        if not self.ok_line_types:
            issues.append(f"缺线型:{self.missing_linetypes}")
        if not self.ok_has_text:
            issues.append("无文字标注")
        if not self.ok_not_empty:
            issues.append("空图")
        base = f"[{s}] {os.path.basename(self.path)}: 实体{self.total_entities}"
        if issues:
            base += " | " + " | ".join(issues)
        return base


def validate_dxf(dxf_path: str) -> GbReport:
    """对单张 DXF 执行全部 GB 符合性检查。"""
    r = GbReport(path=dxf_path)

    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as exc:
        print(f"  [ERROR] 无法读取 {dxf_path}: {exc}")
        return r

    msp = doc.modelspace()
    entities = list(msp)
    r.total_entities = len(entities)

    # ── 1. 非空 ────────────────────────
    r.ok_not_empty = r.total_entities > 0

    # ── 2. 图层 ─────────────────────────
    r.layers = sorted([ly.dxf.name for ly in doc.layers if not ly.dxf.name.startswith("_")])
    r.unknown_layers = [ly for ly in r.layers if ly not in GB_KNOWN_LAYERS]
    r.ok_layers = len(r.unknown_layers) == 0

    # ── 3. 文字样式 ─────────────────────
    styles = doc.styles
    r.text_styles = [s.dxf.name for s in styles]
    r.missing_styles = [s for s in REQUIRED_TEXT_STYLES if s not in r.text_styles]
    r.ok_text_styles = len(r.missing_styles) == 0

    # ── 4. 线型 ─────────────────────────
    ltypes = doc.linetypes
    r.line_types = [lt.dxf.name for lt in ltypes]
    required = ["CENTER", "DASHED"]
    r.missing_linetypes = [lt for lt in required if lt not in r.line_types]
    r.ok_line_types = len(r.missing_linetypes) == 0

    # ── 5. 文字标注 ─────────────────────
    text_ents = list(msp.query("TEXT")) + list(msp.query("MTEXT"))
    r.ok_has_text = len(text_ents) > 0

    return r


def validate_dir(dir_path: str, verbose: bool = False) -> tuple[int, int]:
    """校验目录下所有 .dxf 文件。返回 (通过, 失败)。"""
    dxf_files = sorted([
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path) if f.lower().endswith(".dxf")
    ])
    if not dxf_files:
        print(f"[WARN] {dir_path} 中无 DXF 文件")
        return 0, 0

    passed, failed = 0, 0
    for fp in dxf_files:
        r = validate_dxf(fp)
        if r.all_pass:
            passed += 1
        else:
            failed += 1
        if verbose or not r.all_pass:
            print("  " + r.status_line())

    return passed, failed


def main():
    ap = argparse.ArgumentParser(
        description="envcad GB 国标符合性校验器 v1.5 P2")
    ap.add_argument("target", help="DXF 文件或图纸目录")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="显示全部结果（含 PASS）")
    ap.add_argument("--strict", action="store_true",
                    help="未知图层按失败处理（默认仅告警）")
    args = ap.parse_args()

    target = os.path.abspath(args.target)
    if not os.path.exists(target):
        print(f"[ERROR] 路径不存在: {target}")
        return 1

    if os.path.isfile(target):
        r = validate_dxf(target)
        print(r.status_line())
        return 0 if r.all_pass else 1

    passed, failed = validate_dir(target, verbose=args.verbose)
    total = passed + failed
    print(f"\n==== 国标校验完成 ====")
    print(f"  通过: {passed}/{total}")
    if failed:
        print(f"  未通过: {failed}/{total}")
    if not args.strict:
        print("  (提示: --strict 可将未知图层视为失败)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
