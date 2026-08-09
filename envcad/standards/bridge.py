"""桥梁与特种结构制图 v1.0（JTG D60—2015、GB 50017、GB 50011）。

箱梁/钢桁梁断面、沉井基础、隔震支座、柱脚节点、
钢骨/钢管组合结构、施工临时支架。

纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

def draw_box_girder(msp, origin, width=12.0, depth=2.0, n_cells=3,
                     scale=100.0, label="", params=None, layer="结构", tracker=None):
    """箱梁断面。width/depth m; n_cells 室数"""
    s=scale; ox,oy=_r(*origin); W=width*s; D=depth*s; cells_w=W/n_cells
    # 顶板
    msp.add_line((ox,oy+D),(ox+W,oy+D),dxfattribs={"layer":layer})
    # 底板
    msp.add_line((ox+0.5*s,oy),(ox+W-0.5*s,oy),dxfattribs={"layer":layer})
    # 翼缘板
    msp.add_line((ox-1*s,oy+D),(ox+0.5*s,oy+D),dxfattribs={"layer":layer})
    msp.add_line((ox+W-0.5*s,oy+D),(ox+W+1*s,oy+D),dxfattribs={"layer":layer})
    msp.add_line((ox-1*s,oy+D),(ox+0.5*s,oy+D-0.5*s),dxfattribs={"layer":layer})
    msp.add_line((ox+W+1*s,oy+D),(ox+W-0.5*s,oy+D-0.5*s),dxfattribs={"layer":layer})
    # 腹板
    for i in range(n_cells+1):
        wx=ox+cells_w*i
        msp.add_line((wx-0.3*s,oy),(wx-0.3*s,oy+D-0.5*s),dxfattribs={"layer":layer})
        msp.add_line((wx+0.3*s,oy),(wx+0.3*s,oy+D-0.5*s),dxfattribs={"layer":layer})
    # 预应力管道
    for i in range(n_cells):
        cx_mid=ox+cells_w*(i+0.5)
        for v_frac in [0.2,0.5,0.8]:
            by=oy+D*v_frac
            msp.add_circle((cx_mid,by),1.5*s,dxfattribs={"layer":"细实线"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+W/2,oy+D+6*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=oy+D+6*s+3.5*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
            t.set_placement((ox+W/2,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.5*s
    return (ox+W,oy+D)

def draw_open_caisson(msp, origin, dia=8.0, depth=15.0, section_depth=3.0,
                       scale=100.0, label="", params=None, layer="结构", tracker=None):
    """沉井基础剖面。dia/depth m"""
    s=scale; ox,oy=_r(*origin); R=dia*s/2; D=depth*s; sec_d=section_depth*s
    # 井壁
    wall=1.5*s
    msp.add_line((ox-R,oy),(ox-R,oy-D),dxfattribs={"layer":layer})
    msp.add_line((ox+R,oy),(ox+R,oy-D),dxfattribs={"layer":layer})
    msp.add_line((ox-R+wall,oy-sec_d),(ox+R-wall,oy-sec_d),dxfattribs={"layer":layer})
    # 刃脚
    msp.add_line((ox-R,oy-D),(ox-R+wall,oy-D+sec_d),dxfattribs={"layer":layer})
    msp.add_line((ox+R,oy-D),(ox+R-wall,oy-D+sec_d),dxfattribs={"layer":layer})
    msp.add_line((ox-R+wall,oy-D+sec_d),(ox+R-wall,oy-D+sec_d),dxfattribs={"layer":layer})
    # 取土孔
    msp.add_line((ox-2*s,oy),(ox-2*s,oy-D+sec_d),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    msp.add_line((ox+2*s,oy),(ox+2*s,oy-D+sec_d),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    # 地面线
    gl_y=oy-sec_d*0.5
    msp.add_line((ox-R-3*s,gl_y),(ox+R+3*s,gl_y),dxfattribs={"layer":"细实线","linetype":"DASHDOT"})
    t=msp.add_text("GL",dxfattribs={"layer":"文字","height":2.5*s,"style":"ENG"})
    t.set_placement((ox+R+4*s,gl_y),align=TextEntityAlignment.MIDDLE_LEFT)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+R+6*s,oy-D/2),align=TextEntityAlignment.MIDDLE_LEFT)
    return (ox+R+8*s,oy-D)

def draw_seismic_isolator(msp, center, i_type="LRB", scale=100.0, label="", params=None, layer="隔震", tracker=None):
    """隔震支座符号。i_type: LRB铅芯橡胶 / HDR高阻尼 / FPS摩擦摆"""
    s=scale; cx,cy=_r(*center); w=10*s;h=6*s
    msp.add_lwpolyline([(cx-w/2,cy-h/2),(cx+w/2,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)],close=True,dxfattribs={"layer":layer})
    if i_type=="LRB":
        msp.add_circle((cx,cy),2*s,dxfattribs={"layer":layer})
        for i in range(2):
            ly=cy+(i-0.5)*1.5*s
            msp.add_line((cx-w*0.4,ly),(cx+w*0.4,ly),dxfattribs={"layer":"细实线"})
    elif i_type=="FPS":
        msp.add_arc((cx,cy+h/2),radius=w/2,start_angle=180,end_angle=360,dxfattribs={"layer":layer})
        msp.add_line((cx-w/2,cy+h/2),(cx+w/2,cy+h/2),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":2.5*s,"style":"HZ"})
        t.set_placement((cx,cy-h/2-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=cy-h/2-4*s-2.5*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":1.8*s,"style":"HZ"})
            t.set_placement((cx,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.3*s
    return (cx+w/2,cy-h/2-4*s)

def draw_column_base(msp, center, b_type="exposed", col_w=0.4, base_w=0.6, base_h=0.03,
                      scale=100.0, label="", params=None, layer="节点", tracker=None):
    """柱脚节点详图。b_type: exposed外露式 / embedded埋入式 / encased外包式
    col_w/base_w/base_h 单位 m"""
    s=scale; cx,cy=_r(*center); cw=col_w*s; bw=base_w*s; bh=base_h*s
    # 底板
    msp.add_line((cx-bw/2,cy),(cx+bw/2,cy),dxfattribs={"layer":layer})
    msp.add_line((cx-bw/2,cy),(cx-bw/2,cy-bh),dxfattribs={"layer":layer})
    msp.add_line((cx+bw/2,cy),(cx+bw/2,cy-bh),dxfattribs={"layer":layer})
    msp.add_line((cx-bw/2,cy-bh),(cx+bw/2,cy-bh),dxfattribs={"layer":layer})
    # 柱身
    msp.add_line((cx-cw/2,cy),(cx-cw/2,cy+10*s),dxfattribs={"layer":layer})
    msp.add_line((cx+cw/2,cy),(cx+cw/2,cy+10*s),dxfattribs={"layer":layer})
    if b_type=="exposed":
        for dx in [-2*s,0,2*s]:
            msp.add_circle((cx+dx,cy-bh/2),1.5*s,dxfattribs={"layer":layer})
        t=msp.add_text("锚栓",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
        t.set_placement((cx+bw/2+3*s,cy-bh/2),align=TextEntityAlignment.MIDDLE_LEFT)
    elif b_type=="embedded":
        msp.add_line((cx-cw/2-2*s,cy-bh-5*s),(cx+cw/2+2*s,cy-bh-5*s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
        t=msp.add_text("基础顶面",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
        t.set_placement((cx+cw/2+3*s,cy-bh-5*s),align=TextEntityAlignment.MIDDLE_LEFT)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((cx,cy+13*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx+bw/2+8*s,cy-bh-5*s)

def draw_composite_column(msp, center, c_type="src", dia=0.6, scale=100.0, label="", params=None, layer="组合结构", tracker=None):
    """组合结构柱断面。c_type: src钢骨混凝土 / cfst钢管混凝土"""
    s=scale; cx,cy=_r(*center); R=dia*s/2
    msp.add_circle((cx,cy),R,dxfattribs={"layer":layer})
    if c_type=="src":
        hw=R*0.5;hh=R*0.6
        msp.add_lwpolyline([(cx-hw,cy-hh),(cx+hw,cy-hh),(cx+hw,cy+hh),(cx-hw,cy+hh)],close=True,dxfattribs={"layer":layer})
    elif c_type=="cfst":
        msp.add_circle((cx,cy),R*0.85,dxfattribs={"layer":"细实线"})
    # 纵筋
    for i in range(8):
        ang=2*math.pi*i/8; bx=cx+R*0.8*math.cos(ang); by=cy+R*0.8*math.sin(ang)
        msp.add_circle((bx,by),1.5*s,dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((cx,cy-R-5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (cx+R,cy-R-5*s)

def draw_scaffold(msp, origin, height=15.0, width=1.2, n_lifts=8, scale=100.0, label="", params=None, layer="施工", tracker=None):
    """施工脚手架立面。height m; width m 架体宽; n_lifts 步数"""
    s=scale; ox,oy=_r(*origin); H=height*s; W=width*s; step_h=H/n_lifts
    # 立杆
    for dx in [0,W]:
        msp.add_line((ox+dx,oy),(ox+dx,oy+H),dxfattribs={"layer":layer})
    # 水平杆
    for i in range(n_lifts+1):
        hy=oy+step_h*i
        msp.add_line((ox,hy),(ox+W,hy),dxfattribs={"layer":layer})
    # 剪刀撑
    for i in range(0,n_lifts,2):
        y1=oy+step_h*i; y2=oy+step_h*min(i+2,n_lifts)
        msp.add_line((ox,y1),(ox+W,y2),dxfattribs={"layer":"细实线","linetype":"DASHED"})
        msp.add_line((ox+W,y1),(ox,y2),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    # 连墙件
    for i in range(2,n_lifts,2):
        ly=oy+step_h*i
        msp.add_line((ox-3*s,ly),(ox+W+3*s,ly),dxfattribs={"layer":"细实线"})
        t=msp.add_text("连墙件",dxfattribs={"layer":"文字","height":1.8*s,"style":"HZ"})
        t.set_placement((ox-5*s,ly),align=TextEntityAlignment.MIDDLE_RIGHT)
    # 底座
    msp.add_line((ox-2*s,oy-1*s),(ox+W+2*s,oy-1*s),dxfattribs={"layer":layer,"lineweight":40})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+W/2,oy+H+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+W,oy+H)

# ══════ v1.5+ 桥梁增补：悬索/斜拉/拱桥 ══════
def draw_suspension_bridge(msp,origin,span=200.0,tower_h=60.0,deck_w=20.0,sag=30.0,scale=100.0,label="",layer="桥梁",tracker=None):
    s=scale*0.5;ox,oy=_r(*origin);L=span*s;H=tower_h*s;W=deck_w*s;sg=sag*s
    # 主缆（抛物线近似）
    pts=[(ox,oy+H),(ox+L*0.2,oy+H-sg*0.8),(ox+L*0.5,oy+H-sg),(ox+L*0.8,oy+H-sg*0.8),(ox+L,oy+H)]
    msp.add_lwpolyline(pts,close=False,dxfattribs={"layer":layer})
    # 塔柱
    for tx in[ox,ox+L]:
        msp.add_lwpolyline([(tx-2*s,oy),(tx+2*s,oy),(tx+2*s,oy+H),(tx-2*s,oy+H)],close=True,dxfattribs={"layer":layer})
    # 桥面
    msp.add_lwpolyline([(ox,oy-3*s),(ox+L,oy-3*s),(ox+L,oy-3*s-W),(ox,oy-3*s-W)],close=True,dxfattribs={"layer":layer})
    # 吊索
    for i in range(1,9):
        hx=ox+L*i/9;hy=oy+H-sg*(1-abs(i/4.5-1)**2)
        msp.add_line((hx,hy),(hx,oy-3*s),dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":4*s,"style":"HZ"});t.set_placement((ox+L/2,oy+H+6*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_cable_stayed(msp,origin,span=150.0,tower_h=50.0,deck_w=15.0,scale=100.0,label="",layer="桥梁",tracker=None):
    s=scale*0.5;ox,oy=_r(*origin);L=span*s;H=tower_h*s
    msp.add_line((ox+L/2,oy),(ox+L/2,oy+H),dxfattribs={"layer":layer})
    for i in range(1,8):
        sx=ox+L*i/8
        msp.add_line((ox+L/2,oy+H),(sx,oy-3*s),dxfattribs={"layer":"细实线"})
    msp.add_line((ox,oy-3*s),(ox+L,oy-3*s),dxfattribs={"layer":layer})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":4*s,"style":"HZ"});t.set_placement((ox+L/2,oy+H+6*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_arch_bridge(msp,origin,span=100.0,rise=25.0,deck_w=12.0,scale=100.0,label="",layer="桥梁",tracker=None):
    s=scale*0.5;ox,oy=_r(*origin);L=span*s;R=rise*s
    pts=[(ox+i*L/20,oy+R*(1-(i/10-1)**2))for i in range(21)]
    msp.add_lwpolyline(pts,close=False,dxfattribs={"layer":layer})
    msp.add_line((ox,oy),(ox+L,oy),dxfattribs={"layer":layer})
    for i in range(1,20,3):msp.add_line((ox+L*i/20,oy+R*(1-(i/10-1)**2)),(ox+L*i/20,oy),dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+L/2,oy+R+5*s),align=TextEntityAlignment.MIDDLE_CENTER)


def draw_bridge_deck(msp, origin, L=30.0, w=12.0, t=0.2, n_girders=4,
                     scale=100.0, label="桥面铺装", layer="桥梁", tracker=None):
    """桥面铺装横断面：桥面板+铺装层+护栏+纵梁。"""
    s=scale;ox,oy=_r(*origin);ls,ws,t_s=L*s,w*s,t*s
    # 桥面板
    msp.add_lwpolyline([(ox,oy),(ox+ls,oy),(ox+ls,oy+t_s),(ox,oy+t_s)],close=True,dxfattribs={"layer":layer})
    # 铺装层（上方虚线表示沥青/混凝土面层）
    pl=2*s;msp.add_lwpolyline([(ox,oy-pl),(ox+ls,oy-pl),(ox+ls,oy),(ox,oy)],close=True,dxfattribs={"layer":"细实线"})
    for xi in range(8):msp.add_line((ox+ls*xi/8,oy-pl),(ox+ls*xi/8,oy),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    # 纵梁
    gs=ws/(n_girders+1)*s
    for gi in range(n_girders):
        gx=ox+gs*(gi+1);msp.add_lwpolyline([(gx-3*s,oy+t_s),(gx+3*s,oy+t_s),(gx+3*s,oy+t_s+8*s),(gx-3*s,oy+t_s+8*s)],close=True,dxfattribs={"layer":layer})
    # 护栏
    msp.add_lwpolyline([(ox,oy-pl-3*s),(ox,oy-pl),(ox+ls,oy-pl),(ox+ls,oy-pl-3*s)],close=True,dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+ls/2,oy+t_s+12*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+ls+5*s,oy-pl-5*s)
