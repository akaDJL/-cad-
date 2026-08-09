# -*- coding: utf-8 -*-
"""
专业标注工具库 v1.0
提供建筑/结构/机械等各行业通用的专业标注功能

包含：
- 尺寸标注（带箭头、尺寸界线）
- 标高符号（倒三角）
- 引出标注（带引线、圆点）
- 钢筋编号（圆圈数字）
- 折断线
- 轴线编号
- 材质填充（混凝土、素土、金属等）
- 图层标准（中文图层名）

用法：
    from envcad.standards.pro_dim import ProDim
    pd = ProDim(msp, scale=20)
    pd.linear_dim((x1,y1), (x2,y2), offset=-8, text='2400')
    pd.elevation(x, y, '-0.600')
    pd.leader(x1, y1, x2, y2, 'Φ16@200')
    pd.rebar_number(x, y, 1)
    pd.break_line(x, y, width=20)
    pd.axis_number(x, y, 'A')
    pd.hatch_concrete(x1,y1,x2,y2)
    pd.hatch_soil(x1,y1,x2,y2)
"""
from __future__ import annotations

import math
from typing import Tuple, Optional


class ProDim:
    """专业标注工具类"""
    
    def __init__(self, msp, scale: float = 20, text_style: str = '宋体'):
        """
        初始化专业标注工具
        
        参数:
            msp: ezdxf ModelSpace 对象
            scale: 绘图比例分母（如20表示1:20）
            text_style: 文字样式名
        """
        self.msp = msp
        self.scale = scale
        self.text_style = text_style
        self._arrow_size = 1.5  # 绘图单位
        self._text_height = 2.5
        self._setup_layers()
    
    def _setup_layers(self):
        """确保图层存在"""
        layers = self.msp.doc.layers
        layer_defs = [
            ('粗实线', 1, 50, 'CONTINUOUS'),
            ('细实线', 7, 18, 'CONTINUOUS'),
            ('中心线', 3, 18, 'CENTER'),
            ('虚线', 4, 18, 'DASHED'),
            ('尺寸线', 2, 18, 'CONTINUOUS'),
            ('文字', 7, 18, 'CONTINUOUS'),
            ('钢筋', 1, 35, 'CONTINUOUS'),
            ('标注符号', 2, 18, 'CONTINUOUS'),
            ('混凝土填充', 9, 13, 'CONTINUOUS'),
            ('素土填充', 8, 13, 'CONTINUOUS'),
            ('钢筋混凝土', 6, 13, 'CONTINUOUS'),
            ('金属填充', 5, 13, 'CONTINUOUS'),
        ]
        for name, color, lweight, ltype in layer_defs:
            if name not in layers:
                layers.add(name, color=color, lineweight=lweight, linetype=ltype)
    
    # ============================================================
    # 尺寸标注
    # ============================================================
    
    def linear_dim(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                   offset: float, text: str, 
                   layer: str = '尺寸线', text_layer: str = '文字'):
        """
        线性尺寸标注（带箭头、尺寸界线）
        
        参数:
            p1, p2: 两个测量点 (x, y)
            offset: 尺寸线偏移距离（正向外，负向内）
            text: 尺寸文字
        """
        x1, y1 = p1
        x2, y2 = p2
        
        is_horizontal = abs(y2 - y1) < abs(x2 - x1)
        
        if is_horizontal:
            dim_y = y1 + offset
            # 尺寸线
            self.msp.add_line((x1, dim_y), (x2, dim_y), dxfattribs={'layer': layer})
            # 尺寸界线
            ext = 2 if offset > 0 else -2
            self.msp.add_line((x1, y1), (x1, dim_y + ext), dxfattribs={'layer': layer})
            self.msp.add_line((x2, y2), (x2, dim_y + ext), dxfattribs={'layer': layer})
            # 箭头
            self._arrow(x1, dim_y, 'left' if offset > 0 else 'right', layer)
            self._arrow(x2, dim_y, 'right' if offset > 0 else 'left', layer)
            # 文字
            text_y = dim_y + (2 if offset > 0 else -4)
            self.msp.add_text(text, 
                dxfattribs={'height': self._text_height, 'layer': text_layer, 'style': self.text_style}
            ).set_placement(((x1+x2)/2 - len(text)*0.8, text_y))
        else:
            dim_x = x1 + offset
            # 尺寸线
            self.msp.add_line((dim_x, y1), (dim_x, y2), dxfattribs={'layer': layer})
            # 尺寸界线
            ext = 2 if offset > 0 else -2
            self.msp.add_line((x1, y1), (dim_x + ext, y1), dxfattribs={'layer': layer})
            self.msp.add_line((x2, y2), (dim_x + ext, y2), dxfattribs={'layer': layer})
            # 箭头
            self._arrow(dim_x, y1, 'down' if offset > 0 else 'up', layer)
            self._arrow(dim_x, y2, 'up' if offset > 0 else 'down', layer)
            # 文字
            text_x = dim_x + (2 if offset > 0 else -8)
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': text_layer, 'style': self.text_style}
            ).set_placement((text_x, (y1+y2)/2))
    
    def _arrow(self, x: float, y: float, direction: str, layer: str):
        """绘制实心箭头"""
        s = self._arrow_size
        if direction == 'right':
            pts = [(x, y), (x-s, y-s*0.3), (x-s, y+s*0.3), (x, y)]
        elif direction == 'left':
            pts = [(x, y), (x+s, y-s*0.3), (x+s, y+s*0.3), (x, y)]
        elif direction == 'up':
            pts = [(x, y), (x-s*0.3, y-s), (x+s*0.3, y-s), (x, y)]
        elif direction == 'down':
            pts = [(x, y), (x-s*0.3, y+s), (x+s*0.3, y+s), (x, y)]
        else:
            return
        self.msp.add_solid(pts, dxfattribs={'layer': layer})
    
    # ============================================================
    # 标高符号
    # ============================================================
    
    def elevation(self, x: float, y: float, text: str, 
                  direction: str = 'down', layer: str = '标注符号'):
        """
        绘制标高符号（倒三角形）
        
        参数:
            x, y: 标高符号顶点位置
            text: 标高数值（如 '-0.600'）
            direction: 'down' 倒三角（向下指），'up' 正三角
        """
        size = 3
        if direction == 'down':
            pts = [(x, y), (x-size, y-size), (x+size, y-size), (x, y)]
            self.msp.add_solid(pts, dxfattribs={'layer': layer})
            self.msp.add_line((x+size, y-size), (x+size+15, y-size),
                             dxfattribs={'layer': layer})
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': '文字', 'style': self.text_style}
            ).set_placement((x+size+2, y-size+1))
        else:
            pts = [(x, y), (x-size, y+size), (x+size, y+size), (x, y)]
            self.msp.add_solid(pts, dxfattribs={'layer': layer})
            self.msp.add_line((x+size, y+size), (x+size+15, y+size),
                             dxfattribs={'layer': layer})
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': '文字', 'style': self.text_style}
            ).set_placement((x+size+2, y+size+1))
    
    # ============================================================
    # 引出标注
    # ============================================================
    
    def leader(self, start_x: float, start_y: float, 
               end_x: float, end_y: float, text: str,
               side: str = 'right', layer: str = '标注符号'):
        """
        绘制引出标注（带引线、圆点）
        
        参数:
            start_x, start_y: 引出点（圆点位置）
            end_x, end_y: 文字端引线端点
            text: 标注文字
            side: 文字在引线的哪一侧 'right'/'left'/'above'/'below'
        """
        # 引线
        self.msp.add_line((start_x, start_y), (end_x, end_y), 
                         dxfattribs={'layer': layer})
        # 起始圆点
        self.msp.add_circle((start_x, start_y), radius=0.8,
                           dxfattribs={'layer': layer})
        # 文字
        if side == 'right':
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': '文字', 'style': self.text_style}
            ).set_placement((end_x + 1, end_y - 1))
        elif side == 'left':
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': '文字', 'style': self.text_style}
            ).set_placement((end_x - len(text)*1.5 - 1, end_y - 1))
        elif side == 'above':
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': '文字', 'style': self.text_style}
            ).set_placement((end_x - len(text)*0.8, end_y + 2))
        else:  # below
            self.msp.add_text(text,
                dxfattribs={'height': self._text_height, 'layer': '文字', 'style': self.text_style}
            ).set_placement((end_x - len(text)*0.8, end_y - 4))
    
    # ============================================================
    # 钢筋编号
    # ============================================================
    
    def rebar_number(self, x: float, y: float, number: int,
                     layer: str = '标注符号'):
        """
        绘制钢筋编号（圆圈内数字）
        
        参数:
            x, y: 圆心位置
            number: 编号数字（1,2,3...）
        """
        radius = 2.5
        self.msp.add_circle((x, y), radius=radius, dxfattribs={'layer': layer})
        self.msp.add_text(str(number),
            dxfattribs={'height': 2.5, 'layer': '文字', 'style': self.text_style}
        ).set_placement((x - 0.8, y - 1))
    
    # ============================================================
    # 折断线
    # ============================================================
    
    def break_line(self, x: float, y: float, width: float = 10,
                   direction: str = 'horizontal', layer: str = '细实线'):
        """
        绘制折断线（锯齿形）
        
        参数:
            x, y: 中心点
            width: 总宽度/高度
            direction: 'horizontal' 或 'vertical'
        """
        if direction == 'horizontal':
            pts = []
            n_zig = 4
            seg = width / n_zig
            for i in range(n_zig + 1):
                px = x - width/2 + i * seg
                py = y + (1 if i % 2 == 0 else -1) * 1.5
                pts.append((px, py))
            self.msp.add_lwpolyline(pts, dxfattribs={'layer': layer})
        else:
            pts = []
            n_zig = 4
            seg = width / n_zig
            for i in range(n_zig + 1):
                py = y - width/2 + i * seg
                px = x + (1 if i % 2 == 0 else -1) * 1.5
                pts.append((px, py))
            self.msp.add_lwpolyline(pts, dxfattribs={'layer': layer})
    
    # ============================================================
    # 轴线编号
    # ============================================================
    
    def axis_number(self, x: float, y: float, number: str,
                    layer: str = '细实线'):
        """
        绘制轴线编号（圆圈内字母/数字）
        
        参数:
            x, y: 圆心位置
            number: 编号（如 'A', '1', 'B'）
        """
        radius = 2.5
        self.msp.add_circle((x, y), radius=radius, dxfattribs={'layer': layer})
        self.msp.add_text(number,
            dxfattribs={'height': 2.5, 'layer': '文字', 'style': self.text_style}
        ).set_placement((x - 0.8, y - 1))
    
    # ============================================================
    # 材质填充
    # ============================================================
    
    def hatch_concrete(self, x1: float, y1: float, x2: float, y2: float,
                       angle: float = 45, spacing: float = 8,
                       layer: str = '混凝土填充'):
        """
        混凝土填充（45度斜线）
        
        参数:
            x1,y1: 左下角
            x2,y2: 右上角
            angle: 斜线角度（度）
            spacing: 斜线间距
        """
        rad = math.radians(angle)
        dx = spacing / math.cos(rad)
        dy = spacing / math.sin(rad) if math.sin(rad) != 0 else 0
        
        w = x2 - x1
        h = y2 - y1
        
        # 计算需要多少条线
        n_lines = int((w + h) / spacing) + 2
        
        for i in range(-n_lines, n_lines):
            # 斜线起点（从左下角外开始）
            sx = x1 + i * dx
            sy = y1
            # 斜线终点
            ex = sx + h / math.tan(rad) if math.tan(rad) != 0 else sx
            ey = y2
            
            # 裁剪到矩形内
            # 简化：只画完全在范围内的
            if sx >= x1 and ex <= x2:
                self.msp.add_line((sx, sy), (ex, ey), dxfattribs={'layer': layer})
    
    def hatch_soil(self, x1: float, y1: float, x2: float, y2: float,
                   density: int = 20, layer: str = '素土填充'):
        """
        素土填充（随机小点）
        
        参数:
            x1,y1: 左下角
            x2,y2: 右上角
            density: 点的数量（近似）
        """
        import random
        random.seed(42)  # 固定种子，保证可重复
        
        w = x2 - x1
        h = y2 - y1
        area = w * h
        n_dots = int(area * density / 100)
        
        for _ in range(n_dots):
            rx = x1 + random.random() * w
            ry = y1 + random.random() * h
            self.msp.add_circle((rx, ry), radius=0.4,
                               dxfattribs={'layer': layer})
    
    def hatch_reinforced_concrete(self, x1: float, y1: float, 
                                   x2: float, y2: float,
                                   layer_concrete: str = '混凝土填充',
                                   layer_aggregate: str = '钢筋混凝土'):
        """
        钢筋混凝土填充（斜线 + 骨料点）
        
        参数:
            x1,y1: 左下角
            x2,y2: 右上角
        """
        # 先画混凝土斜线
        self.hatch_concrete(x1, y1, x2, y2, layer=layer_concrete)
        
        # 再画骨料点（较少）
        import random
        random.seed(123)
        w = x2 - x1
        h = y2 - y1
        n_dots = int(w * h / 50)
        
        for _ in range(n_dots):
            rx = x1 + random.random() * w
            ry = y1 + random.random() * h
            self.msp.add_circle((rx, ry), radius=0.6,
                               dxfattribs={'layer': layer_aggregate})
    
    def hatch_metal(self, x1: float, y1: float, x2: float, y2: float,
                    spacing: float = 5, layer: str = '金属填充'):
        """
        金属剖面填充（双向斜线，交叉）
        
        参数:
            x1,y1: 左下角
            x2,y2: 右上角
        """
        # 正向45度
        self.hatch_concrete(x1, y1, x2, y2, angle=45, spacing=spacing, layer=layer)
        # 反向45度
        self.hatch_concrete(x1, y1, x2, y2, angle=135, spacing=spacing, layer=layer)
    
    # ============================================================
    # 图框
    # ============================================================
    
    def draw_frame_a3v(self, margin: float = 10):
        """
        绘制A3竖向图框（420x297）
        
        返回: (frame_width, frame_height, margin)
        """
        FW, FH = 420, 297
        # 外框
        self.msp.add_lwpolyline(
            [(0,0),(FW,0),(FW,FH),(0,FH),(0,0)],
            dxfattribs={'layer': '粗实线', 'closed': True}
        )
        # 内框
        self.msp.add_lwpolyline(
            [(margin,margin),(FW-margin,margin),
             (FW-margin,FH-margin),(margin,FH-margin),(margin,margin)],
            dxfattribs={'layer': '细实线', 'closed': True}
        )
        return FW, FH, margin
    
    def draw_title_block(self, fw: float, fh: float, margin: float = 10,
                         title1: str = '工程名称',
                         title2: str = '图纸名称',
                         spec: str = '规格',
                         standard: str = 'GB/T 50001',
                         scale_text: str = '1:20',
                         discipline: str = '专业',
                         date: str = '2026.08.02'):
        """
        绘制右下角标题栏（120x50）
        
        参数:
            fw, fh: 图框宽高
            margin: 边距
            title1: 第一行标题（工程名称）
            title2: 第二行标题（图纸名称）
            spec: 规格
            standard: 标准号
            scale_text: 比例
            discipline: 专业
            date: 日期
        """
        TW, TH = 120, 50
        TL_x_right = fw - margin
        TL_x_left = TL_x_right - TW
        TL_y_bottom = margin
        TL_y_top = TL_y_bottom + TH
        
        # 外框
        self.msp.add_lwpolyline([
            (TL_x_left, TL_y_bottom),
            (TL_x_right, TL_y_bottom),
            (TL_x_right, TL_y_top),
            (TL_x_left, TL_y_top),
            (TL_x_left, TL_y_bottom)
        ], dxfattribs={'layer': '标题栏', 'lineweight': 50, 'closed': True})
        
        # 分格线
        for h in [10, 20, 30, 40]:
            self.msp.add_line(
                (TL_x_left, TL_y_bottom + h),
                (TL_x_right, TL_y_bottom + h),
                dxfattribs={'layer': '细实线'}
            )
        
        col_split = 65
        self.msp.add_line(
            (TL_x_left + col_split, TL_y_bottom),
            (TL_x_left + col_split, TL_y_top),
            dxfattribs={'layer': '细实线'}
        )
        
        # 文字
        self.msp.add_text(title1,
            dxfattribs={'height': 4, 'layer': '标题栏', 'style': '黑体'}
        ).set_placement((TL_x_left + 3, TL_y_bottom + 42))
        
        self.msp.add_text(title2,
            dxfattribs={'height': 4, 'layer': '标题栏', 'style': '黑体'}
        ).set_placement((TL_x_left + 3, TL_y_bottom + 32))
        
        self.msp.add_text(spec,
            dxfattribs={'height': 3, 'layer': '文字', 'style': self.text_style}
        ).set_placement((TL_x_left + col_split + 3, TL_y_bottom + 42))
        
        self.msp.add_text(standard,
            dxfattribs={'height': 3, 'layer': '文字', 'style': self.text_style}
        ).set_placement((TL_x_left + col_split + 3, TL_y_bottom + 32))
        
        self.msp.add_text(scale_text,
            dxfattribs={'height': 2.5, 'layer': '文字', 'style': self.text_style}
        ).set_placement((TL_x_left + col_split + 3, TL_y_bottom + 22))
        
        self.msp.add_text(discipline,
            dxfattribs={'height': 2.5, 'layer': '文字', 'style': self.text_style}
        ).set_placement((TL_x_left + col_split + 3, TL_y_bottom + 12))
        
        self.msp.add_text(f'日期 {date}',
            dxfattribs={'height': 2.5, 'layer': '文字', 'style': self.text_style}
        ).set_placement((TL_x_left + 3, TL_y_bottom + 3))
        
        return TL_x_left, TL_y_bottom, TW, TH


