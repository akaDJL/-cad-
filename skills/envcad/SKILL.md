---
name: envcad
description: "跨行业国标工程制图 CAD 技能：基于 ezdxf 生成符合 GB 国标（GB/T 17450、GB/T 50001、GB/T 1182、GB/T 324、GB 50010 等）的 DXF 工程图，覆盖建筑/土木/结构/桥梁/基础/机械/环保(水处理·大气·固废·环评)/电气/给排水/暖通/液压/P&ID/农业食品/电子半导体/能源化工/测绘GIS 等 16+ 行业，含 GD&T 形位公差、焊接符号、表面粗糙度、BOM、剖面、钢筋、图纸模板、修订标记等标准标注，并可通过 COM 桥接推送 AutoCAD/ZWCAD。当用户要求生成 CAD 图纸、画工程图、出 DXF、标注形位公差/焊接/粗糙度、材料明细表、污水处理/沉淀池/管网平剖面图、液压原理图、电气控制图、给排水/暖通图、P&ID 流程图，或推送到 AutoCAD 时使用。Use when the user asks to generate CAD drawings, DXF files, engineering blueprints, piping/sedimentation tank/WWTP drawings, GD&T/weld/roughness symbols, BOM, HVAC/electrical/plumbing/P&ID diagrams, or push to AutoCAD."
version: "1.5"
license: MIT
homepage: https://github.com/akaDJL/-cad-
author: 凹凸cad小助手（二集）
---

# envcad — 凹凸cad小助手（二集集成・v1.5）

## Overview

envcad 是**跨行业工程制图** CAD 插件。覆盖 16+ 行业，90+ 标准模块
工程实战工具，基于 text-to-cad-main + multiCAD-mcp 二大开源内核。
其中 18 个领域支持 CLI 快捷调用（`envcad domain <domain> --function <func>`），
11 个组件模块通过 Python API 导入使用（见下方示例）。

> v1.2 砍掉 SynapsCAD（GPL-3.0），许可证 MIT。
> v1.3 深度挖掘 ezdxf，新增 GD&T/焊接/粗糙度/BOM/剖面/公差。
> v1.4 新增土木/暖通/液压三行业。
> v1.5 新增电气/给排水/P&ID + 土木结构/桥梁/基础工程 CLI 领域 + 自动联网搜索策略 + 高级标注/技术说明/图纸模板/修订标记。hydraulic/electrical/plumbing/pid 接入 CLI。机械模块从5函数升级到18函数(齿轮/轴/轴承/弹簧/连接件全系)。19 领域 104 个 CLI 函数 + 11 个 Python API 模块。

**版本区分（重要）**：

| 版本 | 路径 | 定位 |
|------|------|------|
| **二集版 v1.5** (本 Skill) | `桌面\凹凸cad小助手（二集）v1.5` | 二集版：text-to-cad + multiCAD-mcp + 国标规范 + 行业标注，MIT 许可证 |
| 三集版 v2.1 | `桌面\凹凸cad小助手（三集）v1.1 - 副本` | 旧版：含 SynapsCAD（GPL-3.0），已弃用 |
| 非三集版 v1.1 | `桌面\凹凸cad助手 v1.1` | 基础版：text-to-cad + multiCAD-mcp，无规范层 |

**标准规范模块**：

