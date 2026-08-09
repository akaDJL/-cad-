"""multiCAD-mcp COM 桥接：把生成的 DXF 推送到 AutoCAD/ZWCAD/GstarCAD/BricsCAD。

v1.5 加固：
  - 超时保护（COM Dispatch 可能挂死在后台）
  - 静默模式（不弹主窗口、不阻塞 stdin）
  - 错误分类（未安装 / 已安装但忙 / 打开失败）
  - detect_cad 返回 (name, status)，而非仅 name

能力与 multiCAD-mcp 同源（Windows COM 自动化）。提供：
  * detect_cad()        —— 探测已注册的 CAD COM，返回 (name, detail)
  * push_to_cad(path)   —— 在 CAD 里打开 DXF（静默模式默认不弹窗）
  * list_layers_in_cad  —— 读取当前 CAD 图层

不强制依赖 pywin32（缺失时给出清晰提示）。
"""
from __future__ import annotations

import os
import threading
from typing import Literal

CAD_PROGIDS = {
    "autocad": "AutoCAD.Application",
    "zwcad": "ZWCAD.Application",
    "gstarcad": "GstarCAD.Application",
    "bricscad": "BricscadApp.AcadApplication",
}

CAD_INSTALL_GUIDE = {
    "autocad": "请安装 AutoCAD 并注册 COM 组件",
    "zwcad": "请安装 ZWCAD（中望CAD）并注册 COM 组件",
    "gstarcad": "请安装 GstarCAD（浩辰CAD）并注册 COM 组件",
    "bricscad": "请安装 BricsCAD 并注册 COM 组件",
}

_DISPATCH_TIMEOUT = 8.0  # 秒


# ── 内部工具 ──────────────────────────────

def _try_import_win32() -> bool:
    try:
        import win32com.client  # noqa: F401
        import pythoncom  # noqa: F401
        return True
    except ImportError:
        return False


def _win32_help() -> str:
    return (
        "pywin32 未安装。安装后可使用 COM 推送功能：\n"
        "  pip install pywin32\n"
        "  python Scripts/pywin32_postinstall.py -install"
    )


class _DispatchTimeout(Exception):
    """COM Dispatch 超时。"""


def _dispatch_with_timeout(progid: str, timeout: float = _DISPATCH_TIMEOUT):
    """在后台线程中执行 COM Dispatch，超时则抛 _DispatchTimeout。"""
    import win32com.client
    import pythoncom

    result = [None]
    error = [None]

    def _worker():
        pythoncom.CoInitialize()
        try:
            result[0] = win32com.client.Dispatch(progid)
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        # 线程仍活着 → Dispatch 挂死
        raise _DispatchTimeout(
            f"COM Dispatch('{progid}') 超时（{timeout}s），{CAD_INSTALL_GUIDE.get(progid.split('.')[0].lower(), '请确认 CAD 已安装')}"
        )
    if error[0]:
        raise error[0]
    return result[0]


# ── 公开 API ─────────────────────────────

def detect_cad(include_status: bool = False) -> str | None | tuple[str | None, str]:
    """返回第一个可用的 CAD 名（小写）。
    
    无 CAD 时：
      include_status=False → 返回 None
      include_status=True  → 返回 (None, reason_string)

    优先 GetActiveObject（已运行实例），不启动新进程。
    """
    if not _try_import_win32():
        if include_status:
            return None, _win32_help()
        return None

    import win32com.client
    import pythoncom

    pythoncom.CoInitialize()
    for name, progid in CAD_PROGIDS.items():
        try:
            obj = win32com.client.GetActiveObject(progid)
            if obj:
                if include_status:
                    return name, f"已运行的 {name.upper()} 实例"
                return name
        except Exception as _e:
            print(f'[WARNING] multicad_bridge.py: {_e}')

    # GetActiveObject 全失败 → 尝试 Dispatch（会启动新进程，仅探测不实际启动）
    # 改用简短的版本检测
    try:
        for name, progid in CAD_PROGIDS.items():
            try:
                app = win32com.client.Dispatch(progid)
                ver = ""
                try:
                    ver = f" v{app.Version}"
                except Exception as _e:
                    ver = ""
                try:
                    app.Quit()
                except Exception as _e:
                    print(f'[WARNING] multicad_bridge.py: {_e}')
                if include_status:
                    return name, f"{name.upper()}{ver} 已安装（当前未运行）"
                return name
            except Exception as _e:
                continue
    except Exception as _e:
        print(f'[警告] 操作失败：{_e}')

    if include_status:
        return None, "未检测到已安装的 CAD（AutoCAD/ZWCAD/GstarCAD/BricsCAD）"
    return None


def push_to_cad(
    dxf_path: str,
    cad: str = "autocad",
    visible: bool = False,
    timeout: float = _DISPATCH_TIMEOUT,
) -> tuple[bool, str]:
    """在 CAD 里打开 DXF。返回 (success, message)。

    Args:
        dxf_path: DXF 绝对路径
        cad: autocad / zwcad / gstarcad / bricscad
        visible: 是否显示 CAD 主窗口（默认静默）
        timeout: COM Dispatch 超时秒数
    """
    if not _try_import_win32():
        return False, _win32_help()

    dxf_path = os.path.abspath(dxf_path)
    if not os.path.exists(dxf_path):
        return False, f"DXF 文件不存在: {dxf_path}"

    progid = CAD_PROGIDS.get(cad.lower())
    if not progid:
        return False, f"不支持的 CAD: {cad}（支持: {', '.join(CAD_PROGIDS)}）"

    import win32com.client
    import pythoncom

    pythoncom.CoInitialize()

    # Dispatch with timeout protection
    try:
        app = _dispatch_with_timeout(progid, timeout)
    except _DispatchTimeout as e:
        return False, str(e)
    except Exception as e:
        err = str(e)
        if "CoInitialize" in err.lower():
            return False, f"COM 初始化失败: {err}（请确认 {cad.upper()} 已正确安装）"
        return False, f"启动 {cad.upper()} 失败: {err} | {CAD_INSTALL_GUIDE.get(cad.lower(), '')}"

    # Open DXF
    try:
        if visible:
            try:
                app.Visible = True
            except Exception as _e:
                print(f'[WARNING] multicad_bridge.py: {_e}')  # 某些版本不支持设置为 Visible

        # 先尝试 GetActiveObject 复用已打开文档
        doc = None
        try:
            doc = app.ActiveDocument
        except Exception as _e:
            print(f'[WARNING] multicad_bridge.py: {_e}')

        # Open / Import
        try:
            docs = app.Documents
            docs.Open(dxf_path)
        except Exception as _e:
            try:
                doc = docs.Add()
                doc.Import(dxf_path)
                if not visible and hasattr(doc, "Close"):
                    pass  # 保持打开，由调用方决定
            except Exception as e2:
                return False, f"打开 DXF 失败: {e2}（文件可能损坏或 CAD 版本不兼容）"

        return True, f"已推送到 {cad.upper()}"

    except Exception as e:
        return False, f"打开 DXF 时出错: {e}"


def list_layers_in_cad(cad: str = "autocad") -> list[str]:
    """读取当前 CAD 文档图层名列表。无 CAD 返回空列表。"""
    if not _try_import_win32():
        return []

    import win32com.client
    import pythoncom

    pythoncom.CoInitialize()
    progid = CAD_PROGIDS.get(cad.lower(), "")

    try:
        app = win32com.client.GetActiveObject(progid)
    except Exception as _e:
        return []

    try:
        doc = app.ActiveDocument
        if doc is None:
            return []
        return [lt.Name for lt in doc.Layers]
    except Exception as _e:
        return []
