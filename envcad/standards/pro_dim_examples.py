# -*- coding: utf-8 -*-
"""
专业标注工具 - 各行业使用示例

展示如何在建筑、机械、环保、暖通等行业中使用 ProDim 工具

用法：
    from envcad.standards.pro_dim import ProDim, auto_scale
    
    pd = ProDim(msp, scale=20)
    pd.linear_dim(...)
    pd.elevation(...)
    pd.leader(...)
    pd.rebar_number(...)
    pd.break_line(...)
    pd.axis_number(...)
    pd.hatch_concrete(...)
    pd.hatch_soil(...)
    pd.draw_frame_a3v()
    pd.draw_title_block(...)
"""
from __future__ import annotations

import ezdxf
from pathlib import Path


def example_building_foundation():
    """
    【建筑/土木行业】独立基础施工图示例
    
    使用：
    - 专业尺寸标注（带箭头）
    - 标高符号
    - 钢筋编号
    - 引出标注
    - 混凝土/素土填充
    - 折断线
    - 轴线编号
    - 标题栏
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # 初始化专业标注工具
    from envcad.standards.pro_dim import ProDim, auto_scale
    
    # 自动计算比例
    actual_w = 2800  # 实际宽度 mm
    actual_h = 3000  # 实际高度 mm
    scale, scale_text = auto_scale(actual_w, actual_h * 2)  # 双视图
    
    pd = ProDim(msp, scale=scale)
    
    # 绘制A3竖向图框
    FW, FH, M = pd.draw_frame_a3v()
    
    # 绘制标题栏
    pd.draw_title_block(
        FW, FH, M,
        title1='独立基础施工图',
        title2='矩形柱下独立基础',
        spec='2400×1800',
        standard='GB/T 50001',
        scale_text=scale_text,
        discipline='土木建筑',
        date='2026.08.02'
    )
    
    # 简单示意：画一个基础剖面
    s = lambda mm: mm / scale
    sx, sy = 100, 120
    
    # 基础轮廓
    msp.add_lwpolyline([
        (sx, sy), (sx+s(2400), sy),
        (sx+s(2400), sy+s(600)), (sx, sy+s(600)),
        (sx, sy)
    ], dxfattribs={'layer': '粗实线', 'closed': True})
    
    # 混凝土填充
    pd.hatch_reinforced_concrete(sx, sy, sx+s(2400), sy+s(600))
    
    # 垫层
    msp.add_lwpolyline([
        (sx-s(100), sy-s(100)), (sx+s(2400)+s(100), sy-s(100)),
        (sx+s(2400)+s(100), sy), (sx-s(100), sy),
        (sx-s(100), sy-s(100))
    ], dxfattribs={'layer': '细实线', 'closed': True})
    pd.hatch_concrete(sx-s(100), sy-s(100), sx+s(2400)+s(100), sy,
                      layer='混凝土填充')
    
    # 素土
    pd.hatch_soil(sx-s(150), sy-s(200), sx+s(2400)+s(150), sy-s(100))
    
    # 尺寸标注（带箭头）
    pd.linear_dim((sx, sy), (sx+s(2400), sy), -8, '2400')
    pd.linear_dim((sx+s(2400), sy), (sx+s(2400), sy+s(600)), 8, '600')
    
    # 标高
    pd.elevation(sx+s(2400)+20, sy+s(600), '-0.600')
    
    # 钢筋编号
    pd.rebar_number(sx-8, sy+s(40), 1)
    
    # 引出标注
    pd.leader(sx+s(1200), sy+s(300),
              sx+s(1200)+15, sy+s(300)+10,
              'C30 混凝土', side='right')
    
    # 折断线
    pd.break_line(sx+s(1200), sy+s(600), width=s(400))
    
    # 轴线编号
    pd.axis_number(sx+s(1200), sy+s(650), '1')
    
    return doc


def example_mechanical_shaft():
    """
    【机械行业】轴类零件标注示例
    
    使用：
    - 尺寸标注（带箭头）
    - 金属剖面填充
    - 引出标注
    - 折断线
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    from envcad.standards.pro_dim import ProDim, auto_scale
    
    scale = 5  # 1:5
    pd = ProDim(msp, scale=scale)
    
    FW, FH, M = pd.draw_frame_a3v()
    
    pd.draw_title_block(
        FW, FH, M,
        title1='传动轴零件图',
        title2='主动轴',
        spec='Φ50×200',
        standard='GB/T 4458',
        scale_text='1:5',
        discipline='机械制造',
        date='2026.08.02'
    )
    
    s = lambda mm: mm / scale
    sx, sy = 80, 150
    
    # 轴轮廓
    msp.add_lwpolyline([
        (sx, sy-s(25)), (sx+s(50), sy-s(25)),
        (sx+s(50), sy-s(20)), (sx+s(150), sy-s(20)),
        (sx+s(150), sy-s(25)), (sx+s(200), sy-s(25)),
        (sx+s(200), sy+s(25)), (sx+s(150), sy+s(25)),
        (sx+s(150), sy+s(20)), (sx+s(50), sy+s(20)),
        (sx+s(50), sy+s(25)), (sx, sy+s(25)),
        (sx, sy-s(25))
    ], dxfattribs={'layer': '粗实线', 'closed': True})
    
    # 金属填充（剖面）
    pd.hatch_metal(sx+s(50), sy-s(20), sx+s(150), sy+s(20))
    
    # 尺寸标注
    pd.linear_dim((sx, sy-s(30)), (sx+s(200), sy-s(30)), -8, '200')
    pd.linear_dim((sx+s(200)+8, sy-s(25)), (sx+s(200)+8, sy+s(25)), 8, 'Φ50')
    
    # 引出标注（倒角）
    pd.leader(sx+s(50), sy-s(22),
              sx+s(30), sy-s(35),
              'C2', side='left')
    
    # 折断线
    pd.break_line(sx+s(100), sy-s(25), width=s(30))
    pd.break_line(sx+s(100), sy+s(25), width=s(30))
    
    return doc


