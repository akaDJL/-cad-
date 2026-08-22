"""图框图幅尺寸感知测试（GB/T 14689 A0~A4 + 横/纵）。

验证 envcad.standards.frame 不再写死 A3：
  * 默认仍为 A2 横式（向后兼容）；
  * 进程级默认 set_default_paper_size / set_default_orientation 生效；
  * FrameInfo.size / orientation 显式覆盖进程级默认；
  * 标题栏随图幅等比缩放。
"""
import ezdxf
import pytest

from envcad.standards.frame import (
    draw_frame, FrameInfo,
    set_default_paper_size, set_default_orientation,
    _resolve_sheet, PAPER_BASE, TITLE_SCALE, _DEFAULT_PAPER_SIZE,
)


def _outer_dims(info=None, scale=100.0):
    """取模型空间所有 LWPOLYLINE 的包围盒尺寸（即图幅外框）。"""
    doc = ezdxf.new()
    draw_frame(doc, scale, info or FrameInfo())
    msp = doc.modelspace()
    xs, ys = [], []
    for e in msp.query("LWPOLYLINE"):
        for x, y in e.get_points("xy"):
            xs.append(x)
            ys.append(y)
    return round(max(xs) - min(xs)), round(max(ys) - min(ys))


def _title_block_dims(info=None, scale=100.0):
    """找标题栏多段线（尺寸最接近 180*tb x 56*tb）并返回 (w, h)。"""
    doc = ezdxf.new()
    draw_frame(doc, scale, info or FrameInfo())
    msp = doc.modelspace()
    size = info.size if info and info.size else None
    tb = TITLE_SCALE.get((size or "A2").upper(), 1.0)
    target_w = 180 * tb * scale
    target_h = 56 * tb * scale
    best = None
    for e in msp.query("LWPOLYLINE"):
        pts = e.get_points("xy")
        w = max(p[0] for p in pts) - min(p[0] for p in pts)
        h = max(p[1] for p in pts) - min(p[1] for p in pts)
        if abs(w - target_w) < 2 and abs(h - target_h) < 2:
            best = (round(w), round(h))
            break
    return best


@pytest.fixture(autouse=True)
def _reset_default():
    """每个用例后复位为 A2 横式，避免进程级默认串味。"""
    yield
    set_default_paper_size("A2")
    set_default_orientation("landscape")


def test_default_is_A2_landscape():
    w, h = _outer_dims(scale=100)
    assert (w, h) == (59400, 42000), "默认必须仍是 A2 横式"


def test_process_default_A1():
    set_default_paper_size("A1")
    w, h = _outer_dims(scale=100)
    assert (w, h) == (84100, 59400)


def test_process_default_portrait_swaps():
    set_default_paper_size("A4")
    set_default_orientation("portrait")
    w, h = _outer_dims(scale=100)
    # A4 纵式：短边水平、长边垂直
    assert (w, h) == (21000, 29700)


def test_explicit_FrameInfo_overrides_global():
    set_default_paper_size("A4")  # 全局被改成 A4
    # 显式指定 A0，应忽略全局
    w, h = _outer_dims(FrameInfo(size="A0"), 100)
    assert (w, h) == (118900, 84100)


def test_explicit_portrait_overrides_global():
    set_default_paper_size("A2")
    set_default_orientation("landscape")
    w, h = _outer_dims(FrameInfo(size="A2", orientation="portrait"), 100)
    assert (w, h) == (42000, 59400)


def test_title_block_scales_with_sheet():
    # A3 标题栏 = 180x56（×100）
    assert _title_block_dims(FrameInfo(size="A3"), 100) == (18000, 5600)
    # A0 标题栏按 tb=1.8 放大 = 324x100.8 ≈ 32400x10080
    tb = TITLE_SCALE["A0"]
    assert _title_block_dims(FrameInfo(size="A0"), 100) == (
        round(180 * tb * 100), round(56 * tb * 100))


def test_resolve_sheet_unknown_falls_back_default():
    W, H, tb, s = _resolve_sheet("Z9", None)
    assert s == _DEFAULT_PAPER_SIZE
    assert (W, H) == PAPER_BASE[_DEFAULT_PAPER_SIZE]


def test_backward_compat_aliases():
    from envcad.standards.frame import A3_W, A3_H
    assert (A3_W, A3_H) == PAPER_BASE["A3"]
