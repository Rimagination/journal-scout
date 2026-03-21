"""
SciRev 审稿周期爬虫
用法：
    python scrape_scirev.py --issn 0028-0836          # 单本期刊
    python scrape_scirev.py --batch journals.json     # 批量处理 journals.json
    python scrape_scirev.py --slug nature             # 直接用 slug 查询
输出 JSON 到 stdout，或写入 --out 指定路径。
"""
from __future__ import annotations

import argparse
import json
import re
import time
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
BASE = "https://scirev.org"
DELAY = 1.5  # seconds between requests


# ---------------------------------------------------------------------------
# Minimal HTML parser
# ---------------------------------------------------------------------------

class SciRevParser(HTMLParser):
    """Extract review metrics from a SciRev journal page."""

    # Map heading text → output key
    METRIC_MAP = {
        "Duration first review round":        "review_round_1_months",
        "Tot. handling time acc. manuscripts": "total_handling_months",
        "Decision time immediate rejection":   "immediate_rejection_days",
        "Average number of review rounds":     "avg_review_rounds",
        "Difficulty of reviewer comments":     "reviewer_difficulty",
        "Average number of review reports":    "avg_review_reports",
        "Quality of review reports":           "quality_score",
        "Overall rating manuscript handling":  "overall_rating",
    }

    def __init__(self):
        super().__init__()
        self._in_metric_block = False
        self._current_heading = None
        self._capture_next_text = False
        self._depth = 0
        self._metric_depth = None
        self.result: dict = {}
        self.review_count: Optional[int] = None
        self.journal_title: Optional[str] = None
        self._in_h1 = False
        self._in_heading_h6 = False
        self._heading_text = ""
        # For overall rating / review count badge
        self._in_badge = False
        self._badge_depth = 0

    def handle_starttag(self, tag, attrs):
        self._depth += 1
        attr_dict = dict(attrs)

        if tag == "h1":
            self._in_h1 = True
            self._heading_text = ""
        if tag == "h6":
            self._in_heading_h6 = True
            self._heading_text = ""

    def handle_endtag(self, tag):
        if tag == "h1":
            if self._in_h1 and self._heading_text.strip():
                self.journal_title = self._heading_text.strip()
            self._in_h1 = False
        if tag == "h6":
            if self._in_heading_h6:
                self._current_heading = self._heading_text.strip()
                self._capture_next_text = True
            self._in_heading_h6 = False
        self._depth -= 1

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        if self._in_h1:
            self._heading_text += data
            return

        if self._in_heading_h6:
            self._heading_text += data
            return

        if self._capture_next_text and self._current_heading:
            key = self.METRIC_MAP.get(self._current_heading)
            if key:
                self.result[key] = text
            self._capture_next_text = False
            self._current_heading = None

        # Review count: "85 reviews" or "85"
        if "reviews" in text.lower():
            m = re.search(r"(\d+)\s+review", text, re.I)
            if m:
                self.review_count = int(m.group(1))


class SciRevSearchParser(HTMLParser):
    """Find the first journal slug from a search results page."""

    def __init__(self):
        super().__init__()
        self.slugs: list[str] = []
        self._in_result = False

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attr_dict = dict(attrs)
        href = attr_dict.get("href", "")
        # Match /journal/{slug}/ links
        m = re.match(r"^/journal/([^/]+)/?$", href)
        if m:
            slug = m.group(1)
            if slug not in ("", "all"):
                self.slugs.append(slug)


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch(url: str, retries: int = 2) -> Optional[str]:
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except HTTPError as e:
            if e.code == 404:
                return None
            if attempt < retries:
                time.sleep(2 ** attempt)
        except URLError:
            if attempt < retries:
                time.sleep(2)
    return None


def search_by_issn(issn: str) -> Optional[str]:
    """Return the first matching slug for a given ISSN."""
    # Normalise ISSN
    raw = re.sub(r"[^0-9X]", "", issn.upper())
    if len(raw) == 8:
        issn_fmt = f"{raw[:4]}-{raw[4:]}"
    else:
        issn_fmt = issn

    url = f"{BASE}/search/?q={quote_plus(issn_fmt)}"
    html = fetch(url)
    if not html:
        return None
    parser = SciRevSearchParser()
    parser.feed(html)
    return parser.slugs[0] if parser.slugs else None


def scrape_journal(slug: str) -> Optional[dict]:
    """Fetch and parse a SciRev journal page by slug."""
    url = f"{BASE}/journal/{slug}/"
    html = fetch(url)
    if not html:
        return None
    parser = SciRevParser()
    parser.feed(html)

    data = parser.result
    if not data:
        return None

    # Parse numeric values
    def parse_months(v: str) -> Optional[float]:
        m = re.search(r"([\d.]+)\s*month", v or "", re.I)
        return float(m.group(1)) if m else None

    def parse_days(v: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*day", v or "", re.I)
        return int(m.group(1)) if m else None

    def parse_float(v: str) -> Optional[float]:
        m = re.search(r"([\d.]+)", v or "")
        return float(m.group(1)) if m else None

    return {
        "source":                   "scirev",
        "url":                      url,
        "journal_title":            parser.journal_title,
        "review_count":             parser.review_count,
        "review_round_1_months":    parse_months(data.get("review_round_1_months", "")),
        "total_handling_months":    parse_months(data.get("total_handling_months", "")),
        "immediate_rejection_days": parse_days(data.get("immediate_rejection_days", "")),
        "avg_review_rounds":        parse_float(data.get("avg_review_rounds", "")),
        "reviewer_difficulty":      parse_float(data.get("reviewer_difficulty", "")),
        "avg_review_reports":       parse_float(data.get("avg_review_reports", "")),
        "quality_score":            parse_float(data.get("quality_score", "")),
        "overall_rating":           parse_float(data.get("overall_rating", "")),
    }


def get_by_issn(issn: str) -> Optional[dict]:
    slug = search_by_issn(issn)
    if not slug:
        return None
    time.sleep(DELAY)
    return scrape_journal(slug)


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------

def batch_process(journals_path: Path, out_path: Path, delay: float = DELAY):
    with open(journals_path, encoding="utf-8") as f:
        journals = json.load(f)

    results: dict[str, dict] = {}
    total = len(journals)
    for i, j in enumerate(journals, 1):
        issn = j.get("issn") or j.get("eissn") or ""
        title = j.get("title", "?")
        if not issn:
            continue
        print(f"[{i}/{total}] {title} ({issn})", file=sys.stderr)
        data = get_by_issn(issn)
        if data:
            results[issn] = data
            print(f"  -> OK: round1={data.get('review_round_1_months')}mo "
                  f"total={data.get('total_handling_months')}mo", file=sys.stderr)
        else:
            print(f"  -> not found", file=sys.stderr)
        time.sleep(delay)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} records to {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Scrape SciRev review time data")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--issn",  help="单个 ISSN，如 0028-0836")
    group.add_argument("--slug",  help="直接指定 SciRev slug，如 nature")
    group.add_argument("--batch", help="批量：journals.json 路径")
    ap.add_argument("--out", help="输出文件路径（batch 模式必填）")
    ap.add_argument("--delay", type=float, default=DELAY, help="请求间隔秒数")
    args = ap.parse_args()

    if args.batch:
        if not args.out:
            ap.error("--batch 模式必须指定 --out")
        batch_process(Path(args.batch), Path(args.out), args.delay)
        return

    if args.slug:
        data = scrape_journal(args.slug)
    else:
        data = get_by_issn(args.issn)

    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "not found"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