# ============================================================
# 便捷函数：自动计算比例
# ============================================================

def auto_scale(actual_width: float, actual_height: float,
               frame_width: float = 420, frame_height: float = 297,
               margin: float = 25, title_bar_w: float = 130,
               title_bar_h: float = 60) -> Tuple[int, str]:
    """
    自动计算合理的绘图比例
    
    参数:
        actual_width: 实际图形宽度 (mm)
        actual_height: 实际图形高度 (mm)
        frame_width: 图框宽度 (绘图单位 mm)
        frame_height: 图框高度 (绘图单位 mm)
        margin: 预留边距
        title_bar_w: 标题栏宽度（右侧预留）
        title_bar_h: 标题栏高度（底部预留）
    
    返回:
        (scale_denominator, scale_text)
        例如 (20, '1:20')
    """
    avail_w = frame_width - 2 * margin - title_bar_w
    avail_h = frame_height - 2 * margin - title_bar_h
    
    scale = max(actual_width / avail_w, actual_height / avail_h)
    
    # 标准比例系列
    standard = [1, 2, 5, 10, 20, 25, 50, 100, 150, 200]
    for s in standard:
        if s >= scale:
            scale = s
            break
    
    if scale > 200:
        scale = math.ceil(scale / 10) * 10
    
    return int(scale), f"1:{int(scale)}"