| 模块 | 内容 | 依据标准 |
|------|------|----------|
| `standards/layers.py` | 22 层国标图层（粗/中/细实线、虚线、点画线、管道工艺层） | GB/T 17450—1998 |
| `standards/styles.py` | 仿宋 GB2312 汉字样式 + simplex 标注样式 | GB/T 50001—2017 |
| `standards/annotate.py` | 标高三角、坡度箭头、管径标注 | GB/T 50001—2017 |
| `standards/frame.py` | A3 图框 + 标题栏（图名/图号/比例/日期） | GB/T 14689—2008 |
| `standards/legend.py` | 工程图例（阀门、接头、流量计、管道符号） | CJJ/T 158—2011 |
| `standards/gdt.py` | **NEW v1.3** GD&T 形位公差（特征控制框/基准/基准目标） | GB/T 1182—2018 |
| `standards/symbols.py` | **NEW v1.3** 焊接符号（角焊/对焊/塞焊等）+ 表面粗糙度 Ra | GB/T 324/131 |
| `standards/bom.py` | **NEW v1.3** 材料明细表/设备表（4种预设方案） | GB/T 10609.2—2009 |
| `standards/views.py` | **NEW v1.3** 剖切符号线 + 局部放大视图标记 | GB/T 4458.1—2002 |
| `standards/dim.py` | **NEW v1.3** 尺寸公差（±/上下偏差）+ 配合公差 | GB/T 1800.2—2020 |
| `standards/rebar.py` | **NEW v1.4** 钢筋表/梁柱配筋/钢结构节点/弯起钢筋大样 | GB 50010/50017 |
| `standards/hvac.py` | **NEW v1.4** 风管平面/风口符号/设备符号/水力计算表 | GB 50736/50243 |
| `standards/hydraulic.py` | **NEW v1.4** 液压泵/马达/缸/方向阀/溢流阀/集成块 | GB/T 786.1—2021 |
| `standards/electrical.py` | **NEW v1.5** 断路器/接触器/电机/变压器/控制回路/电缆表 | GB/T 4728 |
| `standards/plumbing.py` | **NEW v1.5** 给排水管道/卫生器具/阀门/消火栓/喷淋/立管 | GB 50015/50974 |
| `standards/pid.py` | **NEW v1.5** P&ID容器/仪表/控制阀/控制回路/管线表 | ISA S5.1/GB/T 2625 |
| `standards/dimensions.py` | **NEW v1.6** 坐标/角度/链式基线/半径直径标注 | GB/T 4458.4 |
| `standards/notes.py` | **NEW v1.6** 技术说明块/材料规格/施工说明/自动换行 | — |
| `standards/templates.py` | **NEW v1.6** A0-A4图幅+机械/土木/电气/给排水标题栏 | GB/T 14689 |
| `standards/markup.py` | **NEW v1.6** 修订云线/变更三角/审查意见/版本记录 | — |
| `standards/building.py` | **NEW v1.5** 楼层剖面（层高）/平面布置/墙体/柱/梁/门窗/楼梯 | GB/T 50001/GB 50352 |
| `standards/mechanical.py` | **NEW v1.5** 齿轮(直齿/斜齿/锥齿/蜗轮蜗杆)/轴(阶梯/花键)/轴承/键/螺纹/螺栓连接/弹簧/挡圈/油封/中心孔 — 18函数 | GB/T 4459.2/.3/.4 |
| `standards/hvac.py` | **NEW v1.5** 风管平面/剖面/风口/空调机组/风机盘管/冷却塔/冷水机组/锅炉 — 8函数 | GB/T 50155/GB 50736 |
| `standards/structural.py` | **NEW v1.5 P1** 预应力梁/砌体墙/钢框架/桁架/桥墩台/隧道/边坡 | GB 50010/50017/JTG D60 |
| `standards/bridge.py` | **NEW v1.5 P1** 箱梁/沉井/隔震支座/柱脚/组合柱/脚手架 | JTG D60/GB 50011 |
| `standards/foundation.py` | **NEW v1.5 P1** 独立基础/楼梯剖面/挡土墙/基坑支护 | GB 50007/50010 |

### 两种使用方式

| 方式 | 模块 | 命令 |
|------|------|------|
| **CLI 快捷命令** | `all` `list` `param` | `envcad all` / `envcad param "层高3.6"` |
| **CLI 领域快捷调用** | `building` `mechanical` `hvac` `structural` `bridge` `foundation` `hydraulic` `electrical` `plumbing` `pid` 及环保 11 领域 | `envcad domain <domain> --function <func>` |
| **参数化桥接** | `engine/parametric_bridge.py` | `from envcad.engine.parametric_bridge import resolve_intent, apply_and_redraw` |
| **Python API 导入** | `gdt` `bom` `dim` `dimensions` `symbols` `templates` `views` `markup` `notes` `rebar` `image_bridge` | `from envcad.standards.xxx import draw_xxx` |

底层引擎：

| Project | Role | Module |
|---------|------|--------|
| text-to-cad-main | DXF generation via ezdxf | `envcad/engine/dxf_base.py` |
| multiCAD-mcp | COM bridge to AutoCAD/ZWCAD | `envcad/engine/multicad_bridge.py` |

**环境变量约定**（本文档内）：
- `{PACKAGE_DIR}` = 桌面 `凹凸cad小助手（二集）v1.5` 目录
- `{PYTHON}` = Python 3.10+ 解释器路径

## Environment / Install

要求 Python 3.10+。核心依赖仅 `ezdxf`：

