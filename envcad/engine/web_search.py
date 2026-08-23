# -*- coding: utf-8 -*-
"""离线自包含的联网搜索模块。

策略（公开权威来源优先，不依赖 MCP / WebFetch）：
1. 用 urllib 请求 Bing 网页搜索（无需 API key，GET 即返回结果）—— 作为"搜索入口"。
2. 解析返回结果中的 标题 / 链接 / 摘要，优先保留来自官方/标准/图集/百科/厂商样本的条目。
3. 可选二次抓取：对命中的权威页面用 urllib 再抓取正文摘要（默认关闭，避免慢/被拦）。
4. 从文本中用正则抽取 国标编号(GB/T、CJJ、JGJ...)、图集号(如 02S404)、参数("名称:数值 单位")。

注意：纯 HTTP，仅适用于公开网页；ima 私有知识库不在此模块覆盖（仍由对话内 MCP 触发）。
"""
from __future__ import annotations

import json
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import re
import urllib.parse
import urllib.request

# 优先保留的权威域名关键词（命中则排序靠前）
AUTHORITY_HINTS = [
    "openstd.samr.gov.cn",   # 国家标准全文公开系统
    "gb688.cn",              # 国家标准全文公开
    "std.samr.gov.cn",
    "gov.cn",
    "csgcn.com",             # 国标图集
    "chinabuilding.com.cn",  # 国家建筑标准设计
    "baike",                 # 百科
    "wiki",
    "edu.cn",                # 高校/学院资料
    "doc88", "docin",        # 文档（次优先）
]

# 搜索入口：Bing 网页搜索（无需 API key，GET 即返回结果；cn.bing.com 在本环境无结果，用 www）
_SEARCH_URL = "https://www.bing.com/search"

# 正则
_RE_GB = re.compile(
    r"(GB[\s./-]?T?\d{3,5}(?:\.\d+)?[-–]?(?:\d{4})?|"
    r"CJJ[\s./-]?\d{1,4}(?:\.\d+)?|"
    r"JGJ[\s./-]?\d{1,4}(?:\.\d+)?|"
    r"GBZ[\s./-]?\d{3,5}|"
    r"\d{2}[A-Z]\d{3,4}(?:-\w+)?)"  # 图集号 如 02S404 / 19S707
)
_RE_PARAM = re.compile(
    r"([一-龥A-Za-z][一-龥A-Za-z0-9_/\-·]{1,18})\s*[:：=]\s*"
    r"([0-9]+\.?[0-9]*)\s*([一-龥A-Za-z%/°㎡m³m3kPaMPa℃mmcm²]{0,12})"
)


@dataclass
class SearchHit:
    title: str
    url: str
    snippet: str = ""
    authority: int = 0  # 命中权威域名加分
    relevance: int = 0  # 命中查询词/标准号加分

    def as_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "url": self.url,
                "snippet": self.snippet, "authority": self.authority,
                "relevance": self.relevance}


def _score_authority(url: str) -> int:
    s = 0
    for i, hint in enumerate(AUTHORITY_HINTS):
        if hint in url.lower():
            s += len(AUTHORITY_HINTS) - i  # 越靠前权重越高
    return s


def _score_relevance(query: str, title: str, snippet: str) -> int:
    """query 核心词在标题/摘要中的命中数（含标准号/图集号优先）。"""
    text = (title + " " + snippet).lower()
    # 抽取查询中的标准/图集号（4位以上字母数字混合或含 GB/CJJ/JGJ）
    import re as _re
    codes = _re.findall(r"[A-Za-z]{1,3}\d{2,5}|GB|CGC|02S404|19S707|03S702", query)
    score = 0
    for c in codes:
        if c.lower() in text:
            score += 5
    # 中文/英文关键词命中
    for kw in [w for w in re.split(r"[\s,，、/]+", query) if len(w) >= 2]:
        if kw.lower() in text:
            score += 1
    return score


_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


def _fetch_html(url: str, timeout: int = 12) -> Optional[str]:
    for ua in _UAS:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": ua, "Accept-Language": "zh-CN,zh;q=0.9"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read(1_000_000)
            enc = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(enc, errors="ignore")
        except Exception:
            continue
    return None


def search(query: str, max_results: int = 8, fetch_detail: bool = False) -> List[SearchHit]:
    """联网搜索。返回按权威度+相关度排序的结果列表。

    稳健策略：
    1. 先按原 query 搜；若全部不相关，则用 query 中的图集号/标准号 + "图集" 再搜一次。
    2. UA 轮换重试。
    """
    def _one(q: str) -> List[SearchHit]:
        params = urllib.parse.urlencode({"q": q, "setlang": "zh-CN", "cc": "CN"})
        url = _SEARCH_URL + "?" + params
        for _ in range(2):
            html = _fetch_html(url)
            if not html:
                continue
            hits = _parse_bing(html, q)
            related = [h for h in hits if (h.authority + h.relevance) > 0]
            cand = related if related else hits
            if cand:
                return cand
        return []

    best = _one(query)
    if not best:
        # 抽取图集号/标准号，用 "图集号 图集" 兜底（Bing 对纯图集号查询更稳定）
        codes = re.findall(r"\d{2}[A-Z]\d{3,4}|GB/T?\d{3,5}|CJJ\d+|JGJ\d+", query)
        if codes:
            best = _one(codes[0] + " 图集")
    if not best:
        return []
    best.sort(key=lambda h: (h.authority + h.relevance * 2), reverse=True)
    if fetch_detail:
        for h in best[:3]:
            detail = _fetch_html(h.url)
            if detail:
                h.snippet = _clean_text(detail)[:400]
    return best[:max_results]


