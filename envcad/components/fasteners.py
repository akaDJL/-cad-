"""紧固件组件（GB 国标 + 非标自定义）：螺栓 / 螺母 / 螺钉 / 垫圈。

按机械制图国标画法（GB/T 4459.1—1995 螺纹画法）绘制：
  * 螺栓 GB/T 5780—2016（六角头螺栓 C 级）/ GB/T 5782—2016（六角头螺栓）
  * 螺母 GB/T 6170—2015（1 型六角螺母）/ GB/T 41—2016（六角螺母 C 级）
  * 螺钉 GB/T 70.1—2008（内六角）/ GB/T 818—2016（盘头十字）
  * 垫圈 GB/T 97.1—2002（平垫圈）/ GB/T 93—1987（弹簧垫圈）

所有函数接收 TrackedMSpace 或原始 ModelSpace，绘制主视图（侧视）+ 俯视图，
尺寸乘 scale（出图比例倒数），与 fittings.py 风格一致。
"""
from __future__ import annotations
import re

import math
from typing import Optional, Tuple, List, Dict

from ezdxf.enums import TextEntityAlignment

from ..standards.annotate import _t


# ─── 内部辅助 ───────────────────────────────────────────

def _line(msp, p1, p2, layer):
    msp.add_line(p1, p2, dxfattribs={"layer": layer})


def _poly(msp, pts, layer, close=True):
    msp.add_lwpolyline(pts, close=close, dxfattribs={"layer": layer})


def _rect(msp, x, y, w, h, layer):
    """画矩形（闭合多段线）。"""
    _poly(msp, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer)


# ─── 国标规格参数表 ──────────────────────────────────────
# 每条记录: (螺纹规格 d, 螺距 P, s 对边宽度, k 头部高度, e 对角宽度)
# 数据来源：GB/T 5782 / GB/T 5780 / GB/T 6170 / GB/T 41

GB_BOLTS = {
    # GB/T 5782 六角头螺栓（部分）— (d, P, s, k, e)
    "M3":   (3,   0.5, 5.5,  2.0,  6.01),
    "M4":   (4,   0.7, 7.0,  2.8,  7.66),
    "M5":   (5,   0.8, 8.0,  3.5,  8.79),
    "M6":   (6,   1.0, 10.0, 4.0,  11.05),
    "M8":   (8,   1.25, 13.0, 5.3, 14.38),
    "M10":  (10,  1.5, 16.0, 6.4, 17.77),
    "M12":  (12,  1.75, 18.0, 7.5, 20.03),
    "M16":  (16,  2.0, 24.0, 10.0, 26.75),
    "M20":  (20,  2.5, 30.0, 12.5, 33.53),
    "M24":  (24,  3.0, 36.0, 15.0, 39.98),
}

GB_NUTS = {
    # GB/T 6170 1 型六角螺母 — (d, P, s, m, e)  m=螺母高度
    "M3":   (3,   0.5, 5.5,  2.4,  6.01),
    "M4":   (4,   0.7, 7.0,  3.2,  7.66),
    "M5":   (5,   0.8, 8.0,  4.7,  8.79),
    "M6":   (6,   1.0, 10.0, 5.2,  11.05),
    "M8":   (8,   1.25, 13.0, 6.8, 14.38),
    "M10":  (10,  1.5, 16.0, 8.4, 17.77),
    "M12":  (12,  1.75, 18.0, 10.8, 20.03),
    "M16":  (16,  2.0, 24.0, 14.8, 26.75),
    "M20":  (20,  2.5, 30.0, 18.0, 33.53),
    "M24":  (24,  3.0, 36.0, 21.5, 39.98),
}

GB_SCREWS_HEX_SOCKET = {
    # GB/T 70.1 内六角螺钉 — (d, P, dk头部直径, k头部高度, t内六角深度)
    "M3":   (3,   0.5, 5.5,  3.0, 1.3),
    "M4":   (4,   0.7, 7.0,  4.0, 2.0),
    "M5":   (5,   0.8, 8.5,  5.0, 2.5),
    "M6":   (6,   1.0, 10.0, 6.0, 3.0),
    "M8":   (8,   1.25, 13.0, 8.0, 4.0),
    "M10":  (10,  1.5, 16.0, 10.0, 5.0),
    "M12":  (12,  1.75, 18.0, 12.0, 6.0),
    "M16":  (16,  2.0, 24.0, 16.0, 8.0),
}

GB_SCREWS_PAN = {
    # GB/T 818 盘头十字螺钉 — (d, P, dk, k, rmin)
    "M3":   (3,   0.5, 5.6, 2.4, 0.1),
    "M4":   (4,   0.7, 8.0, 3.1, 0.2),
    "M5":   (5,   0.8, 9.5, 3.7, 0.2),
    "M6":   (6,   1.0, 12.0, 4.6, 0.25),
    "M8":   (8,   1.25, 16.0, 6.0, 0.4),
}

GB_WASHERS = {
    # GB/T 97.1 平垫圈 — (d内径, d2外径, h厚度)
    "M3":   (3.2,  7.0,  0.5),
    "M4":   (4.3,  9.0,  0.8),
    "M5":   (5.3,  10.0, 1.0),
    "M6":   (6.4,  12.0, 1.6),
    "M8":   (8.4,  16.0, 1.6),
    "M10":  (10.5, 20.0, 2.0),
    "M12":  (13.0, 24.0, 2.5),
    "M16":  (17.0, 30.0, 3.0),
    "M20":  (21.0, 37.0, 3.0),
    "M24":  (25.0, 44.0, 4.0),
}