```bash
# 方式 A：直接装核心依赖（最省事，无需构建）
pip install ezdxf

# 方式 B：把本仓库作为可编辑包安装（提供 envcad 命令行）
pip install -e .

# 可选：COM 桥接推送 AutoCAD/ZWCAD（仅 Windows 需要）
pip install pywin32

# 可选：文档自动化层（DOCX 说明书 / XLSX 清单）
pip install openpyxl python-docx
```

> envcad 的 Python 包（`envcad/`）与 `pyproject.toml` 位于**仓库根目录**（即本文件所在 `skills/envcad/` 的上一级）。运行安装与出图命令前，请先 `cd` 到**仓库根目录**（或把仓库根加入 `PYTHONPATH`），否则 `pip install -e .` 与 `from envcad...` 导入会失败。

## Agent 中的两种使用方式

### 方式一：Skill（推荐，本 Skill）

直接对 agent 说需求，agent 会自动调用 envcad CLI 生成图纸。适合：
- 生成标准工程图纸（T1-T5 验收测试）
- 生成后自动校验
- 推送到 AutoCAD

触发示例：
- "生成一套污水处理站施工图"
- "画沉淀池平剖面图，1:50"
- "把图纸推送 AutoCAD"

### 方式二：MCP（补充，精细操作）

非三集版 v1.1 提供了 MCP 服务端（`凹凸cad助手 v1.1\integrated-cad-mcp`），
已配置在 `~/.workbuddy/mcp.json`。提供 15 个工具模块（cad_model、draw_entities、
manage_layers 等），适合细粒度参数化建模。与 Skill 互补使用。

## Trigger Conditions

Use this skill when the user asks any of the following:

- "Generate a CAD drawing" / "生成 CAD 图纸" / "画工程图"
- "Create a DXF file" / "出 DXF 图"
- Requests related to: piping, sedimentation tank, sewage treatment, pool structures,
  pipe networks, mechanical parts with engineering standards
- "Push to AutoCAD" / "推送到 CAD"
- "Add GD&T tolerance" / "形位公差标注" / "标注垂直度"
- "Weld symbol" / "焊接符号" / "标注焊缝"
- "Surface roughness" / "表面粗糙度" / "Ra标注"
- "BOM table" / "材料明细表" / "设备表"
- "Section view" / "剖面视图" / "剖切符号"
- "Dimension tolerance" / "尺寸公差" / "配合公差"
- "Rebar schedule" / "钢筋表" / "梁配筋" / "柱配筋" / "钢结构节点"
- "HVAC duct" / "风管" / "风口" / "暖通" / "水力计算"
- "Hydraulic circuit" / "液压原理图" / "方向阀" / "溢流阀" / "集成块"
- Any request involving engineering blueprint generation with GB standards
- Requests to verify or test CAD output

## Quick Commands

### Generate Drawings

```bash
# 工作方式（在 PACKAGE_DIR 下运行）
cd "{PACKAGE_DIR}"
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','all']; from envcad.cli import main; main()"

# 生成单个测试
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','t1']; from envcad.cli import main; main()"
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','t2']; from envcad.cli import main; main()"
# ... t3, t4, t5 同理

# NEW v1.5: 领域快捷出图（89个函数覆盖18个领域）
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','domain','structural','--function','steel_frame']; from envcad.cli import main; main()"
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','domain','bridge','--function','box_girder']; from envcad.cli import main; main()"
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','domain','hydraulic','--function','pump']; from envcad.cli import main; main()"
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','domain','electrical','--function','breaker']; from envcad.cli import main; main()"
# 列出所有领域和函数
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','list']; from envcad.cli import main; main()"

# 指定输出目录和比例
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','t2','--out','D:/drawings','--scale','50']; from envcad.cli import main; main()"
```

Default output: `{PACKAGE_DIR}\output\`

### Verify Generated Drawings

After generating drawings, always run the verification script:

```bash
# 使用默认输出目录
{PYTHON} {PACKAGE_DIR}\tests\verify.py

# 指定输出目录
{PYTHON} {PACKAGE_DIR}\tests\verify.py D:\drawings
```

This checks every DXF for required annotations, layers, and entity counts.

### Push to CAD Software

```bash
# 生成并推送到 AutoCAD
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','all','--cad','autocad']; from envcad.cli import main; main()"

# 推送到 ZWCAD
{PYTHON} -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','all','--cad','zwcad']; from envcad.cli import main; main()"

