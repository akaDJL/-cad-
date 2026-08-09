# 专业标注工具库 (pro_dim) 使用说明

## 概述

`pro_dim` 是一个通用的专业标注工具库，为建筑、机械、环保、暖通、电气等各行业提供标准化的标注功能。

**核心功能**：
- ✅ 尺寸标注（带箭头、尺寸界线）
- ✅ 标高符号（倒三角形）
- ✅ 引出标注（带引线、圆点）
- ✅ 钢筋编号（圆圈数字）
- ✅ 折断线（锯齿形）
- ✅ 轴线编号（圆圈内字母/数字）
- ✅ 材质填充（混凝土、素土、金属、钢筋混凝土）
- ✅ 标准图框（A3竖向）
- ✅ 标准化标题栏（右下角）
- ✅ 自动比例计算
- ✅ 中文图层命名

---

## 快速开始

```python
from envcad.standards.pro_dim import ProDim, auto_scale
import ezdxf

doc = ezdxf.new('R2010')
msp = doc.modelspace()

# 自动计算比例
scale, scale_text = auto_scale(actual_width=2800, actual_height=3000)

# 初始化专业标注工具
pd = ProDim(msp, scale=scale)

# 绘制图框
FW, FH, M = pd.draw_frame_a3v()

# 绘制标题栏
pd.draw_title_block(
    FW, FH, M,
    title1='工程名称',
    title2='图纸名称',
    spec='规格',
    standard='GB/T 50001',
    scale_text=scale_text,
    discipline='专业名称',
    date='2026.08.02'
)

# ... 绘制你的图形 ...

# 添加专业标注
pd.linear_dim((x1, y1), (x2, y2), offset=-8, text='2400')
pd.elevation(x, y, '-0.600')
pd.leader(x1, y1, x2, y2, 'Φ16@200')
pd.rebar_number(x, y, 1)
pd.break_line(x, y, width=20)
pd.axis_number(x, y, 'A')
pd.hatch_concrete(x1, y1, x2, y2)
pd.hatch_soil(x1, y1, x2, y2)
```

---

## API 参考

### 1. 尺寸标注

```python
pd.linear_dim(p1, p2, offset, text, layer='尺寸线')
```

**参数**：
- `p1, p2`: 两个测量点 `(x, y)`
- `offset`: 尺寸线偏移距离（正向外，负向内）
- `text`: 尺寸文字
- `layer`: 图层名（默认"尺寸线"）

**示例**：
```python
# 水平标注（尺寸线在下方）
pd.linear_dim((0, 0), (100, 0), offset=-8, text='100')

# 垂直标注（尺寸线在右侧）
pd.linear_dim((100, 0), (100, 50), offset=8, text='50')
```

---

### 2. 标高符号

```python
pd.elevation(x, y, text, direction='down', layer='标注符号')
```

**参数**：
- `x, y`: 标高符号顶点位置
- `text`: 标高数值（如 `'-0.600'`, `'+3.500'`）
- `direction`: `'down'` 倒三角（向下指），`'up'` 正三角

**示例**：
```python
pd.elevation(100, 50, '-0.600')      # 向下指
pd.elevation(100, 200, '+3.500', direction='up')  # 向上指
```

---

### 3. 引出标注

```python
pd.leader(start_x, start_y, end_x, end_y, text, side='right', layer='标注符号')
```

**参数**：
- `start_x, start_y`: 引出点（圆点位置）
- `end_x, end_y`: 文字端引线端点
- `text`: 标注文字
- `side`: 文字位置 `'right'` / `'left'` / `'above'` / `'below'`

**示例**：
```python
pd.leader(50, 30, 30, 10, 'C30 混凝土', side='left')
```

---

### 4. 钢筋编号

```python
pd.rebar_number(x, y, number, layer='标注符号')
```

**参数**：
- `x, y`: 圆心位置
- `number`: 编号数字（1, 2, 3...）

**示例**：
```python
pd.rebar_number(80, 50, 1)  # ①号筋
pd.rebar_number(80, 70, 2)  # ②号筋
```

---

### 5. 折断线

```python
pd.break_line(x, y, width=10, direction='horizontal', layer='细实线')
```

**参数**：
- `x, y`: 中心点
- `width`: 总宽度/高度
- `direction`: `'horizontal'` 或 `'vertical'`

**示例**：
```python
pd.break_line(100, 50, width=30)  # 水平折断线
pd.break_line(50, 100, width=30, direction='vertical')  # 垂直折断线
```

---

### 6. 轴线编号

```python
pd.axis_number(x, y, number, layer='细实线')
```

**参数**：
- `x, y`: 圆心位置
- `number`: 编号（如 `'A'`, `'1'`, `'B'`）

**示例**：
```python
pd.axis_number(100, 200, 'A')
pd.axis_number(200, 100, '1')
```

---

### 7. 材质填充

#### 混凝土填充（45度斜线）
```python
pd.hatch_concrete(x1, y1, x2, y2, angle=45, spacing=8, layer='混凝土填充')
```

#### 素土填充（小点）
```python
pd.hatch_soil(x1, y1, x2, y2, density=20, layer='素土填充')
```

#### 钢筋混凝土填充（斜线 + 骨料点）
```python
pd.hatch_reinforced_concrete(x1, y1, x2, y2)
```

#### 金属填充（交叉斜线）
```python
pd.hatch_metal(x1, y1, x2, y2, spacing=5, layer='金属填充')
```

---

### 8. 图框与标题栏