GB_SPRING_WASHERS = {
    # GB/T 93 标准弹簧垫圈 — (d内径, d2外径, h厚度)
    "M3":   (3.1,  6.0, 1.6),
    "M4":   (4.1,  8.0, 2.2),
    "M5":   (5.1,  10.0, 2.6),
    "M6":   (6.1,  11.5, 3.0),
    "M8":   (8.1,  14.5, 3.6),
    "M10":  (10.2, 18.0, 4.2),
    "M12":  (12.2, 21.0, 5.0),
    "M16":  (16.2, 28.0, 6.5),
    "M20":  (20.2, 34.0, 8.0),
    "M24":  (24.5, 40.0, 9.5),
}


# ─── 联网回退累积缓存（运行时 + 落盘）─────────────────────
# 结构: { 'bolt': {spec: params}, 'nut': {...}, 'screw': {...}, 'washer': {...} }
_BACKFILL_PATH = __import__("os").path.join(
    __import__("os").path.dirname(__import__("os").path.dirname(__file__)),
    "knowledge", "web_cache", "fasteners_backfill.json")

_BACKFILL: Dict[str, Dict[str, Dict]] = {}


def _load_backfill() -> None:
    """启动时加载已沉淀的联网结果（仅执行一次）。"""
    import os, json
    if _BACKFILL:
        return
    if os.path.exists(_BACKFILL_PATH):
        try:
            with open(_BACKFILL_PATH, "r", encoding="utf-8") as f:
                _BACKFILL.update(json.load(f))
        except Exception:
            pass


