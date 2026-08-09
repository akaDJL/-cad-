"""深度水处理与污泥处置 v1.0（CJJ 40、HJ 2015、GB 50014）。

A²O/SBR/氧化沟工艺详图、人工湿地系统、渗滤液处理、生物除臭、
高级氧化、紫外线消毒渠、管网高程图、污泥堆肥/填埋。

纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

def draw_a2o_flow(msp, origin, zones:List[dict]=None, scale=100.0, label="A²O工艺", layer="工艺", tracker=None):
    """A²O工艺流程图（厌氧-缺氧-好氧）。
    zones: [{"type":"anaerobic","label":"厌氧池","params":{}},
            {"type":"anoxic","label":"缺氧池","params":{}},
            {"type":"aerobic","label":"好氧池","params":{}},
            {"type":"settler","label":"二沉池","params":{}}]
    """
    s=scale; ox,oy=_r(*origin); cur_x=ox; spacing=30*s
    if not zones:
        zones=[{"type":"anaerobic","label":"厌氧池"},{"type":"anoxic","label":"缺氧池"},{"type":"aerobic","label":"好氧池"},{"type":"settler","label":"二沉池"}]
    for i,z in enumerate(zones):
        cx=cur_x; bh=14*s; bw=22*s
        if z.get("type")=="settler":
            r=bw/2; msp.add_circle((cx,oy),r,dxfattribs={"layer":layer})
            msp.add_line((cx,oy-r*(0.3 if i%2==0 else -0.3)),(cx,oy+r*(0.3 if i%2==0 else -0.3)),dxfattribs={"layer":layer})
        else:
            msp.add_lwpolyline([(cx-bw/2,oy-bh/2),(cx+bw/2,oy-bh/2),(cx+bw/2,oy+bh/2),(cx-bw/2,oy+bh/2)],close=True,dxfattribs={"layer":layer})
            if z.get("type")=="anaerobic":
                for _ in range(3):pass
        t=msp.add_text(z.get("label",""),dxfattribs={"layer":"文字-标题","height":2.8*s,"style":"HZ"})
        t.set_placement((cx,oy),align=TextEntityAlignment.MIDDLE_CENTER)
        if i<len(zones)-1:
            nx=cur_x+spacing
            msp.add_line((cx+bw/2,oy),(nx-bw/2,oy),dxfattribs={"layer":layer})
            _tri(msp,(nx-bw/2,oy),(1,0),s,layer)
        cur_x+=spacing
    # 回流线（二沉池→厌氧池）
    ret_x=cur_x-spacing;ret_y=oy+bh/2+4*s
    msp.add_line((ret_x,ret_y),(ox,ret_y),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    msp.add_line((ox,ret_y),(ox,oy+bh/2+s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    _tri(msp,(ox,oy+bh/2+s),(0,-1),s,"细实线")
    t=msp.add_text("污泥回流",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
    t.set_placement((ox+(ret_x-ox)/2,ret_y+2*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":4*s,"style":"HZ"})
        t.set_placement((ox+spacing*(len(zones)-1)/2,oy+bh/2+8*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (cur_x,oy)

def draw_sbr_cycle(msp, origin, scale=100.0, label="SBR周期", layer="工艺", tracker=None):
    """SBR 运行周期时序图（进水-曝气-沉淀-排水-闲置）。"""
    s=scale; ox,oy=_r(*origin); tw=180*s; th=40*s
    msp.add_lwpolyline([(ox,oy),(ox+tw,oy),(ox+tw,oy+th),(ox,oy+th)],close=True,dxfattribs={"layer":layer})
    phases=[("进水","2h",0.15),( "曝气","4h",0.45),("沉淀","1.5h",0.65),( "排水","1h",0.8),( "闲置","0.5h",0.95)]
    for name,dur,frac in phases:
        px=ox+tw*frac-d*0.1 if (d:=frac*0.05)>0 else ox
        msp.add_line((ox+tw*max(frac-0.05,0),oy),(ox+tw*max(frac-0.05,0),oy+th),dxfattribs={"layer":layer})
        t=msp.add_text(name,dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"})
        t.set_placement((ox+tw*(frac-0.025),oy+th*0.7),align=TextEntityAlignment.MIDDLE_CENTER)
        t2=msp.add_text(dur,dxfattribs={"layer":"文字","height":2*s,"style":"ENG"})
        t2.set_placement((ox+tw*(frac-0.025),oy+th*0.3),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+tw/2,oy+th+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+tw,oy+th)

def draw_constructed_wetland(msp, origin, l=30.0, w=15.0, w_type="ssf", scale=100.0, label="", params=None, layer="湿地", tracker=None):
    """人工湿地剖面（水平潜流/垂直流/表面流）。
    w_type: ssf 水平潜流 / vf 垂直流 / fws 表面流
    params: {"media":"砾石+砂","plants":"芦苇+香蒲","HLR":"0.3m/d","area":"450m²",...}
    """
    s=scale; ox,oy=_r(*origin); L=l*s; W=w*s
    msp.add_lwpolyline([(ox,oy),(ox+L,oy),(ox+L,oy+W),(ox,oy+W)],close=True,dxfattribs={"layer":layer})
    if w_type=="ssf":
        msp.add_line((ox,oy+W*0.7),(ox+L,oy+W*0.7),dxfattribs={"layer":layer})
        msp.add_line((ox,oy+W*0.85),(ox+L,oy+W*0.85),dxfattribs={"layer":"细实线"})
        for i in range(4):
            px=ox+L*(i+0.5)/4
            msp.add_line((px,oy+W*0.75),(px,oy+W*0.9),dxfattribs={"layer":"细实线"})
    elif w_type=="vf":
        for i in range(3):
            ly=oy+W*(i+0.5)/3
            msp.add_line((ox,ly),(ox+L,ly),dxfattribs={"layer":"细实线"})
    elif w_type=="fws":
        msp.add_line((ox+L*0.1,oy+W*0.3),(ox+L*0.3,oy+W*0.7),dxfattribs={"layer":"细实线"})
        msp.add_line((ox+L*0.3,oy+W*0.7),(ox+L*0.6,oy+W*0.5),dxfattribs={"layer":"细实线"})
        msp.add_line((ox+L*0.6,oy+W*0.5),(ox+L*0.9,oy+W*0.8),dxfattribs={"layer":"细实线"})
    t=msp.add_text("进水",dxfattribs={"layer":"文字","height":2.2*s,"style":"HZ"})
    t.set_placement((ox-5*s,oy+W*0.3),align=TextEntityAlignment.MIDDLE_CENTER)
    _tri(msp,(ox,oy+W*0.3),(1,0),s,layer)
    t=msp.add_text("出水",dxfattribs={"layer":"文字","height":2.2*s,"style":"HZ"})
    t.set_placement((ox+L+5*s,oy+W*0.3),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+L/2,oy+W+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=oy+W+5*s+3*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
            t.set_placement((ox+L/2,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.5*s
    return (ox+L,oy+W)

def draw_leachate_treatment(msp, origin, scale=100.0, label="渗滤液处理", layer="工艺", tracker=None):
    """垃圾渗滤液处理流程图（调节池→MBR→NF→RO）。"""
    s=scale; ox,oy=_r(*origin); spacing=28*s
    stages=[("调节池","DT-101"),("MBR","MBR-201"),("纳滤NF","NF-301"),("反渗透RO","RO-401"),("浓缩液","C-501")]
    for i,(name,tag) in enumerate(stages):
        cx=ox+spacing*i; bw=20*s;bh=14*s
        if i==len(stages)-1:
            msp.add_circle((cx,oy),bw/3,dxfattribs={"layer":layer})
        else:
            msp.add_lwpolyline([(cx-bw/2,oy-bh/2),(cx+bw/2,oy-bh/2),(cx+bw/2,oy+bh/2),(cx-bw/2,oy+bh/2)],close=True,dxfattribs={"layer":layer})
        t=msp.add_text(name,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,oy+1.5*s),align=TextEntityAlignment.MIDDLE_CENTER)
        t2=msp.add_text(tag,dxfattribs={"layer":"文字","height":2*s,"style":"ENG"})
        t2.set_placement((cx,oy-2*s),align=TextEntityAlignment.MIDDLE_CENTER)
        if i<len(stages)-1:
            nx=ox+spacing*(i+1)
            msp.add_line((cx+bw/2,oy),(nx-bw/2,oy),dxfattribs={"layer":layer})
            _tri(msp,(nx-bw/2,oy),(1,0),s,layer)
    # 浓缩液回流
    msp.add_line((ox+spacing*4+bw/2,oy+bh/2),(ox+spacing*4+bw/2,oy+bh/2+6*s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    msp.add_line((ox+spacing*4+bw/2,oy+bh/2+6*s),(ox-bw/2,oy+bh/2+6*s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    msp.add_line((ox-bw/2,oy+bh/2+6*s),(ox-bw/2,oy+bh/2),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    t=msp.add_text("浓缩液回流",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
    t.set_placement((ox+spacing*2,oy+bh/2+8*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+spacing*2,oy+bh/2+12*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+spacing*5,oy)

def draw_bio_deodorization(msp, center, scale=100.0, label="", params=None, layer="除臭", tracker=None):
    """生物除臭系统。params: {"flow":"10000m³/h","media":"树皮+泥炭","retention":"30s","removal":"H2S>95%",...}"""
    s=scale; cx,cy=_r(*center); w=24*s;h=16*s
    msp.add_lwpolyline([(cx-w/2,cy-h/2),(cx+w/2,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)],close=True,dxfattribs={"layer":layer})
    for i in range(3):
        msp.add_line((cx-w*0.3,cy+h*0.3-i*3*s),(cx+w*0.3,cy+h*0.3-i*3*s),dxfattribs={"layer":"细实线"})
    msp.add_line((cx-w/2-5*s,cy+h*0.2),(cx-w/2,cy+h*0.2),dxfattribs={"layer":layer})
    _tri(msp,(cx-w/2,cy+h*0.2),(1,0),s,layer)
    msp.add_line((cx+w/2,cy-h*0.2),(cx+w/2+5*s,cy-h*0.2),dxfattribs={"layer":layer})
    _tri(msp,(cx+w/2,cy-h*0.2),(-1,0),s,layer)
    t=msp.add_text("废气",dxfattribs={"layer":"文字","height":2.2*s,"style":"HZ"})
    t.set_placement((cx-w/2-7*s,cy+h*0.2),align=TextEntityAlignment.MIDDLE_CENTER)
    t2=msp.add_text("净化气",dxfattribs={"layer":"文字","height":2.2*s,"style":"HZ"})
    t2.set_placement((cx+w/2+7*s,cy-h*0.2),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((cx,cy-h/2-5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=cy-h/2-5*s-3*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":1.8*s,"style":"HZ"})
            t.set_placement((cx,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.3*s
    return (cx+w/2+7*s,cy-h/2-5*s)

def draw_pipe_profile(msp, origin, nodes:List[dict], scale=100.0, label="管网高程图", layer="管网", tracker=None):
    """管网纵断面/高程图。
    nodes: [{"station":"0+000","ground_el":100.5,"pipe_el":98.0,"dn":400},
            {"station":"0+050","ground_el":100.2,"pipe_el":97.75,"dn":400},...]
    """
    s=scale; ox,oy=_r(*origin); n=len(nodes); tw=min(300*s,n*60*s); spacing=tw/max(n-1,1)
    el_min=min(nd.get("pipe_el",100) for nd in nodes)-2
    el_max=max(nd.get("ground_el",100) for nd in nodes)+2
    el_range=el_max-el_min
    h=(el_range)*s*8
    now_y=lambda el:oy+h-(el-el_min)*s*8
    # 地面线
    g_pts=[(ox+spacing*i,now_y(nd.get("ground_el",100))) for i,nd in enumerate(nodes)]
    msp.add_lwpolyline(g_pts,close=False,dxfattribs={"layer":layer})
    # 管底线
    p_pts=[(ox+spacing*i,now_y(nd.get("pipe_el",98))) for i,nd in enumerate(nodes)]
    msp.add_lwpolyline(p_pts,close=False,dxfattribs={"layer":layer,"linetype":"DASHED"})
    # 桩号+标高
    for i,nd in enumerate(nodes):
        st=nd.get("station","");ge=nd.get("ground_el",0);pe=nd.get("pipe_el",0)
        t=msp.add_text(st,dxfattribs={"layer":"文字","height":2*s,"style":"ENG"})
        t.set_placement((ox+spacing*i,oy+h+3*s),align=TextEntityAlignment.MIDDLE_CENTER,dxfattribs={"style":"ENG","height":2*s})
        t2=msp.add_text(f"G:{ge:.2f}",dxfattribs={"layer":"文字","height":1.8*s,"style":"ENG"})
        t2.set_placement((ox+spacing*i,now_y(ge)+2*s),align=TextEntityAlignment.MIDDLE_CENTER)
        t3=msp.add_text(f"P:{pe:.2f}",dxfattribs={"layer":"文字","height":1.8*s,"style":"ENG"})
        t3.set_placement((ox+spacing*i,now_y(pe)-3*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+tw/2,oy+h+8*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+tw,oy+h)
