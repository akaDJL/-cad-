# CAD助手v1.5 envcad — 环保全领域制图使用说明

## 一、版本更新概览

v1.5 在原有6个领域基础上新增4个领域模块 + 1个非标兜底模块，实现环保行业全领域覆盖。

### 领域清单（11个领域 / 52个绘图函数）

| 领域 | 模块文件 | 函数数 | 覆盖范围 |
|------|---------|--------|---------|
| solid_waste | solid_waste.py | 8 | 填埋、焚烧、堆肥、厌氧消化、分选、转运 |
| soil_remediation | soil_remediation.py | 6 | 注入井、抽提、热脱附、SVE、截污墙 |
| physical_pollution | physical_pollution.py | 6 | 电磁辐射、放射性、光污染、振动 |
| emergency | emergency.py | 5 | 风险源、扩散、疏散、设施、响应流程 |
| water_treatment | treatment.py | 6 | 曝气池、污泥、加药、格栅、膜、消毒 |
| advanced_wtp | advanced_wtp.py | 6 | A2O、SBR、人工湿地、渗滤液、除臭、管道 |
| air_pollution | apc.py | 5 | 集气罩、旋风、布袋、工艺流程、CEMS |
| environmental | environmental.py | 2 | 监测点、工艺框图 |
| ecology | eco.py | 1 | 噪声等值线 |
| eia | eia.py | 1 | 敏感目标 |
| custom | custom.py | 6 | 非标轮廓、组件、装配、标注、引出线 |

---

## 二、命令行使用

### 1. 查看所有可用领域

```bash
cd C:\Users\lenovo\Desktop\凹凸cad小助手（二集）v1.5
python -m envcad.cli list
```

### 2. 单张出图（按领域+函数）

```bash
python -m envcad.cli domain solid_waste --function landfill_section --out D:\输出目录
python -m envcad.cli domain soil_remediation --function injection_well_grid --out D:\输出目录
python -m envcad.cli domain emergency --function risk_dispersion --out D:\输出目录
```

不指定 --function 时列出该领域所有可用函数。

### 3. 批量出图（JSON配置）

```bash
python -m envcad.cli batch --config batch_example.json --out D:\批量输出
```

> 内置示例 `batch_example.json` 位于 `envcad/` 包内。`--config` 若只写文件名（不含路径），
> 会自动回退到包目录查找，因此可从任意目录直接运行上面的命令。

### 4. 生成后自动推送到 CAD

```bash
python -m envcad.cli batch --config batch_example.json --out D:\输出 --cad autocad
python -m envcad.cli domain solid_waste --function landfill_section --out D:\输出 --cad zwcad
```

支持的 CAD：autocad / zwcad / gstarcad / bricscad

### 5. 运行验收测试

```bash
python -m envcad.cli test all --out D:\测试输出
python -m envcad.cli test t1 --out D:\测试输出
```

---

## 三、批量出图 JSON 配置格式

### 文件结构

