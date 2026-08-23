# -*- coding: utf-8 -*-
"""ima 订阅知识库同步引擎。

职责：
1. 按名称/ID 搜索并枚举用户加入的 ima 共享知识库；
2. 拉取每个知识库的文档列表与文本内容；
3. 用简单规则从文档中提取 GB 国标、设计参数、设备尺寸、材料规格；
4. 沉淀为 envcad/knowledge/ 下的 Python 数据模块，供制图/设计/文档生成统一引用。

注意：
- 本模块只提供"本地解析与写入"逻辑；
- 真正调用 ima MCP 拉取内容的部分由 WorkBuddy 会话中的 AI 完成（MCP 在当前会话可用，独立 Python 进程无法直接调用）。
- 用户也可以把 ima 中下载的 .txt/.md/.json 放到 envcad/knowledge/ima_imports/ 后，运行
  `envcad sync-kb --local-dir <dir>` 完成本地增量合并。

领域映射（截图中的订阅库 -> envcad 本地模块）：
  环评知识库                    -> ima_eia_data.py
  暖通智库                      -> ima_hvac_data.py
  土木工程实战                  -> ima_civil_practice.py
  智能建造土木AI库              -> ima_smart_construction.py
  土木工程造价成本知识库        -> ima_civil_cost.py
  建筑结构知识库                -> ima_structural_data.py
  机械国家标准                  -> ima_mech_gb_data.py
  机械设计手册                  -> ima_mech_handbook.py
  机械设计知识                  -> ima_mech_design.py
  污水方案/计算表/手册/报告/图库/规范 -> ima_sewage_design.py
  污水处理标准/规范/书籍/...     -> ima_water_std.py
  环保知识库                    -> ima_env_data.py
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ──────────────────────────────────────────────────────────
# 1. 领域映射表：知识库名称关键词 -> 本地模块/领域
# ──────────────────────────────────────────────────────────
DOMAIN_MAP: Dict[str, Dict[str, str]] = {
    "环评知识库": {"module": "ima_eia_data", "domain": "eia"},
    "暖通智库": {"module": "ima_hvac_data", "domain": "hvac"},
    "土木工程实战": {"module": "ima_civil_practice", "domain": "civil"},
    "智能建造土木AI库": {"module": "ima_smart_construction", "domain": "smart_construction"},
    "土木工程造价成本知识库": {"module": "ima_civil_cost", "domain": "civil_cost"},
    "建筑结构知识库": {"module": "ima_structural_data", "domain": "structural"},
    "机械国家标准": {"module": "ima_mech_gb_data", "domain": "mech_gb"},
    "机械设计手册": {"module": "ima_mech_handbook", "domain": "mech_handbook"},
    "机械设计知识": {"module": "ima_mech_design", "domain": "mech_design"},
    "污水方案": {"module": "ima_sewage_design", "domain": "sewage_design"},
    "污水处理标准": {"module": "ima_water_std", "domain": "water_std"},
    "环保知识库": {"module": "ima_env_data", "domain": "env"},
}


def resolve_domain(name: str) -> Dict[str, str]:
    """根据知识库名称匹配领域映射。"""
    for key, meta in DOMAIN_MAP.items():
        if key in name:
            return meta
    return {"module": "ima_general_data", "domain": "general"}


# ──────────────────────────────────────────────────────────
# 2. 文档模型
# ──────────────────────────────────────────────────────────
@dataclass
class ImaKnowledgeBase:
    id: str
    name: str
    total_size: int = 0
    documents: List["ImaDocument"] = field(default_factory=list)


@dataclass
class ImaDocument:
    media_id: str
    media_type: int
    title: str
    introduction: str = ""
    content: str = ""


# ──────────────────────────────────────────────────────────
# 3. 内容解析器（规则 + 轻量正则）
# ──────────────────────────────────────────────────────────
class KnowledgeExtractor:
    """从 ima 文档纯文本中提取结构化工程知识。"""

    def __init__(self, text: str):
        self.text = text

    def extract_gb_codes(self) -> List[Dict[str, Any]]:
        """提取 GB/T/GBJ/CJJ 等国标编号与名称。"""
        pattern = re.compile(r"(GB[\s/-]?\d{4,5}(?:\.\d+)?[-–]?(?:\d{4})?)\s*[—\-–]?\s*([^\n]{3,80})")
        results = []
        seen = set()
        for code, name in pattern.findall(self.text):
            key = f"{code}-{name.strip()[:60]}"
            if key in seen:
                continue
            seen.add(key)
            results.append({"code": code.replace(" ", ""), "name": name.strip()})
        return results

    def extract_parameters(self) -> Dict[str, Any]:
        """提取 '参数名 = 数值' 或 '参数名：数值' 形式的参数表。"""
        params: Dict[str, Any] = {}
        # 匹配 "参数名 = 数字（单位）" 或 "参数名：数字（单位）"
        pattern = re.compile(r"([一-龥A-Za-z][一-龥A-Za-z0-9_/\-]{1,15})\s*[:：=]\s*([0-9]+\.?[0-9]*)\s*([一-龥A-Za-z%/°㎡m³kPaMPa℃mm]*)")
        for name, value, unit in pattern.findall(self.text):
            try:
                v = float(value)
            except ValueError:
                continue
            params[name.strip()] = {"value": v, "unit": unit.strip()} if unit.strip() else v
        return params

    def extract_dimensions(self) -> List[Dict[str, Any]]:
        """提取尺寸规格，如 1200×800×600mm。"""
        pattern = re.compile(r"(\d+(?:\.\d+)?)\s*[×xX]\s*(\d+(?:\.\d+)?)(?:\s*[×xX]\s*(\d+(?:\.\d+)?))?\s*([一-龥A-Za-z]{1,3})")
        dims = []
        for a, b, c, unit in pattern.findall(self.text)[:20]:
            dims.append({"L": float(a), "W": float(b), "H": float(c) if c else None, "unit": unit})
        return dims

    def extract_tables(self) -> List[List[List[str]]]:
        """简易 Markdown 表格解析。"""
        tables = []
        # 找 | ... | ... | 行
        rows = [line.strip() for line in self.text.splitlines() if line.strip().startswith("|")]
        if not rows:
            return tables
        # 简单切分
        current = []
        for row in rows:
            cells = [c.strip() for c in row.split("|")][1:-1]
            if cells:
                current.append(cells)
            else:
                if current:
                    tables.append(current)
                    current = []
        if current:
            tables.append(current)
        return tables

    def to_module_data(self) -> Dict[str, Any]:
        return {
            "gb_codes": self.extract_gb_codes(),
            "parameters": self.extract_parameters(),
            "dimensions": self.extract_dimensions(),
            "tables": self.extract_tables(),
            "raw_snippets": self.text[:5000],
        }


# ──────────────────────────────────────────────────────────
# 4. 本地知识写入
# ──────────────────────────────────────────────────────────
def write_knowledge_module(module_name: str, data: Dict[str, Any], out_dir: Path) -> Path:
    """把提取出的数据写成 envcad/knowledge/ 下的 Python 模块。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / f"{module_name}.py"
    header = f'''# -*- coding: utf-8 -*-
"""从 ima 订阅知识库自动同步生成的 {module_name} 数据模块。

本文件由 `envcad sync-kb` 自动维护，手动修改可能被后续同步覆盖。
数据来自 ima 共享知识库，供制图/设计/文档生成统一引用。
"""
from __future__ import annotations

'''
    body = "IMA_KB_DATA = " + json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n"
    file_path.write_text(header + body, encoding="utf-8")
    return file_path


