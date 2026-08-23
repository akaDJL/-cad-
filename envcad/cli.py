"""envcad CLI：生成五个验收测试的 DXF + 批量领域出图。

v1.5 — except 清零 / fix_patch 自动接入 / 全模块注册

用法：
  envcad list                                   # 查看所有领域和函数
  envcad all --out <dir>                        # 运行全部验收测试
  envcad param "层高 3.6" --out <dir>           # 自然语言改参重出图
  envcad batch --config projects.json --out <dir>   # JSON配置批量出图
  envcad domain solid_waste --function landfill_section --out <dir>  # 按领域出图
  envcad test all --out <dir>                   # 运行验收测试（可指定t1~t5）
  envcad test all --out <dir> --cad autocad     # 生成后推送到 AutoCAD
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback


def _run(test: str, out: str, scale=None, cad=None):
    from .drawings.t1_sewage_pipe import gen_t1
    from .drawings.t2_settler import gen_t2
    from .drawings.t3_network import gen_t3
    from .drawings.t4_wwtp import gen_t4
    from .drawings.t5_adjustment_pool import gen_t5
    from .drawings.t6_sewage_network import gen_t6
    from .engine.multicad_bridge import push_to_cad

    os.makedirs(out, exist_ok=True)
    paths = []
    kw = {"scale": scale} if scale else {}
    if test in ("t1", "all"):
        paths.append(gen_t1(out, **kw) if scale else gen_t1(out))
    if test in ("t2", "all"):
        paths.append(gen_t2(out, **kw) if scale else gen_t2(out))
    if test in ("t3", "all"):
        paths.append(gen_t3(out, **kw) if scale else gen_t3(out))
    if test in ("t4", "all"):
        paths.extend(gen_t4(out, **kw) if scale else gen_t4(out))
    if test in ("t5", "all"):
        paths.extend(gen_t5(out, **kw) if scale else gen_t5(out))
    if test in ("t6", "all"):
        paths.append(gen_t6(out, **kw) if scale else gen_t6(out))
    for p in paths:
        print("  生成:", p)
    if cad:
        for p in paths:
            ok, msg = push_to_cad(p, cad=cad)
            print(f"  {'推送成功' if ok else '推送失败'}: {msg}")
    return paths


# ─── 领域调度器 ──────────────────────────────────────────

# ── 组件/标注模块（Python API 专用，不通过 CLI 领域调用）──────────
# gdt / bom / dim / dimensions / symbols / templates / views / markup / notes
# rebar / image_bridge
# 这些模块的 draw_* 函数需要用户提供具体数据（公差值/材料清单/
# 尺寸点/焊接参数/技术说明文本等），不适合 CLI 无参快捷调用，
# 请通过 SKILL.md 文档中的 Python API 直接 import 使用。
# 注意：hvac 已升级为完整 CLI 领域（envcad domain hvac），不再属于此处。
#
# 例：from envcad.standards.gdt import draw_feature_control_frame
#     draw_feature_control_frame(msp, target, "垂直度", "0.05", datum="A")
_COMPONENT_ONLY = [
    "gdt", "bom", "dim", "dimensions", "notes",
    "templates", "views", "markup", "symbols", "rebar",
    "image_bridge",
]

# ── 自动注册：扫描 domains/*.yaml 自动加载所有领域 ──
# 新增领域只需在 envcad/domains/ 目录放入 YAML 配置文件，
# 无需修改本文件。多任务并行扩展互不冲突。
from .auto_registry import load_domain_registry as _load_domains

DOMAIN_REGISTRY = _load_domains()



def _run_domain_drawing(domain, func_name, params, out_dir, scale=100.0, cad=None):
    """执行单个领域绘图任务。"""
    import importlib
    from .engine.dxf_base import new_drawing, save_dxf
    from .engine.multicad_bridge import push_to_cad

    dom = DOMAIN_REGISTRY.get(domain)
    if not dom:
        print(f"  [跳过] 未知领域: {domain}")
        return None

    func_real = dom["functions"].get(func_name)
    if not func_real:
        print(f"  [跳过] 未知函数: {domain}.{func_name}")
        return None

    mod = importlib.import_module(dom["module"])
    draw_fn = getattr(mod, func_real)

    doc, dim_name, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()

    # 分离内部参数和绘图参数
    kwargs = dict(params or {})
    filename = kwargs.pop("_filename", f"{domain}_{func_name}.dxf")
    kwargs.setdefault("scale", scale)

    # 国标图框：所有 domain 出图默认套上 A2 横式（或 batch 指定的 paper/orientation）
    # 图框绘制后返回内框范围 (x0,y0,x1,y1)，domain 函数内容应画在框内。
    from .standards.frame import draw_frame, FrameInfo, get_default_paper_size, get_default_orientation
    _frame_info = FrameInfo(
        title=f"{domain}.{func_name}",
        drawing_no=f"ENV-{domain.upper()[:3]}-{func_name[:4].upper()}",
        scale_str=f"1:{int(scale)}",
        project=domain,
        size=get_default_paper_size(),
        orientation=get_default_orientation(),
    )
    _inner = draw_frame(doc, scale, _frame_info, tracker)
    x0, y0, x1, y1 = _inner
    # 内容基准点：内框内左上区域留 1% 边距，避免压到标题栏
    _cx0, _cy0 = x0 + (x1 - x0) * 0.01, y0 + (y1 - y0) * 0.01
    _content_origin = (_cx0, _cy0)

    # 兼容三种函数签名约定：
    #   1) (msp, origin, ...)      origin 为 (x,y) 元组 —— 多数模块
    #   2) (msp, center, ...)      center 为 (x,y) 元组 —— 部分模块
    #   3) (msp, x, y, ...)        x/y 为标量            —— 少数农业/电子/化工模块
    import inspect
    _sig = inspect.signature(draw_fn)
    _params = list(_sig.parameters)
    _second = _params[1] if len(_params) > 1 else ""
    if _second in ("x", "y"):
        # 标量约定：拆成两个位置参数
        _pos = (_content_origin[0], _content_origin[1])
    else:
        # origin / center / 未知：统一传元组
        _pos = (_content_origin,)

    try:
        draw_fn(msp, *_pos, **kwargs)
    except TypeError:
        try:
            draw_fn(msp, *_pos, scale=scale, **{
                k: v for k, v in kwargs.items() if k != "scale"
            })
        except Exception as e:
            print(f"  [错误] {domain}.{func_name}: {e}")
            print(f"  [调试] 参数: {list(kwargs.keys())}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None

    # 保存（自适应图幅：若内容超出默认幅面，自动重选 A0~A4 重画框）
    from .standards.frame import refit_frame
    _size, _orient = refit_frame(doc, scale, _frame_info, tracker)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    save_dxf(doc, path)
    print(f"  生成: {path}（图幅 {_size}-{('横' if _orient=='landscape' else '纵')}）")

    if cad:
        ok, msg = push_to_cad(path, cad=cad)
        print(f"  {'推送成功' if ok else '推送失败'}: {msg}")

    return path


def _run_equip(args):
    """环保设备成套出图（提示词驱动 · A/B/C 分级）。"""
    from .engine.multicad_bridge import push_to_cad
    et = args.etype
    if et == "baghouse":
        from .drawings.t7_baghouse import gen_baghouse as gen
        project = args.project or "袋式除尘器"
        paths = gen(args.out, level=args.level, air_flow=args.air_flow or 20000.0,
                    scale=args.scale, project=project,
                    filter_v=args.filter_v, bag_dia_mm=args.bag_dia,
                    bag_len_mm=args.bag_len, pollutant_in=args.conc)
    elif et == "uasb":
        from .drawings.t8_uasb import gen_uasb as gen
        project = args.project or "UASB厌氧反应器"
        paths = gen(args.out, level=args.level, Q=args.q, cod_in=args.cod,
                    scale=args.scale, project=project,
                    Nv=args.nv, H_reactor=args.hreact)
    elif et == "spray_tower":
        from .drawings.t9_spray_tower import gen_spray_tower as gen
        project = args.project or "湿法脱硫塔"
        paths = gen(args.out, level=args.level, air_flow=args.air_flow or 50000.0,
                    so2_in=args.so2, scale=args.scale, project=project,
                    lg=args.lg, n_spray=args.n_spray)
    elif et == "activated_carbon":
        from .drawings.t10_activated_carbon import gen_activated_carbon as gen
        project = args.project or "活性炭吸附装置"
        paths = gen(args.out, level=args.level, air_flow=args.air_flow or 10000.0,
                    voc_in=args.voc, scale=args.scale, project=project,
                    v_bed=args.v_bed)
    elif et == "chimney":
        from .drawings.t11_chimney import gen_chimney as gen
        project = args.project or "钢烟囱"
        paths = gen(args.out, level=args.level, air_flow=args.air_flow or 50000.0,
                    H=args.height, scale=args.scale, project=project, v_out=args.v_out)
    elif et == "duct":
        from .drawings.t12_duct import gen_duct as gen
        project = args.project or "废气风管系统"
        paths = gen(args.out, level=args.level, air_flow=args.air_flow or 50000.0,
                    scale=args.scale, project=project, v_duct=args.v_duct)
    else:  # fan
        from .drawings.t13_fan import gen_fan as gen
        project = args.project or "离心风机"
        paths = gen(args.out, level=args.level, air_flow=args.air_flow or 50000.0,
                    pressure=args.pressure, scale=args.scale, project=project)
    print(f"\n完成 {len(paths)} 张图 [{args.etype} {args.level}级] -> {args.out}")
    for p in paths:
        print("  " + os.path.basename(p))
    if args.cad:
        for p in paths:
            ok, msg = push_to_cad(p, cad=args.cad)
        print(f"推送CAD: {msg}")
    return 0


def _resolve_config_path(config_path):
    """解析批量配置文件路径。

    若给定的路径不存在，但只是一个文件名（无目录分隔），则回退到
    envcad 包目录内查找（如内置的 batch_example.json），使文档示例命令
    `envcad batch --config batch_example.json` 可从任意目录运行。
    """
    import envcad as _pkg
    if os.path.isfile(config_path):
        return config_path
    base = os.path.basename(config_path)
    if base:
        pkg_dir = os.path.dirname(_pkg.__file__)
        cand = os.path.join(pkg_dir, base)
        if os.path.isfile(cand):
            return cand
    return config_path


def _run_batch(config_path, out_dir, scale=100.0, cad=None):
    """从 JSON 配置文件批量生成图纸。

    配置文件格式:
    [
      {
        "domain": "solid_waste",
        "function": "landfill_section",
        "params": {"length": 60, "depth": 15, "liner_type": "composite"},
        "filename": "填埋场剖面图.dxf",
        "scale": 100
      },
      {
        "domain": "soil_remediation",
        "function": "injection_well_grid",
        "params": {"n_rows": 3, "n_cols": 5, "oxidant": "persulfate"},
        "filename": "注入井网.dxf",
        "scale": 100
      }
    ]
    """
    # 解析路径：若只给了文件名，自动回退到 envcad 包目录内查找（如内置 batch_example.json）
    resolved = _resolve_config_path(config_path)
    if resolved != config_path:
        print(f"[提示] 未找到 {config_path}，改用包内配置: {resolved}")
        config_path = resolved
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except FileNotFoundError:
        print(f"[错误] 配置文件不存在: {config_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"[错误] JSON 格式无效 ({config_path}): {e}")
        return []
    except Exception as e:
        print(f"[错误] 读取配置失败 ({config_path}): {e}")
        return []

    if isinstance(tasks, dict):
        tasks = [tasks]

    os.makedirs(out_dir, exist_ok=True)
    all_paths = []

    for i, task in enumerate(tasks):
        domain = task.get("domain", "")
        func_name = task.get("function", "")
        params = task.get("params", {})
        filename = task.get("filename", f"{domain}_{func_name}_{i+1}.dxf")
        task_scale = task.get("scale", scale)

        params["_filename"] = filename

        # 每条任务可单独指定图幅/方向（覆盖命令行 --size/--orientation）
        _paper = task.get("paper")
        _orient = task.get("orientation")
        if _paper or _orient:
            from .standards.frame import (
                set_default_paper_size, set_default_orientation)
            if _paper:
                set_default_paper_size(_paper)
            if _orient:
                set_default_orientation(_orient)

        print(f"\n[{i+1}/{len(tasks)}] {domain}.{func_name} -> {filename}")
        path = _run_domain_drawing(domain, func_name, params,
                                    out_dir, scale=task_scale, cad=cad)
        if path:
            all_paths.append(path)

    print(f"\n完成 {len(all_paths)}/{len(tasks)} 张图 -> {out_dir}")
    return all_paths


def _list_domains():
    """列出所有可用领域和函数。"""
    print("\n可用领域模块（CLI 直接调用）：\n")
    total = 0
    for domain, info in DOMAIN_REGISTRY.items():
        n = len(info["functions"])
        total += n
        desc = info.get("description", "")
        print(f"  [{domain}] ({n}个函数){' — ' + desc if desc else ''}")
        print(f"    模块: {info['module']}")
        print(f"    函数:")
        for alias, real in info["functions"].items():
            print(f"      {alias} -> {real}()")
        print()
    print(f"共 {len(DOMAIN_REGISTRY)} 个领域, {total} 个 CLI 可调绘图函数")
    print(f"  另有 {len(_COMPONENT_ONLY)} 个组件模块仅支持 Python API 调用"
          f"（{', '.join(_COMPONENT_ONLY)}）")
    print(f"  详见 SKILL.md 文档中的 import 示例\n")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="envcad",
        description="环保工程制图集成插件 v1.5（全领域+批量）")

    sub = ap.add_subparsers(dest="command")

    # 原有测试命令
    test_p = sub.add_parser("test", help="运行验收测试 t1~t5")
    test_p.add_argument("test", choices=["t1", "t2", "t3", "t4", "t5", "t6", "all"])
    test_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    test_p.add_argument("--scale", type=float, default=None)
    test_p.add_argument("--cad", default=None)

    # 批量命令
    batch_p = sub.add_parser("batch", help="JSON配置批量出图")
    batch_p.add_argument("--config", required=True, help="JSON配置文件路径")
    batch_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    batch_p.add_argument("--scale", type=float, default=100.0)
    batch_p.add_argument("--cad", default=None,
                          help="推送到CAD：autocad/zwcad/gstarcad/bricscad")
    batch_p.add_argument("--size", default="A2",
                         choices=["A0", "A1", "A2", "A3", "A4"],
                         help="图幅尺寸（默认 A2）")
    batch_p.add_argument("--orientation", default="landscape",
                         choices=["landscape", "portrait"],
                         help="图幅方向：横式/纵式（默认横式）")

    # 全部验收测试捷径
    all_p = sub.add_parser("all", help="运行全部验收测试（等同 test all）")
    all_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    all_p.add_argument("--scale", type=float, default=None)
    all_p.add_argument("--cad", default=None)

    # 领域命令
    dom_p = sub.add_parser("domain", help="按领域出图")
    dom_p.add_argument("domain", choices=list(DOMAIN_REGISTRY.keys()))
    dom_p.add_argument("--function", default=None, help="指定函数名")
    dom_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    dom_p.add_argument("--scale", type=float, default=100.0)
    dom_p.add_argument("--cad", default=None)
    dom_p.add_argument("--size", default="A2",
                       choices=["A0", "A1", "A2", "A3", "A4"],
                       help="图幅尺寸（默认 A2）")
    dom_p.add_argument("--orientation", default="landscape",
                       choices=["landscape", "portrait"],
                       help="图幅方向：横式/纵式（默认横式）")

    # 列表命令
    sub.add_parser("list", help="列出所有可用领域和函数")

    # 参数化命令
    param_p = sub.add_parser("param", help="自然语言改参重出图（例：envcad param '层高3.6'）")
    param_p.add_argument("text", help="自然语言参数意图（例：絮凝池水深5m）")
    param_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    param_p.add_argument("--scale", type=float, default=100.0)
    param_p.add_argument("--size", default="A2",
                         choices=["A0", "A1", "A2", "A3", "A4"],
                         help="图幅尺寸（默认 A2）")
    param_p.add_argument("--orientation", default="landscape",
                         choices=["landscape", "portrait"],
                         help="图幅方向：横式/纵式（默认横式）")
    # 组件命令（一键标注 / 零件 / 线形 / 列表）
    annotate_p = sub.add_parser("annotate", help="一键标注（闭合轮廓智能分标+管径/坡度/流向+标高+图例+说明+批目录）")
    annotate_p.add_argument("--in", dest="input_dxf", default="",
                            help="待标注 DXF 文件或目录；目录则批处理所有 .dxf；省略则内置演示底图")
    annotate_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    annotate_p.add_argument("--scale", type=float, default=100.0, help="出图比例倒数(1:100 填 100)")
    annotate_p.add_argument("--pipe", default="", help="管线标注 JSON(列表:{x1,y1,x2,y2,dn,slope,flow,angle})")
    annotate_p.add_argument("--el", default="", help="标高标注 JSON(列表:{x,y,value,side})")
    annotate_p.add_argument("--gdt", action="store_true", help="附加机械: 焊接符号/粗糙度/形位公差")
    annotate_p.add_argument("-r", "--recursive", action="store_true", help="批目录时递归子目录")
    annotate_p.add_argument("--ver", default="R2018", help="DXF版本 R2010/R2013/R2018")
    part_p = sub.add_parser("part", help="一键零件示例")
    part_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    part_p.add_argument("--teeth", type=int, default=19, help="齿轮齿数")
    part_p.add_argument("--module", type=float, default=5.0, help="齿轮模数")
    part_p.add_argument("--type", default="gear", choices=["gear","shaft","bearing","key","pulley"],
                        help="零件类型: gear/shaft/bearing/key/pulley")
    part_p.add_argument("--ver", default="R2018", help="DXF版本")
    linetype_p = sub.add_parser("linetype", help="线型图层示例")
    linetype_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    linetype_p.add_argument("--ver", default="R2018", help="DXF版本")
    component_p = sub.add_parser("component", help="列出可一键调用的组件模块")
    ps_p = sub.add_parser("paperspace", help="创建图纸空间布局（A3视口+标题栏）")
    ps_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    ps_p.add_argument("--paper", default="A2", choices=["A0","A1","A2","A3","A4"],
                        help="纸张尺寸")
    ps_p.add_argument("--project", default="", help="项目名")
    ps_p.add_argument("--no", default="", help="图号")

    # 文档自动化（结构 spec/calc/bom；土木 geotech；环保 env/env-bom；机械 mech/mech-bom）
    doc_p = sub.add_parser("doc", help="一键生成工程文档（8 大行业 说明书与清单）")
    doc_p.add_argument("dtype", choices=["spec", "calc", "bom",
                                         "geotech", "env", "env-bom",
                                         "mech", "mech-bom",
                                         "elec", "elec-bom",
                                         "plumb", "plumb-bom",
                                         "hvac", "hvac-bom",
                                         "hyd", "hyd-bom",
                                         "proc", "proc-bom"],
                       help="文档类型：spec/calc/bom(结构) geotech(土木) "
                            "env/env-bom(环保) mech/mech-bom(机械) "
                            "elec/elec-bom(电气) plumb/plumb-bom(给排水) "
                            "hvac/hvac-bom(暖通) hyd/hyd-bom(液压) "
                            "proc/proc-bom(化工)")
    doc_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    doc_p.add_argument("--project", default="XX 工程", help="工程名称")
    # 结构 RC 梁参数
    doc_p.add_argument("--b", type=float, default=250.0, help="梁宽 mm")
    doc_p.add_argument("--h", type=float, default=500.0, help="梁高 mm")
    doc_p.add_argument("--cover", type=float, default=20.0, help="保护层 mm")
    doc_p.add_argument("--conc", default="C30", help="混凝土等级")
    doc_p.add_argument("--rebar", default="HRB400", help="钢筋牌号")
    doc_p.add_argument("--m", type=float, default=120.0, help="弯矩设计值 kN·m")
    doc_p.add_argument("--v", type=float, default=180.0, help="剪力设计值 kN")
    doc_p.add_argument("--l", type=float, default=6000.0, help="计算跨度 mm")
    # 土木 基础/挡土墙参数
    doc_p.add_argument("--fk", type=float, default=1000.0, help="[土木]竖向力标准值 kN")
    doc_p.add_argument("--soil", default=None,
                       help="[土木]土类；基础默认粉质粘土(持力层)，挡墙默认中砂(回填)")
    doc_p.add_argument("--depth", type=float, default=1.5, help="[土木]基础埋深 m")
    doc_p.add_argument("--wallh", type=float, default=4.0, help="[土木]挡土墙墙高 m")
    # 环保 工艺参数
    doc_p.add_argument("--q", type=float, default=10000.0, help="[环保]设计流量 m³/d")
    doc_p.add_argument("--so", type=float, default=200.0, help="[环保]进水 BOD5 mg/L")
    doc_p.add_argument("--se", type=float, default=10.0, help="[环保]出水 BOD5 mg/L")
    doc_p.add_argument("--air", type=float, default=50000.0, help="[环保]除尘风量 m³/h")
    doc_p.add_argument("--std", default="一级A", help="[环保]排放执行标准")
    # 机械 齿轮/轴参数
    doc_p.add_argument("--power", type=float, default=5.0, help="[机械]传递功率 kW")
    doc_p.add_argument("--rpm", type=float, default=960.0, help="[机械]转速 rpm")
    doc_p.add_argument("--z1", type=int, default=20, help="[机械]小齿轮齿数")
    doc_p.add_argument("--z2", type=int, default=60, help="[机械]大齿轮齿数")
    doc_p.add_argument("--mat", default="40Cr", help="[机械]材料")
    # 电气
    doc_p.add_argument("--pe", type=float, default=100.0, help="[电气]安装容量 kW")
    doc_p.add_argument("--use", dest="elec_use", default="办公照明",
                       help="[电气]用电性质")
    doc_p.add_argument("--length", type=float, default=50.0, help="[电气]线路长度 m")
    doc_p.add_argument("--area", type=float, default=800.0,
                       help="[电气/暖通]面积 m²")
    doc_p.add_argument("--place", default="办公室", help="[电气/暖通]场所类型")
    # 给排水
    doc_p.add_argument("--people", type=float, default=500.0,
                       help="[给排水/暖通]用水单位数/人数")
    doc_p.add_argument("--wkind", default="办公楼", help="[给排水]用水部位类型")
    doc_p.add_argument("--ng", type=float, default=100.0, help="[给排水]给水当量总数")
    doc_p.add_argument("--lift", type=float, default=20.0, help="[给排水]提升高度 m")
    # 暖通
    doc_p.add_argument("--height", type=float, default=3.0, help="[暖通]层高 m")
    # 液压
    doc_p.add_argument("--force", type=float, default=50.0, help="[液压]工作负载 kN")
    doc_p.add_argument("--pressure", type=float, default=16.0, help="[液压]工作压力 MPa")
    doc_p.add_argument("--speed", type=float, default=0.1, help="[液压]活塞速度 m/s")
    # 化工
    doc_p.add_argument("--flow", type=float, default=30.0, help="[化工]流量 m³/h")
    doc_p.add_argument("--head", type=float, default=32.0, help="[化工]泵扬程 m")
    doc_p.add_argument("--duty", type=float, default=500.0, help="[化工]换热负荷 kW")
    doc_p.add_argument("--medium", default="水_一般", help="[化工]经济流速介质类别")

    # 设计验算（结构 rc-beam；土木 foundation/retaining；环保 wwtp/dust；机械 gear/shaft）
    design_p = sub.add_parser("design",
                              help="工程验算（结构/土木/环保/机械 强度与稳定校核）")
    design_p.add_argument("kind", nargs="?", default="rc-beam",
                          choices=["rc-beam", "foundation", "retaining",
                                   "wwtp", "dust", "gear", "shaft",
                                   "load", "cable", "illum",
                                   "water", "supply", "drain",
                                   "cooling", "duct",
                                   "cylinder", "pump",
                                   "pipe", "hx"],
                          help="rc-beam(结构) foundation/retaining(土木) "
                               "wwtp/dust(环保) gear/shaft(机械) "
                               "load/cable/illum(电气) water/supply/drain(给排水) "
                               "cooling/duct(暖通) cylinder/pump(液压) pipe/hx(化工)")
    design_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    design_p.add_argument("--project", default="", help="项目名")
    # 结构 RC 梁
    design_p.add_argument("--b", type=float, default=250.0, help="梁宽 mm")
    design_p.add_argument("--h", type=float, default=500.0, help="梁高 mm")
    design_p.add_argument("--cover", type=float, default=20.0, help="保护层 mm")
    design_p.add_argument("--conc", default="C30", help="混凝土等级")
    design_p.add_argument("--rebar", default="HRB400", help="钢筋牌号")
    design_p.add_argument("--m", type=float, default=120.0, help="弯矩 kN·m")
    design_p.add_argument("--v", type=float, default=180.0, help="剪力 kN")
    design_p.add_argument("--l", type=float, default=6000.0, help="跨度 mm")
    design_p.add_argument("--calc", action="store_true", help="同时出计算书 DOCX")
    design_p.add_argument("--dxf", default=None, help="同时出配筋图 DXF 路径")
    # 土木
    design_p.add_argument("--fk", type=float, default=1000.0, help="[土木]竖向力 kN")
    design_p.add_argument("--soil", default=None,
                          help="[土木]土类；基础默认粉质粘土(持力层)，挡墙默认中砂(回填)")
    design_p.add_argument("--depth", type=float, default=1.5, help="[土木]埋深 m")
    design_p.add_argument("--wallh", type=float, default=4.0, help="[土木]墙高 m")
    # 环保
    design_p.add_argument("--q", type=float, default=10000.0, help="[环保]流量 m³/d")
    design_p.add_argument("--so", type=float, default=200.0, help="[环保]进水BOD mg/L")
    design_p.add_argument("--se", type=float, default=10.0, help="[环保]出水BOD mg/L")
    design_p.add_argument("--air", type=float, default=50000.0, help="[环保]风量 m³/h")
    design_p.add_argument("--dust-kind", dest="dust_kind", default="baghouse",
                          choices=["baghouse", "cyclone"], help="[环保]除尘器型式")
    # 机械
    design_p.add_argument("--power", type=float, default=5.0, help="[机械/化工]功率 kW")
    design_p.add_argument("--rpm", type=float, default=960.0, help="[机械]转速 rpm")
    design_p.add_argument("--z1", type=int, default=20, help="[机械]小齿轮齿数")
    design_p.add_argument("--z2", type=int, default=60, help="[机械]大齿轮齿数")
    design_p.add_argument("--mat", default="40Cr", help="[机械]材料")
    # 电气
    design_p.add_argument("--pe", type=float, default=100.0, help="[电气]安装容量 kW")
    design_p.add_argument("--use", dest="elec_use", default="办公照明",
                          help="[电气]用电性质")
    design_p.add_argument("--length", type=float, default=50.0, help="[电气]线路长度 m")
    design_p.add_argument("--area", type=float, default=800.0,
                          help="[电气/暖通]面积 m²")
    design_p.add_argument("--place", default="办公室", help="[电气/暖通]场所类型")
    # 给排水
    design_p.add_argument("--people", type=float, default=500.0,
                          help="[给排水/暖通]用水单位数/人数")
    design_p.add_argument("--wkind", default="办公楼", help="[给排水]用水部位类型")
    design_p.add_argument("--ng", type=float, default=100.0, help="[给排水]给水当量总数")
    design_p.add_argument("--np", dest="np_drain", type=float, default=80.0,
                          help="[给排水]排水当量总数")
    design_p.add_argument("--lift", type=float, default=20.0, help="[给排水]提升高度 m")
    # 暖通
    design_p.add_argument("--height", type=float, default=3.0, help="[暖通]层高 m")
    # 液压
    design_p.add_argument("--force", type=float, default=50.0, help="[液压]工作负载 kN")
    design_p.add_argument("--pressure", type=float, default=16.0, help="[液压]工作压力 MPa")
    design_p.add_argument("--speed", type=float, default=0.1, help="[液压]活塞速度 m/s")
    # 化工
    design_p.add_argument("--flow", type=float, default=30.0, help="[化工]流量 m³/h")
    design_p.add_argument("--head", type=float, default=32.0, help="[化工]泵扬程 m")
    design_p.add_argument("--duty", type=float, default=500.0, help="[化工]换热负荷 kW")
    design_p.add_argument("--medium", default="水_一般", help="[化工]经济流速介质类别")

    # 环保设备成套出图（提示词驱动 · A/B/C 分级）
    equip_p = sub.add_parser("equip",
                             help="环保设备成套出图: baghouse袋式除尘器 / uasb厌氧反应器")
    equip_p.add_argument("etype", choices=["baghouse", "uasb", "spray_tower", "activated_carbon",
                                           "chimney", "duct", "fan"],
                         help="设备类型: baghouse袋式除尘器/uasb厌氧反应器/spray_tower脱硫塔/"
                              "activated_carbon活性炭吸附/chimney烟囱/duct风管/fan风机")
    equip_p.add_argument("--level", default="B", choices=["A", "B", "C"],
                         help="出图级别: A外形2张 / B详图6张 / C成套8张")
    equip_p.add_argument("--out", default=os.path.join(
        os.path.expanduser("~"), "Desktop", "envcad-output"))
    equip_p.add_argument("--scale", type=float, default=100.0)
    equip_p.add_argument("--project", default=None, help="工程名称")
    equip_p.add_argument("--cad", default=None,
                         help="推送到CAD: autocad/zwcad/gstarcad/bricscad")
    equip_p.add_argument("--size", default="A2",
                         choices=["A0", "A1", "A2", "A3", "A4"],
                         help="图幅尺寸（默认 A2）")
    equip_p.add_argument("--orientation", default="landscape",
                         choices=["landscape", "portrait"],
                         help="图幅方向：横式/纵式（默认横式）")
    # 袋式除尘器输入条件
    equip_p.add_argument("--air_flow", type=float, default=None,
                         help="[袋式/脱硫/活性炭]风量或废气量 m³/h（缺省按设备默认）")
    equip_p.add_argument("--filter_v", type=float, default=None, help="[袋式]过滤风速 m/min")
    equip_p.add_argument("--bag_dia", type=float, default=130.0, help="[袋式]滤袋直径 mm")
    equip_p.add_argument("--bag_len", type=float, default=3000.0, help="[袋式]滤袋长度 mm")
    equip_p.add_argument("--conc", type=float, default=5000.0, help="[袋式]入口浓度 mg/m³")
    # UASB 输入条件
    equip_p.add_argument("--q", type=float, default=500.0, help="[UASB]处理水量 m³/d")
    equip_p.add_argument("--cod", type=float, default=3000.0, help="[UASB]进水COD mg/L")
    equip_p.add_argument("--nv", type=float, default=8.0, help="[UASB]容积负荷 kgCOD/m³·d")
    equip_p.add_argument("--hreact", type=float, default=6.0, help="[UASB]反应区高度 m")

    # ima 订阅知识库同步（远程同步需 WorkBuddy 内由 AI 触发；本地模式解析已下载文档）
    sync_kb_p = sub.add_parser("sync-kb", help="同步 ima 订阅知识库到 envcad/knowledge/")
    sync_kb_p.add_argument("--local-dir", default=None,
                           help="本地已下载 ima 文档目录（.txt/.md/.json），将解析并入 knowledge")
    sync_kb_p.add_argument("--knowledge-dir", default=None,
                           help="知识输出目录，默认 envcad/knowledge/")

    # ima 知识库查询（出图时查国标/图集号）
    kb_p = sub.add_parser("kb", help="查询 ima 订阅知识库沉淀的国标/图集/设备数据")
    kb_p.add_argument("kind", choices=["countersink", "stamp-angle", "ejector-pin",
                                        "atlas", "pipe-atlas", "hvac-sample", "hvac-note",
                                        "sleeve", "mb", "septic", "discharge"],
                      help="查询类型")
    kb_p.add_argument("--arg", default=None, help="查询参数(如规格/M4/化粪池/水泵)")
    kb_p.add_argument("--web", action="store_true",
                      help="本地未命中时，自动联网搜索权威标准/图集")

    # 联网估算值"转正"：把沉淀的 _estimated 条目合并进国标源码表（本地）+ 可选推送云端
    sync_p = sub.add_parser("sync-backfill",
                            help="将联网估算沉淀转正为国标数据（本地合并 + 可选 --push 推云端）")
    sync_p.add_argument("--kind", default=None,
                        choices=["bolt", "nut", "screw", "washer"],
                        help="限定转正类型；省略则全部转正")
    sync_p.add_argument("--dry-run", action="store_true",
                        help="仅预览将要转正的条目，不修改源码表/不落盘/不推送")
    sync_p.add_argument("--push", action="store_true",
                        help="转正后自动 commit 并推送 GitHub（云端同步）")
    sync_p.add_argument("--msg", default=None, help="推送时的 commit 信息")

    # 联网搜索（公开权威来源，不依赖 MCP）
    web_p = sub.add_parser("websearch",
                           help="联网搜索权威行业标准/图集/设备参数（公开网页，不依赖 MCP）")
    web_p.add_argument("query", help="搜索关键词，如 'GB/T 50268 给水排水管道'")
    web_p.add_argument("--save", action="store_true", help="保存结果到 knowledge/web_cache/")
    web_p.add_argument("--detail", action="store_true", help="抓取前3条正文摘要")
    web_p.add_argument("--max", type=int, default=8, help="最大结果数")

    # 图块/构件联网检索（与 kb --web 同策略：本地无则搜权威标准/图集）
    block_p = sub.add_parser("block",
                             help="联网检索图块/构件/设备的国标画法·尺寸·图集（公开网页）")
    block_p.add_argument("query", help="图块关键词，如 '柔性防水套管 02S404' 或 '闸阀 图例'")
    block_p.add_argument("--save", action="store_true", help="保存结果到 knowledge/web_cache/")
    block_p.add_argument("--max", type=int, default=8, help="最大结果数")

    # 脱硫塔输入条件
    equip_p.add_argument("--so2", type=float, default=2000.0, help="[脱硫]入口SO2 mg/m³")
    equip_p.add_argument("--lg", type=float, default=15.0, help="[脱硫]液气比 L/m³")
    equip_p.add_argument("--n_spray", type=int, default=3, help="[脱硫]喷淋层数")
    # 活性炭输入条件
    equip_p.add_argument("--voc", type=float, default=200.0, help="[活性炭]入口VOC mg/m³")
    equip_p.add_argument("--v_bed", type=float, default=0.5, help="[活性炭]空塔气速 m/s")
    # 烟囱/风管/风机输入条件
    equip_p.add_argument("--height", type=float, default=30.0, help="[烟囱]烟囱高度 m")
    equip_p.add_argument("--v_out", type=float, default=None, help="[烟囱]出口烟速 m/s")
    equip_p.add_argument("--v_duct", type=float, default=None, help="[风管]风速 m/s")
    equip_p.add_argument("--pressure", type=float, default=2500.0, help="[风机]全压 Pa")

    args = ap.parse_args(argv)

    if args.command == "test":
        paths = _run(args.test, args.out, args.scale, args.cad)
        print(f"完成 {len(paths)} 张图 -> {args.out}")
        return 0

    elif args.command == "all":
        paths = _run("all", args.out, args.scale, args.cad)
        print(f"完成 {len(paths)} 张图 -> {args.out}")
        return 0

    elif args.command == "batch":
        from .standards.frame import set_default_paper_size, set_default_orientation
        set_default_paper_size(args.size)
        set_default_orientation(args.orientation)
        paths = _run_batch(args.config, args.out, args.scale, args.cad)
        return 0

    elif args.command == "domain":
        from .standards.frame import set_default_paper_size, set_default_orientation
        set_default_paper_size(args.size)
        set_default_orientation(args.orientation)
        if args.function:
            path = _run_domain_drawing(
                args.domain, args.function, {},
                args.out, args.scale, args.cad)
            print(f"完成 1 张图 -> {args.out}")
        else:
            # 列出该领域所有函数
            dom = DOMAIN_REGISTRY[args.domain]
            desc = dom.get("description", "")
            print(f"\n领域 [{args.domain}] {desc}")
            print(f"可用函数 ({len(dom['functions'])}个)：\n")
            for alias, real in dom["functions"].items():
                print(f"  envcad domain {args.domain} --function {alias}")
        return 0

    elif args.command == "list":
        _list_domains()
        return 0

    elif args.command == "param":
        from .standards.frame import set_default_paper_size, set_default_orientation
        set_default_paper_size(args.size)
        set_default_orientation(args.orientation)
        from .engine.parametric_bridge import parametric_cli
        path = parametric_cli(args.text, args.out, args.scale)
        if path:
            print(f"完成 1 张图 -> {args.out}")
        return 0
    elif args.command == "annotate":
        return _run_annotate(args)
    elif args.command == "part":
        _demo_part(args.out, args.teeth, args.module, args.ver, args.type)
    elif args.command == "linetype":
        _demo_linetype(args.out, args.ver)
    elif args.command == "component":
        _list_components()
    elif args.command == "paperspace":
        _demo_paperspace(args.out, args.paper, args.project, args.no)
    elif args.command == "doc":
        _demo_doc(args.out, args.dtype, args.project, args)
        return 0
    elif args.command == "design":
        _demo_design(args.out, args.kind, args)
        return 0
    elif args.command == "equip":
        from .standards.frame import set_default_paper_size, set_default_orientation
        set_default_paper_size(args.size)
        set_default_orientation(args.orientation)
        return _run_equip(args)

    elif args.command == "sync-kb":
        from .engine.ima_kb_sync import merge_local_imports
        from pathlib import Path
        knowledge_dir = Path(args.knowledge_dir) if args.knowledge_dir else Path(__file__).parent / "knowledge"
        if args.local_dir:
            local_dir = Path(args.local_dir)
            if not local_dir.exists():
                print(f"[错误] 本地目录不存在: {local_dir}")
                return 1
            files = merge_local_imports(local_dir, knowledge_dir)
            print(f"本地增量同步完成，写入 {len(files)} 个模块:")
            for f in files:
                print(f"  - {f}")
        else:
            print("[提示] 远程 ima 同步需由 WorkBuddy 会话中的 AI 通过 ima MCP 触发。")
            print("       如需本地同步，请把 ima 中下载的 .txt/.md/.json 放入一个目录，")
            print("       然后执行: envcad sync-kb --local-dir <目录路径>")
        return 0

    elif args.command == "sync-backfill":
        from .components.fasteners import promote_backfill
        kind = args.kind
        promoted = promote_backfill(kind_key=kind, dry_run=args.dry_run)
        if not promoted:
            print("无可转正的估算条目（沉淀里没有 _estimated 记录，或已全部转正）。")
            return 0
        print(f"\n{'[预览]' if args.dry_run else '[已转正]'} 共 {len(promoted)} 条：")
        for table, spec, fields in promoted:
            print(f"  {table}[{spec}] = {fields}")
        if args.dry_run:
            print("\n（dry-run 模式：未修改源码表，未落盘，未推送。去掉 --dry-run 执行转正。）")
            return 0
        print(f"\n本地转正完成：以上条目已合并进 envcad/components/fasteners.py 的国标表，"
              f"并标记 _promoted 落盘到 knowledge/web_cache/fasteners_backfill.json。")
        if args.push:
            import subprocess
            # __file__ = .../envcad/cli.py → dirname = envcad → 再 dirname = 仓库根
            repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            msg = args.msg or (
                "feat: 联网估算沉淀转正为国标数据"
                + (f"（{kind}）" if kind else "（全部类型）"))
            try:
                subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
                subprocess.run(["git", "-C", repo, "commit",
                                "-m", msg], check=True)
                # 走代理推送（github.com 主站直连常 reset，代理 65532 在监听时必走）
                pr = subprocess.run(
                    ["git", "-C", repo, "-c", "http.proxy=http://127.0.0.1:65532",
                     "-c", "https.proxy=http://127.0.0.1:65532",
                     "-c", "http.sslBackend=openssl",
                     "push", "origin", "main"],
                    capture_output=True, text=True)
                if pr.returncode == 0:
                    print("✓ 已 commit 并走代理推送 GitHub（云端同步完成）。")
                else:
                    # 代理失败则尝试直连绕过
                    pr2 = subprocess.run(
                        ["git", "-C", repo, "-c", "http.proxy=",
                         "-c", "https.proxy=",
                         "-c", "http.sslBackend=openssl",
                         "push", "origin", "main"],
                        capture_output=True, text=True)
                    if pr2.returncode == 0:
                        print("✓ 已 commit 并直连推送 GitHub（云端同步完成）。")
                    else:
                        print("[警告] 本地已转正，但推送失败：")
                        print(pr.stderr or pr.stdout)
                        print(pr2.stderr or pr2.stdout)
                        print("请手动推送：git push origin master")
            except Exception as _e:
                print(f"[警告] 推送异常：{_e}（本地转正已生效，云端需手动 push）")
        else:
            print("\n未加 --push：本地已转正但未推送云端。"
                  "需同步云端时执行: envcad sync-backfill --push")
        return 0

    elif args.command == "websearch":
        from .engine.web_search import web_search_cli
        web_search_cli(args.query, save=args.save, detail=args.detail, max_n=args.max)
        return 0

    elif args.command == "block":
        from .engine.web_search import web_search_cli
        # 图块检索：优先图集/标准站（供出图时查缺失图块的标准画法/尺寸）
        web_search_cli(args.query.strip(), save=args.save, detail=False, max_n=args.max)
        return 0

    elif args.command == "kb":
        from .knowledge import mech_gb, env_atlas, hvac_extra, env_equip_data
        a = args.arg
        if args.kind == "countersink":
            r = mech_gb.countersink(a or "4")
            print(f"沉孔 GB/T 152.2 规格 {a or '4'}: 螺纹{r[0]} 通孔dh[{r[1]},{r[2]}] "
                  f"沉孔Dc[{r[3]},{r[4]}] 深t≈{r[5]}mm | 标记 {mech_gb.COUNTERSINK_MARK.format(spec=a or '4')}")
        elif args.kind == "stamp-angle":
            grade, L = (a or "AT3,50").split(",")
            t = mech_gb.angle_tolerance(grade.strip(), float(L.strip()))
            print(f"冲压/弯曲角度公差 {grade.strip()} (短边L={L.strip()}mm): ±{t}° (GB/T 13915)")
        elif args.kind == "ejector-pin":
            D = int(a or 6)
            r = mech_gb.DIE_EJECTOR_PIN.get(D)
            if r:
                print(f"压铸模推杆 GB/T 4678.11 D={D} -> D1={r[0]} 可选L={r[1]} h={r[2]} | "
                      f"材料{mech_gb.DIE_EJECTOR_MATERIAL} 硬度{mech_gb.DIE_EJECTOR_HARDNESS}")
            else:
                found = False; miss = f"无 D={D} 的推杆数据"
        elif args.kind == "atlas":
            r = env_atlas.atlas_for(a or "化粪池")
            print(f"环保图集 [{a or '化粪池'}]: {r[0]} {r[1]} — {r[2]}")
        elif args.kind == "pipe-atlas":
            print(f"塑料给水管 {a or 'PVC-U'} 图集: {env_atlas.PLASTIC_PIPE_ATLAS.get(a or 'PVC-U', '未知')}")
        elif args.kind == "hvac-sample":
            r = hvac_extra.sample_category(a or "水泵")
            print(f"暖通样本 [{a or '水泵'}]: {r[0]} — {r[1]}")
        elif args.kind == "hvac-note":
            print(f"暖通出图提示 [{a or '冷却塔'}]: {hvac_extra.drawing_note(a or '冷却塔')}")
        elif args.kind == "sleeve":
            # 防水套管: kb sleeve --arg "200,flexible,I" 或 "200,rigid"
            parts = (a or "200,flexible,I").split(",")
            dn = int(parts[0]); kind = parts[1] if len(parts) > 1 else "flexible"
            seal = parts[2] if len(parts) > 2 else "I"
            r = env_equip_data.waterproof_sleeve(dn, kind, seal)
            if r:
                if kind == "flexible":
                    print(f"02S404 柔性防水套管 DN{dn} {seal}型: D1={r['D1']} D2={r['D2']} "
                          f"D3={r['D3']} D4={r['D4']} D5={r['D5']} l={r['l']} 螺栓{r['bolts']} "
                          f"重{r['weight_kg']}kg")
                else:
                    print(f"02S404 刚性防水套管(A型) DN{dn}: D1={r['D1']} D2={r['D2']} "
                          f"D3={r['D3']} D4={r['D4']} δ={r['delta']} 重{r['weight_kg']}kg")
            else:
                found = False; miss = f"无 DN{dn} 的{kind}套管数据"
        elif args.kind == "mb":
            r = env_equip_data.mbr_plant(a or "II-MBR-12-60A")
            if r:
                print(f"19S707 一体化MBR设备 {r['model']}: 日处理{r['q_d']}m³/d "
                      f"时处理{r['q_h']}m³/h 装机{r['power_kw']}kW")
            else:
                found = False; miss = f"无型号 {a} 的MBR设备数据"
        elif args.kind == "septic":
            r = env_equip_data.septic_tank(int(a or 4))
            if r:
                print(f"03S702 化粪池 {r['no']}号: 有效容积{r['volume_m3']}m³ "
                      f"停留时间{r['hrt_h']}h ({r['note']})")
            else:
                found = False; miss = f"无 {a} 号化粪池数据"
        elif args.kind == "discharge":
            # 排放限值: kb discharge --arg "GB18918,一级A" 或 "GB18466,排放"
            parts = (a or "GB18918,一级A").split(",")
            std = parts[0]; grade = parts[1] if len(parts) > 1 else None
            r = env_equip_data.discharge_limit(std, grade)
            if r:
                print(f"{std} {grade or ''} 排放限值: " +
                      ", ".join(f"{k}={v}" for k, v in r.items()))
            else:
                found = False; miss = f"无 {std}/{grade} 限值数据"

        # 本地未命中 → 联网回退（公开权威搜索，不依赖 MCP）
        if not found:
            print(miss if 'miss' in dir() else "本地未命中")
            if args.web:
                from .engine.web_search import web_search_cli
                # 构造自然语言查询词，避免把原始逗号参数直接丢给搜索引擎
                q_map = {
                    "sleeve": "02S404 防水套管 " + (a.split(",")[0] if a else ""),
                    "mb": "19S707 一体化MBR设备 " + (a or ""),
                    "septic": "03S702 化粪池 " + (a or ""),
                    "discharge": (a or "排放限值") + " 标准",
                    "ejector-pin": "GB/T 4678.11 压铸模推杆 " + (a or ""),
                }
                q = q_map.get(args.kind, a or args.kind)
                print(f"\n🔎 本地未命中，自动联网检索权威标准/图集：{q}")
                web_search_cli(q, save=False)
        return 0

    else:
        ap.print_help()
        return 0



# ---------------------------------------------------------------------------
# 一键标注（annotate）—— 核心引擎
# ---------------------------------------------------------------------------

# 数据库标注图层，--in 重标注时跳过，防实体膨胀
_ANNO_SKIP_LAYERS = {"尺寸标注", "文字", "标注", "引线", "符号", "图例",
                     "标高", "管径", "坡度", "流向", "说明"}

# 图层名 → 轮廓标签的默认推断
_LAYER_LABEL_MAP = {
    "粗实线": "池体",      "细实线": "轮廓",     "墙体": "墙体",
    "管道-给水": "给水管", "管道-污水": "污水管", "管道-雨水": "雨水管",
    "管道-消防": "消防管", "管道-回用": "回用管", "管道-污泥": "污泥管",
    "中心线": "轴线",      "轴线": "轴线",
}


def _contour_label(layer_name: str, index: int) -> str:
    """从图层名推断轮廓标签（如 '池体1'、'墙体2'），找不到映射则用 '轮廓N'。"""
    base = _LAYER_LABEL_MAP.get(layer_name, "轮廓")
    return f"{base}{index + 1}"


def _build_demo_basemap(msp, ver: str = "R2018"):
    """演示底图：矩形水池 + 水平给水管 + 斜向污水管。返回 {} 供标注信息。"""
    msp.add_lwpolyline([(0, 0), (6000, 0), (6000, 4000), (0, 4000)],
                       close=True, dxfattribs={"layer": "粗实线"})
    msp.add_line((7000, 1000), (11000, 1000), dxfattribs={"layer": "管道-给水"})
    msp.add_line((7000, 1600), (11000, 1800), dxfattribs={"layer": "管道-污水"})
    # 为演示提供管线/标高默认
    return {
        "pipe": [
            {"x1": 7000, "y1": 1000, "x2": 11000, "y2": 1000,
             "dn": "300", "slope": "", "flow": "1", "angle": 0},
            {"x1": 7000, "y1": 1600, "x2": 11000, "y2": 1800,
             "dn": "200", "slope": "0.5%", "flow": "1", "angle": 0},
        ],
        "el": [
            {"x": 0, "y": 0, "value": "±0.000", "side": "right"},
            {"x": 6000, "y": 4000, "value": "-3.500", "side": "right"},
        ],
    }


def _annotate_one(input_path, args, is_demo=False):
    """对单个 DXF 执行一键标注流水线。

    input_path: DXF 路径（为 None 时用内置演示底图）
    返回生成文件路径。
    """
    import ezdxf, os, json, math
    from envcad.standards.dim import draw_dimension
    from envcad.standards.auto_dim import auto_smart_dim, auto_chain_dim
    from envcad.standards.annotate import (
        draw_elevation, draw_pipe_diameter, draw_slope, draw_flow_arrow)
    from envcad.standards.legend import draw_legend
    from envcad.standards.notes import draw_construction_notes

    s = args.scale
    demo_info = {}

    # 1) 载入或构建底图
    if input_path and os.path.isfile(input_path):
        doc = ezdxf.readfile(input_path)
        msp = doc.modelspace()
        base = os.path.splitext(os.path.basename(input_path))[0]
        print(f"  [标注] {input_path}")
        is_demo = False
    else:
        doc = ezdxf.new(args.ver)
        msp = doc.modelspace()
        base = "annotate"
        demo_info = _build_demo_basemap(msp, args.ver)
        is_demo = True

    # 2) 智能分组：闭合轮廓 / 直线 / 开放多段线
    closed_contours = []   # (entity, points, layer)
    open_polys = []        # (entity, points, layer)
    line_segments = []     # (entity, p1, p2, layer)

    for e in list(msp):
        layer = e.dxf.layer if e.dxf.hasattr("layer") else ""
        if layer in _ANNO_SKIP_LAYERS:
            continue
        t = e.dxftype()
        if t == "LWPOLYLINE":
            pts = list(e.get_points("xy"))
            if len(pts) >= 3 and e.closed:
                closed_contours.append((e, pts, layer))
            elif len(pts) >= 2:
                open_polys.append((e, pts, layer))
        elif t == "LINE":
            p1 = (e.dxf.start.x, e.dxf.start.y)
            p2 = (e.dxf.end.x, e.dxf.end.y)
            if math.hypot(p2[0] - p1[0], p2[1] - p1[1]) > 1e-6:
                line_segments.append((e, p1, p2, layer))

    # 3) 标注闭合轮廓（每个轮廓 auto_smart_dim + 标签）
    for i, (_, pts, layer) in enumerate(closed_contours):
        info = auto_smart_dim(msp, pts, scale=s)
        # 轮廓标签：在中心点写入
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        label = _contour_label(layer, i)
        msp.add_mtext(
            label,
            dxfattribs={
                "layer": "文字", "style": "Standard",
                "char_height": 3.5 * s,
                "insert": (cx, cy),
                "attachment_point": 5,  # MC 中心对齐
            })
    print(f"  [标注] 闭合轮廓: {len(closed_contours)}")

    # 4) 标注直线段（端到端）
    for _, p1, p2, _ in line_segments:
        draw_dimension(msp, p1, p2, scale=s)
    print(f"  [标注] 直线: {len(line_segments)}")

    # 5) 标注开放多段线
    for _, pts, _ in open_polys:
        auto_chain_dim(msp, pts, scale=s)
    print(f"  [标注] 开放多段线: {len(open_polys)}")

    # 6) 管线标注
    pipe_items = []
    if args.pipe and os.path.exists(args.pipe):
        with open(args.pipe, encoding="utf-8") as fh:
            pipe_items = json.load(fh)
    elif is_demo:
        pipe_items = demo_info.get("pipe", [])
    for it in pipe_items:
        sx, sy, ex, ey = it["x1"], it["y1"], it["x2"], it["y2"]
        mid = ((sx + ex) / 2, (sy + ey) / 2)
        if it.get("dn"):
            draw_pipe_diameter(msp, mid, it["dn"], s)
        if it.get("slope"):
            draw_slope(msp, (sx, sy), (ex, ey), it["slope"], s)
        ang = it.get("angle")
        direction = (math.cos(math.radians(ang)), math.sin(math.radians(ang))) if ang else (1, 0)
        if it.get("flow"):
            draw_flow_arrow(msp, (sx, sy), direction, s, label="流向")
    if pipe_items:
        print(f"  [标注] 管线: {len(pipe_items)}")

    # 7) 标高
    el_items = []
    if args.el and os.path.exists(args.el):
        with open(args.el, encoding="utf-8") as fh:
            el_items = json.load(fh)
    elif is_demo:
        el_items = demo_info.get("el", [])
    for it in el_items:
        draw_elevation(msp, (it["x"], it["y"]), it["value"], s,
                       side=it.get("side", "right"))
    if el_items:
        print(f"  [标注] 标高: {len(el_items)}")

    # 8) 图例 + 施工说明（自动算位置：所有轮廓最右上方 + 偏移）
    all_x = [0]; all_y = [0]
    for _, pts, _ in closed_contours:
        all_x.extend(p[0] for p in pts)
        all_y.extend(p[1] for p in pts)
    for _, p1, p2, _ in line_segments:
        all_x.extend([p1[0], p2[0]]); all_y.extend([p1[1], p2[1]])
    max_x = max(all_x); max_y = max(all_y)

    legend_origin = (max_x + 1000, max_y + 500)
    draw_legend(msp, legend_origin, s, [
        ("pipe_hdpe", "给水管", "DN300"),
        ("pipe_sewage", "污水管", "DN200"),
        ("elevation", "标高", "\u00b10.000"),
        ("arrow_flow", "流向", ""),
        ("wall", "池壁", "C30"),
    ], title="图  例")
    draw_construction_notes(msp, (max_x + 1000, max_y - 500), [
        {"title": "施工说明", "items": [
            "1. 图中尺寸单位除标高以米计外，其余均为毫米。",
            "2. 管道标高以管中心计，坡度按 i 标注方向坡降。",
            "3. 水池混凝土强度等级 C30，抗渗等级 P6。",
            "4. 未尽事宜按国家现行规范执行。",
        ]},
    ], scale=s)
    print("  [标注] 已附加图例与施工说明")

    # 8.5) 国标图框：以所有内容（含图例/说明）的外包络绘制图框与标题栏。
    #      直接包住内容（不平移已有实体，避免 MTEXT/INSERT 平移失败导致错位），
    #      标题栏固定在内容外包络右下角。
    from .standards.frame import draw_frame_at, FrameInfo, PAPER_BASE
    _bb_min_x, _bb_min_y, _bb_max_x, _bb_max_y = 0.0, 0.0, 0.0, 0.0
    for e in list(msp):
        try:
            b = e.bbox()
        except Exception:
            b = None
        if not b:
            # MTEXT/INSERT 等 bbox 可能为 None，退而取插入点
            try:
                ip = e.dxf.insert
                _bb_min_x = min(_bb_min_x, ip.x); _bb_min_y = min(_bb_min_y, ip.y)
                _bb_max_x = max(_bb_max_x, ip.x); _bb_max_y = max(_bb_max_y, ip.y)
            except Exception:
                pass
            continue
        _bb_min_x = min(_bb_min_x, b.extmin.x)
        _bb_min_y = min(_bb_min_y, b.extmin.y)
        _bb_max_x = max(_bb_max_x, b.extmax.x)
        _bb_max_y = max(_bb_max_y, b.extmax.y)
    # 纳入已知图例/说明区域（MTEXT bbox 不稳定时兜底）
    _bb_min_x = min(_bb_min_x, legend_origin[0])
    _bb_min_y = min(_bb_min_y, legend_origin[1])
    _bb_max_x = max(_bb_max_x, legend_origin[0] + 5000 * s, max_x + 1000 + 5000 * s)
    _bb_max_y = max(_bb_max_y, legend_origin[1] + 4000 * s, max_y - 500 + 2500 * s)
    # 选幅面：取不小于内容尺寸（含留白）的最小标准幅面（横式）
    _pad_w = (25 + 10) * s
    _pad_h = (10 + 10) * s
    _frame_w = (_bb_max_x - _bb_min_x) + _pad_w
    _frame_h = (_bb_max_y - _bb_min_y) + _pad_h
    _chosen = "A0"
    for _sz in ("A4", "A3", "A2", "A1", "A0"):
        _long, _short = PAPER_BASE[_sz]
        if _frame_w <= _long * s and _frame_h <= _short * s:
            _chosen = _sz
            break
    _info = FrameInfo(
        title="一键标注成果图",
        drawing_no="ENV-ANN-001",
        scale_str=f"1:{int(s)}",
        project="标注",
        size=_chosen,
        orientation="landscape",
    )
    draw_frame_at(doc, s, _info, (_bb_min_x, _bb_min_y, _bb_max_x, _bb_max_y))
    print(f"  [标注] 已套国标图框(内容自适应，选用 {_chosen} 横式)")

    # 9) 机械形位公差（--gdt）
    if args.gdt:
        from envcad.standards.symbols import draw_weld_symbol, draw_surface_roughness
        from envcad.standards.gdt import draw_feature_control_frame
        cx_mech = (min(all_x) + max(all_x)) / 2
        draw_weld_symbol(msp, (cx_mech, max_y + 2000), "\u89d2\u710a\u7f1d", leg="5", scale=s)
        draw_surface_roughness(msp, (cx_mech, max_y + 2500), "6.3", scale=s)
        draw_feature_control_frame(msp, (cx_mech, max_y + 3000),
                                   "\u5782\u76f4\u5ea6", "0.05", datum="A", scale=s)
        print("  [标注] 已附加焊接符号/粗糙度/形位公差(GD&T)")

    # 10) 保存
    out_name = f"{base}_annotated.dxf" if (input_path and not is_demo) else "annotate.dxf"
    p = os.path.join(args.out, out_name)
    doc.saveas(p)
    print(f"  \u2713 -> {p}")
    return p


# ---------------------------------------------------------------------------
# 顶层入口：文件 / 目录分发
# ---------------------------------------------------------------------------

def _run_annotate(args):
    """一键标注入口 —— 单文件、目录批量或演示底图。"""
    import os, glob

    os.makedirs(args.out, exist_ok=True)

    # 目录批量模式
    target = args.input_dxf
    if target and os.path.isdir(target):
        pattern = os.path.join(target, "**/*.dxf") if args.recursive else os.path.join(target, "*.dxf")
        dxf_files = sorted(glob.glob(pattern, recursive=args.recursive))
        if not dxf_files:
            print(f"[标注] 目录 {target} 中未找到 .dxf 文件")
            return 1
        print(f"[标注] 批量模式：发现 {len(dxf_files)} 个 .dxf 文件")
        for f in dxf_files:
            _annotate_one(f, args)
        print(f"\n\u2713 一键标注批量完成：{len(dxf_files)} 个文件 -> {args.out}")
        return 0

    # 单文件 / 演示
    _annotate_one(target if (target and os.path.isfile(target)) else None, args)
    return 0



def _demo_part(out, teeth=19, module=5.0, ver="R2018", ptype="gear"):
    import ezdxf, os
    from envcad.standards.mechanical import (
        draw_spur_gear, draw_stepped_shaft, draw_rolling_bearing,
        draw_key, draw_compression_spring,
    )
    doc = ezdxf.new(ver); msp = doc.modelspace()
    if ptype == "gear":
        draw_spur_gear(msp, (50, 50), z=teeth, m=module)
        tag = f"齿数={teeth} 模数={module}"
    elif ptype == "shaft":
        draw_stepped_shaft(msp, (50, 50), diameters=[30,40,30], lengths=[40,60,40])
        tag = f"阶梯轴 Φ30-40-30"
    elif ptype == "bearing":
        draw_rolling_bearing(msp, (50, 50))
        tag = "滚动轴承"
    elif ptype == "key":
        draw_key(msp, (50, 50))
        tag = "平键"
    elif ptype == "pulley":
        draw_compression_spring(msp, (50, 50))  # spring as pulley stand-in
        tag = f"弹簧(零件)"
    else:
        draw_spur_gear(msp, (50, 50), z=teeth, m=module)
        tag = f"齿数={teeth}"
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, f"part_{ptype}.dxf"); doc.saveas(p)
    print(f"已生成零件示例({tag}) -> {p}")



def _demo_linetype(out, ver="R2018"):
    import ezdxf, os
    from ezdxf.enums import TextEntityAlignment
    from envcad.standards.layers import setup_layers
    doc = ezdxf.new(ver); setup_layers(doc)
    msp = doc.modelspace()
    # 画可见线条——粗实线/细实线/虚线/中心线/双点画线
    lines = [
        ((50,80),(250,80),"粗实线","CONTINUOUS", "粗实线"), 
        ((50,70),(250,70),"细实线","CONTINUOUS", "细实线"),
        ((50,60),(250,60),"虚线","DASHED",   "虚线"),
        ((50,50),(250,50),"中心线","CENTER",  "中心线"),
        ((50,40),(250,40),"双点画线","PHANTOM","双点画线"),
    ]
    for (s,e,ly,lt,label) in lines:
        msp.add_line(s,e,dxfattribs={"layer":ly,"linetype":lt})
        t = msp.add_text(label,dxfattribs={"layer":"文字","height":3,"style":"HZ"})
        t.set_placement((260,e[1]),align=TextEntityAlignment.MIDDLE_LEFT)
    os.makedirs(out,exist_ok=True)
    p = os.path.join(out,"linetype_demo.dxf"); doc.saveas(p)
    print(f"已生成线型示例 -> {p}")


def _demo_paperspace(out, paper="A2", project="", drawing_no=""):
    import ezdxf, os
    from envcad.standards.paperspace import create_layout, add_viewport, add_title_block
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    msp.add_line((0,0),(500,500))
    layout = create_layout(doc, "Sheet1", paper)
    add_viewport(layout, (210,148), 380, 270, 100)
    pw, ph = {"A0":(1189,841),"A1":(841,594),"A2":(594,420),"A3":(420,297),"A4":(297,210)}.get(paper,(420,297))
    tw, th = 180, 20
    add_title_block(layout, (pw-10-tw, ph-10), tw, th,
                    project=project, drawing_no=drawing_no)
    p = os.path.join(out, f"sheet_{paper}.dxf"); doc.saveas(p)
    print(f"已生成纸空间布局({paper}) -> {p}")


def _list_components():
    print("以下 11 个组件模块已内置（_COMPONENT_ONLY，Python API 调用）：")
    print("  gdt / bom / dim / dimensions / symbols / templates / views / markup / notes / rebar / image_bridge")
    print("调用方式（Python API）：")
    print("  from envcad.standards.dimensions import draw_dimension")
    print("  doc = ezdxf.new('R2018'); msp = doc.modelspace()")
    print("  draw_dimension(msp, (0, 0), (120, 0), text='100'); doc.saveas('out.dxf')")


def _run_rc_beam(args):
    """解析 CLI 参数并跑钢筋混凝土梁设计，返回结果 dict。"""
    from .design.rc_beam import design_rc_beam
    M = (args.m or 0.0) * 1e6      # kN·m -> N·mm
    V = (args.v or 0.0) * 1e3      # kN -> N
    return design_rc_beam(
        b=args.b, h=args.h, cover=args.cover,
        concrete_grade=args.conc, rebar_grade=args.rebar,
        M=M, V=V, l=args.l,
    )


def _demo_doc(out, dtype, project, args):
    import os
    os.makedirs(out, exist_ok=True)

    # ---- 结构（原有）----
    if dtype == "spec":
        from .docgen.spec_doc import generate_structure_spec
        p = os.path.join(out, "结构设计总说明.docx")
        generate_structure_spec(p, project=project)
        print(f"已生成: {p}")
    elif dtype == "calc":
        from .docgen.calc_book import generate_calc_book
        from .design.rc_beam import format_rc_beam_result
        r = _run_rc_beam(args)
        p = os.path.join(out, "结构计算书.docx")
        generate_calc_book(p, r, project=project or "XX 构件")
        print(format_rc_beam_result(r))
        print(f"已生成: {p}")
    elif dtype == "bom":
        from .docgen.bom_xlsx import generate_material_bom
        p = os.path.join(out, "材料表.xlsx")
        generate_material_bom(p)
        print(f"已生成: {p}")

    # ---- 土木：地基与基础设计说明 ----
    elif dtype == "geotech":
        from .design.foundation import (design_spread_footing,
                                        design_retaining_wall)
        from .docgen.geotech_doc import generate_geotech_spec
        bearing = args.soil or "粉质粘土"      # 持力层
        backfill = args.soil or "中砂"          # 挡墙回填料
        footing = design_spread_footing(args.fk, soil=bearing, d=args.depth)
        retaining = design_retaining_wall(args.wallh, soil=backfill)
        p = os.path.join(out, "地基与基础设计说明.docx")
        generate_geotech_spec(p, project=project, footing=footing,
                              retaining=retaining, bearing_layer=bearing)
        print(footing["note"])
        print(retaining["note"])
        print(f"已生成: {p}")

    # ---- 环保：工艺设计说明书 / 排放达标清单 ----
    elif dtype == "env":
        from .design.env_process import (design_aeration_tank, design_sed_tank,
                                         design_dust_collector)
        from .docgen.env_report import generate_env_spec
        aer = design_aeration_tank(args.q, args.so, Se=args.se)
        sed = design_sed_tank(args.q)
        dust = design_dust_collector(args.air)
        p = os.path.join(out, "环保工艺设计说明书.docx")
        generate_env_spec(p, project=project, discharge_std=args.std,
                          aeration=aer, sed=sed, dust=dust)
        print(aer["note"])
        print(sed["note"])
        print(f"已生成: {p}")
    elif dtype == "env-bom":
        from .docgen.env_report import generate_discharge_xlsx
        p = os.path.join(out, "污染物排放达标清单.xlsx")
        generate_discharge_xlsx(p, standard=args.std)
        print(f"已生成: {p}")

    # ---- 机械：设计计算说明书 / 零件明细表 ----
    elif dtype == "mech":
        from .design.gear import check_spur_gear
        from .design.shaft import design_shaft
        from .docgen.mech_calc import generate_mech_calc
        gear = check_spur_gear(args.power, args.rpm, z1=args.z1, z2=args.z2,
                               material=args.mat)
        shaft = design_shaft(args.power, args.rpm, material="45钢")
        p = os.path.join(out, "机械设计计算说明书.docx")
        generate_mech_calc(p, project=project, gear=gear, shaft=shaft)
        print(gear["note"])
        print(shaft["check"]["note"])
        print(f"已生成: {p}")
    elif dtype == "mech-bom":
        from .docgen.mech_calc import generate_parts_xlsx
        p = os.path.join(out, "零件明细表.xlsx")
        generate_parts_xlsx(p, project=project)
        print(f"已生成: {p}")

    # ---- 电气：设计说明书 / 负荷计算表 ----
    elif dtype == "elec":
        from .design.electrical import (design_power_load, select_cable,
                                        design_illumination,
                                        estimate_short_circuit)
        from .docgen.elec_doc import generate_elec_spec
        load = design_power_load(args.pe, kind=args.elec_use)
        cable = select_cable(load["Ijs"], cos=load["cos"], length=args.length)
        illum = design_illumination(args.area, place=args.place)
        sc = estimate_short_circuit(max(args.pe * 1.5, 400))
        p = os.path.join(out, "电气设计说明书.docx")
        generate_elec_spec(p, project=project, load=load, cable=cable,
                           illum=illum, sc=sc)
        print(load["note"]); print(cable["note"])
        print(f"已生成: {p}")
    elif dtype == "elec-bom":
        from .docgen.elec_doc import generate_load_xlsx
        p = os.path.join(out, "负荷计算表.xlsx")
        generate_load_xlsx(p)
        print(f"已生成: {p}")

    # ---- 给排水：设计说明书 / 用水量计算表 ----
    elif dtype == "plumb":
        from .design.plumbing import (design_water_demand, design_supply_flow,
                                      size_supply_pipe, design_drainage,
                                      design_pump_head)
        from .docgen.plumb_doc import generate_plumb_spec
        demand = design_water_demand(args.people, kind=args.wkind)
        flow = design_supply_flow(args.ng)
        pipe = size_supply_pipe(flow["qg"])
        drain = design_drainage(args.ng * 0.8)
        pump = design_pump_head(args.lift)
        p = os.path.join(out, "给排水设计说明书.docx")
        generate_plumb_spec(p, project=project, demand=demand, flow=flow,
                            pipe=pipe, drain=drain, pump=pump)
        print(demand["note"]); print(pipe["note"])
        print(f"已生成: {p}")
    elif dtype == "plumb-bom":
        from .docgen.plumb_doc import generate_water_xlsx
        p = os.path.join(out, "用水量计算表.xlsx")
        generate_water_xlsx(p)
        print(f"已生成: {p}")

    # ---- 暖通：设计说明书 / 负荷设备表 ----
    elif dtype == "hvac":
        from .design.hvac import (design_load, design_air_volume,
                                  design_fresh_air, size_duct)
        from .docgen.hvac_doc import generate_hvac_spec
        load = design_load(args.area, place=args.place)
        air = design_air_volume(args.area, args.height, place=args.place)
        fresh = design_fresh_air(args.people, place=args.place)
        duct = size_duct(air["L"])
        p = os.path.join(out, "暖通空调设计说明书.docx")
        generate_hvac_spec(p, project=project, load=load, air=air,
                           fresh=fresh, duct=duct)
        print(load["note"]); print(air["note"])
        print(f"已生成: {p}")
    elif dtype == "hvac-bom":
        from .docgen.hvac_doc import generate_hvac_xlsx
        p = os.path.join(out, "分区负荷设备表.xlsx")
        generate_hvac_xlsx(p)
        print(f"已生成: {p}")

    # ---- 液压：系统计算书 / 元件清单 ----
    elif dtype == "hyd":
        from .design.hydraulic import design_cylinder, select_pump, size_hyd_pipe
        from .docgen.hyd_doc import generate_hyd_calc
        cyl = design_cylinder(args.force, p=args.pressure, v=args.speed)
        pump = select_pump(cyl["Q"], p=args.pressure)
        pipe = size_hyd_pipe(cyl["Q"], p=args.pressure)
        p = os.path.join(out, "液压系统设计计算书.docx")
        generate_hyd_calc(p, project=project, cyl=cyl, pump=pump, pipe=pipe)
        print(cyl["note"]); print(pump["note"])
        print(f"已生成: {p}")
    elif dtype == "hyd-bom":
        from .docgen.hyd_doc import generate_hyd_bom
        p = os.path.join(out, "液压元件清单.xlsx")
        generate_hyd_bom(p)
        print(f"已生成: {p}")

    # ---- 化工：工艺设计说明书 / 设备管道清单 ----
    elif dtype == "proc":
        from .design.process import (size_econ_pipe, design_pump,
                                     design_heat_exchanger)
        from .docgen.proc_doc import generate_proc_spec
        pipe = size_econ_pipe(args.flow, medium=args.medium)
        pump = design_pump(args.flow, args.head)
        hx = design_heat_exchanger(args.duty)
        p = os.path.join(out, "化工工艺设计说明书.docx")
        generate_proc_spec(p, project=project, pipe=pipe, pump=pump, hx=hx)
        print(pipe["note"]); print(pump["note"])
        print(f"已生成: {p}")
    elif dtype == "proc-bom":
        from .docgen.proc_doc import generate_proc_bom
        p = os.path.join(out, "设备管道清单.xlsx")
        generate_proc_bom(p)
        print(f"已生成: {p}")

    else:
        print("[错误] 未知文档类型")


def _demo_design(out, kind, args):
    import os
    os.makedirs(out, exist_ok=True)

    # ---- 结构：RC 梁 ----
    if kind == "rc-beam":
        from .design.rc_beam import format_rc_beam_result
        r = _run_rc_beam(args)
        print(format_rc_beam_result(r))
        if getattr(args, "calc", False):
            from .docgen.calc_book import generate_calc_book
            p = os.path.join(out, "结构计算书.docx")
            generate_calc_book(p, r, project=args.project or "RC梁")
            print(f"已生成计算书: {p}")
        if getattr(args, "dxf", None):
            from .engine.dxf_base import new_drawing, save_dxf
            from .standards.rebar_auto import draw_beam_with_schedule
            doc, _, _ = new_drawing(100.0, return_tracker=True)
            msp = doc.modelspace()
            draw_beam_with_schedule(msp, (3000, 5000),
                                    width=args.b, height=args.h, scale=100.0)
            save_dxf(doc, args.dxf)
            print(f"已生成配筋图: {args.dxf}")

    # ---- 土木：独立基础 ----
    elif kind == "foundation":
        from .design.foundation import (design_spread_footing,
                                        format_footing_result)
        r = design_spread_footing(args.fk, soil=args.soil or "粉质粘土",
                                  d=args.depth)
        print(format_footing_result(r))

    # ---- 土木：挡土墙 ----
    elif kind == "retaining":
        from .design.foundation import (design_retaining_wall,
                                        format_retaining_result)
        r = design_retaining_wall(args.wallh, soil=args.soil or "中砂")
        print(format_retaining_result(r))

    # ---- 环保：污水处理（曝气+二沉）----
    elif kind == "wwtp":
        from .design.env_process import (design_aeration_tank, design_sed_tank,
                                         format_wwtp_result)
        aer = design_aeration_tank(args.q, args.so, Se=args.se)
        sed = design_sed_tank(args.q)
        print(format_wwtp_result(aer, sed))

    # ---- 环保：除尘器 ----
    elif kind == "dust":
        from .design.env_process import (design_dust_collector,
                                         format_dust_result)
        r = design_dust_collector(args.air, kind=args.dust_kind)
        print(format_dust_result(r))

    # ---- 机械：齿轮 ----
    elif kind == "gear":
        from .design.gear import check_spur_gear, format_gear_result
        r = check_spur_gear(args.power, args.rpm, z1=args.z1, z2=args.z2,
                            material=args.mat)
        print(format_gear_result(r))

    # ---- 机械：轴 ----
    elif kind == "shaft":
        from .design.shaft import design_shaft, format_shaft_result
        r = design_shaft(args.power, args.rpm, material="45钢")
        print(format_shaft_result(r))

    # ---- 电气：负荷计算 ----
    elif kind == "load":
        from .design.electrical import (design_power_load, select_cable,
                                        format_load_result)
        load = design_power_load(args.pe, kind=args.elec_use)
        cable = select_cable(load["Ijs"], cos=load["cos"], length=args.length)
        print(format_load_result(load, cable))

    # ---- 电气：电缆选型 ----
    elif kind == "cable":
        from .design.electrical import select_cable
        r = select_cable(args.pe, length=args.length)  # 此处 --pe 复用为计算电流 A
        print(r["note"])

    # ---- 电气：照度 ----
    elif kind == "illum":
        from .design.electrical import (design_illumination,
                                        format_illumination_result)
        r = design_illumination(args.area, place=args.place)
        print(format_illumination_result(r))

    # ---- 给排水：用水量 ----
    elif kind == "water":
        from .design.plumbing import design_water_demand, format_supply_result
        r = design_water_demand(args.people, kind=args.wkind)
        print(format_supply_result(r))

    # ---- 给排水：给水管径 ----
    elif kind == "supply":
        from .design.plumbing import (design_supply_flow, size_supply_pipe,
                                      format_supply_result)
        demand = design_supply_flow(args.ng)
        pipe = size_supply_pipe(demand["qg"])
        print(demand["note"]); print(pipe["note"])

    # ---- 给排水：排水 ----
    elif kind == "drain":
        from .design.plumbing import design_drainage, format_drain_result
        r = design_drainage(args.np_drain)
        print(format_drain_result(r))

    # ---- 暖通：冷热负荷 + 送风 ----
    elif kind == "cooling":
        from .design.hvac import (design_load, design_air_volume,
                                  format_hvac_result)
        load = design_load(args.area, place=args.place)
        air = design_air_volume(args.area, args.height, place=args.place)
        print(format_hvac_result(load, air))

    # ---- 暖通：风管 ----
    elif kind == "duct":
        from .design.hvac import design_air_volume, size_duct
        air = design_air_volume(args.area, args.height, place=args.place)
        r = size_duct(air["L"])
        print(air["note"]); print(r["note"])

    # ---- 液压：液压缸 ----
    elif kind == "cylinder":
        from .design.hydraulic import design_cylinder, format_cylinder_result
        r = design_cylinder(args.force, p=args.pressure, v=args.speed)
        print(format_cylinder_result(r))

    # ---- 液压：泵 + 管径 ----
    elif kind == "pump":
        from .design.hydraulic import (design_cylinder, select_pump,
                                       size_hyd_pipe, format_pump_result)
        cyl = design_cylinder(args.force, p=args.pressure, v=args.speed)
        pump = select_pump(cyl["Q"], p=args.pressure)
        pipe = size_hyd_pipe(cyl["Q"], p=args.pressure)
        print(format_pump_result(pump, pipe))

    # ---- 化工：经济管径 ----
    elif kind == "pipe":
        from .design.process import size_econ_pipe, format_pipe_result
        r = size_econ_pipe(args.flow, medium=args.medium)
        print(format_pipe_result(r))

    # ---- 化工：换热器 ----
    elif kind == "hx":
        from .design.process import design_heat_exchanger, format_hx_result
        r = design_heat_exchanger(args.duty)
        print(format_hx_result(r))

    else:
        print(f"[错误] 未知设计类型: {kind}")


if __name__ == "__main__":
    sys.exit(main())