# 支持: autocad, zwcad, gstarcad, bricscad
```

### DXF → DWG 转换（v1.5.1）

插件本体通过 `multicad_bridge.dxf_to_dwg()` 输出 DWG（借助本机已装 CAD 的 COM，
无需额外依赖；纯 Python 无法直写 DWG 专有格式）：

```python
from envcad.engine.multicad_bridge import dxf_to_dwg, dxf_dir_to_dwg

# 单文件：DXF → DWG（默认 AutoCAD 2018 格式）
ok, path_or_err = dxf_to_dwg("output.dxf", "output.dwg", cad="autocad", version="2018")

# 批量：目录下所有 .dxf → .dwg
ok, fail = dxf_dir_to_dwg("./out", cad="autocad", version="2018")
```

## The Five Acceptance Tests

| # | Test | What it validates | Output files |
|---|------|-------------------|-------------|
| T1 | DN300 sewage pipe annotation | Pipe diameter, invert elevation, slope, flow arrows | 1 DXF |
| T2 | Sedimentation tank | Parametric tank, sludge hopper, inlet/outlet, A3 frame 1:50 | 1 DXF |
| T3 | Sewage pipe network | HDPE pipe, gate valves, flexible joints, flowmeters, legend | 1 DXF |
| T4 | 50m³/day WWTP | Full construction drawing set with 6 sheets | 6 DXF |
| T5 | Adjustment pool iteration | Parameter changes, anti-corrosion layers | 2 DXF |

## When User Wants Custom Drawings

If the user requests a custom drawing (not one of the 5 preset tests), use the Python API:

```python
from envcad.engine.dxf_base import new_drawing, save_dxf
from envcad.components.pool import RectPoolParams
from envcad.components.pipe import pipe_segment
from envcad.standards.frame import draw_frame, FrameInfo

doc, dim_name = new_drawing(scale=100)
msp = doc.modelspace()

# Add geometry, annotations, components...
# msp.add_line(...)
# ...

# Add A3 frame and title block
draw_frame(doc, scale=100,
           info=FrameInfo(title="图名", drawing_no="编号", scale_str="1:100"))

save_dxf(doc, r"path\to\output.dxf")
```

For reference, read the component source files:
- `{PACKAGE_DIR}\envcad\components\pool.py`
- `{PACKAGE_DIR}\envcad\components\pipe.py`
- `{PACKAGE_DIR}\envcad\components\fittings.py`
- `{PACKAGE_DIR}\envcad\standards\frame.py`

### v1.3 GD&T and Mechanical Annotations

```python
from envcad.standards.gdt import (
    draw_feature_control_frame, draw_datum_symbol,
    draw_datum_target, draw_gdt_table,
)
from envcad.standards.symbols import (
    draw_weld_symbol, draw_surface_roughness,
    draw_weld_table, draw_roughness_on_surface,
)
from envcad.standards.bom import draw_bom, draw_bom_from_dict
from envcad.standards.views import draw_section_line, draw_detail_circle
from envcad.standards.dim import draw_dimension, draw_fit_annotation

# GD&T: 垂直度公差 + 基准
draw_datum_symbol(msp, (x, y), "A", scale=50, direction="down")
draw_feature_control_frame(
    msp, (x, y+10), "垂直度", "0.05", datum="A",
    scale=50, leader_dir=(0, 1))

# 焊接: 角焊缝 5mm 焊脚
draw_weld_symbol(msp, (x, y), "角焊缝", leg="5",
                 site_weld=False, all_around=True, scale=50)

# 粗糙度: Ra 3.2
draw_surface_roughness(msp, (x, y), "3.2", method="removal", scale=50)

# BOM 表格
draw_bom(msp, (x0, y0), [
    ["1", "法兰 DN100", "4", "Q235B", ""],
    ["2", "螺栓 M16×60", "32", "8.8级", "GB/T 5782"],
], columns="standard", scale=50, title="材料明细表")

# 配合公差: φ20 H7/g6（查表模式，覆盖 ≤3~500mm 全直径段）
draw_fit_annotation(msp, (x, y), "φ20", "H7/g6", scale=50)

# 显式模式：Agent 搜索 GB/T 1800.2 后传入精确偏差值（mm）
draw_fit_annotation(msp, (x, y), "φ35", "H7/r6", scale=50,
    hole_es=0.025, hole_ei=0, shaft_es=0.050, shaft_ei=0.034)

### v1.4 Civil / HVAC / Hydraulic

