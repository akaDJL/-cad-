# -*- coding: utf-8 -*-
"""用户订阅数据 / 自有数据库的 drop-in 接入点。

把「你订阅的所有类型数据、规范、理论」统一放在这里即可被全插件调用：
  1) 直接在此文件 USER_SUBSCRIPTION 字典里追加（适合少量、保密数据）；
  2) 或在插件目录放一份 envcad/knowledge/user_subscription.json，
     运行时会被自动合并覆盖（适合频繁更新的外部订阅导出）。

合并后可通过 get_user_data(key) / list_user_keys() 读取，
绘图、设计、文档三处共用，无需改动业务代码。
"""
from __future__ import annotations

import json
import os

# ── 内置占位（示例结构，删改随你）──────────────────────────
USER_SUBSCRIPTION = {
    # 例：「某图集库」常用构造做法
    # "构造做法": {"散水": "宽600 混凝土C20", ...},
    # 例：「订阅的某地风压雪压」
    # "地方风雪压": {"阳泉": {"基本风压": 0.40, "基本雪压": 0.30}},
    # 例：「自定义规范补充」
    # "补充规范": {"DBJxx": "山西省某地方标准"},
}

_JSON_PATH = os.path.join(os.path.dirname(__file__), "user_subscription.json")


def _load_json() -> dict:
    if not os.path.exists(_JSON_PATH):
        return {}
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as _e:
        return {}


def get_user_data(key=None):
    """返回合并后的用户数据；不传 key 返回整本字典。"""
    data = dict(USER_SUBSCRIPTION)
    data.update(_load_json())  # JSON 优先覆盖
    if key is None:
        return data
    return data.get(key)


def list_user_keys() -> list:
    """列出当前可用的用户数据键。"""
    data = dict(USER_SUBSCRIPTION)
    data.update(_load_json())
    return list(data.keys())


def reload_user_data() -> int:
    """重新加载并统计条目数（供 CLI 自检）。"""
    return len(list_user_keys())
