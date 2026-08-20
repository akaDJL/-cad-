# envcad — 跨行业国标工程制图集成插件

> CAD助手· 国标工程制图插件 · [示例 DXF](examples/) · [使用手册](USAGE.md)
>
> [![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
> [![python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)](https://www.python.org)
> [![pip](https://img.shields.io/badge/pip-install-9cf.svg)](https://pypi.org/project/envcad/)

集成两个 GitHub 开源项目，面向**建筑/土木/结构/机械/环保/电气/给排水/暖通/液压/化工及农业食品、电子半导体、能源化工、测绘GIS、桥梁、土壤修复、环境应急、环评等 16+ 行业**日常制图，输出符合
国标制图规范（GB/T 50001、GB/T 14689、GB/T 17450、GB 50141/50268）的 DXF 工程图。

## 集成的两个开源项目

| 开源项目 | 在本插件中的角色 | 集成方式 |
| --- | --- | --- |
| **text-to-cad** (`text-to-cad-main`) | 二维几何生成内核（ezdxf） | `envcad/engine/dxf_base.py` 复用其 `gen_dxf()` 模式，用 ezdxf 生成 DXF |
| **multiCAD-mcp** (`multiCAD-mcp`) | COM 桥接，把 DXF 推送到 AutoCAD/ZWCAD/GstarCAD/BricsCAD | `envcad/engine/multicad_bridge.py`，与 multiCAD-mcp 同源（Windows COM 自动化） |

## 支持行业（16+）

建筑 · 土木 · 结构 · 机械 · 环保 · 电气 · 给排水 · 暖通 · 液压 · 化工 ·
农业食品机械 · 电子半导体 · 能源化工 · 测绘 GIS · 桥梁 · 土壤修复 · 环境应急 · 环评

每个行业均内置材料库、规范表、设计验算（强度 / 工艺 / 达标判定）与文档自动化（DOCX 说明书 / XLSX 清单）。

## 架构

```
envcad/
├── standards/      制图规范库：A3图框/标题栏/图例/标高/管径/坡度/流向/国标图层/文字样式
├── components/     环保专业组件库：管道/管件(闸阀·软接头·流量计·套管)/池体(矩形·圆形,参数化)
├── knowledge/      知识层：材料库/规范表/理论/公式/行业数据（结构·土木·环保·机械·电气·给排水·暖通·液压·化工…）
├── design/         设计验算层：RC梁/地基/挡土墙/齿轮/轴/负荷/电缆/用水量/冷热负荷/除尘器…（19 模块）
├── docgen/         文档自动化层：各专业说明书 DOCX / 计算书 / 材料清单 XLSX（15 模块）
├── engine/         集成内核：dxf_base(text-to-cad) + multicad_bridge(COM桥接) + 批量/参数化
├── domains/        领域 YAML 配置（52 个，自动发现）
├── drawings/       验收测试图纸生成器 T1~T13，参数化、可迭代
├── cli.py          CLI 入口：envcad list|all|test|domain|batch|param|annotate|design|doc|equip
└── auto_registry.py  domains/*.yaml 零冲突自动注册
```

## 安装

```powershell
cd "凹凸cad小助手（二集）v1.5"   # 进入插件根目录
pip install -e .            # 核心（ezdxf）：绘图 / 标注 / 设计验算
pip install -e ".[cad]"     # + COM 桥接（pywin32，推送 AutoCAD/ZWCAD）
pip install -e ".[doc]"     # + 文档自动化（openpyxl + python-docx）→ 启用 envcad doc
pip install -e ".[all]"     # 全套：cad + doc
```

依赖：Python >=3.10、ezdxf>=1.3。`envcad doc`（DOCX 说明书 / XLSX 清单）需要 `[doc]` 额外依赖，
全新安装务必使用 `pip install -e ".[all]"` 或 `".[doc]"`，否则运行文档命令会报 `ModuleNotFoundError`。
本机已验证 Python 3.14.4 + ezdxf 1.4.4 + pywin32。

## 用法

```powershell
# 生成全部五个测试（11 张 DXF）到桌面 envcad-output/
envcad all

# 单个测试
envcad t1
envcad t4

# 指定输出目录与比例
envcad t2 --out D:\drawings --scale 50

# 生成后推送到 AutoCAD（COM 桥接）
envcad all --cad autocad
```

Python API：

```python
from envcad.drawings.t2_settler import gen_t2
gen_t2(r"D:\out")                      # -> D:\out\T2_竖流斜管沉淀池平剖面图.dxf

from envcad.components.pool import RectPoolParams   # 参数化池体
p = RectPoolParams(length=8000, width=6000, inlet_il=-0.800)
```

## 一键标注（annotate）

把散落的标注积木（自动尺寸链 / 管径·坡度·流向 / 标高 / 图例 / 施工说明 / 机械 GD&T）
串成**一条命令**，自动完成施工图标注。

```powershell
# 1) 内置演示底图（矩形水池 + 给/污水管）一键标注 -> out/annotate.dxf
envcad annotate --out out/annotate

# 2) 附加机械标注：焊接符号 / 表面粗糙度 / 形位公差
envcad annotate --out out/annotate --gdt

# 3) 标注单个 DXF（闭合轮廓→智能尺寸+标签；直线→端到端）
envcad annotate --in 你的图.dxf --out out/annotate

# 4) 批量标注整个目录（--in 指向目录，自动遍历所有 .dxf）
envcad annotate --in 图纸目录/ --out out/annotate

# 5) 递归子目录
envcad annotate --in 图纸目录/ --out out/annotate -r
```

**智能轮廓识别**：扫描 `LWPOLYLINE`（闭合→包围盒尺寸+中心标签）、
`LINE`（端到端尺寸），自动从图层名推断标签（如 `粗实线`→"池体N"、`墙体`→"墙体N"）；
图例/说明自动定位到图纸最右上方。`--in` 指向目录时批量处理所有 `.dxf`。

可选参数：

| 参数 | 说明 |
|------|------|
| `--in <path>` | 待标注 DXF 文件或**目录**；省略则生成演示底图 |
| `--out <dir>` | 输出目录（默认 `~/Desktop/envcad-output`） |
| `--scale 100` | 出图比例倒数（1:100 填 100，影响字高/偏移） |
| `--pipe <json>` | 管线语义数据：`[{x1,y1,x2,y2,dn,slope,flow,angle}]` |
| `--el <json>` | 标高数据：`[{x,y,value,side}]` |
| `--gdt` | 附加机械：焊接符号 / 粗糙度 / 形位公差 |
| `-r`, `--recursive` | 批目录时递归子目录 |
| `--ver R2018` | DXF 版本（R2010 / R2013 / R2018） |

> 图层约定：尺寸标注落在 `尺寸标注`/`文字` 等图层；`--in` 重标注时会跳过这些图层，
> 只对新几何（如 `粗实线`/`管道-*`）补标，避免实体无限膨胀。

Python API 等价于直接调用 `envcad.cli.main(["annotate", ...])`。

## 验收测试（T1~T13）

| # | 测试 | 验收点 | 结果 |
| --- | --- | --- | --- |
| 1 | 基础单元：DN300 铸铁污水管道标注 | 管径/管内底标高(±1.200/1.176)/0.4%坡度/流向箭头 | PASS |
| 2 | 单体构筑物：竖流斜管沉淀池平剖面 | D6m/总高5.5/污泥斗1.5/斜管1.2/DN300进水/DN150排泥/周边出水堰/A3·1:50/技术要求 | PASS |
| 3 | 工艺管线：污水自流管网平面布置 | DN350 HDPE/12m/0.3%/闸阀·软接头·流量计/穿墙刚性防水套管/图例 | PASS |
| 4 | 成套项目：50m³/d 生活污水处理站施工图 | 6张图(总平面/调节池/接触氧化池/沉淀池/工艺管道/设备材料表)+标题栏+图例+技术要求 | PASS |
| 5 | 边界容错：调节池参数迭代 | 第一步8×5×4/进水-0.500；第二步宽6m/进水-0.800/新增两布三油防腐 | PASS |
| 6 | 污水自流管网（新版） | 管网平面布置（DN350 HDPE/0.3%/节点标注） | PASS |
| 7 | 袋式除尘器 | 除尘器施工图（箱体/灰斗/脉冲阀/进出口） | PASS |
| 8 | UASB 厌氧反应器 | 反应器施工图（三相分离器/布水/出水） | PASS |
| 9 | 湿法脱硫塔 | 脱硫塔施工图（塔体/喷淋/除雾/进出口） | PASS |
| 10 | 活性炭吸附 | 吸附装置施工图（吸附罐/阀门/风机） | PASS |
| 11 | 钢烟囱 | 烟囱施工图（筒体/平台/爬梯/避雷） | PASS |
| 12 | 废气风管系统 | 风管平面/剖面（弯头/三通/支吊架） | PASS |
| 13 | 离心风机 | 风机安装图（机壳/叶轮/电机/基础） | PASS |

完整命令与领域速查见 [USAGE.md](USAGE.md)。

校验：`python tests/verify.py`（自动核对每张图的关键标注/图层/实体数）。

## 制图规范落实

- **图幅/图框**：A3 横式（420×297），装订边 25，内框 + 对中标志（GB/T 14689）
- **标题栏**：180×56 标准分格（图名/图号/比例/设计·校核·审核/单位/日期）（GB/T 50001）
- **图线**：粗0.5/中0.35/细0.18mm，实线·虚线·点画线·双点画线（GB/T 17450）
- **图层**：25 个国标图层（粗实线/管道-污水/池体-壁/标高/流向/图框…），颜色/线型/线宽合规
- **文字**：仿宋 GB2312（simfang.ttf），标注字高 3.5mm×比例
- **标注**：标高（等腰直角三角符号）、管径(DN)、坡度(i=%)、流向箭头、剖面剖切符号
- **比例**：1:1 实物坐标建模，图框按出图比例放大，出图 1:1 即得正确比例

## 知识层 · 设计验算 · 文档自动化（v1.5 深化）

把「数据 / 规范 / 理论」作为第一类公民沉淀进插件，对标天正、探索者的规范内置能力。

```
envcad/
├── knowledge/   知识层：材料库/规范表/理论/公式/用户订阅（结构·土木·环保·机械）
├── design/      设计验算层：RC梁·型钢·地基基础·挡土墙·污水除尘·齿轮·轴
└── docgen/      文档自动化层：各专业说明书DOCX / 计算书DOCX / 材料清单XLSX
```

知识库现含（按行业）：
- **结构**：混凝土 14 级、钢筋 6 种、直径 14 档、钢材 5 种、型钢 60 个、GB 规范 10 本
- **土木**：土层 15 类、承载力修正 8 组、公路 5 级、岩土/桥梁/道路规范 9 本
- **环保**：水/气/噪声/焚烧排放限值 + 曝气/沉淀/除尘工艺参数、环保规范 8 本
- **机械**：材料 10 种、标准模数 29 档、标准直径 28 档、螺纹 9 规格、机械规范 8 本
- **电气**：导线/载流量/需要系数/照度标准库，供配电与照明规范 7 本
- **给排水**：用水定额/卫生器具/管径/坡度库，建筑与市政给排水规范 6 本
- **暖通**：室内参数/负荷指标/换气次数/风管库，采暖通风与空调规范 6 本
- **液压**：油液/缸径/杆径/压力等级库，液压传动与系统规范 6 本
- **化工**：公称直径/壁厚等级/经济流速/介质物性/换热器 K 值库，化工工艺与管道规范 6 本

一键命令：

```powershell
# 生成《结构设计总说明》DOCX
envcad doc spec --out D:\out --project "阳泉某车间"

# 生成《结构计算书》DOCX（给定内力自动配筋验算）
envcad doc calc --out D:\out --b 250 --h 500 --conc C30 --rebar HRB400 \
                 --m 120 --v 180 --l 6000

# 生成《材料表》XLSX（钢筋 + 型钢全库）
envcad doc bom --out D:\out

# 结构验算（打印配筋结论，可同时出计算书与配筋图 DXF）
envcad design rc-beam --b 250 --h 500 --m 120 --v 180 --l 6000 --calc --dxf D:\out\beam.dxf
```

按行业一键出文档 / 验算：

```powershell
# 土木：地基基础 + 挡土墙设计说明；独立基础 / 挡土墙稳定验算
envcad doc geotech --out D:\out --project "阳泉厂房" --fk 1200 --soil 粉质粘土 --wallh 4.5
envcad design foundation --fk 1500 --soil 粉质粘土 --depth 1.5
envcad design retaining  --wallh 5           # 回填默认中砂

# 环保：工艺设计说明书 + 排放达标清单；污水 / 除尘工艺验算
envcad doc env      --out D:\out --project "阳泉污水厂" --q 10000 --so 200 --se 10 --std 一级A
envcad doc env-bom  --out D:\out --std 一级A
envcad design wwtp  --q 20000 --so 200 --se 10
envcad design dust  --air 60000 --dust-kind baghouse

# 机械：设计计算说明书 + 零件明细表；齿轮 / 轴强度校核
envcad doc mech      --out D:\out --project "减速器" --power 5 --rpm 960 --z1 20 --z2 60 --mat 40Cr
envcad doc mech-bom  --out D:\out
envcad design gear   --power 7.5 --rpm 1000 --z1 20 --z2 60 --mat 40Cr
envcad design shaft  --power 7.5 --rpm 1000
```

Python API：

```python
from envcad.knowledge import materials, codes
from envcad.design.rc_beam import design_rc_beam
from envcad.docgen.spec_doc import generate_structure_spec

r = design_rc_beam(250, 500, 20, "C30", "HRB400", M=120e6, V=180e3, l=6000)
generate_structure_spec("说明.docx", project="XX 工程")   # 自动引用知识层数据
```

### 新增 5 行业（电气 / 给排水 / 暖通 / 液压 / 化工）

知识层（`envcad/knowledge/elec_data.py` 等 5 模块）+ 设计验算层（`envcad/design/` 对应 5 模块）
+ 文档自动化层（`envcad/docgen/` 对应 5 模块），与既有行业同一套三层架构。

一键出文档（10 类，DOCX 说明书 + XLSX 清单）：

```powershell
# 电气：设计说明书 + 负荷计算表
envcad doc elec      --out D:\out --project "阳泉配电" --pe 100 --use 办公照明 --length 50 --area 800 --place 办公室
envcad doc elec-bom  --out D:\out

# 给排水：设计说明书 + 用水量计算表
envcad doc plumb     --out D:\out --project "阳泉给排水" --people 500 --wkind 办公楼 --ng 100 --lift 20
envcad doc plumb-bom --out D:\out

# 暖通：设计说明书 + 分区负荷设备表
envcad doc hvac      --out D:\out --project "阳泉空调" --area 800 --height 3 --people 80 --place 办公室
envcad doc hvac-bom  --out D:\out

# 液压：系统设计计算书 + 元件清单
envcad doc hyd       --out D:\out --project "阳泉液压站" --force 50 --pressure 16 --speed 0.1
envcad doc hyd-bom   --out D:\out

# 化工：工艺设计说明书 + 设备管道清单
envcad doc proc      --out D:\out --project "阳泉化工" --flow 30 --head 32 --duty 500 --medium 水_一般
envcad doc proc-bom  --out D:\out
```

一键验算（12 类 kind）：

```powershell
envcad design load      --pe 100 --use 办公照明 --length 50   # 负荷+电缆选型
envcad design cable     --pe 135        # 计算电流 → 截面
envcad design illum     --area 800 --place 办公室             # 照度
envcad design water     --people 500 --wkind 办公楼           # 最高日用水量
envcad design supply    --ng 100                              # 给水管径
envcad design drain     --np 80                               # 排水管径+坡度
envcad design cooling   --area 800 --height 3 --place 办公室  # 冷热负荷+送风
envcad design duct      --area 800 --height 3 --place 办公室  # 风管尺寸
envcad design cylinder  --force 50 --pressure 16 --speed 0.1  # 液压缸
envcad design pump      --force 50 --pressure 16 --speed 0.1  # 液压泵+管路
envcad design pipe      --flow 30 --medium 水_一般            # 经济管径
envcad design hx        --duty 500                            # 换热器面积
```

Python API：

```python
from envcad.design.electrical import design_power_load, select_cable
from envcad.docgen.elec_doc import generate_elec_spec, generate_load_xlsx

load  = design_power_load(100, kind="办公照明")
cable = select_cable(load["Ijs"], cos=load["cos"], length=50)
generate_elec_spec("电气设计说明书.docx", project="阳泉配电",
                   load=load, cable=cable,
                   illum=design_illumination(800, place="办公室"),
                   sc=estimate_short_circuit(630))
generate_load_xlsx("负荷计算表.xlsx")   # 规范附录式负荷计算表
```

测试：`python -m pytest tests/test_new_industries.py -q`（5 行业 知识/设计/文档 + CLI 全绿）。


用户自有 / 订阅数据接入：在 `envcad/knowledge/user_data.py` 的 `USER_SUBSCRIPTION` 字典追加，
或在 `envcad/knowledge/user_subscription.json` 放一份 JSON，运行时自动合并，绘图/设计/文档三处共用。
