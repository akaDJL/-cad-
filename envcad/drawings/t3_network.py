"""测试3：污水自流管网平面布置图。

调节池至厌氧池污水自流管道，总长 12m，DN350 HDPE，坡度 0.3%；
依次安装手动闸阀、橡胶软接头、电磁流量计；穿墙处设刚性防水套管；
标注管径、管内底标高、坡度流向；配套图例。
"""
from __future__ import annotations

import os

from ..engine.dxf_base import new_drawing, save_dxf
from ..standards.frame import FrameInfo, draw_frame, save_dxf_autofit
from ..standards.annotate import _t, draw_elevation, draw_slope, draw_flow_arrow, draw_pipe_diameter
from ..standards.legend import draw_legend
from ..components.pipe import draw_pipe
from ..components.fittings import draw_valve, draw_soft_joint, draw_flow_meter, draw_wall_sleeve
from . import draw_tech_notes
from ezdxf.enums import TextEntityAlignment


def gen_t3(out_dir: str, scale: float = 50.0,
           length: float = 12000.0, dn: float = 350.0,
           slope: float = 0.003, start_il: float = -1.200) -> str:
    doc, dim, tracker = new_drawing(scale, return_tracker=True)
    msp = doc.modelspace()
    info = FrameInfo(
        title="污水自流管网平面布置图",
        drawing_no="T3-01",
        scale_str=f"1:{int(scale)}",
        project="工艺管线测试",
        unit="环保工程",
        designer="envcad",
        date="2026.07",
    )
    x0, y0, x1, y1 = draw_frame(doc, scale, info, tracker=tracker)

    # 管中线
    pipe_y = y0 + (y1 - y0) * 0.45
    px0 = x0 + 2500          # 调节池墙（起点）
    px1 = px0 + length       # 厌氧池墙（终点）

    # 调节池墙、厌氧池墙（剖面线方块）
    _wall(msp, px0, pipe_y, scale)
    _wall(msp, px1, pipe_y, scale)

    # 管段（单线）
    draw_pipe(msp, (px0, pipe_y), (px1, pipe_y), dn=dn, scale=scale,
              style="single", layer="管道-污水")

    # 管件（沿管轴）
    valve_x = px0 + length * 0.18
    joint_x = px0 + length * 0.40
    meter_x = px0 + length * 0.62
    draw_valve(msp, (valve_x, pipe_y), scale, "h", label="手动闸阀")
    draw_soft_joint(msp, (joint_x, pipe_y), scale, "h", label="橡胶软接头")
    draw_flow_meter(msp, (meter_x, pipe_y), scale, "h", label="电磁流量计")
    # 穿墙刚性防水套管（厌氧池墙处）
    draw_wall_sleeve(msp, (px1, pipe_y), scale, wall_thick=250, dn=dn, orientation="h",
                     label="刚性防水套管")

    # 管径标注
    draw_pipe_diameter(msp, (px0 + length * 0.30, pipe_y), f"DN{int(dn)} HDPE", scale,
                       leader_dir=(0, -1), label="")

    # 管内底标高（起点、终点）
    end_il = start_il - slope * (length / 1000)  # 顺流下降
    draw_elevation(msp, (px0, pipe_y - 4 * scale), f"{start_il:.3f}", scale, side="left")
    draw_elevation(msp, (px1, pipe_y - 4 * scale), f"{end_il:.3f}", scale, side="right")

    # 坡度 + 坡向
    slope_pct = slope * 100
    draw_slope(msp, (px0, pipe_y), (px1, pipe_y), f"{slope_pct:.1f}%", scale, offset=10.0)

    # 水流方向箭头（调节池→厌氧池）
    draw_flow_arrow(msp, (px0 + length * 0.50, pipe_y - 10 * scale), (1, 0), scale,
                    length=20.0, label="水流方向")

    # 管长标注
    _t(msp, f"L={int(length)}mm  i={slope_pct:.1f}%",
       ((px0 + px1) / 2, pipe_y + 12 * scale), 3 * scale,
       align=TextEntityAlignment.MIDDLE_CENTER, layer="文字",
       tracker=tracker)

    # 调节池/厌氧池标注
    _t(msp, "调节池", (px0 - 3 * scale, pipe_y + 8 * scale), 3 * scale, layer="文字-标题",
       tracker=tracker)
    _t(msp, "厌氧池", (px1 + 3 * scale, pipe_y + 8 * scale), 3 * scale, layer="文字-标题",
       tracker=tracker)

    # 图例
    draw_legend(msp, (x1 - 50 * scale, y1 - 75 * scale), scale,
                [("pipe_solid", "污水管", f"DN{int(dn)} HDPE"),
                 ("valve", "手动闸阀", "DN350"),
                 ("soft_joint", "橡胶软接头", "DN350"),
                 ("flow_meter", "电磁流量计", "DN350"),
                 ("sleeve", "刚性防水套管", "DN350"),
                 ("arrow_flow", "水流方向", "顺坡"),
                 ("elevation", "管内底标高", "单位 m")],
                tracker=tracker)

    # 技术要求
    draw_tech_notes(msp, (x0 + 3 * scale, y1 - 32 * scale), scale,
                    "管道施工技术要求",
                    [f"管材采用 HDPE 管 DN{int(dn)}，电熔连接。",
                     f"管道坡度 {slope_pct:.1f}%，坡向水流方向，严禁倒坡。",
                     "穿墙处设刚性防水套管，套管与管道间填麻丝沥青密封。",
                     "闸阀、软接头、流量计安装间距满足检修要求。",
                     "管道施工及验收执行 GB 50268—2008。"],
                    tracker=tracker)

    return save_dxf_autofit(doc, os.path.join(out_dir, "T3_污水自流管网平面布置图.dxf"), scale, info, tracker)


def _wall(msp, x, pipe_y, scale):
    s = scale
    half = 125  # 墙厚 250 一半
    pts = [(x - half, pipe_y - 5 * s), (x + half, pipe_y - 5 * s),
           (x + half, pipe_y + 5 * s), (x - half, pipe_y + 5 * s)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "粗实线"})
    from ..components.fittings import _hatch
    _hatch(msp, pts)