def _save_backfill() -> None:
    """把累积结果落盘，供下次启动复用。"""
    import os, json
    try:
        os.makedirs(os.path.dirname(_BACKFILL_PATH), exist_ok=True)
        with open(_BACKFILL_PATH, "w", encoding="utf-8") as f:
            json.dump(_BACKFILL, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _verify_from_hits(kind_key: str, hits: List) -> Dict[str, float]:
    """从搜索结果（含 authority 与 url）抓权威页面正文抽取精确尺寸。

    返回 {字段: 数值}；不足关键字段则返回可能为空 dict。
    联网失败 / 抽取不足均返回 {}（交由调用方退回估算）。
    """
    from ..engine.web_search import extract_fastener_params, _fetch_html
    verified: Dict[str, float] = {}
    try:
        for h in sorted(hits, key=lambda x: getattr(x, "authority", 0), reverse=True):
            html = _fetch_html(getattr(h, "url", ""))
            if not html:
                continue
            params = extract_fastener_params(html, kind_key)
            for kk, vv in params.items():
                if kk not in verified and vv > 0:
                    verified[kk] = vv
            if kind_key in ("bolt", "nut") and "s" in verified:
                break
            if kind_key == "washer" and "d1" in verified and "d2" in verified:
                break
    except Exception:
        return {}
    return verified


def _web_lookup_fallback(spec: str, kind_zh: str, std_guess: str, kind_key: str) -> Dict:
    """本地未收录规格时的联网回退：不报错，检索权威尺寸并沉淀。

    流程：先查本地落盘缓存 → 命中直接返回；否则联网检索，优先抓权威页面正文
    抽取精确尺寸（_verified），抽取不足则退回按比例估算（_estimated）。
    返回 dict 含尺寸字段与 _refs（权威链接）。
    """
    _load_backfill()
    cache = _BACKFILL.setdefault(kind_key, {})
    if spec in cache:
        rec = dict(cache[spec])
        rec["_from_cache"] = True
        return rec
    # 基础估算（兜底）
    m = re.search(r"(\d+(?:\.\d+)?)", spec)
    d = float(m.group(1)) if m else 10.0
    rec = {
        "d": d, "P": round(d * 0.15, 2), "s": round(d * 1.6, 1),
        "k": round(d * 0.6, 1), "e": round(d * 1.8, 2),
        "d1": round(d * 1.1, 1), "d2": round(d * 2.0, 1), "h": round(d * 0.2, 1),
        "m": round(d * 0.8, 1), "dk": round(d * 1.7, 1),
        "_estimated": True,
        "_note": f"本地未收录 {kind_zh} {spec}，已联网检索权威出处（数值为估算，以标准为准）",
        "_refs": [],
    }
    try:
        from ..engine.web_search import search as _raw_search
        q = f"{std_guess} {spec} 尺寸"
        hits = _raw_search(q, max_results=5)
        verified = _verify_from_hits(kind_key, hits)
        if verified:
            for kk, vv in verified.items():
                rec[kk] = round(vv, 3)
            rec["_estimated"] = False
            rec["_verified"] = True
            rec["_note"] = (
                f"本地未收录 {kind_zh} {spec}，已联网抓取权威页面正文抽取精确尺寸"
            )
        rec["_refs"] = [{"title": getattr(h, "title", ""),
                         "url": getattr(h, "url", "")} for h in hits[:3]]
    except Exception:
        pass
    cache[spec] = rec
    _save_backfill()
    return rec


def get_bolt_params(spec: str, length: float = 30.0,
                    custom: Optional[Dict] = None) -> Dict:
    """获取螺栓参数。spec 如 'M10'，custom 可覆盖任意参数。

    返回 dict: d, P, s,  k, e, L, b(螺纹长度)。
    本地未收录时自动联网检索权威尺寸（不报错）。
    """
    if custom:
        p = {"d": 10, "P": 1.5, "s": 16, "k": 6.4, "e": 17.77}
        p.update(custom)
    else:
        if spec not in GB_BOLTS:
            fb = _web_lookup_fallback(spec, "螺栓", "GB/T 5782", "bolt")
            fb["L"] = length
            return fb
        d, P, s, k, e = GB_BOLTS[spec]
        p = {"d": d, "P": P, "s": s, "k": k, "e": e}
    p["L"] = length
    # 螺纹长度 b（近似）
    if p["d"] <= 8:
        p["b"] = min(length, 16 + 2 * p["d"])
    elif p["d"] <= 20:
        p["b"] = min(length, 22 + 2 * p["d"])
    else:
        p["b"] = min(length, 38 + 2.5 * p["d"])
    return p


def get_nut_params(spec: str, custom: Optional[Dict] = None) -> Dict:
    """获取螺母参数。返回 dict: d, P, s, m, e。本地未收录时自动联网检索。"""
    if custom:
        p = {"d": 10, "P": 1.5, "s": 16, "m": 8.4, "e": 17.77}
        p.update(custom)
    else:
        if spec not in GB_NUTS:
            return _web_lookup_fallback(spec, "螺母", "GB/T 6170", "nut")
        d, P, s, m, e = GB_NUTS[spec]
        p = {"d": d, "P": P, "s": s, "m": m, "e": e}
    return p


def get_screw_params(spec: str, screw_type: str = "hex_socket",
                     length: float = 20.0,
                     custom: Optional[Dict] = None) -> Dict:
    """获取螺钉参数。screw_type: 'hex_socket'(内六角) / 'pan'(盘头十字)。本地未收录时自动联网检索。"""
    table = GB_SCREWS_HEX_SOCKET if screw_type == "hex_socket" else GB_SCREWS_PAN
    if custom:
        p = {"d": 6, "P": 1.0, "dk": 10, "k": 6}
        if screw_type == "hex_socket":
            p["t"] = 3.0
        else:
            p["rmin"] = 0.25
        p.update(custom)
    else:
        if spec not in table:
            fb = _web_lookup_fallback(spec, "螺钉", "GB/T 70.1", "screw")
            fb["L"] = length
            fb["type"] = screw_type
            fb["b"] = min(length, max(2 * fb["d"], 12))
            return fb
        row = table[spec]
        if screw_type == "hex_socket":
            d, P, dk, k, t = row
            p = {"d": d, "P": P, "dk": dk, "k": k, "t": t}
        else:
            d, P, dk, k, rmin = row
            p = {"d": d, "P": P, "dk": dk, "k": k, "rmin": rmin}
    p["L"] = length
    p["type"] = screw_type
    # 螺纹长度（螺钉通常全螺纹或部分）
    p["b"] = min(length, max(2 * p["d"], 12))
    return p


def get_washer_params(spec: str, washer_type: str = "flat",
                      custom: Optional[Dict] = None) -> Dict:
    """获取垫圈参数。washer_type: 'flat'(平垫) / 'spring'(弹簧垫)。本地未收录时自动联网检索。"""
    table = GB_WASHERS if washer_type == "flat" else GB_SPRING_WASHERS
    if custom:
        p = {"d1": 10.5, "d2": 20.0, "h": 2.0}
        p.update(custom)
    else:
        if spec not in table:
            fb = _web_lookup_fallback(spec, "垫圈", "GB/T 97.1", "washer")
            fb["type"] = washer_type
            return fb
        d1, d2, h = table[spec]
        p = {"d1": d1, "d2": d2, "h": h}
    p["type"] = washer_type
    return p


# ─── 螺栓绘制 ───────────────────────────────────────────

def draw_hex_bolt(msp, center, scale: float, spec: str = "M10",
                  length: float = 30.0, orientation: str = "h",
                  custom: Optional[Dict] = None,
                  label: str = None, tracker=None):
    """六角头螺栓（GB/T 5782 / 5780）：主视图（侧视）+ 俯视图。

    主视图：六角头 + 圆柱杆 + 螺纹线
    俯视图：六边形外接圆

    center: 主视图头部底面中心点
    orientation: 'h' 杆水平向右 / 'v' 杆竖直向上
    返回 (主视图末端中心, 俯视图中心)
    """
    p = get_bolt_params(spec, length, custom)
    s = scale
    d, P, sw, k, e, L, b = (p["d"], p["P"], p["s"], p["k"], p["e"],
                             p["L"], p["b"])
    cx, cy = center

    if orientation == "h":
        # ── 主视图（水平）──
        # 六角头（简化：矩形 + 倒角线）
        head_x = cx
        _rect(msp, head_x, cy - sw / 2 * s, k * s, sw * s, "粗实线")
        # 头部倒角线（近似）
        _line(msp, (head_x, cy - sw / 2 * s),
              (head_x + k * 0.3 * s, cy - sw / 2 * s + k * 0.2 * s), "粗实线")
        _line(msp, (head_x, cy + sw / 2 * s),
              (head_x + k * 0.3 * s, cy + sw / 2 * s - k * 0.2 * s), "粗实线")
        # 杆
        rod_x = head_x + k * s
        _rect(msp, rod_x, cy - d / 2 * s, L * s, d * s, "粗实线")
        # 螺纹线（细实线，杆底部偏移 P*0.85*s）
        thread_end = rod_x + b * s
        _line(msp, (rod_x, cy - d / 2 * s * 0.85),
              (thread_end, cy - d / 2 * s * 0.85), "细实线")
        _line(msp, (rod_x, cy + d / 2 * s * 0.85),
              (thread_end, cy + d / 2 * s * 0.85), "细实线")
        # 螺纹终止线
        _line(msp, (thread_end, cy - d / 2 * s),
              (thread_end, cy + d / 2 * s), "细实线")
        # 末端倒角
        _line(msp, (rod_x + L * s, cy - d / 2 * s),
              (rod_x + L * s - d * 0.3 * s, cy), "粗实线")
        _line(msp, (rod_x + L * s, cy + d / 2 * s),
              (rod_x + L * s - d * 0.3 * s, cy), "粗实线")
        # 中心线
        _line(msp, (head_x - 2 * s, cy), (rod_x + L * s + 5 * s, cy), "点画线")

        main_end = (rod_x + L * s, cy)
        # ── 俯视图（六边形）──
        top_cx = cx + k * s / 2
        top_cy = cy - sw * s - 10 * s
        _draw_hexagon(msp, top_cx, top_cy, e / 2 * s, "粗实线")
        # 内圆（螺纹孔）
        msp.add_circle((top_cx, top_cy), d / 2 * s * 0.85,
                       dxfattribs={"layer": "细实线"})
        msp.add_circle((top_cx, top_cy), d / 2 * s,
                       dxfattribs={"layer": "粗实线"})

        if label:
            _t(msp, f"{spec}×{int(L)}", (cx + (k + L) * s / 2, cy + sw * s),
               3.5 * s, align=TextEntityAlignment.MIDDLE_CENTER,
               layer="文字", tracker=tracker)
    else:
        # ── 主视图（竖直）──
        head_y = cy
        _rect(msp, cx - sw / 2 * s, head_y - k * s, sw * s, k * s, "粗实线")
        # 倒角线
        _line(msp, (cx - sw / 2 * s, head_y),
              (cx - sw / 2 * s + k * 0.2 * s, head_y - k * 0.3 * s), "粗实线")
        _line(msp, (cx + sw / 2 * s, head_y),
              (cx + sw / 2 * s - k * 0.2 * s, head_y - k * 0.3 * s), "粗实线")
        # 杆（向下）
        rod_y = head_y - k * s
        _rect(msp, cx - d / 2 * s, rod_y - L * s, d * s, L * s, "粗实线")
        # 螺纹线
        thread_end_y = rod_y - b * s
        _line(msp, (cx - d / 2 * s * 0.85, rod_y),
              (cx - d / 2 * s * 0.85, thread_end_y), "细实线")
        _line(msp, (cx + d / 2 * s * 0.85, rod_y),
              (cx + d / 2 * s * 0.85, thread_end_y), "细实线")
        _line(msp, (cx - d / 2 * s, thread_end_y),
              (cx + d / 2 * s, thread_end_y), "细实线")
        # 末端倒角
        _line(msp, (cx - d / 2 * s, rod_y - L * s),
              (cx, rod_y - L * s + d * 0.3 * s), "粗实线")
        _line(msp, (cx + d / 2 * s, rod_y - L * s),
              (cx, rod_y - L * s + d * 0.3 * s), "粗实线")
        # 中心线
        _line(msp, (cx, head_y + 2 * s),
              (cx, rod_y - L * s - 5 * s), "点画线")

        main_end = (cx, rod_y - L * s)
        # 俯视图
        top_cx = cx + sw * s + 10 * s
        top_cy = cy - k * s / 2
        _draw_hexagon(msp, top_cx, top_cy, e / 2 * s, "粗实线")
        msp.add_circle((top_cx, top_cy), d / 2 * s * 0.85,
                       dxfattribs={"layer": "细实线"})
        msp.add_circle((top_cx, top_cy), d / 2 * s,
                       dxfattribs={"layer": "粗实线"})

        if label:
            _t(msp, f"{spec}×{int(L)}", (cx + sw * s, cy - (k + L) * s / 2),
               3.5 * s, align=TextEntityAlignment.MIDDLE_CENTER,
               layer="文字", tracker=tracker)

    return main_end, (top_cx, top_cy)


def _draw_hexagon(msp, cx, cy, r, layer):
    """画正六边形（顶点朝上/下）。"""
    pts = []
    for i in range(6):
        a = math.pi / 6 + i * math.pi / 3  # 30°起步
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    _poly(msp, pts, layer)


# ─── 螺母绘制 ───────────────────────────────────────────

def draw_hex_nut(msp, center, scale: float, spec: str = "M10",
                 orientation: str = "h",
                 custom: Optional[Dict] = None,
                 label: str = None, tracker=None):
    """六角螺母（GB/T 6170 / 41）：主视图 + 俯视图。

    center: 主视图中心
    返回 (主视图右侧端, 俯视图中心)
    """
    p = get_nut_params(spec, custom)
    s = scale
    d, P, sw, m, e = (p["d"], p["P"], p["s"], p["m"], p["e"])
    cx, cy = center

    if orientation == "h":
        # 主视图（水平）：矩形 + 倒角 + 螺纹孔
        _rect(msp, cx, cy - sw / 2 * s, m * s, sw * s, "粗实线")
        # 倒角线
        _line(msp, (cx, cy - sw / 2 * s),
              (cx + m * 0.2 * s, cy - sw / 2 * s + m * 0.15 * s), "粗实线")
        _line(msp, (cx, cy + sw / 2 * s),
              (cx + m * 0.2 * s, cy + sw / 2 * s - m * 0.15 * s), "粗实线")
        _line(msp, (cx + m * s, cy - sw / 2 * s),
              (cx + m * 0.8 * s, cy - sw / 2 * s + m * 0.15 * s), "粗实线")
        _line(msp, (cx + m * s, cy + sw / 2 * s),
              (cx + m * 0.8 * s, cy + sw / 2 * s - m * 0.15 * s), "粗实线")
        # 螺纹线（3/4 圆 + 细线）
        _line(msp, (cx, cy - d / 2 * s * 0.85),
              (cx + m * s, cy - d / 2 * s * 0.85), "细实线")
        _line(msp, (cx, cy + d / 2 * s * 0.85),
              (cx + m * s, cy + d / 2 * s * 0.85), "细实线")
        # 中心线
        _line(msp, (cx - 2 * s, cy), (cx + m * s + 5 * s, cy), "点画线")

        main_end = (cx + m * s, cy)
        # 俯视图
        top_cx = cx + m * s / 2
        top_cy = cy - sw * s - 10 * s
        _draw_hexagon(msp, top_cx, top_cy, e / 2 * s, "粗实线")
        msp.add_circle((top_cx, top_cy), d / 2 * s * 0.85,
                       dxfattribs={"layer": "细实线"})
        msp.add_circle((top_cx, top_cy), d / 2 * s,
                       dxfattribs={"layer": "粗实线"})
    else:
        # 竖直
        _rect(msp, cx - sw / 2 * s, cy - m * s, sw * s, m * s, "粗实线")
        _line(msp, (cx - sw / 2 * s, cy),
              (cx - sw / 2 * s + m * 0.15 * s, cy - m * 0.2 * s), "粗实线")
        _line(msp, (cx + sw / 2 * s, cy),
              (cx + sw / 2 * s - m * 0.15 * s, cy - m * 0.2 * s), "粗实线")
        _line(msp, (cx - sw / 2 * s, cy - m * s),
              (cx - sw / 2 * s + m * 0.15 * s, cy - m * 0.8 * s), "粗实线")
        _line(msp, (cx + sw / 2 * s, cy - m * s),
              (cx + sw / 2 * s - m * 0.15 * s, cy - m * 0.8 * s), "粗实线")
        _line(msp, (cx - d / 2 * s * 0.85, cy - m * s),
              (cx - d / 2 * s * 0.85, cy), "细实线")
        _line(msp, (cx + d / 2 * s * 0.85, cy - m * s),
              (cx + d / 2 * s * 0.85, cy), "细实线")
        _line(msp, (cx, cy + 2 * s), (cx, cy - m * s - 5 * s), "点画线")

        main_end = (cx, cy - m * s)
        top_cx = cx + sw * s + 10 * s
        top_cy = cy - m * s / 2
        _draw_hexagon(msp, top_cx, top_cy, e / 2 * s, "粗实线")
        msp.add_circle((top_cx, top_cy), d / 2 * s * 0.85,
                       dxfattribs={"layer": "细实线"})
        msp.add_circle((top_cx, top_cy), d / 2 * s,
                       dxfattribs={"layer": "粗实线"})

    if label:
        _t(msp, spec, (top_cx, top_cy + e / 2 * s + 5 * s), 3.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)

    return main_end, (top_cx, top_cy)


# ─── 螺钉绘制 ───────────────────────────────────────────

def draw_screw(msp, center, scale: float, spec: str = "M6",
               length: float = 20.0, screw_type: str = "hex_socket",
               orientation: str = "h",
               custom: Optional[Dict] = None,
               label: str = None, tracker=None):
    """螺钉（内六角 / 盘头十字）：主视图 + 俯视图。

    screw_type: 'hex_socket' GB/T 70.1 / 'pan' GB/T 818
    center: 主视图头部底面中心
    返回 (主视图末端中心, 俯视图中心)
    """
    p = get_screw_params(spec, screw_type, length, custom)
    s = scale
    d, P, dk, k, L, b = (p["d"], p["P"], p["dk"], p["k"],
                           p["L"], p["b"])
    cx, cy = center

    if orientation == "h":
        if screw_type == "hex_socket":
            # 内六角头：圆柱头
            _rect(msp, cx, cy - dk / 2 * s, k * s, dk * s, "粗实线")
            # 内六角孔（俯视为六边形，主视简化为小矩形）
            _rect(msp, cx + k * 0.3 * s, cy - dk / 4 * s,
                  k * 0.3 * s, dk / 2 * s, "细实线")
        else:
            # 盘头：半圆头
            _rect(msp, cx, cy - dk / 2 * s, k * 0.6 * s, dk * s, "粗实线")
            # 圆弧顶（近似用圆弧）
            msp.add_arc((cx + k * 0.6 * s, cy), dk / 2 * s,
                        90, 270, dxfattribs={"layer": "粗实线"})
            # 十字槽（俯视可见，主视省略）

        # 杆
        rod_x = cx + k * s
        _rect(msp, rod_x, cy - d / 2 * s, L * s, d * s, "粗实线")
        # 螺纹线
        thread_end = rod_x + b * s
        _line(msp, (rod_x, cy - d / 2 * s * 0.85),
              (thread_end, cy - d / 2 * s * 0.85), "细实线")
        _line(msp, (rod_x, cy + d / 2 * s * 0.85),
              (thread_end, cy + d / 2 * s * 0.85), "细实线")
        _line(msp, (thread_end, cy - d / 2 * s),
              (thread_end, cy + d / 2 * s), "细实线")
        # 中心线
        _line(msp, (cx - 2 * s, cy), (rod_x + L * s + 5 * s, cy), "点画线")

        main_end = (rod_x + L * s, cy)
        # 俯视图
        top_cx = cx + k * s / 2
        top_cy = cy - dk * s - 10 * s
        msp.add_circle((top_cx, top_cy), dk / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        if screw_type == "hex_socket":
            _draw_hexagon(msp, top_cx, top_cy, dk / 4 * s, "细实线")
        else:
            # 十字槽
            _line(msp, (top_cx - dk / 3 * s, top_cy),
                  (top_cx + dk / 3 * s, top_cy), "细实线")
            _line(msp, (top_cx, top_cy - dk / 3 * s),
                  (top_cx, top_cy + dk / 3 * s), "细实线")
    else:
        if screw_type == "hex_socket":
            _rect(msp, cx - dk / 2 * s, cy - k * s, dk * s, k * s, "粗实线")
            _rect(msp, cx - dk / 4 * s, cy - k * 0.7 * s,
                  dk / 2 * s, k * 0.3 * s, "细实线")
        else:
            _rect(msp, cx - dk / 2 * s, cy - k * 0.6 * s, dk * s, k * 0.6 * s,
                  "粗实线")
            msp.add_arc((cx, cy - k * 0.6 * s), dk / 2 * s,
                        0, 180, dxfattribs={"layer": "粗实线"})

        rod_y = cy - k * s
        _rect(msp, cx - d / 2 * s, rod_y - L * s, d * s, L * s, "粗实线")
        thread_end_y = rod_y - b * s
        _line(msp, (cx - d / 2 * s * 0.85, rod_y),
              (cx - d / 2 * s * 0.85, thread_end_y), "细实线")
        _line(msp, (cx + d / 2 * s * 0.85, rod_y),
              (cx + d / 2 * s * 0.85, thread_end_y), "细实线")
        _line(msp, (cx - d / 2 * s, thread_end_y),
              (cx + d / 2 * s, thread_end_y), "细实线")
        _line(msp, (cx, cy + 2 * s),
              (cx, rod_y - L * s - 5 * s), "点画线")

        main_end = (cx, rod_y - L * s)
        top_cx = cx + dk * s + 10 * s
        top_cy = cy - k * s / 2
        msp.add_circle((top_cx, top_cy), dk / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        if screw_type == "hex_socket":
            _draw_hexagon(msp, top_cx, top_cy, dk / 4 * s, "细实线")
        else:
            _line(msp, (top_cx - dk / 3 * s, top_cy),
                  (top_cx + dk / 3 * s, top_cy), "细实线")
            _line(msp, (top_cx, top_cy - dk / 3 * s),
                  (top_cx, top_cy + dk / 3 * s), "细实线")

    if label:
        _t(msp, f"{spec}×{int(L)}", (top_cx, top_cy + dk / 2 * s + 5 * s),
           3.5 * s, align=TextEntityAlignment.MIDDLE_CENTER,
           layer="文字", tracker=tracker)

    return main_end, (top_cx, top_cy)


# ─── 垫圈绘制 ───────────────────────────────────────────

def draw_washer(msp, center, scale: float, spec: str = "M10",
                washer_type: str = "flat",
                orientation: str = "h",
                custom: Optional[Dict] = None,
                label: str = None, tracker=None):
    """垫圈（平垫 / 弹簧垫）：主视图（剖面）+ 俯视图。

    center: 主视图中心
    返回 (主视图右侧端, 俯视图中心)
    """
    p = get_washer_params(spec, washer_type, custom)
    s = scale
    d1, d2, h = (p["d1"], p["d2"], p["h"])
    cx, cy = center

    if orientation == "h":
        # 主视图（剖面：两个矩形表示垫圈截面）
        w_h = h * s
        outer_w = (d2 - d1) / 2 * s
        x_left = cx
        x_right = cx + outer_w
        _rect(msp, x_left, cy - w_h / 2, outer_w, w_h, "粗实线")
        # 剖面线
        try:
            hatch = msp.add_hatch(color=7, dxfattribs={"layer": "剖面线"})
            hatch.paths.add_polyline_path(
                [(x_left, cy - w_h / 2), (x_right, cy - w_h / 2),
                 (x_right, cy + w_h / 2), (x_left, cy + w_h / 2)],
                is_closed=True)
            hatch.set_pattern_fill("ANSI31", scale=1.5)
        except Exception as _e:
            print(f'[WARNING] fasteners.py: {_e}')

        main_end = (x_right, cy)
        # 俯视图（同心圆）
        top_cx = cx + outer_w / 2
        top_cy = cy - d2 * s - 10 * s
        msp.add_circle((top_cx, top_cy), d2 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        msp.add_circle((top_cx, top_cy), d1 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
    else:
        w_h = h * s
        outer_h = (d2 - d1) / 2 * s
        y_top = cy
        y_bot = cy - outer_h
        _rect(msp, cx - w_h / 2, y_bot, w_h, outer_h, "粗实线")
        try:
            hatch = msp.add_hatch(color=7, dxfattribs={"layer": "剖面线"})
            hatch.paths.add_polyline_path(
                [(cx - w_h / 2, y_bot), (cx + w_h / 2, y_bot),
                 (cx + w_h / 2, y_top), (cx - w_h / 2, y_top)],
                is_closed=True)
            hatch.set_pattern_fill("ANSI31", scale=1.5)
        except Exception as _e:
            print(f'[WARNING] fasteners.py: {_e}')

        main_end = (cx, y_bot)
        top_cx = cx + d2 * s + 10 * s
        top_cy = cy - outer_h / 2
        msp.add_circle((top_cx, top_cy), d2 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        msp.add_circle((top_cx, top_cy), d1 / 2 * s,
                       dxfattribs={"layer": "粗实线"})

    if label:
        _t(msp, spec, (top_cx, top_cy + d2 / 2 * s + 5 * s), 3.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)

    return main_end, (top_cx, top_cy)


def draw_spring_washer(msp, center, scale: float, spec: str = "M10",
                       orientation: str = "h",
                       custom: Optional[Dict] = None,
                       label: str = None, tracker=None):
    """弹簧垫圈（GB/T 93）：开口的倾斜环。

    主视图画成一个带开口的矩形截面，俯视图画成一个开口圆环。
    center: 主视图中心
    返回 (主视图右侧端, 俯视图中心)
    """
    p = get_washer_params(spec, "spring", custom)
    s = scale
    d1, d2, h = (p["d1"], p["d2"], p["h"])
    cx, cy = center
    w_h = h * s
    outer_w = (d2 - d1) / 2 * s

    if orientation == "h":
        # 主视图：倾斜的矩形截面（弹簧垫圈特征）
        tilt = h * 0.3 * s
        pts = [(cx, cy - w_h / 2),
               (cx + outer_w, cy - w_h / 2 + tilt),
               (cx + outer_w, cy + w_h / 2 + tilt),
               (cx, cy + w_h / 2)]
        _poly(msp, pts, "粗实线")

        main_end = (cx + outer_w, cy)
        # 俯视图：开口圆环
        top_cx = cx + outer_w / 2
        top_cy = cy - d2 * s - 10 * s
        # 外圆
        msp.add_circle((top_cx, top_cy), d2 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        # 内圆
        msp.add_circle((top_cx, top_cy), d1 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        # 开口（一条短线表示开口）
        gap_x = top_cx + d2 / 2 * s
        _line(msp, (gap_x, top_cy - h * 0.5 * s),
              (gap_x, top_cy + h * 0.5 * s), "粗实线")
    else:
        tilt = h * 0.3 * s
        pts = [(cx - w_h / 2, cy),
               (cx - w_h / 2 + tilt, cy - outer_w),
               (cx + w_h / 2 + tilt, cy - outer_w),
               (cx + w_h / 2, cy)]
        _poly(msp, pts, "粗实线")

        main_end = (cx, cy - outer_w)
        top_cx = cx + d2 * s + 10 * s
        top_cy = cy - outer_w / 2
        msp.add_circle((top_cx, top_cy), d2 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        msp.add_circle((top_cx, top_cy), d1 / 2 * s,
                       dxfattribs={"layer": "粗实线"})
        gap_y = top_cy - d2 / 2 * s
        _line(msp, (top_cx - h * 0.5 * s, gap_y),
              (top_cx + h * 0.5 * s, gap_y), "粗实线")

    if label:
        _t(msp, spec, (top_cx, top_cy + d2 / 2 * s + 5 * s), 3.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER, layer="文字", tracker=tracker)

    return main_end, (top_cx, top_cy)


# ─── 螺栓组件（螺栓+垫圈+螺母装配图）─────────────────────

def draw_bolt_assembly(msp, center, scale: float, spec: str = "M10",
                       length: float = 30.0, grip: float = 20.0,
                       orientation: str = "h",
                       label: str = None, tracker=None):
    """螺栓装配组件：螺栓 + 平垫圈 + 弹簧垫圈 + 螺母。

    grip: 夹紧厚度（被连接件总厚度）
    自动计算需要的螺栓长度（取标准值）。
    center: 螺栓头部底面中心
    返回 (末端中心, 规格标注位置)
    """
    s = scale
    p = get_bolt_params(spec, length)
    d = p["d"]

    # 垫圈参数
    wp_flat = get_washer_params(spec, "flat")
    wp_spring = get_washer_params(spec, "spring")
    np = get_nut_params(spec)
    h_flat = wp_flat["h"]
    h_spring = wp_spring["h"]
    m_nut = np["m"]

    cx, cy = center

    if orientation == "h":
        # 被连接件（简化为两个矩形剖面）
        plate_w = d * 4 * s
        plate_h = grip / 2 * s
        _rect(msp, cx + p["k"] * s, cy - plate_w / 2,
              plate_h, plate_w, "中实线")
        _rect(msp, cx + p["k"] * s + plate_h, cy - plate_w / 2,
              plate_h, plate_w, "中实线")
        # 剖面线
        for px in [cx + p["k"] * s, cx + p["k"] * s + plate_h]:
            try:
                hatch = msp.add_hatch(color=7, dxfattribs={"layer": "剖面线"})
                hatch.paths.add_polyline_path(
                    [(px, cy - plate_w / 2), (px + plate_h, cy - plate_w / 2),
                     (px + plate_h, cy + plate_w / 2), (px, cy + plate_w / 2)],
                    is_closed=True)
                hatch.set_pattern_fill("ANSI31", scale=2.0)
            except Exception as _e:
                print(f'[WARNING] fasteners.py: {_e}')

        # 螺栓（穿过被连接件）
        draw_hex_bolt(msp, center, scale, spec, length, "h",
                      label=None, tracker=tracker)

        # 螺母（在杆末端）
        nut_cx = cx + (p["k"] + length - m_nut) * s
        draw_hex_nut(msp, (nut_cx, cy), scale, spec, "h",
                     label=None, tracker=tracker)

        # 中心线
        _line(msp, (cx - 2 * s, cy),
              (cx + (p["k"] + length + 5) * s, cy), "点画线")

        end = (cx + (p["k"] + length) * s, cy)
    else:
        plate_w = d * 4 * s
        plate_h = grip / 2 * s
        _rect(msp, cx - plate_w / 2, cy - p["k"] * s - plate_h * 2,
              plate_w, plate_h, "中实线")
        _rect(msp, cx - plate_w / 2, cy - p["k"] * s - plate_h,
              plate_w, plate_h, "中实线")
        for py in [cy - p["k"] * s - plate_h * 2, cy - p["k"] * s - plate_h]:
            try:
                hatch = msp.add_hatch(color=7, dxfattribs={"layer": "剖面线"})
                hatch.paths.add_polyline_path(
                    [(cx - plate_w / 2, py), (cx + plate_w / 2, py),
                     (cx + plate_w / 2, py + plate_h), (cx - plate_w / 2, py + plate_h)],
                    is_closed=True)
                hatch.set_pattern_fill("ANSI31", scale=2.0)
            except Exception as _e:
                print(f'[WARNING] fasteners.py: {_e}')

        draw_hex_bolt(msp, center, scale, spec, length, "v",
                      label=None, tracker=tracker)
        nut_cy = cy - (p["k"] + length - m_nut) * s
        draw_hex_nut(msp, (cx, nut_cy), scale, spec, "v",
                     label=None, tracker=tracker)
        _line(msp, (cx, cy + 2 * s),
              (cx, cy - (p["k"] + length + 5) * s), "点画线")
        end = (cx, cy - (p["k"] + length) * s)

    if label:
        _t(msp, f"{spec}×{int(length)}", (cx + (p["k"] + length) * s / 2,
           cy + d * 3 * s), 3.5 * s,
           align=TextEntityAlignment.MIDDLE_CENTER,
           layer="文字", tracker=tracker)

    return end, (cx + (p["k"] + length) * s / 2, cy + d * 3 * s)


# ─── 批量生成规格列表 ────────────────────────────────────

# ─── 联网估算值"转正"（promote）──────────────────────────
# 把联网回退沉淀下来的 _estimated 条目，正式合并进国标源码表，
# 下次直接当标准用，不再走估算/联网流程。
_PROMOTE_FIELDS = {
    "bolt":   ("GB_BOLTS", ("d", "P", "s", "k", "e")),
    "nut":    ("GB_NUTS", ("d", "P", "s", "m", "e")),
    "screw":  ("GB_SCREWS_TABLE", ("d", "P", "dk", "k")),  # 特殊处理见下
    "washer": ("GB_WASHERS_TABLE", ("d1", "d2", "h")),       # 特殊处理见下
}


def _promote_one(kind_key: str, spec: str, rec: Dict) -> Optional[tuple]:
    """计算单条 _estimated 记录转正后的 (table_name, spec, fields)，不写全局表。

    返回 (table_name, spec, fields) 或 None（已转正/非估算/字段缺失）。
    """
    if not (rec.get("_estimated") or rec.get("_verified")):
        return None
    if rec.get("_promoted"):
        return None
    try:
        if kind_key == "bolt":
            t = (float(rec["d"]), float(rec["P"]), float(rec["s"]),
                 float(rec["k"]), float(rec["e"]))
            return ("GB_BOLTS", spec, t)
        elif kind_key == "nut":
            t = (float(rec["d"]), float(rec["P"]), float(rec["s"]),
                 float(rec["m"]), float(rec["e"]))
            return ("GB_NUTS", spec, t)
        elif kind_key == "screw":
            # screw 表区分 hex_socket / pan，按 rec["type"] 决定落哪个表
            st = rec.get("type", "hex_socket")
            if st == "hex_socket":
                t = (float(rec["d"]), float(rec["P"]), float(rec["dk"]),
                     float(rec["k"]), float(rec.get("t", 3.0)))
                return ("GB_SCREWS_HEX_SOCKET", spec, t)
            else:
                t = (float(rec["d"]), float(rec["P"]), float(rec["dk"]),
                     float(rec["k"]), float(rec.get("rmin", 0.25)))
                return ("GB_SCREWS_PAN", spec, t)
        elif kind_key == "washer":
            # washer 表区分 flat / spring，按 rec["type"] 决定落哪个表
            wt = rec.get("type", "flat")
            t = (float(rec["d1"]), float(rec["d2"]), float(rec["h"]))
            if wt == "flat":
                return ("GB_WASHERS", spec, t)
            else:
                return ("GB_SPRING_WASHERS", spec, t)
    except (KeyError, ValueError, TypeError):
        return None
    return None


def _apply_promoted(table_name: str, spec: str, fields: tuple) -> None:
    """把转正结果写入对应的全局国标表（实际生效）。"""
    global GB_BOLTS, GB_NUTS, GB_SCREWS_HEX_SOCKET, GB_SCREWS_PAN, GB_WASHERS, GB_SPRING_WASHERS
    {
        "GB_BOLTS": GB_BOLTS,
        "GB_NUTS": GB_NUTS,
        "GB_SCREWS_HEX_SOCKET": GB_SCREWS_HEX_SOCKET,
        "GB_SCREWS_PAN": GB_SCREWS_PAN,
        "GB_WASHERS": GB_WASHERS,
        "GB_SPRING_WASHERS": GB_SPRING_WASHERS,
    }[table_name][spec] = fields


def promote_backfill(kind_key: str = None, dry_run: bool = False) -> List[tuple]:
    """把联网估算沉淀转正进国标源码表。

    kind_key: 限定类型 'bolt'/'nut'/'screw'/'washer'，None 表示全部。
    dry_run: True 只返回将要转正的条目，不实际修改表/不落盘。
    返回被转正的 [(table_name, spec, fields), ...]
    """
    _load_backfill()
    promoted = []
    targets = [kind_key] if kind_key else list(_BACKFILL.keys())
    for kk in targets:
        cache = _BACKFILL.get(kk, {})
        for spec, rec in list(cache.items()):
            res = _promote_one(kk, spec, rec)
            if res:
                promoted.append(res)
                if not dry_run:
                    _apply_promoted(*res)
                    rec["_promoted"] = True
                    rec["_promoted_at"] = __import__("datetime").datetime.now().isoformat()
    if promoted and not dry_run:
        _save_backfill()
    return promoted


def list_specs(component: str = "bolt") -> List[str]:
    """列出某类紧固件的可用国标规格。

    component: 'bolt' / 'nut' / 'screw_hex' / 'screw_pan' /
               'washer_flat' / 'washer_spring'
    """
    tables = {
        "bolt": GB_BOLTS,
        "nut": GB_NUTS,
        "screw_hex": GB_SCREWS_HEX_SOCKET,
        "screw_pan": GB_SCREWS_PAN,
        "washer_flat": GB_WASHERS,
        "washer_spring": GB_SPRING_WASHERS,
    }
    table = tables.get(component, GB_BOLTS)
    return list(table.keys())
