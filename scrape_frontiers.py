"""
Frontiers Journal Statistics 爬虫
数据来源：frontiersin.org/journals/{slug} 页面内嵌文本

提取字段：
  - days_to_decision        （天数，如 "77 days" → 77）
  - acceptance_rate_pct     （接受率 %，如 "37%" → 37.0）
  - acceptance_rate_year    （接受率数据年份）

用法：
    python scrape_frontiers.py --slug psychology
    python scrape_frontiers.py --issn 1664-1078
    python scrape_frontiers.py --build-map          # 构建 ISSN→slug 映射
    python scrape_frontiers.py --batch journals.json --out out.json

依赖：pip install curl_cffi
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from curl_cffi import requests as creq
    _HAS_CURL_CFFI = True
except ImportError:
    _HAS_CURL_CFFI = False
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError

BASE = "https://www.frontiersin.org"
DELAY = 2.0
MAP_FILE = Path(__file__).parent / "data" / "frontiers_issn_slug_map.json"

_SESSION = None


def _get_session():
    global _SESSION
    if _SESSION is None and _HAS_CURL_CFFI:
        _SESSION = creq.Session(impersonate='chrome124')
    return _SESSION


def fetch(url: str, retries: int = 2) -> Optional[str]:
    for attempt in range(retries + 1):
        try:
            if _HAS_CURL_CFFI:
                r = _get_session().get(url, timeout=30)
                if r.status_code == 200:
                    return r.text
                if r.status_code == 404:
                    return None
            else:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                req = Request(url, headers=headers)
                with urlopen(req, timeout=30) as resp:
                    return resp.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if attempt < retries:
            time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# ISSN → slug mapping  (从 Frontiers 期刊列表页构建)
# ---------------------------------------------------------------------------

def build_issn_map(save: bool = True) -> dict[str, str]:
    """
    Fetch https://www.frontiersin.org/journals and extract {ISSN → slug} map.
    Frontiers embeds journal metadata as JSON in a Next.js/React __NEXT_DATA__ block.
    """
    url = f"{BASE}/journals"
    html = fetch(url)
    if not html:
        raise RuntimeError("Failed to fetch Frontiers journal list")

    mapping: dict[str, str] = {}

    # Try __NEXT_DATA__ JSON blob first
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if m:
        try:
            next_data = json.loads(m.group(1))
            # Walk the structure looking for journal objects with issn + slug/url fields
            journals_list = _deep_find_journals(next_data)
            for j in journals_list:
                slug = j.get("slug") or j.get("journalSlug") or _slug_from_url(j.get("url", ""))
                issn = j.get("eissn") or j.get("issn") or j.get("eIssn") or j.get("onlineIssn", "")
                if slug and issn:
                    raw = re.sub(r"[^0-9Xx]", "", issn).upper()
                    if raw:
                        mapping[raw] = slug
        except (json.JSONDecodeError, Exception):
            pass

    # Fallback: regex over raw HTML
    if not mapping:
        for m in re.finditer(
            r'href=["\'](?:https://www\.frontiersin\.org)?/journals/([^"\'/?#]+)["\']'
            r'.{0,500}?(\d{4}-[\dXx]{4})',
            html, re.S | re.I
        ):
            slug = m.group(1)
            issn_raw = re.sub(r"[^0-9Xx]", "", m.group(2)).upper()
            if slug and issn_raw:
                mapping.setdefault(issn_raw, slug)

        for m in re.finditer(
            r'(\d{4}-[\dXx]{4}).{0,300}?href=["\'](?:https://www\.frontiersin\.org)?/journals/([^"\'/?#]+)["\']',
            html, re.S | re.I
        ):
            issn_raw = re.sub(r"[^0-9Xx]", "", m.group(1)).upper()
            slug = m.group(2)
            if slug and issn_raw:
                mapping.setdefault(issn_raw, slug)

    if save and mapping:
        MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(mapping)} entries to {MAP_FILE}", file=sys.stderr)

    return mapping


def _deep_find_journals(obj, depth: int = 0) -> list[dict]:
    """Recursively find objects that look like journal records."""
    if depth > 10:
        return []
    results = []
    if isinstance(obj, dict):
        if ("slug" in obj or "journalSlug" in obj) and (
            "eissn" in obj or "issn" in obj or "eIssn" in obj
        ):
            results.append(obj)
        for v in obj.values():
            results.extend(_deep_find_journals(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_deep_find_journals(item, depth + 1))
    return results


def _slug_from_url(url: str) -> str:
    m = re.search(r'/journals/([^/?#]+)', url or "")
    return m.group(1) if m else ""


def load_issn_map() -> dict[str, str]:
    if MAP_FILE.exists():
        with open(MAP_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def issn_to_slug(issn: str, mapping: dict[str, str]) -> Optional[str]:
    raw = re.sub(r"[^0-9Xx]", "", issn).upper()
    return mapping.get(raw)


# ---------------------------------------------------------------------------
# Parse Frontiers journal page
# ---------------------------------------------------------------------------

def scrape_slug(slug: str) -> Optional[dict]:
    url = f"{BASE}/journals/{slug}"
    html = fetch(url)
    if not html:
        return None

    result: dict = {"source": "frontiers", "url": url}

    # ── 1. Days to decision ─────────────────────────────────────────────────
    # Pattern: "in just 77 days" or "in 77 days" inside CardA__text
    m = re.search(
        r'<p[^>]*class=["\'][^"\']*CardA__text[^"\']*["\'][^>]*>.*?'
        r'in(?:\s+just)?\s+(\d+)\s+days',
        html, re.S | re.I
    )
    if not m:
        # Broader fallback
        m = re.search(
            r'peer\s+review.*?(\d+)\s+days|'
            r'decision.*?in\s+(?:just\s+)?(\d+)\s+days',
            html, re.S | re.I
        )
        if m:
            days_str = m.group(1) or m.group(2)
            if days_str:
                result["days_to_decision"] = int(days_str)
    else:
        result["days_to_decision"] = int(m.group(1))

    # ── 2. Acceptance rate ──────────────────────────────────────────────────
    # Pattern: "acceptance rate of 37% in 2024"
    m2 = re.search(
        r'acceptance\s+rate\s+of\s+([\d.]+)%\s+in\s+(\d{4})',
        html, re.I
    )
    if m2:
        result["acceptance_rate_pct"] = float(m2.group(1))
        result["acceptance_rate_year"] = m2.group(2)

    if len(result) <= 2:  # only source + url
        return None
    return result


def get_by_issn(issn: str, mapping: dict[str, str]) -> Optional[dict]:
    slug = issn_to_slug(issn, mapping)
    if not slug:
        return None
    return scrape_slug(slug)


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

def batch_process(journals_path: Path, out_path: Path, delay: float = DELAY):
    mapping = load_issn_map()
    if not mapping:
        print("ISSN map empty — run --build-map first", file=sys.stderr)
        sys.exit(1)

    with open(journals_path, encoding="utf-8") as f:
        journals = json.load(f)

    results: dict[str, dict] = {}
    total = len(journals)
    hit = 0
    for i, j in enumerate(journals, 1):
        issn = j.get("eissn") or j.get("issn") or ""
        title = j.get("title", "?")
        if not issn:
            continue
        raw = re.sub(r"[^0-9Xx]", "", issn).upper()
        if raw not in mapping:
            continue
        print(f"[{i}/{total}] {title} ({issn})", file=sys.stderr)
        data = get_by_issn(issn, mapping)
        if data:
            hit += 1
            results[issn] = data
            print(
                f"  -> days={data.get('days_to_decision')} "
                f"acc={data.get('acceptance_rate_pct')}% "
                f"({data.get('acceptance_rate_year', '?')})",
                file=sys.stderr,
            )
        else:
            print("  -> no data", file=sys.stderr)
        time.sleep(delay)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Done: {hit}/{total} journals saved to {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Scrape Frontiers journal stats")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--slug",      help="Frontiers slug，如 psychology")
    group.add_argument("--issn",      help="EISSN，如 1664-1078")
    group.add_argument("--build-map", action="store_true", help="构建 ISSN→slug 映射")
    group.add_argument("--batch",     help="批量：journals.json 路径")
    ap.add_argument("--out",   help="输出路径（batch 必填）")
    ap.add_argument("--delay", type=float, default=DELAY)
    args = ap.parse_args()

    if args.build_map:
        m = build_issn_map(save=True)
        print(f"Built map: {len(m)} journals")
        return

    if args.batch:
        if not args.out:
            ap.error("--batch 需要 --out")
        batch_process(Path(args.batch), Path(args.out), args.delay)
        return

    mapping = load_issn_map()

    if args.slug:
        data = scrape_slug(args.slug)
    else:
        if not mapping:
            print("Building ISSN map...", file=sys.stderr)
            mapping = build_issn_map(save=True)
            time.sleep(1)
        data = get_by_issn(args.issn, mapping)

    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "not found or no data"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