def merge_local_imports(local_dir: Path, knowledge_dir: Path) -> List[Path]:
    """扫描本地目录中的 .txt/.md/.json，解析后写入 knowledge。"""
    written: List[Path] = []
    for p in sorted(local_dir.glob("*")):
        if p.suffix.lower() not in (".txt", ".md", ".json"):
            continue
        text = p.read_text(encoding="utf-8")
        domain = resolve_domain(p.stem)
        extractor = KnowledgeExtractor(text)
        data = extractor.to_module_data()
        data["source_file"] = p.name
        out = write_knowledge_module(domain["module"], data, knowledge_dir)
        written.append(out)
    return written


# ──────────────────────────────────────────────────────────
# 5. 高层 API：供 WorkBuddy 会话或 cli sync-kb 调用
# ──────────────────────────────────────────────────────────
def ingest_documents(
    kb_list: List[ImaKnowledgeBase],
    knowledge_dir: Path,
) -> Tuple[List[Path], List[str]]:
    """把 ima MCP 拉取到的一批知识库+文档沉淀为本地模块。

    参数:
        kb_list: WorkBuddy AI 通过 ima MCP 获取的知识库对象列表。
        knowledge_dir: envcad/knowledge/ 目录路径。

    返回:
        (written_files, log_messages)
    """
    written: List[Path] = []
    logs: List[str] = []
    for kb in kb_list:
        domain = resolve_domain(kb.name)
        logs.append(f"处理知识库: {kb.name} -> {domain['module']}")
        merged: Dict[str, Any] = {
            "knowledge_base": {"id": kb.id, "name": kb.name},
            "documents": {},
        }
        for doc in kb.documents:
            extractor = KnowledgeExtractor(doc.content)
            merged["documents"][doc.title] = extractor.to_module_data()
        if merged["documents"]:
            out = write_knowledge_module(domain["module"], merged, knowledge_dir)
            written.append(out)
            logs.append(f"  写入 {out} ({len(merged['documents'])} 篇文档)")
        else:
            logs.append("  无文档内容，跳过")
    return written, logs


# 兼容旧名称
__all__ = [
    "DOMAIN_MAP",
    "resolve_domain",
    "ImaKnowledgeBase",
    "ImaDocument",
    "KnowledgeExtractor",
    "write_knowledge_module",
    "merge_local_imports",
    "ingest_documents",
]