def _parse_bing(html: str, query: str = "") -> List[SearchHit]:
    """解析 Bing 搜索结果：以 b_algo 为锚点切分，再抓主链接与摘要。

    Bing 结果块结构不稳定（class 常带后缀），这里用宽松策略：
    - 主链接：块内第一个 <a class="tilk" ... href="..."> 或任意带 http(s) 的标题链接
    - 摘要：class 含 caption / b_lineclamp 的段落
    """
    hits: List[SearchHit] = []
    parts = re.split(r'<li class="b_algo', html)
    for blk in parts[1:]:
        end = re.search(r'\n<!/?(li|ol|ul)', blk)
        seg = blk[:end.start()] if end else blk[:5000]
        # 主链接：优先 tilk，其次任意外链
        a = re.search(r'<a[^>]*class="tilk"[^>]*href="(https?://[^"]+)"[^>]*>', seg)
        if not a:
            a = re.search(r'<h2>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>', seg)
        if not a:
            a = re.search(r'href="(https?://[^"]+)"[^>]*class="tilk"', seg)
        if not a:
            continue
        href = _unescape(a.group(1))
        # 标题：优先 h2 内文本
        t = re.search(r'<h2[^>]*>(.*?)</h2>', seg, re.S)
        title = _strip_tags(t.group(1)) if t else href
        # 摘要：caption 段落
        snip_m = re.search(r'class="[^"]*b_caption[^"]*"[^>]*>(.*?)</p>', seg, re.S)
        if not snip_m:
            snip_m = re.search(r'class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</', seg, re.S)
        snippet = _strip_tags(snip_m.group(1)) if snip_m else ""
        hit = SearchHit(title=title, url=href, snippet=snippet,
                        authority=_score_authority(href),
                        relevance=_score_relevance(query, title, snippet))
        hits.append(hit)
    return hits


def extract_standards(text: str) -> List[Dict[str, str]]:
    """从全文/摘要抽取标准号与上下文。"""
    out: List[Dict[str, str]] = []
    seen = set()
    for code in _RE_GB.findall(text):
        code = code.replace(" ", "")
        if code in seen:
            continue
        seen.add(code)
        ctx = ""
        m = re.search(re.escape(code) + r"\s*[—\-–]?\s*([^\n。]{3,60})", text)
        if m:
            ctx = m.group(1).strip()
        out.append({"code": code, "context": ctx})
    return out


def extract_params(text: str) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for name, val, unit in _RE_PARAM.findall(text):
        try:
            v = float(val)
        except ValueError:
            continue
        params[name.strip()] = {"value": v, "unit": unit.strip()} if unit.strip() else v
    return params


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _clean_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _unescape(s: str) -> str:
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'"))
    return s


def web_search_cli(query: str, save: bool = False, detail: bool = False, max_n: int = 8):
    """CLI 入口：搜索并打印，save 时把结构化结果写到 envcad/knowledge/web_cache/。"""
    hits = search(query, max_results=max_n, fetch_detail=detail)
    if not hits:
        print("⚠ 联网搜索无结果（可能网络受限或被搜索引擎拦截）。")
        return []
    print(f"🌐 联网搜索「{query}」共 {len(hits)} 条（按权威度排序）：\n")
    for i, h in enumerate(hits, 1):
        tag = "🔹" if h.authority > 0 else "  "
        print(f"{tag} {i}. {h.title}")
        print(f"   {h.url}")
        if h.snippet:
            print(f"   {h.snippet[:160]}")
        std = extract_standards(h.title + " " + h.snippet)
        if std:
            codes = ", ".join(s["code"] for s in std)
            print(f"   标准号: {codes}")
        print()
    if save:
        out_dir = Path(__file__).resolve().parent.parent / "knowledge" / "web_cache"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^\w一-龥-]", "_", query)[:40]
        fp = out_dir / f"{ts}_{safe}.json"
        data = {
            "query": query,
            "hits": [h.as_dict() for h in hits],
            "standards": extract_standards(
                " ".join(h.title + h.snippet for h in hits)),
        }
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 已保存搜索结果 → {fp}")
    return hits


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "GB/T 50268 给水排水管道工程施工及验收规范"
    web_search_cli(q, detail=False)
