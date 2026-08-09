"""土木深度结构制图 v1.0（GB 50010、GB 50017、JTG D60、GB 50011）。

预应力梁、砌体墙、钢结构框架立面、屋架桁架、桥梁墩台、隧道断面、边坡支护。
纯 ezdxf，零新依赖。所有参数由 Agent 搜索后传入。
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from ezdxf.enums import TextEntityAlignment
from ..utils import _r, _tri

def draw_prestressed_beam(msp, origin, span=12.0, depth=0.8, width=0.3, scale=100.0, label="", params=None, layer="结构", tracker=None):
    """预应力梁立面。span/depth/width m; params: tendons/grade/force"""
    s=scale; ox,oy=_r(*origin); L=span*s; H=depth*s; B=width*s
    msp.add_lwpolyline([(ox,oy),(ox+L,oy),(ox+L,oy+H),(ox,oy+H)],close=True,dxfattribs={"layer":layer})
    # 预应力筋（抛物线形）
    pts=[(ox+L*0.05,oy+H*0.85),"ctl",(ox+L*0.3,oy+H*0.25),(ox+L*0.5,oy+H*0.15),(ox+L*0.7,oy+H*0.25),(ox+L*0.95,oy+H*0.85)]
    ctl_pts=[(ox+L*0.05,oy+H*0.85),(ox+L*0.3,oy+H*0.25),(ox+L*0.5,oy+H*0.15),(ox+L*0.7,oy+H*0.25),(ox+L*0.95,oy+H*0.85)]
    try:msp.add_spline(points=ctl_pts,dxfattribs={"layer":"细实线"})
    except Exception:msp.add_lwpolyline(ctl_pts,close=False,dxfattribs={"layer":"细实线"})
    # 锚具
    for ax in [ox+L*0.05,ox+L*0.95]:
        msp.add_lwpolyline([(ax-2*s,oy+H*0.85-2*s),(ax+2*s,oy+H*0.85-2*s),(ax+2*s,oy+H*0.85+2*s),(ax-2*s,oy+H*0.85+2*s)],close=True,dxfattribs={"layer":layer})
    # 支座
    msp.add_line((ox-2*s,oy),(ox+2*s,oy),dxfattribs={"layer":layer});msp.add_line((ox,oy),(ox,oy-3*s),dxfattribs={"layer":layer})
    msp.add_line((ox+L-2*s,oy),(ox+L+2*s,oy),dxfattribs={"layer":layer});msp.add_line((ox+L,oy),(ox+L,oy-3*s),dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+L/2,oy+H+4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=oy+H+4*s+3*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
            t.set_placement((ox+L/2,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.5*s
    return (ox+L,oy-5*s)

def draw_masonry_wall(msp, origin, width=3.0, height=3.0, thickness=0.24, scale=100.0, label="", params=None, layer="结构", tracker=None):
    """砌体墙立面。width/height/thickness m"""
    s=scale; ox,oy=_r(*origin); w=width*s; h=height*s
    msp.add_lwpolyline([(ox,oy),(ox+w,oy),(ox+w,oy+h),(ox,oy+h)],close=True,dxfattribs={"layer":layer})
    # 砌块纹理（水平线+竖线）
    n_h=8; n_v=int(w/(h/n_h*2))
    for i in range(n_h+1):
        ly=oy+h*i/n_h
        msp.add_line((ox,ly),(ox+w,ly),dxfattribs={"layer":"细实线"})
        if i%2==0:
            for j in range(n_v+1):
                lx=ox+w*j/n_v
                msp.add_line((lx,ly),(lx,ly-h/n_h*0.5),dxfattribs={"layer":"细实线"})
        else:
            for j in range(n_v):
                lx=ox+w*(j+0.5)/n_v
                msp.add_line((lx,ly),(lx,ly-h/n_h*0.5),dxfattribs={"layer":"细实线"})
    # 构造柱
    col_w=3*s;msp.add_lwpolyline([(ox+w-col_w,oy),(ox+w,oy),(ox+w,oy+h),(ox+w-col_w,oy+h)],close=True,dxfattribs={"layer":layer})
    tt=msp.add_text("构造柱",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
    tt.set_placement((ox+w-col_w/2,oy+h+1*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+w/2,oy+h+4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+w,oy+h)

def draw_steel_frame(msp, origin, stories=3, bays=2, story_h=3.6, bay_w=6.0, scale=100.0, label="", params=None, layer="结构", tracker=None):
    """钢结构框架立面。stories/bays 数量; story_h/bay_w m"""
    s=scale; ox,oy=_r(*origin); sh=story_h*s; bw=bay_w*s; tw=sh*stories; tw_b=bw*bays
    # 柱
    for i in range(bays+1):
        cx=ox+bw*i; col=1.5*s
        msp.add_line((cx-col,oy),(cx-col,oy+tw),dxfattribs={"layer":layer})
        msp.add_line((cx+col,oy),(cx+col,oy+tw),dxfattribs={"layer":layer})
    # 梁
    for i in range(stories+1):
        ly=oy+sh*i; beam=1.2*s
        msp.add_line((ox,ly+beam),(ox+tw_b,ly+beam),dxfattribs={"layer":layer})
        msp.add_line((ox,ly-beam),(ox+tw_b,ly-beam),dxfattribs={"layer":layer})
    # 支撑（交叉）
    for i in range(bays):
        for j in range(stories):
            x0=ox+bw*i; y0=oy+sh*j; x1=x0+bw; y1=y0+sh
            msp.add_line((x0+0.5*s,y0+0.5*s),(x1-0.5*s,y1-0.5*s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
            msp.add_line((x1-0.5*s,y0+0.5*s),(x0+0.5*s,y1-0.5*s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+tw_b/2,oy+tw+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+tw_b,oy+tw)

def draw_truss(msp, origin, span=18.0, rise=2.5, n_panels=8, scale=100.0, label="", params=None, layer="结构", tracker=None):
    """屋架/桁架立面。span/rise m; n_panels 节间数"""
    s=scale; ox,oy=_r(*origin); L=span*s; H=rise*s; pw=L/n_panels
    # 上弦
    u_pts=[(ox,oy)]; l_pts=[(ox,oy-H)]
    for i in range(1,n_panels):
        ux=ox+pw*i; frac=i/n_panels; arch=1-((frac-0.5)*2)**2; uy=oy+H*arch*0.8
        u_pts.append((ux,uy)); l_pts.append((ux,oy-H))
    u_pts.append((ox+L,oy)); l_pts.append((ox+L,oy-H))
    msp.add_lwpolyline(u_pts,close=False,dxfattribs={"layer":layer})
    msp.add_line(l_pts[0],l_pts[-1],dxfattribs={"layer":layer})
    # 腹杆
    for i in range(n_panels):
        sx=ox+pw*i; ex=ox+pw*(i+1)
        msp.add_line(u_pts[i],l_pts[i+1],dxfattribs={"layer":"细实线"})
        msp.add_line(l_pts[i],u_pts[i+1],dxfattribs={"layer":"细实线"})
    # 端竖杆
    msp.add_line(u_pts[0],l_pts[0],dxfattribs={"layer":layer})
    msp.add_line(u_pts[-1],l_pts[-1],dxfattribs={"layer":layer})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox+L/2,oy+H+4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+L,oy-H)

def draw_bridge_pier(msp, origin, height=15.0, width=2.0, scale=100.0, label="", params=None, layer="结构", tracker=None):
    """桥梁墩台立面。height/width m"""
    s=scale; ox,oy=_r(*origin); H=height*s; W=width*s; cap_h=3*s;cap_w=W+4*s;found_w=W+6*s;found_h=4*s
    # 墩身
    msp.add_lwpolyline([(ox-W/2,oy+found_h),(ox+W/2,oy+found_h),(ox+W/2,oy+found_h+H-cap_h),(ox-W/2,oy+found_h+H-cap_h)],close=True,dxfattribs={"layer":layer})
    # 帽梁
    msp.add_lwpolyline([(ox-cap_w/2,oy+found_h+H-cap_h),(ox+cap_w/2,oy+found_h+H-cap_h),(ox+cap_w/2,oy+found_h+H),(ox-cap_w/2,oy+found_h+H)],close=True,dxfattribs={"layer":layer})
    # 承台
    msp.add_lwpolyline([(ox-found_w/2,oy),(ox+found_w/2,oy),(ox+found_w/2,oy+found_h),(ox-found_w/2,oy+found_h)],close=True,dxfattribs={"layer":layer})
    # 桩
    for dx in [-3*s,0,3*s]:
        ph=6*s;pile_x=ox+dx
        msp.add_line((pile_x-1*s,oy-found_h*0.3),(pile_x-1*s,oy-found_h*0.3-ph),dxfattribs={"layer":"细实线"})
        msp.add_line((pile_x+1*s,oy-found_h*0.3),(pile_x+1*s,oy-found_h*0.3-ph),dxfattribs={"layer":"细实线"})
    # 地面线
    msp.add_line((ox-found_w-2*s,oy-found_h*0.3),(ox+found_w+2*s,oy-found_h*0.3),dxfattribs={"layer":"细实线","linetype":"DASHDOT"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"})
        t.set_placement((ox,oy+found_h+H+4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+found_w/2,oy-ph)

def draw_tunnel_section(msp, origin, t_type="horseshoe", width=8.0, height=6.0, scale=100.0, label="", params=None, layer="结构", tracker=None):
    """隧道断面。t_type: horseshoe/circular/rectangular"""
    s=scale; ox,oy=_r(*origin); w=width*s; h=height*s
    if t_type=="horseshoe":
        pts=[(ox-w/2,oy),(ox-w*0.4,oy+h*0.3),(ox-w*0.1,oy+h),(ox+w*0.1,oy+h),(ox+w*0.4,oy+h*0.3),(ox+w/2,oy)]
        msp.add_lwpolyline(pts,close=False,dxfattribs={"layer":layer})
        msp.add_line((ox-w*0.4,oy+h*0.3),(ox+w*0.4,oy+h*0.3),dxfattribs={"layer":layer})
    elif t_type=="circular":
        r=w/2
        msp.add_circle((ox,oy+h/2),r,dxfattribs={"layer":layer})
    elif t_type=="rectangular":
        msp.add_lwpolyline([(ox-w/2,oy),(ox+w/2,oy),(ox+w/2,oy+h),(ox-w/2,oy+h)],close=True,dxfattribs={"layer":layer})
    # 衬砌（外层虚线）
    lining=1.5*s
    if t_type=="circular":
        msp.add_circle((ox,oy+h/2),w/2+lining,dxfattribs={"layer":"细实线","linetype":"DASHED"})
    else:
        msp.add_lwpolyline([(ox-w/2-lining,oy-lining),(ox+w/2+lining,oy-lining),(ox+w/2+lining,oy+h+lining),(ox-w/2-lining,oy+h+lining)],close=True,dxfattribs={"layer":"细实线","linetype":"DASHED"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox,oy+h+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if params:
        py=oy+h+5*s+3*s
        for k,v in params.items():
            t=msp.add_text(f"{k}:{v}",dxfattribs={"layer":"文字","height":2*s,"style":"HZ"})
            t.set_placement((ox,py),align=TextEntityAlignment.MIDDLE_CENTER);py-=2.5*s
    return (ox+w/2+lining,oy+h+lining)

def draw_slope_protection(msp, origin, slope_h=8.0, slope_ratio=1.5, s_type="frame", scale=100.0, label="", params=None, layer="边坡", tracker=None):
    """边坡支护剖面。slope_h m; slope_ratio 坡比; s_type: frame/vegetation/net"""
    s=scale; ox,oy=_r(*origin); h=slope_h*s; l=h*slope_ratio
    # 边坡线
    msp.add_line((ox,oy),(ox+l,oy+h),dxfattribs={"layer":layer})
    msp.add_line((ox,oy+h),(ox+l,oy+h),dxfattribs={"layer":"细实线","linetype":"DASHDOT"})
    if s_type=="frame":
        grid_rows=4;grid_cols=3
        for i in range(grid_rows+1):
            frac=i/grid_rows; sx=ox+l*frac; sy=oy+h*frac
            msp.add_line((sx,sy),(sx+l*(1-frac)*0.7,sy+h*(1-frac)*0.7),dxfattribs={"layer":"细实线"})
        for i in range(grid_cols+1):
            frac=i/grid_cols; cy=oy+h*frac
            msp.add_line((ox,cy),(ox+l,cy+h),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    elif s_type=="vegetation":
        for i in range(6):
            frac=(i+0.5)/6; gx=ox+l*frac; gy=oy+h*frac
            msp.add_line((gx,gy),(gx-1*s,gy+2*s),dxfattribs={"layer":layer})
            for d in [-1,1]:
                msp.add_line((gx-1*s,gy+2*s),(gx-1*s+d*1.5*s,gy+3*s),dxfattribs={"layer":"细实线"})
    elif s_type=="net":
        for i in range(10):
            frac=(i+0.5)/10; gx=ox+l*frac; gy=oy+h*frac
            msp.add_circle((gx,gy-1*s),1*s,dxfattribs={"layer":layer})
        msp.add_line((ox+1*s,oy-1*s),(ox+l-1*s,oy+h-1*s),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    if label:
        t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"})
        t.set_placement((ox+l/2,oy+h+4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+l,oy+h)

# ══════ v1.5+ 土木增补：框架节点/剪力墙/空间网架 ══════
def draw_frame_joint(msp,origin,width=0.5,depth=0.5,beam_w=0.3,beam_d=0.6,scale=100.0,label="",layer="结构",tracker=None):
    s=scale*2;ox,oy=_r(*origin);cw=width*s;cd=depth*s;bw=beam_w*s;bd=beam_d*s
    msp.add_lwpolyline([(ox,oy),(ox+cw,oy),(ox+cw,oy+cd),(ox,oy+cd)],close=True,dxfattribs={"layer":layer})
    for(lx,ly,lw,lh)in[(ox-bd,oy,2*bd,bw),(ox-bd,oy+cd-bw,2*bd,bw),(ox,oy-bd,cw,bd*2),(ox+cw-bw,oy-bd,bw,bd*2)]:msp.add_lwpolyline([(lx,ly),(lx+lw,ly),(lx+lw,ly+lh),(lx,ly+lh)],close=True,dxfattribs={"layer":layer})
    msp.add_lwpolyline([(ox+2*s,oy+2*s),(ox+cw-2*s,oy+2*s),(ox+cw-2*s,oy+cd-2*s),(ox+2*s,oy+cd-2*s)],close=True,dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+cw/2,oy+cd+5*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_shear_wall(msp,origin,length=8.0,height=30.0,thickness=0.3,scale=100.0,label="",layer="结构",tracker=None):
    s=scale;ox,oy=_r(*origin);L=length*s;H=height*s
    msp.add_lwpolyline([(ox,oy),(ox+L,oy),(ox+L,oy+H),(ox,oy+H)],close=True,dxfattribs={"layer":layer})
    for i in range(1,8):msp.add_line((ox,oy+H*i/8),(ox+L,oy+H*i/8),dxfattribs={"layer":"细实线"})
    t=msp.add_text(f"{thickness*1000:.0f}mm",dxfattribs={"layer":"文字","height":2.5*s,"style":"HZ"});t.set_placement((ox+L/2,oy-4*s),align=TextEntityAlignment.MIDDLE_CENTER)
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+L/2,oy+H+5*s),align=TextEntityAlignment.MIDDLE_CENTER)

def draw_space_frame(msp,origin,span_x=30.0,span_y=40.0,height=3.0,module_size=3.0,scale=100.0,label="",layer="结构",tracker=None):
    s=scale;ox,oy=_r(*origin);sx=span_x*s;sy=span_y*s
    nx=int(span_x/module_size);ny=int(span_y/module_size)
    for i in range(nx+1):
        for j in range(ny+1):
            px,py=ox+i*sx/nx,oy+j*sy/ny
            if i<nx:msp.add_line((px,py),(ox+(i+1)*sx/nx,py),dxfattribs={"layer":layer})
            if j<ny:msp.add_line((px,py),(px,oy+(j+1)*sy/ny),dxfattribs={"layer":layer})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3.5*s,"style":"HZ"});t.set_placement((ox+sx/2,oy+sy+5*s),align=TextEntityAlignment.MIDDLE_CENTER)


def draw_retaining_wall(msp, origin, H=3.0, top_w=0.3, base_w=1.5, base_h=0.5,
                        backfill_h=2.5, scale=100.0, label="挡土墙", layer="结构", tracker=None):
    """重力式挡土墙：墙身+基础+回填土标记+排水孔。"""
    s=scale;ox,oy=_r(*origin);hs,tw,bw,bh=H*s,top_w*s,base_w*s,base_h*s
    # 墙身（梯形）
    msp.add_lwpolyline([(ox+bw/2-tw/2,oy),(ox+bw/2+tw/2,oy),(ox+bw,oy-hs),(ox,oy-hs)],close=True,dxfattribs={"layer":layer})
    # 基础
    msp.add_lwpolyline([(ox-1*s,oy-hs),(ox+bw+1*s,oy-hs),(ox+bw+1*s,oy-hs-bh),(ox-1*s,oy-hs-bh)],close=True,dxfattribs={"layer":layer})
    # 回填土标记
    bfh=backfill_h*s
    for xi in range(4):
        msp.add_line((ox+bw/2-tw/2+xi*s*2,oy),(ox+bw/2-tw/2+xi*s*2,oy-bfh),dxfattribs={"layer":"细实线","linetype":"DASHED"})
    msp.add_line((ox+bw/2-tw/2,oy-bfh),(ox+bw/2-tw/2+6*s,oy-bfh),dxfattribs={"layer":"细实线"})
    # 排水孔
    for yi in range(2):
        dy=oy-hs*0.3-yi*0.3*hs
        msp.add_circle((ox+bw/2,dy),1.5*s,dxfattribs={"layer":"细实线"})
    if label:t=msp.add_text(label,dxfattribs={"layer":"文字-标题","height":3*s,"style":"HZ"});t.set_placement((ox+bw/2,oy+5*s),align=TextEntityAlignment.MIDDLE_CENTER)
    return (ox+bw+6*s,oy-hs-bh)
