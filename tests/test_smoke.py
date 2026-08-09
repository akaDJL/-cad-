"""冒烟测试：验证关键模块可导入、核心链路可出图。"""
import os, sys, ezdxf, pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_import_core():
    """核心模块导入"""
    from envcad.standards.dim import draw_dimension
    from envcad.standards.mechanical import draw_spur_gear
    from envcad.standards.layers import setup_layers
    assert callable(draw_dimension)
    assert callable(draw_spur_gear)
    assert callable(setup_layers)


def test_import_standards():
    """标准模块导入"""
    for mod in ["frame", "layers", "styles", "annotate", "building", "hvac",
                "electrical", "plumbing", "hydraulic", "paperspace"]:
        __import__(f"envcad.standards.{mod}")


def test_import_engine():
    """引擎模块导入"""
    from envcad.engine.collision_fix import post_process_overlaps
    from envcad.engine.parametric_bridge import resolve_intent, parametric_cli
    assert resolve_intent("齿轮齿数 19")["domain"] == "mechanical"
    assert resolve_intent("齿轮齿数 19")["param"] == "z"


def test_draw_dimension_works():
    """标注出图"""
    from envcad.standards.dim import draw_dimension
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    draw_dimension(msp, (0, 0), (100, 0), text="test")
    doc.saveas("out/pytest_dim.dxf")
    assert os.path.exists("out/pytest_dim.dxf")


def test_draw_gear_works():
    """零件出图"""
    from envcad.standards.mechanical import draw_spur_gear
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    draw_spur_gear(msp, (50, 50), z=19)
    doc.saveas("out/pytest_gear.dxf")
    assert os.path.exists("out/pytest_gear.dxf")


def test_setup_layers_works():
    """线型图层"""
    from envcad.standards.layers import setup_layers
    doc = ezdxf.new("R2018")
    setup_layers(doc)
    doc.saveas("out/pytest_layers.dxf")
    assert os.path.exists("out/pytest_layers.dxf")


def test_collision_fix():
    """碰撞检测"""
    from envcad.engine.collision_fix import post_process_overlaps
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    for i in range(20):
        msp.add_line((i * 10, 0), (i * 10 + 5, 30))
    for i in range(20):
        t = msp.add_text("X")
        t.set_placement((i * 10, 35))
    n = post_process_overlaps(doc)
    assert n >= 0  # crash-free


def test_paperspace():
    """纸空间布局"""
    from envcad.standards.paperspace import create_layout, add_viewport
    doc = ezdxf.new("R2018")
    layout = create_layout(doc, "Test", "A3")
    add_viewport(layout, (210, 148), 380, 270, 100)
    assert layout.name == "Test"


def test_parametric_bridge():
    """参数化桥接"""
    from envcad.engine.parametric_bridge import parametric_cli
    p = parametric_cli("齿轮齿数 19", "out/pytest_param", scale=50)
    assert p is not None
    assert os.path.exists(p)


def test_font_fallback():
    """字体回退不崩溃"""
    from envcad.standards.styles import HZ_FONT
    assert isinstance(HZ_FONT, str)