```python
from envcad.standards.rebar import (
    draw_rebar_schedule, draw_beam_section,
    draw_column_section, draw_steel_connection, draw_rebar_bend,
)
from envcad.standards.hvac import (
    draw_duct, draw_duct_network, draw_diffuser,
    draw_equipment, draw_duct_sizing_table,
)
from envcad.standards.hydraulic import (
    draw_line as draw_hyd_line, draw_pump, draw_motor,
    draw_cylinder, draw_directional_valve,
    draw_relief_valve, draw_throttle_valve,
    draw_check_valve_hyd, draw_accumulator, draw_manifold,
)

# 土木: 梁配筋断面（所有数值由 Agent 搜索后传入）
draw_beam_section(msp, (x, y), width=300, height=600,
    bottom_bars=[{"count":4,"dia":20}],
    top_bars=[{"count":2,"dia":16}],
    stirrup={"dia":8,"spacing":200},
    cover=25, scale=50, label="KL1 300×600")

# 钢筋表
draw_rebar_schedule(msp, (x, y), [
    {"pos":"1","dia":20,"shape":"直筋","length":3200,"qty":4},
    {"pos":"2","dia":8,"shape":"箍筋","length":1800,"qty":20},
], scale=50, title="梁 KL1 钢筋表")

# 暖通: 风管（所有风速/风量/管径由 Agent 搜索后传入）
draw_duct(msp, (x0, y0), (x1, y1), width=800, height=0,
    scale=50, label="800×400", layer="送风管")

# 风口
draw_diffuser(msp, (cx, cy), w=400, d_type="square",
    scale=50, label="FP-1", flow_rate="500m³/h")

# 设备
draw_equipment(msp, (cx, cy), "fan", w=600, h=600,
    scale=50, label="SF-1",
    params={"flow":"5000m³/h","pressure":"300Pa"})

# 液压: 泵 + 马达 + 方向阀
draw_pump(msp, (x, y), "fixed_uni", scale=30, label="P1",
    params={"flow":"40L/min","pressure":"21MPa"})

draw_directional_valve(msp, (cx, cy), ports=4, positions=3,
    center_type="O", solenoids=["left","right"],
    springs=["left","right"], scale=30, label="DV1")
```

### v1.5 Electrical / Plumbing / P&amp;ID