```json
[
  {
    "domain": "领域名",
    "function": "函数别名",
    "params": {
      "参数1": "值1",
      "参数2": "值2",
      "label": "图纸标题",
      "params": { "工程参数键值对" }
    },
    "filename": "输出文件名.dxf",
    "scale": 100
  }
]
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| domain | 是 | 领域名，如 solid_waste |
| function | 是 | 函数别名，如 landfill_section |
| params | 否 | 绘图参数（几何尺寸、类型、标注等） |
| params.label | 否 | 图纸标题文字 |
| params.params | 否 | 工程参数标注（容量、流量、温度等） |
| filename | 否 | 输出文件名，默认 domain_function_N.dxf |
| scale | 否 | 出图比例，默认 100 |

### 完整示例

```json
[
  {
    "domain": "solid_waste",
    "function": "landfill_section",
    "params": {
      "length": 60,
      "depth": 15,
      "base_width": 25,
      "liner_type": "composite",
      "label": "卫生填埋场剖面图",
      "params": {
        "capacity": "80万m³",
        "area": "6万m²",
        "leachate": "150m³/d"
      }
    },
    "filename": "01_填埋场剖面图.dxf",
    "scale": 100
  },
  {
    "domain": "soil_remediation",
    "function": "injection_well_grid",
    "params": {
      "n_rows": 3,
      "n_cols": 5,
      "spacing": 5.0,
      "oxidant": "persulfate",
      "label": "原位化学氧化注入井网"
    },
    "filename": "02_注入井网.dxf",
    "scale": 100
  },
  {
    "domain": "emergency",
    "function": "risk_dispersion",
    "params": {
      "substance_type": "gas",
      "wind_dir": "E",
      "wind_speed": 3.0,
      "label": "事故风险扩散范围图",
      "params": {
        "substance": "氯气",
        "leak_rate": "5kg/s"
      }
    },
    "filename": "03_风险扩散.dxf",
    "scale": 100
  }
]
```

运行：
```bash
python -m envcad.cli batch --config my_project.json --out D:\项目图纸
```

---

## 四、各领域函数速查

### solid_waste（固废处理）

| 别名 | 函数 | 关键参数 |
|------|------|---------|
| landfill_section | draw_landfill_section | length, depth, base_width, liner_type |
| leachate_collection | draw_leachate_collection | pipe_dia, slope, spacing |
| incinerator_flow | draw_incinerator_flow | f_type(grate/fluidized) |
| incinerator_section | draw_incinerator_section | capacity, temp |
| composting | draw_composting | type(aerobic/anaerobic) |
| anaerobic_digester | draw_anaerobic_digester | volume, temp |
| sorting_line | draw_sorting_line | capacity |
| transfer_station | draw_transfer_station | capacity |

### soil_remediation（土壤修复）

| 别名 | 函数 | 关键参数 |
|------|------|---------|
| injection_well_grid | draw_injection_well_grid | n_rows, n_cols, spacing, oxidant |
| injection_profile | draw_injection_profile | depth, radius |
| pump_treat_flow | draw_pump_treat_flow | wells, flow |
| thermal_desorption | draw_thermal_desorption | temp, capacity |
| sve_system | draw_sve_system | radius, depth |
| cutoff_wall | draw_cutoff_wall | wall_type, depth |

### physical_pollution（物理污染防治）

| 别名 | 函数 | 关键参数 |
|------|------|---------|
| emf_contour | draw_emf_contour | source_type, levels |
| emf_monitoring_network | draw_emf_monitoring_network | n_points, radius |
| radiation_zone | draw_radiation_zone | source_type, zones |
| radiation_shielding | draw_radiation_shielding | wall_type, thickness |
| light_pollution_zone | draw_light_pollution_zone | zone_type, levels |
| vibration_contour | draw_vibration_contour | source_type, levels |

### emergency（环境应急）

| 别名 | 函数 | 关键参数 |
|------|------|---------|
| risk_source_map | draw_risk_source_map | sources, area |
| risk_dispersion | draw_risk_dispersion | substance_type, wind_dir, wind_speed |
| evacuation_route | draw_evacuation_route | routes |
| emergency_facilities | draw_emergency_facilities | facilities |
| emergency_response_flow | draw_emergency_response_flow | — |

### custom（非标兜底）

| 别名 | 函数 | 关键参数 |
|------|------|---------|
| outline | draw_outline | points, layer |
| spline_outline | draw_spline_outline | points, layer |
| custom_component | draw_custom_component | shapes |
| custom_assembly | draw_custom_assembly | components |
| custom_dimension | draw_custom_dimension | p1, p2 |
| leader_note | draw_leader_note | target, text |

---

## 五、三层兜底策略

当标准模块无法覆盖时，按以下顺序降级：

1. **模块函数匹配** — 在11个领域中查找匹配的绘图函数
2. **跨模块组合** — 用 process_box / monitoring_point 等通用函数组合拼接
3. **非标几何基元** — 使用 custom 模块从点、线、弧自由构建任意形状

示例：某个异形反应器没有对应标准函数
```json
{
  "domain": "custom",
  "function": "custom_component",
  "params": {
    "shapes": [
      {"type": "rect", "x": 0, "y": 0, "w": 200, "h": 100},
      {"type": "circle", "cx": 100, "cy": 50, "r": 30},
      {"type": "line", "x1": 0, "y1": 0, "x2": 200, "y2": 100}
    ],
    "label": "定制反应器"
  },
  "filename": "定制反应器.dxf"
}
```

---

## 六、Python API 直接调用

```python
import sys
sys.path.insert(0, r"C:\Users\lenovo\Desktop\凹凸cad小助手（二集）v1.5")

from envcad.engine.dxf_base import new_drawing, save_dxf
from envcad.standards.solid_waste import draw_landfill_section

# 创建图纸
doc, dim_style, tracker = new_drawing(100, return_tracker=True)
msp = doc.modelspace()

# 绘制
draw_landfill_section(
    msp, (5000, 5000),
    length=60, depth=15, base_width=25,
    liner_type="composite",
    scale=100,
    label="卫生填埋场剖面图",
    params={"capacity": "80万m³", "leachate": "150m³/d"}
)

# 保存
save_dxf(doc, r"D:\输出\填埋场.dxf")
```

---

## 七、文件结构

```
凹凸cad小助手（二集）v1.5/
├── envcad/
│   ├── __init__.py              # 包入口（v1.5）
│   ├── cli.py                   # 命令行（list/batch/domain/test）
│   ├── batch_example.json       # 批量出图示例配置
│   ├── utils.py
│   ├── engine/
│   │   ├── dxf_base.py          # DXF引擎内核
│   │   ├── multicad_bridge.py   # CAD COM桥接
│   │   ├── batch_layout.py      # 批量布局
│   │   └── collision_fix.py     # 碰撞修正
│   ├── standards/
│   │   ├── __init__.py          # 领域注册（11个模块）
│   │   ├── solid_waste.py       # ★ 固废处理（8函数）
│   │   ├── soil_remediation.py  # ★ 土壤修复（6函数）
│   │   ├── physical_pollution.py # ★ 物理污染（6函数）
│   │   ├── emergency.py         # ★ 环境应急（5函数）
│   │   ├── treatment.py         # 水处理（6函数）
│   │   ├── advanced_wtp.py      # 高级水处理（6函数）
│   │   ├── apc.py               # 废气治理（5函数）
│   │   ├── environmental.py     # 环境通用（2函数）
│   │   ├── eco.py               # 生态环境（1函数）
│   │   ├── eia.py               # 环评（1函数）
│   │   ├── custom.py            # ★ 非标兜底（6函数）
│   │   ├── layers.py            # 国标图层
│   │   ├── styles.py            # 文字样式
│   │   ├── frame.py             # 图框标题栏
│   │   ├── annotate.py          # 标注
│   │   └── legend.py            # 图例
│   ├── drawings/                # 验收测试图
│   └── components/              # 参数化组件库
└── USAGE.md                     # 本文件
```

★ = v1.5 领域模块
