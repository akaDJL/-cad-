"""组件层联网检索桥：供 components 在本地未收录时调用，避免依赖 CLI argparse。"""

from typing import List, Dict, Any


def search_web(query: str, max_n: int = 5) -> List[Dict[str, Any]]:
    """联网检索权威标准/图集。返回 [{"title","url","snippet","authority"}]，失败返回空列表。"""
    try:
        from .web_search import search
        hits = search(query, max_results=max_n)
        return [
            {"title": h.title, "url": h.url, "snippet": h.snippet,
             "authority": h.authority}
            for h in hits
        ]
    except Exception:
        return []