```python
from envcad.standards.electrical import (
    draw_breaker, draw_contactor, draw_motor_symbol,
    draw_transformer, draw_terminal,
    draw_busbar, draw_feeder, draw_control_circuit,
    draw_cable_schedule,
)
from envcad.standards.plumbing import (
    draw_plumbing_pipe, draw_fixture, draw_valve_plumbing,
    draw_fire_hydrant, draw_sprinkler, draw_plumbing_riser,
)
from envcad.standards.pid import (
    draw_process_line, draw_vessel, draw_instrument,
    draw_control_valve, draw_control_loop, draw_line_list,
)

# 电气: 断路器 + 接触器 + 电机控制
draw_breaker(msp, (x, y), poles=3, b_type="mccb",
    scale=50, label="QF1", params={"In":"63A","Icu":"10kA"})
draw_contactor(msp, (cx, cy), contacts=3, coil=True, scale=50, label="KM1")
draw_motor_symbol(msp, (mx, my), "induction", scale=50,
    label="M1", params={"P":"5.5kW","V":"380V","rpm":"1450"})
draw_control_circuit(msp, (ox, oy), [
    {"type":"breaker","label":"QF1"},
    {"type":"contactor","label":"KM1"},
    {"type":"relay","label":"FR1"},
    {"type":"motor","label":"M1","params":{"P":"5.5kW"}},
], scale=50)

# 给排水: 卫生器具 + 消防
draw_fixture(msp, (x, y), "toilet", scale=50, label="W-1")
draw_fire_hydrant(msp, (cx, cy), "indoor", scale=50, label="FH-1")
draw_sprinkler(msp, (sx, sy), "pendant", scale=50,
    label="SP-1", params={"K":"80","temp":"68°C"})
draw_plumbing_riser(msp, (ox, oy), [
    {"name":"1F","el":0},{"name":"2F","el":3.6},{"name":"3F","el":7.2},
], pipe_types=["cold","hot","drain","fire"], scale=50, label="JL-1")

# P&ID: 容器 + 仪表 + 控制阀
draw_vessel(msp, (cx, cy), "reactor", width=30, height=40,
    scale=50, tag="R-101", label="反应器")
draw_instrument(msp, (ix, iy), tag="TIC-101", mounting="dcc",
    func_id="温度指示控制", scale=50)
draw_control_valve(msp, (vx, vy), "globe", actuator="pneumatic",
    fail="FC", scale=50, label="TV-101")

## Workflow

1. Understand what drawings the user needs (match to T1-T5 or build custom)
2. Generate with `envcad <test>` or Python API
3. Run `verify.py` to confirm correctness
4. If requested, push to CAD with `--cad autocad`
5. Present results: list generated files with paths

## Important: Always Verify

After ANY drawing generation, run `verify.py`. Never skip this step.
Report verification results to the user: PASS/FAIL status for each drawing.

## Python Environment

Python 3.13+ with ezdxf and pywin32 required.
On this machine: `{PYTHON}`

Dependencies: ezdxf >= 1.3, pywin32 >= 305.
License: MIT (clean — no GPL-3.0 viral terms).

## 行业标准搜索策略（v1.5 强化）

**核心原则：代码只负责绘图框架。所有行业标准数值必须由 Agent 搜索后显式传入绘图函数。**

### 自动搜索规则（最高优先级）

**凡是代码模块中不存在、不确定、或只覆盖部分范围的行业数据，Agent 必须自动上互联网搜索。**
不得猜测或使用默认值替代。

搜索优先级：
1. 国家标准全文公开系统 `site:openstd.samr.gov.cn` — 最权威
2. 搜狗微信/知乎/百度文库 — 工程实践参考
3. 中英文混合搜索 — 提高命中率

### 各行业搜索关键词

| 行业 | 标准编号 | 搜索模板 |
|------|---------|---------|
| 机械公差 | GB/T 1800.2 | `φ<直径> <精度> 上下偏差 GB/T 1800` |
| 机械GD&T | GB/T 1182/1184 | `<公差类型> 数值 GB/T 1184 <直径段>` |
| 机械焊接 | GB/T 324 | `角焊缝 焊脚尺寸 GB/T 324 <板厚>` |
| 机械粗糙度 | GB/T 131 | `表面粗糙度 Ra值 加工方法 GB/T 131` |
| 环保 | GB 50014 | `污水管道 最小坡度 DN<管径> GB 50014` |
| 土木配筋 | GB 50010 | `梁配筋率 保护层厚度 GB 50010 <截面>` |
| 土木抗震 | GB 50011 | `抗震等级 构造要求 GB 50011 <烈度>` |
| 钢结构 | GB 50017 | `螺栓间距 焊缝尺寸 GB 50017 <截面>` |
| 暖通风管 | GB 50736 | `风管 风速 比摩阻 GB 50736 <风量>` |
| 暖通水力 | GB 50243 | `风管水力计算 局部阻力系数` |
| 液压元件 | GB/T 786.1 | `液压<元件> 符号 GB/T 786.1` |
| 液压参数 | GB/T 8105 | `液压阀 额定流量 通径 <规格>` |
| 电气保护 | GB 50054 | `断路器 整定电流 电缆截面 GB 50054` |
| 电气线缆 | GB 50217 | `电缆载流量 截面选择 <功率>` |
| 给出配管 | GB 50015 | `给水管径 流量 流速 GB 50015` |
| 消防 | GB 50974 | `消火栓 流量 充实水柱 GB 50974` |
| P&ID仪表 | ISA S5.1 | `ISA S5.1 instrument symbol <功能>` |
| 工艺管道 | GB/T 2625 | `GB/T 2625 工艺流程图 符号` |

### 找不到时的操作流程

```
用户说"标注 φ50 H7/g6 配合公差"
    ↓
dim.py 有 lookup_fit(50, "H7/g6") → 直接用 ✓
    ↓
用户说"φ300 H8/e7 配合公差"
    ↓
dim.py 的 lookup_fit() 只到 φ500，范围内 → 直接用 ✓
    ↓
用户说"这个梁的配筋率是多少"
    ↓
rebar.py 零标准数据 → Agent 自动搜索 "GB 50010 梁 最小配筋率"
    ↓
搜索结果确认 0.2% → 传入 draw_beam_section()
    ↓
用户说"DN200 污水管最小坡度"
    ↓
pipe.py 无此数据 → Agent 搜索 "污水管道 DN200 最小坡度 GB 50014"
    ↓
搜索结果 0.004 → 传入绘图函数
```
