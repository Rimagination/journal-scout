"""
MDPI Journal Statistics 爬虫
数据来源：/journal/{slug}/stats 页面内嵌数据块

MDPI 同时运行新旧两套前端：
  旧版 (jQuery/ZingChart): 内嵌 $.parseJSON(...) 数据，包含月度时间序列
  新版 (Nuxt.js):          内嵌 ShallowReactive 状态，仅含 medianTfd

本脚本自动识别版本并提取可用字段，当旧版数据不可用时回退到新版。

用法：
    python scrape_mdpi.py --slug molecules          # 单本期刊
    python scrape_mdpi.py --issn 1420-3049          # 按 ISSN 查（需先建图）
    python scrape_mdpi.py --build-map               # 建 ISSN→slug 映射
    python scrape_mdpi.py --batch journals.json --out out.json

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

BASE = "https://www.mdpi.com"
DELAY = 2.0
MAP_FILE = Path(__file__).parent / "data" / "mdpi_issn_slug_map.json"

_SESSION = None

def _get_session():
    global _SESSION
    if _SESSION is None and _HAS_CURL_CFFI:
        _SESSION = creq.Session(impersonate='chrome124')
    return _SESSION


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch(url: str, retries: int = 3) -> Optional[str]:
    for attempt in range(retries + 1):
        try:
            if _HAS_CURL_CFFI:
                sess = _get_session()
                r = sess.get(url, timeout=25)
                if r.status_code == 200:
                    return r.text
                if r.status_code == 404:
                    return None
                if attempt < retries:
                    time.sleep(2 ** attempt)
            else:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": "https://www.mdpi.com/",
                    "Upgrade-Insecure-Requests": "1",
                }
                req = Request(url, headers=headers)
                with urlopen(req, timeout=25) as resp:
                    return resp.read().decode("utf-8", errors="replace")
        except Exception:
            if attempt < retries:
                time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# ISSN → slug mapping
# ---------------------------------------------------------------------------

def build_issn_map(save: bool = True) -> dict[str, str]:
    url = f"{BASE}/about/journals"
    html = fetch(url)
    if not html:
        raise RuntimeError("Failed to fetch MDPI journal list")

    mapping: dict[str, str] = {}

    for m in re.finditer(
        r'href="/journal/([^"/?#]+)"[^>]*>[^<]*</a>'
        r'(?:(?!</a>).){0,800}'
        r'(?:E?ISSN|ISSN)[\s:]*(\\d{4}-[\\dXx]{4})',
        html, re.S | re.I
    ):
        slug = m.group(1)
        issn_raw = re.sub(r"[^0-9Xx]", "", m.group(2)).upper()
        if slug and issn_raw:
            mapping[issn_raw] = slug

    for m in re.finditer(
        r'(\d{4}-[\dXx]{4})[^<]{0,200}href="/journal/([^"/?#]+)"',
        html, re.S | re.I
    ):
        issn_raw = re.sub(r"[^0-9Xx]", "", m.group(1)).upper()
        slug = m.group(2)
        if slug and issn_raw and issn_raw not in mapping:
            mapping[issn_raw] = slug

    if save and mapping:
        MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(mapping)} entries to {MAP_FILE}", file=sys.stderr)

    return mapping


def load_issn_map() -> dict[str, str]:
    if MAP_FILE.exists():
        with open(MAP_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def issn_to_slug(issn: str, mapping: dict[str, str]) -> Optional[str]:
    raw = re.sub(r"[^0-9Xx]", "", issn).upper()
    return mapping.get(raw)


# ---------------------------------------------------------------------------
# Parse old-format page (jQuery / ZingChart / $.parseJSON)
# ---------------------------------------------------------------------------

def _extract_parseJSON_vars(html: str) -> dict[str, any]:
    results: dict[str, any] = {}
    pattern = re.compile(
        r"var\s+(\w+)\s*=\s*\$\.parseJSON\('((?:[^'\\]|\\.)*)'\)",
        re.S
    )
    for m in pattern.finditer(html):
        var_name = m.group(1)
        raw_json = m.group(2).replace('\\"', '"').replace("\\'", "'")
        try:
            results[var_name] = json.loads(raw_json)
        except json.JSONDecodeError:
            pass
    return results


def _parse_old_format(html: str, url: str) -> Optional[dict]:
    data = _extract_parseJSON_vars(html)
    if not data:
        return None

    result: dict = {"source": "mdpi", "url": url, "data_format": "full"}

    # ── 1. Submission to First Decision (medianElements1) ──────────────────
    median1 = data.get("medianElements1")
    if median1 and isinstance(median1, dict):
        values = [v for v in median1.values() if isinstance(v, (int, float))]
        if values:
            result["submission_to_decision_latest_days"] = round(values[-1], 1)
            result["submission_to_decision_avg_days"] = round(
                sum(values) / len(values), 1)
            recent = values[-3:] if len(values) >= 3 else values
            result["submission_to_decision_recent3m_days"] = round(
                sum(recent) / len(recent), 1)
            labels = list(median1.keys())
            result["submission_to_decision_period"] = (
                f"{labels[0].replace('<br/>', ' ')} – {labels[-1].replace('<br/>', ' ')}"
            )

    # ── 2. Acceptance to Publication (medianElements2) ─────────────────────
    median2 = data.get("medianElements2")
    if median2 and isinstance(median2, dict):
        values2 = [v for v in median2.values() if isinstance(v, (int, float))]
        if values2:
            result["acceptance_to_pub_latest_days"] = round(values2[-1], 1)
            result["acceptance_to_pub_avg_days"] = round(
                sum(values2) / len(values2), 1)

    # ── 3. Rejection rate (papersYearlyElements) ───────────────────────────
    yearly = data.get("papersYearlyElements")
    if yearly and isinstance(yearly, dict):
        for year in sorted(yearly.keys(), reverse=True):
            row = yearly[year]
            accepted = row.get("accepted", 0) or 0
            rejected = row.get("rejected", 0) or 0
            total = accepted + rejected
            if total > 0:
                result["rejection_rate_pct"] = round(rejected / total * 100, 1)
                result["acceptance_rate_pct"] = round(accepted / total * 100, 1)
                result["rejection_rate_year"] = year
                result["submissions_count"] = total
                break

    if len(result) <= 3:  # only source + url + data_format
        return None
    return result


# ---------------------------------------------------------------------------
# Parse new-format page (Nuxt.js / ShallowReactive)
# ---------------------------------------------------------------------------

def _dereference(arr: list, idx) -> any:
    """Follow integer index references in the flat Nuxt state array."""
    if isinstance(idx, int) and 0 <= idx < len(arr):
        val = arr[idx]
        if isinstance(val, int) and val != idx:
            return _dereference(arr, val)
        return val
    return idx


def _parse_new_format(html: str, url: str) -> Optional[dict]:
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    for s in scripts:
        if "ShallowReactive" not in s or len(s) < 500:
            continue
        try:
            arr = json.loads(s)
        except json.JSONDecodeError:
            continue

        # Find the journal object (has 'medianTfd' key)
        median_tfd = None
        for item in arr:
            if isinstance(item, dict) and "medianTfd" in item:
                tfd_idx = item["medianTfd"]
                val = arr[tfd_idx] if isinstance(tfd_idx, int) and tfd_idx < len(arr) else None
                if isinstance(val, (int, float)):
                    median_tfd = float(val)
                break

        if median_tfd is None:
            continue

        return {
            "source": "mdpi",
            "url": url,
            "data_format": "basic",
            "submission_to_decision_latest_days": round(median_tfd, 1),
        }

    return None


# ---------------------------------------------------------------------------
# Main scrape entry point
# ---------------------------------------------------------------------------

def scrape_slug(slug: str, max_attempts: int = 4) -> Optional[dict]:
    """
    Fetch MDPI stats page, handling both old (full data) and new (basic) formats.
    Retries up to max_attempts times to try to get the old format if the first
    attempt returns the new Nuxt format.
    """
    url = f"{BASE}/journal/{slug}/stats"

    best: Optional[dict] = None
    for attempt in range(max_attempts):
        if attempt > 0:
            time.sleep(DELAY)
        html = fetch(url)
        if not html:
            return None

        if "parseJSON" in html:
            result = _parse_old_format(html, url)
            if result:
                return result   # got full data, done
        elif "ShallowReactive" in html:
            result = _parse_new_format(html, url)
            if result and best is None:
                best = result   # keep as fallback

    return best


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
            fmt = data.get("data_format", "?")
            print(
                f"  -> [{fmt}] rej={data.get('rejection_rate_pct')}% "
                f"s2d={data.get('submission_to_decision_latest_days')}d "
                f"a2p={data.get('acceptance_to_pub_latest_days')}d",
                file=sys.stderr,
            )
        else:
            print(f"  -> failed / no data", file=sys.stderr)
        time.sleep(delay)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Done: {hit}/{total} journals saved to {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Scrape MDPI journal stats")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--slug",      help="MDPI slug，如 molecules")
    group.add_argument("--issn",      help="ISSN/EISSN，如 1420-3049")
    group.add_argument("--build-map", action="store_true", help="重建 ISSN→slug 映射")
    group.add_argument("--batch",     help="批量处理 journals.json")
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
