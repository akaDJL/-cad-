# -*- coding: utf-8 -*-
"""离线自包含的联网搜索模块。

策略（公开权威来源优先，不依赖 MCP / WebFetch）：
1. 用 urllib 请求搜索引擎网页结果（无需 API key）—— 作为"搜索入口"。
2. 多引擎兜底：Bing 优先，失败/无结果时依次尝试 DuckDuckGo HTML、Sogou、Baidu。
3. 解析返回结果中的 标题 / 链接 / 摘要，优先保留来自官方/标准/图集/百科/厂商样本的条目。
4. 增强解析：宽松锚点 + 任意 h2/a 外链兜底，适配搜索引擎改版；结果去重、去广告/导航噪音。
5. 可选二次抓取：对命中的权威页面用 urllib 再抓取正文（默认关闭，避免慢/被拦）。
6. 从文本中用正则抽取 国标编号(GB/T、CJJ、JGJ...)、图集号(如 02S404)、参数("名称:数值 单位")；
   正文抽取支持 HTML 表格单元格配对（<td>标签</td><td>数值</td>）。

注意：纯 HTTP，仅适用于公开网页；ima 私有知识库不在此模块覆盖（仍由对话内 MCP 触发）。
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

# 噪音域名/链接特征，命中则降权或丢弃（搜索引擎自身、广告、登录页等）
NOISE_URL_HINTS = [
    "bing.com", "bingj.com", "go.microsoft.com", "msn.com",
    "duckduckgo.com", "duckduckgo.ca",
    "sogou.com", "sogoucdn.com",
    "baidu.com", "baiducontent.com", "百度",
    "doubleclick.net", "googleadservices.com", "google.com/ads",
    "ad.", "/ads/", "advertising",
    "login", "signin", "account.",
    "cache:", "translate.google", "cc.bingj.com",
]

# 搜索入口：Bing 网页搜索（无需 API key；cn.bing.com 在本环境无结果，用 www）
_SEARCH_ENGINES = [
    ("bing", "https://www.bing.com/search"),
    ("ddg", "https://html.duckduckgo.com/html"),
    ("sogou", "https://www.sogou.com/web"),
    ("baidu", "https://www.baidu.com/s"),
]

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
    engine: str = ""    # 来源引擎
    noise: bool = False  # 是否为广告/导航噪音（应丢弃）

    def as_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "url": self.url,
                "snippet": self.snippet, "authority": self.authority,
                "relevance": self.relevance, "engine": self.engine,
                "noise": self.noise}


def _score_authority(url: str) -> int:
    s = 0
    for i, hint in enumerate(AUTHORITY_HINTS):
        if hint in url.lower():
            s += len(AUTHORITY_HINTS) - i  # 越靠前权重越高
    return s


def _is_noise(url: str, title: str = "") -> bool:
    u = url.lower()
    t = title.lower()
    for hint in NOISE_URL_HINTS:
        if hint in u or hint in t:
            return True
    return False


def _score_relevance(query: str, title: str, snippet: str) -> int:
    """query 核心词在标题/摘要中的命中数（含标准号/图集号优先）。"""
    text = (title + " " + snippet).lower()
    qlower = query.lower()
    score = 0
    # 抽取查询中的标准/图集号（4位以上字母数字混合或含 GB/CJJ/JGJ）
    codes = re.findall(r"[A-Za-z]{1,3}\d{2,5}|GB|CGC|02S404|19S707|03S702", query)
    for c in codes:
        if c.lower() in text:
            score += 8  # 标准号/图集号命中权重更高
    # 中文/英文关键词命中（标题命中加权）
    kws = [w for w in re.split(r"[\s,，、/]+", qlower) if len(w) >= 2]
    for kw in kws:
        if kw in title.lower():
            score += 3
        elif kw in snippet.lower():
            score += 1
    return score


# UA 轮换 + 移动端 UA（部分引擎对移动端返回更干净的结果）
_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


def _fetch_html(url: str, timeout: int = 12, retries: int = 2) -> Optional[str]:
    """稳健抓取：UA 轮换 + 指数退避重试 + 编码探测 + 去 content-type 非文本。"""
    last_err = None
    for attempt in range(retries + 1):
        ua = _UAS[attempt % len(_UAS)]
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": ua,
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ctype = resp.headers.get("Content-Type", "")
                if "text/html" not in ctype and "xml" not in ctype:
                    # 非 HTML（如 PDF）跳过
                    return None
                raw = resp.read(2_000_000)
            enc = resp.headers.get_content_charset()
            if not enc:
                # 探测 <meta charset>
                m = re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', raw[:2000],
                              re.I)
                enc = m.group(1).decode() if m else "utf-8"
            return raw.decode(enc, errors="ignore")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429, 503):
                time.sleep(0.5 * (attempt + 1))  # 退避
                continue
            return None
        except Exception as e:  # 超时/连接失败等
            last_err = e
            time.sleep(0.3 * (attempt + 1))
            continue
    return None


# ----------------------------------------------------------------------------
# 各引擎结果解析
# ----------------------------------------------------------------------------

def _parse_bing(html: str, query: str = "") -> List[SearchHit]:
    """解析 Bing 搜索结果。

    宽松策略：以 b_algo 为锚点切分；每个块抓第一个外链 + h2 标题 + 摘要。
    若 b_algo 锚点失效（改版），回退到『任意 <li> 内含 h2>a 外链』扫描。
    """
    hits: List[SearchHit] = []

    def _extract_from_block(seg: str) -> Optional[SearchHit]:
        a = re.search(r'<a[^>]*class="tilk"[^>]*href="(https?://[^"]+)"[^>]*>', seg)
        if not a:
            a = re.search(r'<h2>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>', seg)
        if not a:
            a = re.search(r'href="(https?://[^"]+)"[^>]*class="tilk"', seg)
        if not a:
            a = re.search(r'<a[^>]*href="(https?://[^"]+)"[^>]*>', seg)
        if not a:
            return None
        href = _unescape(a.group(1))
        t = re.search(r'<h2[^>]*>(.*?)</h2>', seg, re.S)
        title = _strip_tags(t.group(1)) if t else href
        snip_m = re.search(r'class="[^"]*b_caption[^"]*"[^>]*>(.*?)</p>', seg, re.S)
        if not snip_m:
            snip_m = re.search(r'class="[^"]*b_lineclamp[^"]*"[^>]*>(.*?)</', seg, re.S)
        if not snip_m:
            snip_m = re.search(r'<p[^>]*class="[^"]*b_paractl[^"]*"[^>]*>(.*?)</p>', seg, re.S)
        snippet = _strip_tags(snip_m.group(1)) if snip_m else ""
        return SearchHit(title=title, url=href, snippet=snippet, engine="bing",
                         authority=_score_authority(href),
                         relevance=_score_relevance(query, title, snippet),
                         noise=_is_noise(href, title))

    parts = re.split(r'<li[^>]*class="b_algo', html)
    if len(parts) > 1:
        for blk in parts[1:]:
            end = re.search(r'\n<!/?(li|ol|ul)', blk)
            seg = blk[:end.start()] if end else blk[:6000]
            hit = _extract_from_block(seg)
            if hit:
                hits.append(hit)
    else:
        # 回退：扫描所有 <li> 块中的 h2>a 外链
        for blk in re.findall(r'<li[^>]*>(.*?)</li>', html, re.S):
            t = re.search(r'<h2[^>]*>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', blk, re.S)
            if not t:
                continue
            href = _unescape(t.group(1))
            title = _strip_tags(t.group(2))
            snip_m = re.search(r'class="[^"]*b_caption[^"]*"[^>]*>(.*?)</p>', blk, re.S)
            snippet = _strip_tags(snip_m.group(1)) if snip_m else ""
            hits.append(SearchHit(title=title, url=href, snippet=snippet, engine="bing",
                                  authority=_score_authority(href),
                                  relevance=_score_relevance(query, title, snippet),
                                  noise=_is_noise(href, title)))
    return hits


def _parse_ddg(html: str, query: str = "") -> List[SearchHit]:
    """解析 DuckDuckGo HTML 结果（result__a 链接 + result__snippet）。

    不依赖 div 块分割（DDG 结构多变），直接全局搜 result__a 链接，
    并从链接后续片段中抓 result__snippet 摘要。
    """
    hits: List[SearchHit] = []
    for a in re.finditer(
        r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href = _unescape(a.group(1))
        m = re.search(r"uddg=([^&]+)", href)
        if m:
            href = urllib.parse.unquote(m.group(1))
        title = _strip_tags(a.group(2))
        # 从链接后 500 字符内找 snippet
        tail = html[a.end():a.end() + 600]
        snip_m = re.search(r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</', tail, re.S)
        snippet = _strip_tags(snip_m.group(1)) if snip_m else ""
        hits.append(SearchHit(title=title, url=href, snippet=snippet, engine="ddg",
                              authority=_score_authority(href),
                              relevance=_score_relevance(query, title, snippet),
                              noise=_is_noise(href, title)))
    return hits


def _parse_sogou(html: str, query: str = "") -> List[SearchHit]:
    """解析 Sogou 结果：全局搜外链 + 就近标题/摘要（不依赖特定 div class）。"""
    hits: List[SearchHit] = []
    for a in re.finditer(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href = _unescape(a.group(1))
        title = _strip_tags(a.group(2))
        if len(title) < 4:
            continue
        tail = html[a.end():a.end() + 400]
        snip_m = re.search(r'class="[^"]*(?:text|content|abs)[^"]*"[^>]*>(.*?)</', tail, re.S)
        snippet = _strip_tags(snip_m.group(1)) if snip_m else ""
        hits.append(SearchHit(title=title, url=href, snippet=snippet, engine="sogou",
                              authority=_score_authority(href),
                              relevance=_score_relevance(query, title, snippet),
                              noise=_is_noise(href, title)))
    return hits


def _parse_baidu(html: str, query: str = "") -> List[SearchHit]:
    """解析 Baidu 结果：全局搜外链 + 就近标题/摘要（不依赖特定 div class）。"""
    hits: List[SearchHit] = []
    for a in re.finditer(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href = _unescape(a.group(1))
        title = _strip_tags(a.group(2))
        if len(title) < 4:
            continue
        tail = html[a.end():a.end() + 400]
        snip_m = re.search(r'class="[^"]*(?:content|abstract|c-abstract)[^"]*"[^>]*>(.*?)</', tail, re.S)
        snippet = _strip_tags(snip_m.group(1)) if snip_m else ""
        hits.append(SearchHit(title=title, url=href, snippet=snippet, engine="baidu",
                              authority=_score_authority(href),
                              relevance=_score_relevance(query, title, snippet),
                              noise=_is_noise(href, title)))
    return hits


_PARSERS = {
    "bing": _parse_bing,
    "ddg": _parse_ddg,
    "sogou": _parse_sogou,
    "baidu": _parse_baidu,
}


def _build_query(engine: str, q: str) -> str:
    if engine == "bing":
        return urllib.parse.urlencode({"q": q, "setlang": "zh-CN", "cc": "CN"})
    if engine == "ddg":
        return urllib.parse.urlencode({"q": q})
    if engine == "sogou":
        return urllib.parse.urlencode({"query": q})
    if engine == "baidu":
        return urllib.parse.urlencode({"wd": q})
    return urllib.parse.urlencode({"q": q})


def _dedup_hits(hits: List[SearchHit]) -> List[SearchHit]:
    """同 url 归一去重（保留权威/相关度更高者），并丢弃噪音。"""
    seen: Dict[str, SearchHit] = {}
    for h in hits:
        if h.noise:
            continue
        key = h.url.split("?")[0].rstrip("/").lower()
        if key in seen:
            old = seen[key]
            # 保留分更高的
            if (h.authority + h.relevance) > (old.authority + old.relevance):
                seen[key] = h
        else:
            seen[key] = h
    return list(seen.values())


def search(query: str, max_results: int = 8, fetch_detail: bool = False) -> List[SearchHit]:
    """联网搜索。返回按权威度+相关度排序的结果列表。

    多引擎兜底：依次尝试 Bing → DDG → Sogou → Baidu，主引擎拿到有效结果即返回。
    结果经过去重、去噪音、相关度过滤。

    稳健策略：
    1. 先按原 query 搜；若全部不相关，则用 query 中的图集号/标准号 + "图集" 再搜一次。
    2. UA 轮换 + 重试退避。
    """
    def _one_engine(engine: str, q: str) -> List[SearchHit]:
        base, _ = next((b for n, b in _SEARCH_ENGINES if n == engine), (None, None))
        if not base:
            return []
        url = base + "?" + _build_query(engine, q)
        for _ in range(2):
            html = _fetch_html(url)
            if not html:
                continue
            parser = _PARSERS.get(engine)
            if not parser:
                continue
            hits = parser(html, q)
            hits = _dedup_hits(hits)
            related = [h for h in hits if (h.authority + h.relevance) > 0]
            cand = related if related else hits
            if cand:
                return cand
        return []

    def _try_all(q: str) -> List[SearchHit]:
        for name, _ in _SEARCH_ENGINES:
            try:
                hits = _one_engine(name, q)
            except Exception:
                hits = []
            if hits:
                return hits
        return []

    best = _try_all(query)
    if not best:
        # 抽取图集号/标准号，用 "图集号 图集" 兜底（对纯图集号查询更稳定）
        codes = re.findall(r"\d{2}[A-Z]\d{3,4}|GB/T?\d{3,5}|CJJ\d+|JGJ\d+", query)
        if codes:
            best = _try_all(codes[0] + " 图集")
    if not best:
        return []
    best.sort(key=lambda h: (h.authority + h.relevance * 2), reverse=True)
    if fetch_detail:
        for h in best[:3]:
            detail = _fetch_html(h.url)
            if detail:
                h.snippet = _clean_text(detail)[:400]
    return best[:max_results]


# ----------------------------------------------------------------------------
# 文本抽取
# ----------------------------------------------------------------------------

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


# 紧固件尺寸中文标签 → 字段映射（用于从网页正文抽取精确值）
_FASTENER_LABELS = {
    "bolt": [
        ("对边宽度", "s"), ("对边", "s"), ("扳手尺寸", "s"), ("头部高度", "k"),
        ("厚度", "k"), ("对角宽度", "e"), ("对角", "e"), ("螺距", "P"),
        ("螺纹大径", "d"), ("公称直径", "d"),
    ],
    "nut": [
        ("对边宽度", "s"), ("对边", "s"), ("扳手尺寸", "s"), ("螺母高度", "m"),
        ("厚度", "m"), ("对角宽度", "e"), ("对角", "e"), ("螺距", "P"),
        ("公称直径", "d"),
    ],
    "screw": [
        ("头部直径", "dk"), ("盘头直径", "dk"), ("对边", "s"), ("头部高度", "k"),
        ("厚度", "k"), ("螺距", "P"), ("公称直径", "d"),
    ],
    "washer": [
        ("内径", "d1"), ("孔径", "d1"), ("外径", "d2"), ("公称外径", "d2"),
        ("厚度", "h"), ("高度", "h"),
    ],
}


def _html_to_text(html: str) -> str:
    """把 HTML 转成便于抽取的文本：去 script/style、拆表格单元格、保留可见文本。"""
    # 去 script / style / noscript
    html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    # 表格行结束 → 换行（不同 tr 之间分隔）
    html = re.sub(r"</tr>", "\n", html, flags=re.I)
    # 单元格边界 → \t 分隔（td/th 开闭标签都替换为 \t，使标签单元格与数值单元格同行配对）
    html = re.sub(r"</?(?:td|th)[^>]*>", "\t", html, flags=re.I)
    # 其他块级标签结束 → 换行，便于逐行扫描
    html = re.sub(r"</(li|p|div|br|h[1-6])>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = _unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text


def extract_fastener_params(text: str, kind_key: str) -> Dict[str, float]:
    """从网页正文抽取紧固件精确尺寸，返回 {字段: 数值}。

    策略：
    1. 先把 HTML（若有）转成可见文本：拆表格单元格、去 script/style。
    2. 逐行扫描，支持三种模式：
       - 标签与数值同处一行（如「公称直径 d = 20」）；
       - HTML 表格单元格配对：上一单元格是标签、下一单元格是数值（用 \t 分隔后跨列对齐）；
       - 退化兼容：标签后直接数值。

    同名标签取第一个有效数字；标签与数值禁止跨行贪婪（避免吸到远处数字）。
    """
    labels = _FASTENER_LABELS.get(kind_key, [])
    if not labels:
        return {}

    # 若是 HTML，先转文本
    if "<" in text and ">" in text:
        text = _html_to_text(text)

    found: Dict[str, float] = {}
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        # 表格行：用 \t 拆分单元格，检查「标签单元格 + 数值单元格」配对
        cells = [c.strip() for c in line.split("\t") if c.strip()]
        for li, (label, field) in enumerate(labels):
            if field in found:
                continue
            # 同行：标签后 可选代号+[:：=]+数值
            m = re.search(
                re.escape(label) +
                r"\s*[A-Za-z]+\d{0,2}\s*[:：=]?\s*([0-9]+\.?[0-9]*)", line)
            if not m:
                m = re.search(
                    re.escape(label) + r"\s*[:：=]?\s*([0-9]+\.?[0-9]*)", line)
            if not m:
                m = re.search(
                    re.escape(label) + r"[^\d]*?([0-9]+\.?[0-9]*)", line)
            if m:
                found[field] = float(m.group(1))
                continue
            # 表格配对：本行某单元格 == 标签，且同行后续单元格为纯数值
            for ci, cell in enumerate(cells):
                if cell == label or cell.startswith(label):
                    # 后续单元格数值
                    for nxt in cells[ci + 1:]:
                        nm = re.match(r"^([0-9]+\.?[0-9]*)\s*(?:mm|毫米)?$", nxt)
                        if nm:
                            found[field] = float(nm.group(1))
                            break
                    if field in found:
                        break
    return found


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
        print(f"{tag} {i}. [{h.engine}] {h.title}")
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
