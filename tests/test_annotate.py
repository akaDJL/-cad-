"""一键标注命令回归测试。

关键防护：用独立进程 + 超时运行 cli.main(['annotate', ...])，
避免历史上『遍历 modelspace 时插入标注实体导致无限循环』的缺陷复发时拖垮整个 pytest。
"""
import os
import sys
import tempfile
import glob

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeout


def _run_annotate_worker(out_dir, gdt=False, input_dxf=None):
    """在子进程里跑 annotate，返回生成文件的实体数。"""
    from envcad import cli
    import ezdxf

    argv = ["annotate", "--out", out_dir]
    if gdt:
        argv.append("--gdt")
    if input_dxf:
        argv += ["--in", input_dxf]
    rc = cli.main(argv)
    if input_dxf:
        path = os.path.join(out_dir, "annotate_annotated.dxf")
    else:
        path = os.path.join(out_dir, "annotate.dxf")
    assert os.path.exists(path), f"标注输出未生成: {path}"
    doc = ezdxf.readfile(path)
    n = sum(1 for _ in doc.modelspace())
    return {"rc": rc, "n": n, "path": path}


def _safe_run(out_dir, gdt=False, input_dxf=None, timeout=30):
    with ProcessPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_run_annotate_worker, out_dir, gdt, input_dxf)
        try:
            return fut.result(timeout=timeout)
        except FuturesTimeout:
            pytest.fail(f"annotate 命令在 {timeout}s 内未完成（疑似无限循环回归）")


def test_annotate_demo_default():
    """默认演示底图一键标注：生成 DXF 且实体数合理（不应无限膨胀）。"""
    d = tempfile.mkdtemp()
    res = _safe_run(d)
    assert res["rc"] == 0
    assert 50 < res["n"] < 500, f"实体数异常: {res['n']}"


def test_annotate_with_gdt():
    """--gdt 机械形位公差版本应正常完成。"""
    d = tempfile.mkdtemp()
    res = _safe_run(d, gdt=True)
    assert res["rc"] == 0
    assert res["n"] > 0


def test_annotate_on_existing_dxf():
    """--in 标注已有图应完成且实体数收敛（不应爆炸到成千上万）。"""
    d = tempfile.mkdtemp()
    base = _safe_run(d)  # 先生成底图
    d2 = tempfile.mkdtemp()
    res = _safe_run(d2, input_dxf=base["path"])
    assert res["rc"] == 0
    assert res["n"] < 5000, f"--in 重标注实体数爆炸: {res['n']}"


def _run_annotate_cmd(argv):
    """在子进程里跑 cli.main，返回 {rc, paths}。"""
    from envcad import cli
    rc = cli.main(argv)
    # 根据 argv 推断输出路径
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else None
    import os, glob
    paths = sorted(glob.glob(os.path.join(out_dir, "*.dxf"))) if out_dir else []
    return {"rc": rc, "paths": paths}


def _safe_cmd(argv, timeout=30):
    with ProcessPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_run_annotate_cmd, argv)
        try:
            return fut.result(timeout=timeout)
        except FuturesTimeout:
            pytest.fail(f"annotate 命令在 {timeout}s 内未完成")


def test_batch_directory():
    """--in 指向目录时批量处理所有 .dxf。"""
    import ezdxf
    d_in = tempfile.mkdtemp()
    d_out = tempfile.mkdtemp()
    # 两个 DXF
    for name, layer in [("池体A", "粗实线"), ("池体B", "墙体")]:
        doc = ezdxf.new("R2018"); msp = doc.modelspace()
        msp.add_lwpolyline([(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
                           close=True, dxfattribs={"layer": layer})
        doc.saveas(os.path.join(d_in, f"{name}.dxf"))
    res = _safe_cmd(["annotate", "--in", d_in, "--out", d_out])
    assert res["rc"] == 0
    assert len(res["paths"]) == 2, f"应生成 2 个标注文件，实际: {res['paths']}"
    for p in res["paths"]:
        doc = ezdxf.readfile(p)
        n = sum(1 for _ in doc.modelspace())
        assert 30 < n < 500, f"{os.path.basename(p)} 实体数异常: {n}"


def test_contour_label_from_layer():
    """闭合轮廓应自动从图层名推断标签（如 粗实线→池体1）。"""
    import ezdxf
    d_in = tempfile.mkdtemp()
    d_out = tempfile.mkdtemp()
    path = os.path.join(d_in, "test.dxf")
    doc = ezdxf.new("R2018"); msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (5000, 0), (5000, 3000), (0, 3000)],
                       close=True, dxfattribs={"layer": "粗实线"})
    doc.saveas(path)
    _safe_cmd(["annotate", "--in", d_in, "--out", d_out])
    out_paths = sorted(glob.glob(os.path.join(d_out, "*.dxf")))
    assert out_paths, "未生成标注文件"
    doc = ezdxf.readfile(out_paths[0])
    mtexts = [e for e in doc.modelspace() if e.dxftype() == "MTEXT"]
    labels = [e.text for e in mtexts]
    assert any("池体1" in lbl for lbl in labels), f"未找到轮廓标签 '池体1'，MTEXT 内容: {labels}"


def test_empty_directory():
    """空目录批量标注应返回 1。"""
    d_empty = tempfile.mkdtemp()
    d_out = tempfile.mkdtemp()
    res = _safe_cmd(["annotate", "--in", d_empty, "--out", d_out])
    assert res["rc"] == 1
    assert res["paths"] == []