#### A3竖向图框
```python
FW, FH, M = pd.draw_frame_a3v(margin=10)
# 返回: 图框宽度, 图框高度, 边距
```

#### 右下角标题栏
```python
pd.draw_title_block(
    fw, fh, margin,
    title1='工程名称',      # 第一行（大标题）
    title2='图纸名称',      # 第二行
    spec='规格',            # 规格/尺寸
    standard='GB/T 50001',  # 标准号
    scale_text='1:20',      # 比例
    discipline='专业',      # 专业名称
    date='2026.08.02'       # 日期
)
```

---

### 9. 自动比例计算

```python
from envcad.standards.pro_dim import auto_scale

scale, scale_text = auto_scale(
    actual_width=2800,      # 实际图形宽度 (mm)
    actual_height=3000,     # 实际图形高度 (mm)
    frame_width=420,        # 图框宽度 (绘图单位 mm)
    frame_height=297,       # 图框高度 (绘图单位 mm)
    margin=25,              # 预留边距
    title_bar_w=130,        # 标题栏宽度（右侧预留）
    title_bar_h=60          # 标题栏高度（底部预留）
)
# 返回: (20, '1:20')
```

**标准比例系列**：1, 2, 5, 10, 20, 25, 50, 100, 150, 200...

---

## 各行业使用示例

### 🏗️ 建筑/土木行业

```python
from envcad.standards.pro_dim import ProDim

pd = ProDim(msp, scale=20)

# 混凝土填充
pd.hatch_reinforced_concrete(x1, y1, x2, y2)

# 素土填充
pd.hatch_soil(x1, y1, x2, y2)

# 标高
pd.elevation(x, y, '-0.600')

# 钢筋编号
pd.rebar_number(x, y, 1)

# 轴线编号
pd.axis_number(x, y, 'A')
```

### ⚙️ 机械行业

```python
from envcad.standards.pro_dim import ProDim

pd = ProDim(msp, scale=5)

# 金属剖面填充
pd.hatch_metal(x1, y1, x2, y2)

# 折断线
pd.break_line(x, y, width=20)

# 引出标注（倒角、粗糙度等）
pd.leader(x1, y1, x2, y2, 'C2', side='left')
```

### 🌬️ 暖通行业

```python
from envcad.standards.pro_dim import ProDim

pd = ProDim(msp, scale=50)

# 风管尺寸
pd.linear_dim((x1,y), (x2,y), -8, '800')

# 标高
pd.elevation(x, y, '+3.500', direction='up')

# 引出标注（材质、规格）
pd.leader(x, y, x+15, y+10, '镀锌钢板 δ=1.2', side='right')
```

### 🌿 环保行业

```python
from envcad.standards.pro_dim import ProDim

pd = ProDim(msp, scale=100)

# 混凝土池壁
pd.hatch_concrete(x1, y1, x2, y2)

# 水位标高
pd.elevation(x, y, '+0.000', direction='up')

# 池体尺寸
pd.linear_dim((x1,y1), (x2,y1), -10, '10000')
```

### ⚡ 电气行业

```python
from envcad.standards.pro_dim import ProDim

pd = ProDim(msp, scale=50)

# 尺寸标注
pd.linear_dim((x1,y1), (x2,y1), -8, '2000')

# 引出标注（设备型号）
pd.leader(x, y, x+15, y+10, '配电柜 G-01', side='right')
```

### 💧 给排水行业

```python
from envcad.standards.pro_dim import ProDim

pd = ProDim(msp, scale=50)

# 管道标高
pd.elevation(x, y, '-0.800')

# 管径标注
pd.leader(x, y, x+15, y+10, 'DN100', side='right')
```

---

## 图层标准（中文）

| 图层名 | 颜色 | 线宽 | 用途 |
|--------|------|------|------|
| 粗实线 | 红 (1) | 50 | 可见轮廓 |
| 细实线 | 白 (7) | 18 | 尺寸、标注 |
| 中心线 | 绿 (3) | 18 | 轴线、对称线 |
| 虚线 | 蓝 (4) | 18 | 不可见结构 |
| 尺寸线 | 黄 (2) | 18 | 尺寸标注 |
| 文字 | 白 (7) | 18 | 文字 |
| 钢筋 | 红 (1) | 35 | 钢筋 |
| 标注符号 | 黄 (2) | 18 | 标高、引出线等 |
| 混凝土填充 | 灰 (9) | 13 | 混凝土剖面 |
| 素土填充 | 灰 (8) | 13 | 素土/地基 |
| 钢筋混凝土 | 洋红 (6) | 13 | 钢筋混凝土 |
| 金属填充 | 蓝 (5) | 13 | 金属剖面 |

---

## 遵循标准

- GB/T 50001-2017 《房屋建筑制图统一标准》
- GB/T 50105-2010 《建筑结构制图标准》
- GB/T 4458.4-2003 《机械制图 尺寸注法》
- GB/T 50114-2010 《暖通空调制图标准》
- GB/T 50106-2010 《建筑给水排水制图标准》

---

## 文件位置

- 模块文件：`envcad/standards/pro_dim.py`
- 示例文件：`envcad/standards/pro_dim_examples.py`
- 示例输出：`envcad-output/pro_dim_examples/`

---

## 版本历史

- **v1.0** (2026-08-02)
  - 初始版本
  - 支持尺寸标注、标高、引出标注、钢筋编号、折断线、轴线编号
  - 支持混凝土、素土、钢筋混凝土、金属填充
  - 支持A3竖向图框和标准化标题栏
  - 支持自动比例计算
  - 全中文图层和标注
