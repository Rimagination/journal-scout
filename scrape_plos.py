"""
PLOS Journal Statistics 爬虫
数据来源：
  1. plos.org/metrics/     → 所有 PLOS 期刊汇总页（所有期刊首选）
  2. journals.plos.org/{slug}/s/journal-information
                            → PLOS ONE 的详细分半年度时间序列表

提取字段（均为天数中位数，除非另注）：
  来自 plos.org/metrics/ :
    time_to_first_decision_days   (首次决定天数)
    time_to_publication_days      (收稿到发表天数)
    acceptance_rate_pct           (接受率 %)
    citations                     (引用数，最新统计年)
    publications_count            (发文量)

  来自 PLOS ONE journal-information 页（更详细，仅限 PLOS ONE）:
    time_to_first_editorial_decision_days
    time_to_final_decision_days
    time_to_acceptance_days
    acceptance_to_pub_days
    desk_rejection_rate_pct
    data_period                   (数据区间，如 "Jan - Jun 23")

用法：
    python scrape_plos.py --slug plosone
    python scrape_plos.py --issn 1932-6203
    python scrape_plos.py --all                 # 爬取所有 PLOS 期刊
    python scrape_plos.py --batch journals.json --out out.json

依赖：pip install curl_cffi
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

try:
    from curl_cffi import requests as creq
    _HAS_CURL_CFFI = True
except ImportError:
    _HAS_CURL_CFFI = False
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError

BASE_JOURNALS = "https://journals.plos.org"
METRICS_URL   = "https://plos.org/metrics/"
DELAY = 1.5

# PLOS maintains a small fixed set of journals — hardcode the EISSN→slug mapping.
ISSN_TO_SLUG: dict[str, str] = {
    "1932-6203": "plosone",          # PLOS ONE
    "1545-7885": "plosbiology",      # PLOS Biology
    "1549-1676": "plosmedicine",     # PLOS Medicine
    "1553-7404": "plosgenetics",     # PLOS Genetics
    "1553-7358": "ploscompbiol",     # PLOS Computational Biology
    "1553-7374": "plospathogens",    # PLOS Pathogens
    "1935-2735": "plosntds",         # PLOS Neglected Tropical Diseases
    "2767-3375": "climate",          # PLOS Climate
    "2767-054X": "water",            # PLOS Water
    "2767-3308": "sustainability",   # PLOS Sustainability and Transformation
    "2767-1593": "digitalhealth",    # PLOS Digital Health
    "2767-3162": "globalhealth",     # PLOS Global Public Health
}

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
                r = _get_session().get(url, timeout=20)
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
                with urlopen(req, timeout=20) as resp:
                    return resp.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if attempt < retries:
            time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# Parse plos.org/metrics/  (primary source, all journals)
# ---------------------------------------------------------------------------

def _parse_plos_metrics_page(html: str) -> dict[str, dict]:
    """
    Returns { slug → {time_to_first_decision_days, time_to_publication_days,
                       acceptance_rate_pct, citations, publications_count} }
    """
    results: dict[str, dict] = {}

    # Each journal block contains:
    #   <a href="https://journals.plos.org/{slug}/">...<img ...>
    #   followed soon by:
    #   <p>Citations: <strong>N</strong>...
    #     Time to first decision: <strong>N</strong>&nbsp;days<br>
    #     Time to publication: <b>N days<br></b>
    #     Acceptance rate: <b>N%<br></b>
    #     Number of publications: <b> N<br></b>
    # The blocks are Elementor text-editor widgets.

    # Find all journal slugs via the logo links
    slug_positions: list[tuple[int, str]] = []
    for m in re.finditer(
        r'href="https://journals\.plos\.org/([^/"]+)/"[^>]*>\s*<img',
        html, re.S | re.I
    ):
        slug = m.group(1)
        if slug not in ("", "all", "about"):
            slug_positions.append((m.start(), slug))

    # For each slug, find the nearest metrics paragraph after it
    for i, (pos, slug) in enumerate(slug_positions):
        end_pos = slug_positions[i + 1][0] if i + 1 < len(slug_positions) else pos + 5000
        chunk = html[pos:end_pos]

        data: dict = {}

        m_cit = re.search(r'Citations:\s*<(?:strong|b)>([\d,]+)', chunk, re.I)
        if m_cit:
            data["citations"] = int(m_cit.group(1).replace(",", ""))

        m_tfd = re.search(r'Time to first decision:\s*<(?:strong|b)>(\d+)', chunk, re.I)
        if m_tfd:
            data["time_to_first_decision_days"] = int(m_tfd.group(1))

        m_pub = re.search(r'Time to publication:\s*<(?:strong|b)>(\d+)\s*days', chunk, re.I)
        if m_pub:
            data["time_to_publication_days"] = int(m_pub.group(1))

        m_acc = re.search(r'Acceptance rate:\s*<(?:strong|b)>([\d.]+)%', chunk, re.I)
        if m_acc:
            data["acceptance_rate_pct"] = float(m_acc.group(1))

        m_np = re.search(r'Number of publications:\s*<(?:strong|b)>\s*([\d,]+)', chunk, re.I)
        if m_np:
            data["publications_count"] = int(m_np.group(1).replace(",", ""))

        if data:
            results[slug] = data

    return results


_metrics_cache: Optional[dict[str, dict]] = None


def _get_metrics() -> dict[str, dict]:
    global _metrics_cache
    if _metrics_cache is None:
        html = fetch(METRICS_URL)
        _metrics_cache = _parse_plos_metrics_page(html) if html else {}
    return _metrics_cache


# ---------------------------------------------------------------------------
# Parse PLOS ONE journal-information page  (detailed half-year table)
# ---------------------------------------------------------------------------

class PlosOneTableParser(HTMLParser):
    ROW_MAP = {
        "Time to First Editorial Decision (Rejection or Peer Review)":
            "time_to_first_editorial_decision_days",
        "Time to First Decision":
            "time_to_first_decision_days",
        "Time to Final Decision (Rejection or Acceptance)":
            "time_to_final_decision_days",
        "Time to Acceptance":
            "time_to_acceptance_days",
        "Time to Publication":
            "time_to_publication_days",
        "Time from Acceptance to Publication":
            "acceptance_to_pub_days",
        "Desk Rejections without peer review (%)":
            "desk_rejection_rate_pct",
        "Acceptance Rate":
            "acceptance_rate_pct",
        "Acceptance Rate*":
            "acceptance_rate_pct",
    }

    def __init__(self):
        super().__init__()
        self._in_table = False
        self._in_th = self._in_td = False
        self._text_buf = ""
        self._col_headers: list[str] = []
        self._current_row: list[str] = []
        self._rows: list[list[str]] = []
        self._header_done = False
        self._in_thead = False

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "table" and "table-basic" in attr.get("class", ""):
            self._in_table = True
        if not self._in_table:
            return
        if tag == "thead":
            self._in_thead = True
        if tag in ("th", "td"):
            self._text_buf = ""
        if tag == "th":
            self._in_th = True
        if tag == "td":
            self._in_td = True
        if tag == "tr":
            self._current_row = []

    def handle_endtag(self, tag):
        if not self._in_table:
            return
        if tag == "table":
            self._in_table = False
        if tag == "thead":
            self._in_thead = False
        if tag == "th":
            self._in_th = False
            if self._in_thead or not self._header_done:
                text = self._text_buf.strip()
                if text and text != "\xa0":
                    self._col_headers.append(text)
            self._text_buf = ""
        if tag == "td":
            self._in_td = False
            self._current_row.append(self._text_buf.strip())
            self._text_buf = ""
        if tag == "tr":
            if self._col_headers and not self._header_done:
                self._header_done = True
            if self._current_row:
                self._rows.append(self._current_row)
            self._current_row = []

    def handle_data(self, data):
        if self._in_th or self._in_td:
            self._text_buf += data

    def get_result(self) -> Optional[dict]:
        if not self._col_headers or not self._rows:
            return None
        period = self._col_headers[-1]
        last_col_idx = len(self._col_headers)
        result = {"data_period": period}
        for row in self._rows:
            if not row:
                continue
            label = row[0].strip().rstrip("*")
            key = self.ROW_MAP.get(label) or self.ROW_MAP.get(label.rstrip("*"))
            if key and len(row) > last_col_idx:
                raw = row[last_col_idx].strip().rstrip("%").strip()
                try:
                    result[key] = float(raw)
                except ValueError:
                    result[key] = raw
        return result if len(result) > 1 else None


def _scrape_plosone_detail(slug: str) -> Optional[dict]:
    url = f"{BASE_JOURNALS}/{slug}/s/journal-information"
    html = fetch(url)
    if not html:
        return None
    parser = PlosOneTableParser()
    parser.feed(html)
    return parser.get_result()


# ---------------------------------------------------------------------------
# Main scrape entry point
# ---------------------------------------------------------------------------

def scrape_slug(slug: str) -> Optional[dict]:
    metrics = _get_metrics()
    base_data = metrics.get(slug, {})

    # For PLOS ONE, also fetch the detailed table
    detail = {}
    if slug == "plosone":
        detail = _scrape_plosone_detail(slug) or {}

    if not base_data and not detail:
        return None

    return {
        "source": "plos",
        "url": f"{BASE_JOURNALS}/{slug}/s/journal-information",
        **base_data,
        **detail,   # detail fields override base if both exist for same key
    }


def get_by_issn(issn: str) -> Optional[dict]:
    raw = re.sub(r"[^0-9Xx]", "", issn.upper())
    fmt = f"{raw[:4]}-{raw[4:]}" if len(raw) == 8 else issn
    slug = ISSN_TO_SLUG.get(fmt)
    if not slug:
        return None
    return scrape_slug(slug)


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

def batch_process(journals_path: Path, out_path: Path, delay: float = DELAY):
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
        raw = re.sub(r"[^0-9Xx]", "", issn.upper())
        fmt = f"{raw[:4]}-{raw[4:]}" if len(raw) == 8 else issn
        if fmt not in ISSN_TO_SLUG:
            continue
        print(f"[{i}/{total}] {title} ({issn})", file=sys.stderr)
        data = get_by_issn(issn)
        if data:
            hit += 1
            results[issn] = data
            print(
                f"  -> tfd={data.get('time_to_first_decision_days')}d "
                f"pub={data.get('time_to_publication_days')}d "
                f"acc={data.get('acceptance_rate_pct')}%",
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
    ap = argparse.ArgumentParser(description="Scrape PLOS journal timing stats")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--slug",  help="PLOS slug，如 plosone / plosbiology")
    group.add_argument("--issn",  help="EISSN，如 1932-6203")
    group.add_argument("--all",   action="store_true", help="爬取所有已知 PLOS 期刊")
    group.add_argument("--batch", help="批量：journals.json 路径")
    ap.add_argument("--out",   help="输出路径（--all / --batch 时可选）")
    ap.add_argument("--delay", type=float, default=DELAY)
    args = ap.parse_args()

    if args.all:
        all_results = {}
        for issn, slug in sorted(ISSN_TO_SLUG.items()):
            print(f"Scraping {slug} ({issn})...", file=sys.stderr)
            data = scrape_slug(slug)
            if data:
                all_results[issn] = data
                print(f"  OK: tfd={data.get('time_to_first_decision_days')}d "
                      f"acc={data.get('acceptance_rate_pct')}%", file=sys.stderr)
            else:
                print("  no data", file=sys.stderr)
            time.sleep(args.delay)
        out = json.dumps(all_results, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
            print(f"Saved to {args.out}", file=sys.stderr)
        else:
            print(out)
        return

    if args.batch:
        if not args.out:
            ap.error("--batch 需要 --out")
        batch_process(Path(args.batch), Path(args.out), args.delay)
        return

    if args.slug:
        data = scrape_slug(args.slug)
    else:
        data = get_by_issn(args.issn)

    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "not found or no data"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
