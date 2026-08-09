"""废气治理与除尘制图 v1.0（HJ 2000、GB 16297、HJ/T 75）。

集气罩、风管、旋风除尘、布袋除尘器详图、治理流程、在线监测站房。
纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

def draw_hood(msp, center, h_type="canopy", width=1.0, scale=100.0,
              label="", params=None, layer="集气罩", tracker=None):
    """集气罩/吸风罩。h_type: canopy/slot/enclosure/push_pull"""
    s=scale; cx,cy=_r(*center); w=width*s; hh=w*0.6
    if h_type=="canopy":
        msp.add_line((cx-w/2,cy+hh),(cx,cy),dxfattribs={"layer":layer})
        msp.add_line((cx,cy),(cx+w/2,cy+hh),dxfattribs={"layer":layer})
        msp.add_line((cx,cy+hh*0.3),(cx,cy+hh+3*s),dxfattribs={"layer":layer})
    elif h_type=="slot":
        r=w*0.3; msp.add_arc((cx,cy+r),radius=r,start_angle=180,end_angle=360,dxfattribs={"layer":layer})
        msp.add_line((cx-r,cy+r),(cx-r,cy-r*0.5),dxfattribs={"layer":layer})
        msp.add_line((cx+r,cy+r),(cx+r,cy-r*0.5),dxfattribs={"layer":layer})
        msp.add_line((cx,cy+r*2),(cx,cy+r*2+3*s),dxfattribs={"layer":layer})
    elif h_type=="enclosure":
        msp.add_lwpolyline([(cx-w/2,cy-hh/2),(cx+w/2,cy-hh/2),(cx+w/2,cy+hh/2),(cx-w/2,cy+hh/2)],close=True,dxfattribs={"layer":layer})
    elif h_type=="push_pull":
        msp.add_lwpolyline([(cx-w/2,cy-hh/2),(cx+w/2,cy-hh/2),(cx+w/2,cy+hh/2),(cx-w/2,cy+hh/2)],close=True,dxfattribs={"layer":layer})
        _tri(msp,(cx-w/2,cy),(-1,0),s,layer); _tri(msp,(cx+w/2,cy),(1,0),s,layer)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,cy-hh/2-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=cy-hh/2-4*s-2.5*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":1.8*s,"style":"ENG"})
            t.set_placement((cx,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.3*s
    return (cx+w/2,cy-hh/2)

def draw_cyclone(msp, center, dia=1.0, scale=100.0, label="", params=None, layer="设备", tracker=None):
    """旋风除尘器。params: dia/flow/efficiency/dp"""
    s=scale; cx,cy=_r(*center); r=dia*s/2; h=dia*s*2
    msp.add_line((cx-r,cy),(cx-1*s,cy+h),dxfattribs={"layer":layer})
    msp.add_line((cx+r,cy),(cx+1*s,cy+h),dxfattribs={"layer":layer})
    msp.add_line((cx-1*s,cy+h),(cx+1*s,cy+h),dxfattribs={"layer":layer})
    msp.add_line((cx-r,cy),(cx+r,cy),dxfattribs={"layer":layer})
    msp.add_line((cx-r-4*s,cy+2*s),(cx-r,cy+2*s),dxfattribs={"layer":layer})
    _tri(msp,(cx-r,cy+2*s),(1,0),s,layer)
    msp.add_line((cx,cy),(cx,cy-4*s),dxfattribs={"layer":layer})
    msp.add_line((cx,cy+h),(cx,cy+h+2*s),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((cx,cy-6*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=cy-6*s-3*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":1.8*s,"style":"ENG"})
            t.set_placement((cx,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.3*s
    return (cx+r+6*s,cy-6*s)

def draw_baghouse_detail(msp, origin, n_bags=32, bag_len=3.0, bag_dia=0.13, scale=100.0,
                          label="", params=None, layer="设备", tracker=None):
    """布袋除尘器内部详图。params: filtration_area/air_cloth/pressure/cleaning/material"""
    s=scale; ox,oy=_r(*origin); bw=8*s; gap=2*s; l=bag_len*s
    cols=min(n_bags//4,8); total_w=(bw+gap)*cols-gap
    msp.add_lwpolyline([(ox,oy),(ox+total_w,oy),(ox+total_w,oy+l),(ox,oy+l)],close=True,dxfattribs={"layer":layer})
    for i in range(cols):
        bx=ox+(bw+gap)*i
        for j in range(4):
            fx=bx+j*1.5*s+0.5*s
            msp.add_line((fx,oy+1*s),(fx,oy+l-1*s),dxfattribs={"layer":"细实线"})
    msp.add_line((ox-6*s,oy+2*s),(ox,oy+2*s),dxfattribs={"layer":layer})
    _tri(msp,(ox,oy+2*s),(1,0),s,layer)
    msp.add_line((ox+total_w/2,oy+l),(ox+total_w/2,oy+l+4*s),dxfattribs={"layer":layer})
    hopper_h=6*s
    msp.add_line((ox,oy),(ox+2*s,oy-hopper_h),dxfattribs={"layer":layer})
    msp.add_line((ox+total_w,oy),(ox+total_w-2*s,oy-hopper_h),dxfattribs={"layer":layer})
    msp.add_line((ox+2*s,oy-hopper_h),(ox+total_w-2*s,oy-hopper_h),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+total_w/2,oy+l+6*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=oy+l+6*s+3*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
            t.set_placement((ox+total_w/2,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.5*s
    return (ox+total_w,oy-hopper_h)

def draw_apc_flow(msp, origin, stages, scale=100.0, label="", layer="工艺", tracker=None):
    """废气治理工艺流程。stages: [{"label":"集气罩"},{"label":"旋风除尘"},...]"""
    s=scale; ox,oy=_r(*origin); cur_x=ox; spacing=28*s
    for i,st in enumerate(stages):
        cx=cur_x; tl=st.get("label","")
        msp.add_lwpolyline([(cx-10*s,cy:=oy-6*s),(cx+10*s,cy),(cx+10*s,oy+6*s),(cx-10*s,oy+6*s)],close=True,dxfattribs={"layer":layer})
        t=msp.add_text(tl,dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,oy),align=TextEntityAlignment.MIDDLE_CENTER)
        if i<len(stages)-1:
            nx=cur_x+spacing
            msp.add_line((cx+10*s,oy),(nx-10*s,oy),dxfattribs={"layer":layer})
            _tri(msp,(nx-10*s,oy),(1,0),s,layer)
        cur_x+=spacing
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+spacing*(len(stages)-1)/2,oy+10*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (cur_x,oy)

def draw_cems_station(msp, center, scale=100.0, params=None, layer="监测站", tracker=None):
    """在线监测站房(CEMS)。params: area/temp/power/analyzer/sampling"""
    s=scale; cx,cy=_r(*center); w=16*s; h=12*s
    msp.add_lwpolyline([(cx-w/2,cy-h/2),(cx+w/2,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)],close=True,dxfattribs={"layer":layer})
    msp.add_line((cx-w/2,cy),(cx-w/2-4*s,cy),dxfattribs={"layer":layer})
    msp.add_circle((cx-w/2-4*s,cy),1.5*s,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(cx-3*s,cy-2*s),(cx+3*s,cy-2*s),(cx+3*s,cy+2*s),(cx-3*s,cy+2*s)],close=True,dxfattribs={"layer":"细实线"})
    t=msp.add_text("CEMS",dxfattribs={"layer":"文字","height":2.5*s,"style":"ENG"})
    t.set_placement((cx,cy),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=cy-h/2-4*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":1.8*s,"style":"HZ"})
            t.set_placement((cx,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.3*s
    return (cx+w/2,cy-h/2)


def draw_scrubber(msp, origin, d=1.2, H=4.0, packing_h=2.0, scale=100.0,
                  label="湿式洗涤塔", layer="废气治理", tracker=None):
    """湿式洗涤塔：塔体+填料层+喷淋管+进出气口。"""
    s=scale;ox,oy=_r(*origin);ds=d*s;hs=H*s;ph=packing_h*s
    cx,cy=ox+ds/2,oy-hs/2
    # 塔体
    msp.add_lwpolyline([(ox,oy),(ox+ds,oy),(ox+ds,oy-hs),(ox,oy-hs)],close=True,dxfattribs={"layer":layer})
    # 填料层（斜线填充区）
    py=oy-hs*0.3
    for xi in range(5):
        msp.add_line((ox+xi*ds/5,py),(ox+xi*ds/5,py-ph),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    msp.add_line((ox,py),(ox+ds,py),dxfattribs={"layer":"细实线"})
    msp.add_line((ox,py-ph),(ox+ds,py-ph),dxfattribs={"layer":"细实线"})
    # 喷淋管
    msp.add_line((ox-3*s,oy-hs*0.4),(ox+ds+3*s,oy-hs*0.4),dxfattribs={"layer":"细实线","linetype":"CENTER"})
    for xi in range(3):
        msp.add_line((ox+ds*(xi+1)/4,oy-hs*0.4),(ox+ds*(xi+1)/4,py),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    # 进出气
    msp.add_line((ox-3*s,oy-hs*0.15),(ox,oy-hs*0.15),dxfattribs={"layer":layer})
    msp.add_line((ox+ds,oy-hs*0.85),(ox+ds+3*s,oy-hs*0.85),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.8*s,"style":"HZ"})
        t.set_placement((cx,oy-hs-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+ds+5*s,oy)
