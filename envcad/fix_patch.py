"""
envcad 修复补丁 v1.5
修复三大核心问题：
1. 线型失效（虚线/中心线变实线）
2. 字体重合（碰撞检测失效）
3. 文字出框（边界检查缺失）

使用方法：在 envcad 初始化后调用 apply_fixes(doc)
    from envcad.fix_patch import apply_fixes
    apply_fixes(doc)
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

from ezdxf.enums import TextEntityAlignment


# ══════════════════════════════════════════════════════════
#  修复1：线型系统 - 确保非连续线型正确加载和应用
# ══════════════════════════════════════════════════════════

# 修复后的线型定义（更精确的 dash-gap 序列）
LINETYPE_DEFS_FIXED = {
    "DASHED":  ([2.5, -1.0], "__ __ __"),
    "CENTER":  ([6.0, -1.2, 0.6, -1.2], "____ . ____"),
    "PHANTOM": ([6.0, -1.0, 0.5, -1.0, 0.5, -1.0], "____ . ____ . ____"),
}


def _ensure_linetype_fixed(doc, name: str) -> None:
    """修复版：确保线型正确加载，使用 has_entry() 检查。"""
    if name == "CONTINUOUS":
        return
    
    # 正确检查线型是否存在
    if name in doc.linetypes:
        return
    
    if name not in LINETYPE_DEFS_FIXED:
        return
    
    pattern, desc = LINETYPE_DEFS_FIXED[name]
    try:
        # ezdxf 1.0+ API
        doc.linetypes.add(name, pattern, desc)
    except Exception as _e:
        try:
            doc.linetypes.add(name, pattern=pattern, description=desc)
        except Exception as _e:
            # 最终兜底：尝试 DXF12 格式
            try:
                doc.linetypes.add(name, [2.0, -1.0], desc)
            except Exception as _e:
                print(f'[WARNING] fix_patch.py: {_e}')


def setup_layers_fixed(doc) -> None:
    """修复版：正确创建图层并应用线型。"""
    # 先确保所有非连续线型存在
    for lt in ("DASHED", "CENTER", "PHANTOM"):
        _ensure_linetype_fixed(doc, lt)
    
    # 应用图层定义
    from .standards.layers import LAYER_DEFS
    
    for name, color, ltype, lw in LAYER_DEFS:
        if name in doc.layers:
            continue
        try:
            layer = doc.layers.add(name)
            layer.dxf.color = color
            
            # 修复：正确验证线型可用性
            if ltype == "CONTINUOUS":
                layer.dxf.linetype = "CONTINUOUS"
            else:
                # 检查线型是否真正可用
                if ltype in doc.linetypes:
                    layer.dxf.linetype = ltype
                else:
                    # 尝试强制添加
                    _ensure_linetype_fixed(doc, ltype)
                    if ltype in doc.linetypes:
                        layer.dxf.linetype = ltype
                    else:
                        layer.dxf.linetype = "CONTINUOUS"
            
            layer.dxf.lineweight = lw
        except Exception as _e:
            print(f'[WARNING] fix_patch.py: {_e}')


# ══════════════════════════════════════════════════════════
#  修复2：改进的文字宽度估算 - 更精确
# ══════════════════════════════════════════════════════════

def estimate_text_width_fixed(text: str, height: float) -> float:
    """修复版：更精确的文字宽度估算。
    
    实际测试表明中文约为字高×0.85，ASCII约为字高×0.5。
    加入安全系数1.1以防止估算偏小。
    """
    w = 0.0
    for ch in str(text):
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f':
            w += height * 0.85  # 中文/全角
        elif ord(ch) > 127:
            w += height * 0.85  # 全角符号
        else:
            w += height * 0.50  # ASCII/半角
    return w * 1.1  # 安全系数


# ══════════════════════════════════════════════════════════
#  修复3：智能文字放置 - 带边界检查的碰撞避让
# ══════════════════════════════════════════════════════════

class SmartTextPlacer:
    """智能文字放置器：带边界约束的碰撞避让。
    
    使用方法：
        placer = SmartTextPlacer(tracker, frame_bbox=(x0, y0, x1, y1), scale=100)
        placer.place(msp, text, position, height, align=...)
    """
    
    def __init__(self, tracker=None, frame_bbox: Tuple = None, scale: float = 1.0):
        self.tracker = tracker
        self.frame_bbox = frame_bbox  # (x0, y0, x1, y1) 图框内框范围
        self.scale = scale
        self.margin = 5.0 * scale  # 距图框边安全距离
    
    def _within_frame(self, x: float, y: float, w: float, h: float) -> bool:
        """检查位置是否在图框内。"""
        if self.frame_bbox is None:
            return True
        fx0, fy0, fx1, fy1 = self.frame_bbox
        return (fx0 + self.margin <= x - w/2 and 
                x + w/2 <= fx1 - self.margin and
                fy0 + self.margin <= y - h/2 and 
                y + h/2 <= fy1 - self.margin)
    
    def _get_safe_positions(self, px: float, py: float, 
                            text_w: float, text_h: float,
                            align) -> list:
        """生成候选位置列表（优先级排序）。"""
        positions = []
        
        # 原位置
        positions.append((px, py, 0))
        
        # 尝试多个方向
        step = text_h * 1.2
        directions = [
            (0, 1, "up"),      # 上
            (0, -1, "down"),   # 下
            (1, 0, "right"),   # 右
            (-1, 0, "left"),   # 左
            (1, 1, "up-right"),
            (-1, 1, "up-left"),
            (1, -1, "down-right"),
            (-1, -1, "down-left"),
        ]
        
        for i in range(1, 6):  # 最多5步
            for dx, dy, name in directions:
                nx, ny = px + dx * step * i, py + dy * step * i
                positions.append((nx, ny, i))
        
        return positions
    
    def place(self, msp, content: str, point: Tuple[float, float],
              height: float, align=TextEntityAlignment.LEFT,
              layer: str = "文字", rotation: float = 0) -> Optional:
        """放置文字，带碰撞检测和边界约束。"""
        if not content:
            return None
        
        px, py = point
        
        # 估算文字尺寸
        text_w = estimate_text_width_fixed(str(content), height)
        text_h = height * 1.6  # 行高含充足留白
        
        # 计算包围盒
        if align in (TextEntityAlignment.MIDDLE_CENTER,):
            bbox = (px - text_w/2, py - text_h/2, px + text_w/2, py + text_h/2)
        elif align in (TextEntityAlignment.MIDDLE_LEFT, TextEntityAlignment.LEFT):
            bbox = (px, py - text_h/2, px + text_w, py + text_h/2)
        else:
            bbox = (px - text_w/2, py - text_h/2, px + text_w/2, py + text_h/2)
        
        # 如果有 tracker，尝试找到合适位置
        final_pos = (px, py)
        
        if self.tracker is not None:
            # 检查原位置是否可用
            if self.tracker.is_occupied(*bbox) or not self._within_frame(px, py, text_w, text_h):
                # 搜索合适位置
                candidates = self._get_safe_positions(px, py, text_w, text_h, align)
                found = False
                
                for nx, ny, priority in candidates:
                    # 计算新包围盒
                    if align in (TextEntityAlignment.MIDDLE_CENTER,):
                        nbbox = (nx - text_w/2, ny - text_h/2, nx + text_w/2, ny + text_h/2)
                    elif align in (TextEntityAlignment.MIDDLE_LEFT, TextEntityAlignment.LEFT):
                        nbbox = (nx, ny - text_h/2, nx + text_w, ny + text_h/2)
                    else:
                        nbbox = (nx - text_w/2, ny - text_h/2, nx + text_w/2, ny + text_h/2)
                    
                    # 检查碰撞和边界
                    if (not self.tracker.is_occupied(*nbbox) and 
                        self._within_frame(nx, ny, text_w, text_h)):
                        final_pos = (nx, ny)
                        bbox = nbbox
                        found = True
                        break
                
                # 如果找不到完全合适的位置，使用最小偏移
                if not found:
                    # 尝试最小步长微调
                    for dy in [text_h, -text_h, text_h*0.8, -text_h*0.8, text_h*0.5, -text_h*0.5]:
                        nx, ny = px, py + dy
                        if self._within_frame(nx, ny, text_w, text_h):
                            if align in (TextEntityAlignment.MIDDLE_CENTER,):
                                nbbox = (nx - text_w/2, ny - text_h/2, nx + text_w/2, ny + text_h/2)
                            elif align in (TextEntityAlignment.MIDDLE_LEFT, TextEntityAlignment.LEFT):
                                nbbox = (nx, ny - text_h/2, nx + text_w, ny + text_h/2)
                            else:
                                nbbox = (nx - text_w/2, ny - text_h/2, nx + text_w/2, ny + text_h/2)
                            
                            if not self.tracker.is_occupied(*nbbox):
                                final_pos = (nx, ny)
                                bbox = nbbox
                                found = True
                                break
        
        # 注册最终位置
        if self.tracker is not None:
            self.tracker.register(*bbox, margin=height * 0.8)
        
        # 绘制文字
        t = msp.add_text(str(content), dxfattribs={
            "layer": layer, "height": height, "style": "HZ"})
        t.set_placement(final_pos, align=align)
        if rotation:
            t.dxf.rotation = rotation
        
        return t


# ══════════════════════════════════════════════════════════
#  统一应用所有修复
# ══════════════════════════════════════════════════════════

def apply_fixes(doc, frame_bbox: Tuple = None, scale: float = 1.0):
    """应用所有修复到文档。
    
    Args:
        doc: ezdxf Drawing 文档对象
        frame_bbox: 图框内框坐标 (x0, y0, x1, y1)
        scale: 出图比例倒数
    """
    # 修复1：重新初始化图层系统
    setup_layers_fixed(doc)
    
    # 修复2：返回智能放置器供后续使用
    from .engine.dxf_base import BBoxTracker
    tracker = BBoxTracker(padding=300)  # 增大默认 padding
    
    placer = SmartTextPlacer(tracker=tracker, frame_bbox=frame_bbox, scale=scale)
    
    return tracker, placer


def get_fixed_placer(tracker, frame_bbox=None, scale=1.0) -> SmartTextPlacer:
    """获取修复版文字放置器。"""
    return SmartTextPlacer(tracker=tracker, frame_bbox=frame_bbox, scale=scale)