def example_hvac_duct():
    """
    【暖通行业】风管标注示例
    
    使用：
    - 尺寸标注
    - 标高符号
    - 引出标注
    - 中心线
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    from envcad.standards.pro_dim import ProDim, auto_scale
    
    scale = 50  # 1:50
    pd = ProDim(msp, scale=scale)
    
    FW, FH, M = pd.draw_frame_a3v()
    
    pd.draw_title_block(
        FW, FH, M,
        title1='通风系统图',
        title2='送风主管',
        spec='800×400',
        standard='GB/T 50114',
        scale_text='1:50',
        discipline='暖通空调',
        date='2026.08.02'
    )
    
    s = lambda mm: mm / scale
    sx, sy = 100, 150
    
    # 风管轮廓
    msp.add_lwpolyline([
        (sx, sy-s(200)), (sx+s(3000), sy-s(200)),
        (sx+s(3000), sy+s(200)), (sx, sy+s(200)),
        (sx, sy-s(200))
    ], dxfattribs={'layer': '粗实线', 'closed': True})
    
    # 中心线
    msp.add_line((sx-20, sy), (sx+s(3000)+20, sy),
                 dxfattribs={'layer': '中心线'})
    
    # 尺寸标注
    pd.linear_dim((sx, sy-s(220)), (sx+s(3000), sy-s(220)), -8, '3000')
    pd.linear_dim((sx+s(3000)+8, sy-s(200)), (sx+s(3000)+8, sy+s(200)), 8, '400')
    
    # 标高
    pd.elevation(sx+s(1500), sy+s(200), '+3.500', direction='up')
    
    # 引出标注
    pd.leader(sx+s(1500), sy,
              sx+s(1500)+15, sy+15,
              '800×400 镀锌钢板', side='right')
    
    return doc


def example_env_tank():
    """
    【环保行业】沉淀池标注示例
    
    使用：
    - 尺寸标注
    - 标高符号
    - 混凝土填充
    - 引出标注
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    from envcad.standards.pro_dim import ProDim, auto_scale
    
    scale = 100  # 1:100
    pd = ProDim(msp, scale=scale)
    
    FW, FH, M = pd.draw_frame_a3v()
    
    pd.draw_title_block(
        FW, FH, M,
        title1='沉淀池施工图',
        title2='平流式沉淀池',
        spec='10000×5000',
        standard='GB/T 50106',
        scale_text='1:100',
        discipline='环保工程',
        date='2026.08.02'
    )
    
    s = lambda mm: mm / scale
    sx, sy = 80, 150
    
    # 池体轮廓
    msp.add_lwpolyline([
        (sx, sy), (sx+s(10000), sy),
        (sx+s(10000), sy+s(3500)), (sx, sy+s(3500)),
        (sx, sy)
    ], dxfattribs={'layer': '粗实线', 'closed': True})
    
    # 混凝土填充（池壁）
    wall_t = s(250)
    pd.hatch_concrete(sx, sy, sx+wall_t, sy+s(3500))
    pd.hatch_concrete(sx+s(10000)-wall_t, sy, sx+s(10000), sy+s(3500))
    pd.hatch_concrete(sx, sy, sx+s(10000), sy+wall_t)
    
    # 尺寸标注
    pd.linear_dim((sx, sy-s(300)), (sx+s(10000), sy-s(300)), -8, '10000')
    pd.linear_dim((sx+s(10000)+8, sy), (sx+s(10000)+8, sy+s(3500)), 8, '3500')
    
    # 水位标高
    pd.elevation(sx+s(5000), sy+s(3200), '+0.000', direction='up')
    
    # 引出标注
    pd.leader(sx+s(5000), sy+wall_t,
              sx+s(5000)+15, sy+wall_t+10,
              'C30 钢筋混凝土', side='right')
    
    return doc


# ============================================================
# 测试运行
# ============================================================
if __name__ == '__main__':
    out_dir = Path(r'C:\Users\lenovo\Desktop\envcad-output\pro_dim_examples')
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("生成各行业专业标注示例...")
    
    # 1. 建筑基础
    doc1 = example_building_foundation()
    path1 = out_dir / '示例1_建筑基础.dxf'
    doc1.saveas(str(path1))
    print(f"  [OK] 建筑基础示例: {path1}")
    
    # 2. 机械轴
    doc2 = example_mechanical_shaft()
    path2 = out_dir / '示例2_机械轴.dxf'
    doc2.saveas(str(path2))
    print(f"  [OK] 机械轴示例: {path2}")
    
    # 3. 暖通风管
    doc3 = example_hvac_duct()
    path3 = out_dir / '示例3_暖通风管.dxf'
    doc3.saveas(str(path3))
    print(f"  [OK] 暖通风管示例: {path3}")
    
    # 4. 环保沉淀池
    doc4 = example_env_tank()
    path4 = out_dir / '示例4_环保沉淀池.dxf'
    doc4.saveas(str(path4))
    print(f"  [OK] 环保沉淀池示例: {path4}")
    
    print(f"\n全部示例生成完成！输出目录: {out_dir}")
