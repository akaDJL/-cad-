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

envcad 是**跨行业工程制图** CAD 插件。基于 ezdxf 生成符合国标的 DXF 工程图，
覆盖 16+ 行业（建筑/土木/结构/桥梁/基础/机械/环保/电气/给排水/暖通/液压/P&ID/农业食品/电子半导体/能源化工/测绘GIS），
含 GD&T 形位公差、焊接符号、表面粗糙度、BOM、剖切符号、钢筋表、图纸模板、修订标记等标准标注模块，
并可通过 COM 桥接把图纸推送到 AutoCAD / ZWCAD（仅 Windows）。

**许可证：MIT**（干净，无 GPL-3.0 传染性条款）。

代码只负责绘图框架：**所有行业标准数值（配筋率/风速/压力/坡度/偏差等）由调用方/智能体搜索后显式传入绘图函数**，不得猜测或用默认值替代。

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

> 本技能目录即仓库根目录。运行命令时请先 `cd` 到该目录（或把仓库根加入 `PYTHONPATH`）。

## Usage — CLI

```bash
# 列出所有领域模块与可用函数
python -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','list']; from envcad.cli import main; main()"

# 领域快捷出图（<domain> 见下方清单，--out 指定输出目录）
python -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','domain','structural','--function','steel_frame','--out','./out']; from envcad.cli import main; main()"

# 五大验收测试（T1 污水管标注 / T2 沉淀池 / T3 管网 / T4 50m³/d 污水厂 / T5 调节池迭代）
python -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','t1']; from envcad.cli import main; main()"
# t2..t5 同理

# 生成后校验（检查图层/标注/实体数）
python tests/verify.py ./out

# 推送到 CAD（需 Windows + 已装对应软件 + pywin32）
python -c "import sys; sys.path.insert(0,'.'); sys.argv=['envcad','all','--cad','autocad']; from envcad.cli import main; main()"
# 支持 autocad / zwcad / gstarcad / bricscad
```

若已 `pip install -e .`，上述 `python -c "..."` 可直接替换为 `envcad <args>`。

## Usage — Python API

```python
from envcad.engine.dxf_base import new_drawing, save_dxf
from envcad.standards.frame import add_a3_frame, add_title_block

doc, dim_name = new_drawing(scale=100)
msp = doc.modelspace()
# ... 用 envcad.standards.* 下的 draw_xxx() 添加几何/标注 ...
add_a3_frame(doc, scale=100)
add_title_block(doc, name="图名", drawing_no="编号", scale="1:100")
save_dxf(doc, r"path/to/output.dxf")
```

常用标准模块（均在 `envcad.standards` 下）：

- 基础：`layers`（22 层国标图层）、`styles`（仿宋样式）、`frame`（图框标题栏）、`annotate`（标高/坡度/管径）、`legend`（图例）
- 标注 v1.3：`gdt`（形位公差）、`symbols`（焊接/粗糙度）、`bom`（材料表）、`views`（剖切/局部放大）、`dim`（尺寸/配合公差）
- 土木/结构 v1.4–v1.5：`rebar`、`building`、`structural`、`bridge`、`foundation`、`hvac`、`hydraulic`
- 电气/给排水/P&ID v1.5：`electrical`、`plumbing`、`pid`
- 高级 v1.6：`dimensions`（坐标/角度/链式标注）、`notes`（技术说明）、`templates`（A0–A4 标题栏）、`markup`（修订云线）
- 环保行业（CLI 领域）：`activated_carbon` `advanced_wtp` `air_pollution` `baghouse` `baf` `daf` `eco` `eia` `emergency` `energy_chemical` `esp` `fgd` `hazwaste` `mbr` `noise_control` `oxidation_ditch` `rto` `scr` `sludge_dewatered` `soil_remediation` `solid_waste` `spray_tower` `uasb` `wesp` 等

## 行业标准搜索策略（关键）

**代码只画框架，行业数值必须显式传入。** 凡模块中没有、不确定、或只覆盖部分范围的行业数据，调用方应自动联网搜索后传入，不得猜测：

- 国家标准全文公开系统 `site:openstd.samr.gov.cn`（最权威）
- 搜狗微信 / 知乎 / 百度文库（工程实践参考）

示例：标注 `φ50 H7/g6` 配合公差——`dim.lookup_fit(50,"H7/g6")` 有则直接用；`rebar` 的配筋率等无内置数据时必须先搜 GB 50010 再传入。

## CAD 推送说明

`--cad` 推送依赖 Windows + 已安装 AutoCAD/ZWCAD/GstarCAD/Bricscad + `pywin32`。
非 Windows 环境只能生成 DXF 文件，无法推送桌面 CAD 软件，属正常限制。

## License

MIT。详见仓库 `LICENSE` 文件。
