from __future__ import annotations

import csv
import json
import re
import sqlite3
import html as html_lib
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_FILE = OUT_DIR / "journals.json"
SEARCH_INDEX_FILE = OUT_DIR / "search_index.json"
HQ_STATS_FILE = OUT_DIR / "hq_field_stats.json"
SHOWJCR_DATA_SUBDIR = "中科院分区表及JCR原始数据文件"
CNKI_SCHOLAR_JSON_URL = "https://gitee.com/kailangge/cnki-journals/raw/main/cnki_journals.json"

SEARCH_INDEX_FIELDS = [
    "id",
    "title",
    "issn",
    "eissn",
    "cn_number",
    "if_2023",
    "if_year",
    "jcr_quartile",
    "cas_2025",
    "is_top",
    "hq_level",
    "pku_core",
    "cssci_type",
    "cscd_type",
    "warning_latest",
    "tags",
]


ISSN_RE = re.compile(r"\b(\d{4})-?([\dXx]{4})\b")
CN_RE = re.compile(r"\b(?:CN\s*)?(\d{2})-?(\d{4})/([A-Za-z0-9]{1,4})\b")
LEVEL_RE = re.compile(
    r"(?:中文|外文)?\s*(?:[CE]\s*)?(T\s*[1-4])(?:\s*级)?",
    flags=re.I,
)
ABC_LEVEL_RE = re.compile(r"([ABC])\s*类", flags=re.I)


def norm_key(raw: str) -> str:
    s = str(raw or "").strip().replace("（", "(").replace("）", ")")
    s = re.sub(r"\s+", "", s)
    return s


def soft_key(raw: str) -> str:
    s = norm_key(raw).lower()
    s = re.sub(r"[^\w\u4e00-\u9fff]", "", s)
    return s


def level_rank(level: str) -> Tuple[int, str]:
    s = str(level or "").strip().upper().replace(" ", "")
    if re.fullmatch(r"T[1-4]", s):
        return (int(s[1]), s)
    if s in {"A+", "A", "B", "C", "D"}:
        order = {"A+": 1, "A": 2, "B": 3, "C": 4, "D": 5}
        return (20 + order[s], s)
    if re.fullmatch(r"[ABC]类", s):
        return (10 + ord(s[0]) - ord("A"), s)
    return (99, s)


def parse_hq_level(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    compact = re.sub(r"\s+", "", s).upper()
    if compact in {"A+", "A", "B", "C", "D"}:
        return compact
    m = LEVEL_RE.search(s)
    if m:
        return m.group(1).upper().replace(" ", "")
    m2 = ABC_LEVEL_RE.search(s)
    if m2:
        return f"{m2.group(1).upper()}类"
    return ""


def best_hq_level(levels: List[str]) -> str:
    cleaned = [str(x).strip() for x in levels if str(x or "").strip()]
    if not cleaned:
        return ""
    cleaned.sort(key=level_rank)
    return cleaned[0]


@dataclass
class Journal:
    id: int
    title: str
    issn: str = ""
    eissn: str = ""
    cn_number: str = ""
    publisher: str = ""
    official_url: str = ""
    if_2023: Optional[float] = None
    if_year: str = ""
    jcr_quartile: str = ""
    cas_2025: str = ""
    cas_2023: str = ""
    cas_year: str = ""
    is_top: Optional[bool] = None
    oa_status: str = ""
    warning_latest: str = ""
    warning_latest_year: str = ""
    cscd_type: str = ""
    pku_core: bool = False
    cssci_type: str = ""
    ei_indexed: bool = False
    if_history: List[Dict] = field(default_factory=list)
    cas_history: List[Dict] = field(default_factory=list)
    warning_history: List[Dict] = field(default_factory=list)
    ccf_records: List[Dict] = field(default_factory=list)
    ccft_records: List[Dict] = field(default_factory=list)
    hq_catalog: bool = False
    hq_level: str = ""
    hq_records: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        unique_records: List[Dict[str, str]] = []
        seen: set[Tuple[str, str, str, str]] = set()
        for rec in self.hq_records:
            field_name = str(rec.get("field") or "").strip()
            society = str(rec.get("society") or "").strip()
            level = str(rec.get("level") or "").strip()
            subfield = str(rec.get("subfield") or "").strip()
            key = (field_name, society, level, subfield)
            if key in seen:
                continue
            seen.add(key)
            unique_records.append(
                {
                    "field": field_name,
                    "society": society,
                    "level": level,
                    "subfield": subfield,
                }
            )
        unique_records.sort(
            key=lambda x: (
                level_rank(x.get("level", "")),
                x.get("field", ""),
                x.get("society", ""),
                x.get("subfield", ""),
            )
        )

        hq_fields = sorted({r["field"] for r in unique_records if r.get("field")})
        hq_societies = sorted({r["society"] for r in unique_records if r.get("society")})
        hq_levels = sorted({r["level"] for r in unique_records if r.get("level")}, key=level_rank)

        def dedupe_dict_list(rows: List[Dict], keys: List[str]) -> List[Dict]:
            out: List[Dict] = []
            seen_keys: set[Tuple] = set()
            for row in rows:
                cleaned = {k: row.get(k, "") for k in keys}
                dedupe_key = tuple(cleaned.get(k, "") for k in keys)
                if dedupe_key in seen_keys:
                    continue
                seen_keys.add(dedupe_key)
                out.append(cleaned)
            return out

        if_history = dedupe_dict_list(self.if_history, ["year", "if_value", "quartile", "rank"])
        if_history.sort(key=lambda x: int(str(x.get("year") or "0")), reverse=True)

        cas_history: List[Dict] = []
        seen_cas: set[Tuple] = set()
        for row in self.cas_history:
            subcategories_raw = row.get("subcategories", [])
            subcategories_clean: List[Dict[str, str]] = []
            seen_sub: set[Tuple[str, str]] = set()
            for sub in (subcategories_raw if isinstance(subcategories_raw, list) else []):
                if not isinstance(sub, dict):
                    continue
                sub_name = str(sub.get("name") or "").strip()
                sub_rank = parse_rank(sub.get("rank", ""))
                if not sub_name and not sub_rank:
                    continue
                sub_key = (sub_name, sub_rank)
                if sub_key in seen_sub:
                    continue
                seen_sub.add(sub_key)
                subcategories_clean.append({"name": sub_name, "rank": sub_rank})
            subcategories_clean.sort(key=lambda x: (cas_rank_value(x.get("rank", "")), x.get("name", "")))

            cleaned_row = {
                "year": str(row.get("year", "")).strip(),
                "rank": parse_rank(row.get("rank", "")),
                "top": str(row.get("top", "")).strip(),
                "oa_status": str(row.get("oa_status", "")).strip(),
                "review": str(row.get("review", "")).strip(),
                "wos": str(row.get("wos", "")).strip(),
                "category": str(row.get("category", "")).strip(),
                "subcategories": subcategories_clean,
            }

            dedupe_key = (
                cleaned_row["year"],
                cleaned_row["rank"],
                cleaned_row["top"],
                cleaned_row["oa_status"],
                cleaned_row["review"],
                cleaned_row["wos"],
                cleaned_row["category"],
                tuple((x["name"], x["rank"]) for x in subcategories_clean),
            )
            if dedupe_key in seen_cas:
                continue
            seen_cas.add(dedupe_key)
            cas_history.append(cleaned_row)

        cas_history.sort(key=lambda x: int(str(x.get("year") or "0")), reverse=True)

        warning_history = dedupe_dict_list(self.warning_history, ["year", "value"])
        warning_history.sort(key=lambda x: int(str(x.get("year") or "0")), reverse=True)

        ccf_records = dedupe_dict_list(self.ccf_records, ["year", "area", "category", "level"])
        ccf_records.sort(key=lambda x: (int(str(x.get("year") or "0")), x.get("level", "")), reverse=True)

        ccft_records = dedupe_dict_list(self.ccft_records, ["year", "tier", "category", "cn_number", "zh_title"])
        ccft_records.sort(key=lambda x: (int(str(x.get("year") or "0")), x.get("tier", "")), reverse=True)

        return {
            "id": self.id,
            "title": self.title,
            "issn": self.issn,
            "eissn": self.eissn,
            "cn_number": self.cn_number,
            "publisher": self.publisher,
            "official_url": self.official_url,
            "if_2023": self.if_2023,
            "if_year": self.if_year,
            "jcr_quartile": self.jcr_quartile,
            "cas_2025": self.cas_2025,
            "cas_2023": self.cas_2023,
            "cas_year": self.cas_year,
            "is_top": self.is_top,
            "oa_status": self.oa_status,
            "warning_latest": self.warning_latest,
            "warning_latest_year": self.warning_latest_year,
            "cscd_type": self.cscd_type,
            "pku_core": self.pku_core,
            "cssci_type": self.cssci_type,
            "ei_indexed": self.ei_indexed,
            "if_history": if_history,
            "cas_history": cas_history,
            "warning_history": warning_history,
            "ccf_records": ccf_records,
            "ccft_records": ccft_records,
            "hq_catalog": self.hq_catalog,
            "hq_level": self.hq_level,
            "hq_fields": hq_fields,
            "hq_societies": hq_societies,
            "hq_levels": hq_levels,
            "hq_records": unique_records,
            "tags": sorted(set(self.tags)),
            "sources": sorted(set(self.sources)),
        }


def normalize_title(title: str) -> str:
    t = str(title or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\u4e00-\u9fff]", "", t)
    return t


def normalize_issn(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().upper().replace(" ", "")
    m = ISSN_RE.search(s)
    if not m:
        return ""
    return f"{m.group(1)}-{m.group(2).upper()}"


def normalize_cn(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().upper().replace(" ", "")
    s = s.removeprefix("CN")
    m = CN_RE.search(s)
    if not m:
        return ""
    return f"{m.group(1)}-{m.group(2)}/{m.group(3).upper()}"


def parse_rank(raw) -> str:
    if raw is None:
        return ""
    if isinstance(raw, (int, float)) and int(raw) in (1, 2, 3, 4):
        return f"{int(raw)}区"
    s = str(raw).strip()
    if not s:
        return ""
    m = re.search(r"([1-4])\s*区", s)
    if m:
        return f"{m.group(1)}区"
    m2 = re.search(r"\b([1-4])\s*(?:\[|$)", s)
    if m2:
        return f"{m2.group(1)}区"
    if s in {"1", "2", "3", "4"}:
        return f"{s}区"
    return ""


def parse_bool_zh(raw) -> Optional[bool]:
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in {"是", "y", "yes", "true", "1"}:
        return True
    if s in {"否", "n", "no", "false", "0"}:
        return False
    return None


class JournalStore:
    def __init__(self) -> None:
        self.items: Dict[int, Journal] = {}
        self.by_issn: Dict[str, int] = {}
        self.by_eissn: Dict[str, int] = {}
        self.by_cn: Dict[str, int] = {}
        self.by_title: Dict[str, int] = {}
        self.seq = 1

    def get_or_create(
        self,
        title: str = "",
        issn: str = "",
        eissn: str = "",
        cn_number: str = "",
    ) -> Journal:
        issn_key = normalize_issn(issn)
        eissn_key = normalize_issn(eissn)
        cn_key = normalize_cn(cn_number)

        for idx_key, idx_map in (
            (issn_key, self.by_issn),
            (eissn_key, self.by_eissn),
            (cn_key, self.by_cn),
        ):
            if idx_key and idx_key in idx_map:
                return self.items[idx_map[idx_key]]

        # Important: when CN exists but no current mapping, avoid title-based merge.
        # Many rows in high-quality catalog reuse generic titles/levels, and title merge
        # would incorrectly collapse different CN journals into one record.
        if cn_key:
            jid = self.seq
            self.seq += 1
            j = Journal(id=jid, title=(str(title or "").strip() or f"Unknown-{jid}"))
            self.items[jid] = j
            return j

        t_key = normalize_title(title)
        if t_key and t_key in self.by_title:
            return self.items[self.by_title[t_key]]

        jid = self.seq
        self.seq += 1
        j = Journal(id=jid, title=(str(title or "").strip() or f"Unknown-{jid}"))
        self.items[jid] = j
        return j

    def touch_index(self, j: Journal) -> None:
        if j.issn:
            self.by_issn[normalize_issn(j.issn)] = j.id
        if j.eissn:
            self.by_eissn[normalize_issn(j.eissn)] = j.id
        if j.cn_number:
            self.by_cn[normalize_cn(j.cn_number)] = j.id
        t_key = normalize_title(j.title)
        if t_key:
            self.by_title[t_key] = j.id

    def finalize(self) -> List[Dict]:
        rows = []
        for j in self.items.values():
            if j.hq_records:
                j.hq_catalog = True
                if not j.hq_level:
                    levels = [r.get("level", "") for r in j.hq_records]
                    j.hq_level = best_hq_level(levels)
            if j.jcr_quartile:
                j.tags.append(j.jcr_quartile)
            if j.cas_2025:
                j.tags.append(j.cas_2025)
            if j.cscd_type:
                j.tags.append(f"CSCD-{j.cscd_type}")
            if j.pku_core:
                j.tags.append("北大核心")
            if j.cssci_type:
                j.tags.append("CSSCI" if j.cssci_type == "来源版" else "CSSCI(扩展)")
            if j.ei_indexed:
                j.tags.append("EI")
            if j.hq_catalog:
                j.tags.append("高质量目录")
            if j.hq_level:
                j.tags.append(f"HQ-{j.hq_level}")
            if j.is_top is True:
                j.tags.append("中科院Top")
            if j.warning_latest:
                j.tags.append("期刊预警")
            if j.ccf_records:
                ccf_levels = sorted({str(x.get("level") or "").strip() for x in j.ccf_records if str(x.get("level") or "").strip()})
                if ccf_levels:
                    j.tags.append(f"CCF-{ccf_levels[0]}")
            if j.ccft_records:
                ccft_tiers = sorted({str(x.get("tier") or "").strip() for x in j.ccft_records if str(x.get("tier") or "").strip()}, key=level_rank)
                if ccft_tiers:
                    j.tags.append(f"CCFT-{ccft_tiers[0]}")
            rows.append(j.to_dict())
        rows.sort(
            key=lambda x: (
                0 if x["if_2023"] is not None else 1,
                -(x["if_2023"] or 0),
                x["title"],
            )
        )
        return rows


def find_showjcr_data_dir() -> Optional[Path]:
    direct = DATA_DIR / SHOWJCR_DATA_SUBDIR
    if direct.exists() and direct.is_dir():
        return direct

    repo_path = DATA_DIR / "showjcr_repo" / SHOWJCR_DATA_SUBDIR
    if repo_path.exists() and repo_path.is_dir():
        return repo_path

    for p in DATA_DIR.rglob("FQBJCR*-UTF8.csv"):
        return p.parent
    return None


def pick_latest_showjcr_file(data_dir: Path, prefix: str) -> Tuple[Optional[Path], str]:
    best_path: Optional[Path] = None
    best_year = 0
    pattern = re.compile(rf"{re.escape(prefix)}(\d{{4}})-UTF8\.csv$", flags=re.I)
    for p in data_dir.glob("*.csv"):
        m = pattern.match(p.name)
        if not m:
            continue
        year = int(m.group(1))
        if year > best_year:
            best_year = year
            best_path = p
    return best_path, (str(best_year) if best_year else "")


def parse_if_value(raw) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "")
    if not s:
        return None
    if s.startswith("<"):
        s = s[1:]
    try:
        return float(s)
    except Exception:
        return None


def parse_issn_pair(raw: str) -> Tuple[str, str]:
    vals: List[str] = []
    for hit in re.findall(r"\d{4}-?[\dXx]{4}", str(raw or "")):
        n = normalize_issn(hit)
        if n and n not in vals:
            vals.append(n)
    issn = vals[0] if len(vals) >= 1 else ""
    eissn = vals[1] if len(vals) >= 2 else ""
    return issn, eissn


def parse_wos_quartile(raw) -> str:
    s = str(raw or "").strip().upper()
    m = re.search(r"Q([1-4])", s)
    if not m:
        return ""
    return f"Q{m.group(1)}"


def cas_rank_value(rank: str) -> int:
    m = re.match(r"^([1-4])区$", str(rank or "").strip())
    return int(m.group(1)) if m else 99


def parse_year_token(raw) -> str:
    s = str(raw or "").strip()
    m = re.search(r"(20\d{2})", s)
    return m.group(1) if m else ""


def year_value(raw) -> int:
    y = parse_year_token(raw)
    return int(y) if y else 0


def get_row_value(row, key: str):
    if isinstance(row, dict):
        return row.get(key, "")
    if hasattr(row, "keys"):
        try:
            keys = set(row.keys())
            if key in keys:
                return row[key]
        except Exception:
            return ""
    return ""


def parse_cas_subcategories(row) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    seen: set[Tuple[str, str]] = set()
    for idx in range(1, 7):
        name = str(get_row_value(row, f"小类{idx}") or "").strip()
        rank = parse_rank(get_row_value(row, f"小类{idx}分区"))
        if not name and not rank:
            continue
        key = (name, rank)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, "rank": rank})
    out.sort(key=lambda x: (cas_rank_value(x.get("rank", "")), x.get("name", "")))
    return out


def append_if_history(j: Journal, year: str, if_value: Optional[float], quartile: str, rank: str) -> None:
    y = parse_year_token(year)
    if not y:
        return
    j.if_history.append(
        {
            "year": y,
            "if_value": if_value if if_value is not None else "",
            "quartile": quartile.strip(),
            "rank": str(rank or "").strip(),
        }
    )
    if if_value is not None and year_value(y) >= year_value(j.if_year):
        j.if_2023 = if_value
        j.if_year = y
        if quartile:
            j.jcr_quartile = quartile
    elif quartile and (not j.jcr_quartile) and year_value(y) >= year_value(j.if_year):
        j.jcr_quartile = quartile


def append_cas_history(
    j: Journal,
    year: str,
    rank: str,
    top: Optional[bool],
    oa_status: str,
    review: str,
    wos: str,
    category: str,
    subcategories: Optional[List[Dict[str, str]]] = None,
) -> None:
    y = parse_year_token(year)
    if not y:
        return
    clean_rank = parse_rank(rank)
    j.cas_history.append(
        {
            "year": y,
            "rank": clean_rank,
            "top": "是" if top is True else ("否" if top is False else ""),
            "oa_status": str(oa_status or "").strip(),
            "review": str(review or "").strip(),
            "wos": str(wos or "").strip(),
            "category": str(category or "").strip(),
            "subcategories": subcategories or [],
        }
    )
    if clean_rank and year_value(y) >= year_value(j.cas_year):
        j.cas_2025 = clean_rank
        j.cas_year = y
        if top is not None:
            j.is_top = top
        if oa_status:
            j.oa_status = str(oa_status).strip()
    if y == "2023" and clean_rank:
        j.cas_2023 = clean_rank


def append_warning_history(j: Journal, year: str, value: str) -> None:
    y = parse_year_token(year)
    v = str(value or "").strip()
    if not y or not v:
        return
    j.warning_history.append({"year": y, "value": v})
    if year_value(y) >= year_value(j.warning_latest_year):
        j.warning_latest_year = y
        j.warning_latest = v


def append_ccf_record(j: Journal, year: str, area: str, category: str, level: str) -> None:
    y = parse_year_token(year)
    if not y:
        return
    j.ccf_records.append(
        {
            "year": y,
            "area": str(area or "").strip(),
            "category": str(category or "").strip(),
            "level": str(level or "").strip(),
        }
    )


def append_ccft_record(j: Journal, year: str, tier: str, category: str, cn_number: str, zh_title: str) -> None:
    y = parse_year_token(year)
    if not y:
        return
    j.ccft_records.append(
        {
            "year": y,
            "tier": str(tier or "").strip(),
            "category": str(category or "").strip(),
            "cn_number": normalize_cn(cn_number),
            "zh_title": str(zh_title or "").strip(),
        }
    )


def load_showjcr_jcr(store: JournalStore, csv_path: Path, jcr_year: str) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [str(x) for x in (reader.fieldnames or [])]
        if_col = ""
        quartile_col = ""
        for fn in fieldnames:
            if not if_col and re.fullmatch(r"IF\(\d{4}\)", fn, flags=re.I):
                if_col = fn
            if not quartile_col and "quartile" in fn.lower():
                quartile_col = fn

        for row in reader:
            title = str(row.get("Journal", "") or "").strip()
            issn = normalize_issn(row.get("ISSN", ""))
            eissn = normalize_issn(row.get("eISSN", ""))
            if not title and not issn and not eissn:
                continue

            j = store.get_or_create(title=title, issn=issn, eissn=eissn)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            if issn and not j.issn:
                j.issn = issn
            if eissn and not j.eissn:
                j.eissn = eissn

            if if_col:
                v = parse_if_value(row.get(if_col))
                q = parse_wos_quartile(row.get(quartile_col)) if quartile_col else ""
                append_if_history(j, jcr_year, v, q, "")
            if quartile_col:
                q = parse_wos_quartile(row.get(quartile_col))
                if q and not j.jcr_quartile:
                    j.jcr_quartile = q

            j.sources.append(f"showjcr:{csv_path.name}")
            store.touch_index(j)


def load_showjcr_fqb(store: JournalStore, csv_path: Path, cas_year: str) -> None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = str(row.get("Journal", "") or "").strip()
            issn, eissn = parse_issn_pair(row.get("ISSN/EISSN", ""))
            if not title and not issn and not eissn:
                continue

            rank = parse_rank(row.get("大类分区", ""))
            top = parse_bool_zh(row.get("Top", ""))
            oa = str(row.get("Open Access", "") or "").strip()
            review = str(row.get("Review", "") or "").strip()
            wos = str(row.get("Web of Science", "") or "").strip()
            category = str(row.get("大类", "") or "").strip()
            subcategories = parse_cas_subcategories(row)

            j = store.get_or_create(title=title, issn=issn, eissn=eissn)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            if issn and not j.issn:
                j.issn = issn
            if eissn and not j.eissn:
                j.eissn = eissn

            append_cas_history(
                j=j,
                year=cas_year,
                rank=rank,
                top=top,
                oa_status=oa,
                review=review,
                wos=wos,
                category=category,
                subcategories=subcategories,
            )

            j.sources.append(f"showjcr:{csv_path.name}")
            store.touch_index(j)


def find_showjcr_db_file(data_dir: Optional[Path] = None) -> Optional[Path]:
    candidates: List[Path] = []
    if data_dir:
        direct = data_dir / "jcr.db"
        if direct.exists():
            return direct
        candidates.extend(sorted(data_dir.glob("*.db")))
    candidates.extend(sorted(DATA_DIR.rglob("jcr.db")))
    if not candidates:
        return None
    candidates.sort(key=lambda p: (0 if "showjcr_repo" in str(p) else 1, len(str(p))))
    return candidates[0]


def load_showjcr_db(store: JournalStore, db_path: Path) -> Dict[str, str]:
    meta = {
        "showjcr_db_file": db_path.name,
        "showjcr_db_path": str(db_path),
        "showjcr_jcr_file": "",
        "showjcr_jcr_year": "",
        "showjcr_fqb_file": "",
        "showjcr_fqb_year": "",
        "showjcr_warning_file": "",
        "showjcr_warning_year": "",
        "showjcr_ccf_file": "",
        "showjcr_ccft_file": "",
    }

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = sorted([str(r[0]) for r in cur.fetchall()])
    table_set = set(table_names)

    jcr_tables = sorted([t for t in table_names if re.fullmatch(r"JCR\d{4}", t)], key=year_value)
    fqb_tables = sorted([t for t in table_names if re.fullmatch(r"FQBJCR\d{4}", t)], key=year_value)
    warn_tables = sorted([t for t in table_names if re.fullmatch(r"GJQKYJMD\d{4}", t)], key=year_value)

    if jcr_tables:
        meta["showjcr_jcr_file"] = ",".join(jcr_tables)
        meta["showjcr_jcr_year"] = ",".join([parse_year_token(x) for x in jcr_tables if parse_year_token(x)])
    if fqb_tables:
        meta["showjcr_fqb_file"] = ",".join(fqb_tables)
        meta["showjcr_fqb_year"] = ",".join([parse_year_token(x) for x in fqb_tables if parse_year_token(x)])
    if warn_tables:
        meta["showjcr_warning_file"] = ",".join(warn_tables)
        meta["showjcr_warning_year"] = ",".join([parse_year_token(x) for x in warn_tables if parse_year_token(x)])
    if "CCF2022" in table_set:
        meta["showjcr_ccf_file"] = "CCF2022"
    if "CCFT2022" in table_set:
        meta["showjcr_ccft_file"] = "CCFT2022"

    for table in jcr_tables:
        year = parse_year_token(table)
        cur.execute(f'SELECT * FROM "{table}"')
        for row in cur.fetchall():
            title = str(row["Journal"] or "").strip() if "Journal" in row.keys() else ""
            issn = normalize_issn(row["ISSN"]) if "ISSN" in row.keys() else ""
            eissn = normalize_issn(row["eISSN"]) if "eISSN" in row.keys() else ""
            if not title and not issn and not eissn:
                continue
            j = store.get_or_create(title=title, issn=issn, eissn=eissn)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            if issn and not j.issn:
                j.issn = issn
            if eissn and not j.eissn:
                j.eissn = eissn

            if_col = next((k for k in row.keys() if re.fullmatch(r"IF\(\d{4}\)", str(k), flags=re.I)), "")
            quartile_col = next((k for k in row.keys() if "quartile" in str(k).lower()), "")
            rank_col = next((k for k in row.keys() if "rank" in str(k).lower()), "")
            if_value = parse_if_value(row[if_col]) if if_col else None
            quartile = parse_wos_quartile(row[quartile_col]) if quartile_col else ""
            rank = str(row[rank_col] or "").strip() if rank_col else ""
            append_if_history(j, year, if_value, quartile, rank)

            j.sources.append(f"showjcr:{table}")
            store.touch_index(j)

    for table in fqb_tables:
        year = parse_year_token(table)
        cur.execute(f'SELECT * FROM "{table}"')
        for row in cur.fetchall():
            title = str(row["Journal"] or "").strip() if "Journal" in row.keys() else ""
            issn = ""
            eissn = ""
            if "ISSN/EISSN" in row.keys():
                issn, eissn = parse_issn_pair(row["ISSN/EISSN"])
            elif "ISSN" in row.keys():
                issn = normalize_issn(row["ISSN"])
            if not title and not issn and not eissn:
                continue

            j = store.get_or_create(title=title, issn=issn, eissn=eissn)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            if issn and not j.issn:
                j.issn = issn
            if eissn and not j.eissn:
                j.eissn = eissn

            raw_year = year or (str(row["年份"]) if "年份" in row.keys() else "")
            subcategories = parse_cas_subcategories(row)
            append_cas_history(
                j=j,
                year=raw_year,
                rank=row["大类分区"] if "大类分区" in row.keys() else "",
                top=parse_bool_zh(row["Top"] if "Top" in row.keys() else ""),
                oa_status=str(row["Open Access"] or "").strip() if "Open Access" in row.keys() else "",
                review=str(row["Review"] or "").strip() if "Review" in row.keys() else "",
                wos=str(row["Web of Science"] or "").strip() if "Web of Science" in row.keys() else "",
                category=str(row["大类"] or "").strip() if "大类" in row.keys() else "",
                subcategories=subcategories,
            )

            j.sources.append(f"showjcr:{table}")
            store.touch_index(j)

    for table in warn_tables:
        year = parse_year_token(table)
        cur.execute(f'SELECT * FROM "{table}"')
        for row in cur.fetchall():
            if "Journal" not in row.keys():
                continue
            title = str(row["Journal"] or "").strip()
            if not title:
                continue
            value_col = next((k for k in row.keys() if str(k) != "Journal"), "")
            value = str(row[value_col] or "").strip() if value_col else ""
            if not value:
                continue
            j = store.get_or_create(title=title)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            append_warning_history(j, year, value)
            j.sources.append(f"showjcr:{table}")
            store.touch_index(j)

    if "CCF2022" in table_set:
        cur.execute('SELECT * FROM "CCF2022"')
        for row in cur.fetchall():
            title = str(row["Journal"] or "").strip() if "Journal" in row.keys() else ""
            if not title:
                continue
            j = store.get_or_create(title=title)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            publisher = str(row["出版社"] or "").strip() if "出版社" in row.keys() else ""
            website = str(row["网址"] or "").strip() if "网址" in row.keys() else ""
            if publisher and not j.publisher:
                j.publisher = publisher
            if website and not j.official_url:
                j.official_url = website
            append_ccf_record(
                j=j,
                year=row["年份"] if "年份" in row.keys() else "2022",
                area=row["领域"] if "领域" in row.keys() else "",
                category=row["CCF推荐类别（国际学术刊物/会议）"] if "CCF推荐类别（国际学术刊物/会议）" in row.keys() else "",
                level=row["CCF推荐类型"] if "CCF推荐类型" in row.keys() else "",
            )
            j.sources.append("showjcr:CCF2022")
            store.touch_index(j)

    if "CCFT2022" in table_set:
        cur.execute('SELECT * FROM "CCFT2022"')
        for row in cur.fetchall():
            title = str(row["Journal"] or "").strip() if "Journal" in row.keys() else ""
            zh_title = str(row["中文刊名"] or "").strip() if "中文刊名" in row.keys() else ""
            cn_number = str(row["CN号"] or "").strip() if "CN号" in row.keys() else ""
            sponsor = str(row["主办单位"] or "").strip() if "主办单位" in row.keys() else ""
            cn_norm = normalize_cn(cn_number)
            seed_title = title or zh_title
            if not seed_title and not cn_norm:
                continue
            j = store.get_or_create(title=seed_title, cn_number=cn_norm)
            if seed_title and (not j.title or j.title.startswith("Unknown-")):
                j.title = seed_title
            if cn_norm and not j.cn_number:
                j.cn_number = cn_norm
            if sponsor and not j.publisher:
                j.publisher = sponsor
            append_ccft_record(
                j=j,
                year="2022",
                tier=row["T分区"] if "T分区" in row.keys() else "",
                category=row["CCF推荐类别"] if "CCF推荐类别" in row.keys() else "",
                cn_number=cn_norm,
                zh_title=zh_title,
            )
            j.sources.append("showjcr:CCFT2022")
            store.touch_index(j)

    conn.close()
    return meta


def load_showjcr_data(store: JournalStore) -> Dict[str, str]:
    meta = {
        "showjcr_data_dir": "",
        "showjcr_db_file": "",
        "showjcr_db_path": "",
        "showjcr_fqb_file": "",
        "showjcr_fqb_year": "",
        "showjcr_jcr_file": "",
        "showjcr_jcr_year": "",
        "showjcr_warning_file": "",
        "showjcr_warning_year": "",
        "showjcr_ccf_file": "",
        "showjcr_ccft_file": "",
    }
    data_dir = find_showjcr_data_dir()
    if not data_dir:
        return meta

    meta["showjcr_data_dir"] = str(data_dir)
    db_file = find_showjcr_db_file(data_dir)
    if db_file:
        meta.update(load_showjcr_db(store, db_file))
        return meta

    fqb_file, fqb_year = pick_latest_showjcr_file(data_dir, "FQBJCR")
    jcr_file, jcr_year = pick_latest_showjcr_file(data_dir, "JCR")

    if fqb_file:
        load_showjcr_fqb(store, fqb_file, fqb_year)
        meta["showjcr_fqb_file"] = fqb_file.name
        meta["showjcr_fqb_year"] = fqb_year
    if jcr_file:
        load_showjcr_jcr(store, jcr_file, jcr_year)
        meta["showjcr_jcr_file"] = jcr_file.name
        meta["showjcr_jcr_year"] = jcr_year

    return meta


def load_cscd_md(store: JournalStore) -> None:
    file_path = None
    for p in DATA_DIR.glob("*.md"):
        if "CSCD" in p.name:
            file_path = p
            break
    if not file_path:
        return

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    rows = re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", text)
    for no, title, issn, cscd_type in rows:
        if no == "序号":
            continue
        issn_norm = normalize_issn(issn)
        if not issn_norm and not title:
            continue
        j = store.get_or_create(title=title, issn=issn_norm)
        if title and (not j.title or j.title.startswith("Unknown-")):
            j.title = title.strip()
        if issn_norm and not j.issn:
            j.issn = issn_norm
        c_type = str(cscd_type).strip()
        if c_type:
            j.cscd_type = c_type
        j.sources.append(f"md:{file_path.name}")
        store.touch_index(j)


def fetch_json_url(url: str, timeout: int = 30):
    req = urllib_request.Request(
        url,
        headers={
            "User-Agent": "JournalScoutDataBuilder/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except (HTTPError, URLError, TimeoutError, OSError):
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def normalize_tag_text(raw: str) -> str:
    s = str(raw or "").strip()
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\s+", "", s)
    return s


def pick_cssci_type(current: str, candidate: str) -> str:
    cur = str(current or "").strip()
    cand = str(candidate or "").strip()
    if not cand:
        return cur
    if not cur:
        return cand
    rank = {"来源版": 1, "扩展版": 2}
    return cand if rank.get(cand, 99) < rank.get(cur, 99) else cur


def pick_cscd_type(current: str, candidate: str) -> str:
    cur = str(current or "").strip()
    cand = str(candidate or "").strip()
    if not cand:
        return cur
    if not cur:
        return cand
    rank = {"核心库": 1, "扩展库": 2}
    return cand if rank.get(cand, 99) < rank.get(cur, 99) else cur


def extract_wos_tokens(raw: str) -> List[str]:
    s = str(raw or "").upper().strip()
    if not s:
        return []
    out: set[str] = set()
    parts = [x for x in re.split(r"[^A-Z0-9]+", s) if x]
    for token in parts:
        if token in {"SCI", "SCIE", "ESCI", "SSCI", "AHCI", "EI"}:
            out.add(token)
        if "SSCI" in token:
            out.add("SSCI")
        if "SCIE" in token:
            out.add("SCIE")
        if "ESCI" in token:
            out.add("ESCI")
    if re.search(r"\bSCI\b", re.sub(r"[^A-Z]", " ", s)):
        out.add("SCI")
    if re.search(r"\bEI\b", re.sub(r"[^A-Z]", " ", s)):
        out.add("EI")
    return sorted(out)


def load_cnki_scholar_data(store: JournalStore) -> Dict[str, object]:
    meta: Dict[str, object] = {
        "cnki_scholar_source_url": CNKI_SCHOLAR_JSON_URL,
        "cnki_scholar_total_rows": 0,
        "cnki_scholar_matched_rows": 0,
        "cnki_scholar_updated_journals": 0,
        "cnki_scholar_ambiguous_rows": 0,
        "cnki_scholar_error": "",
    }

    payload = fetch_json_url(CNKI_SCHOLAR_JSON_URL, timeout=45)
    if not isinstance(payload, list):
        meta["cnki_scholar_error"] = "fetch_failed_or_invalid_payload"
        return meta

    meta["cnki_scholar_total_rows"] = len(payload)

    title_map: Dict[str, List[int]] = {}
    for j in store.items.values():
        key = normalize_title(j.title)
        if not key:
            continue
        title_map.setdefault(key, []).append(j.id)

    updated_ids: set[int] = set()
    for row in payload:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        key = normalize_title(title)
        if not key:
            continue

        ids = title_map.get(key, [])
        if len(ids) != 1:
            if len(ids) > 1:
                meta["cnki_scholar_ambiguous_rows"] = int(meta["cnki_scholar_ambiguous_rows"]) + 1
            continue

        j = store.items.get(ids[0])
        if not j:
            continue
        meta["cnki_scholar_matched_rows"] = int(meta["cnki_scholar_matched_rows"]) + 1

        changed = False
        raw_tags = row.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        tags = {normalize_tag_text(t) for t in raw_tags if str(t or "").strip()}

        wos_raw = str(row.get("WOS") or "").strip()
        wos_tokens = set(extract_wos_tokens(wos_raw))

        if "北大核心" in tags and not j.pku_core:
            j.pku_core = True
            changed = True

        cssci_candidate = ""
        if "CSSCI(扩展)" in tags or "CSSCI扩展" in tags:
            cssci_candidate = "扩展版"
        elif "CSSCI" in tags:
            cssci_candidate = "来源版"
        cssci_merged = pick_cssci_type(j.cssci_type, cssci_candidate)
        if cssci_merged != j.cssci_type:
            j.cssci_type = cssci_merged
            changed = True

        cscd_candidate = ""
        if "CSCD(核心)" in tags or "CSCD核心" in tags:
            cscd_candidate = "核心库"
        elif "CSCD(扩展)" in tags or "CSCD扩展" in tags:
            cscd_candidate = "扩展库"
        elif "CSCD" in tags:
            cscd_candidate = "核心库"
        cscd_merged = pick_cscd_type(j.cscd_type, cscd_candidate)
        if cscd_merged != j.cscd_type:
            j.cscd_type = cscd_merged
            changed = True

        if ("EI" in tags or "EI" in wos_tokens) and not j.ei_indexed:
            j.ei_indexed = True
            changed = True

        for token in ("SCI", "SCIE", "ESCI", "SSCI", "EI"):
            if token in tags and token not in j.tags:
                j.tags.append(token)
                changed = True
            if token in wos_tokens and token not in j.tags:
                j.tags.append(token)
                changed = True

        if changed:
            updated_ids.add(j.id)

        j.sources.append("cnki-scholar")
        store.touch_index(j)

    meta["cnki_scholar_updated_journals"] = len(updated_ids)
    return meta


def parse_html_table_rows(text: str) -> List[List[str]]:
    out: List[List[str]] = []
    for row_html in re.findall(r"<tr>(.*?)</tr>", text, flags=re.S):
        cells = []
        for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S | re.I):
            clean = re.sub(r"<.*?>", "", c, flags=re.S)
            clean = html_lib.unescape(clean).strip()
            clean = re.sub(r"\s+", " ", clean)
            cells.append(clean)
        if cells:
            out.append(cells)
    return out


def choose_hq_md_file() -> Optional[Path]:
    preferred = [
        p
        for p in DATA_DIR.glob("*.md")
        if ("高质量" in p.name and ("目录" in p.name or "分级" in p.name))
    ]
    if preferred:
        return sorted(preferred, key=lambda p: p.stat().st_size, reverse=True)[0]
    md_files = sorted(DATA_DIR.glob("*.md"), key=lambda p: p.stat().st_size, reverse=True)
    return md_files[0] if md_files else None


def parse_hq_toc_entries(text: str, headings: List[Tuple[int, int, str]]) -> List[Dict]:
    if len(headings) < 3:
        return []
    toc_text = text[headings[1][1] : headings[2][0]]

    entries: List[Dict] = []
    for line in toc_text.splitlines():
        s = line.strip()
        if not s:
            continue
        m_num = re.match(r"^(\d+)\.", s)
        if not m_num:
            continue
        m_cnt = re.search(r"(\d+)\s*[种本]", s)
        if not m_cnt:
            continue
        idx = int(m_num.group(1))
        count = int(m_cnt.group(1))
        start = m_num.end()
        open_pos = max(
            s.rfind("（", start, m_cnt.start()),
            s.rfind("(", start, m_cnt.start()),
        )
        title = (s[start:open_pos] if open_pos != -1 else s[start : m_cnt.start()]).strip(" .")
        if not title:
            continue
        entries.append({"index": idx, "field": title, "declared_count": count})

    # Keep one row per index in ascending order.
    by_idx: Dict[int, Dict] = {}
    for e in entries:
        if e["index"] not in by_idx:
            by_idx[e["index"]] = e
    ordered = [by_idx[i] for i in sorted(by_idx.keys())]
    return ordered


def split_hq_sections(text: str, headings: List[Tuple[int, int, str]], toc_entries: List[Dict]) -> List[Dict]:
    heading_norms = [norm_key(h[2]) for h in headings]
    heading_softs = [soft_key(h[2]) for h in headings]
    toc_norms = [norm_key(e["field"]) for e in toc_entries]
    toc_softs = [soft_key(e["field"]) for e in toc_entries]
    toc_norm_set = set(toc_norms)
    toc_soft_set = set(toc_softs)

    def combined_keys(i: int) -> Tuple[str, str]:
        if i + 1 >= len(headings):
            return "", ""
        merged = headings[i][2] + headings[i + 1][2]
        return norm_key(merged), soft_key(merged)

    def find_heading_idx(target_norm: str, target_soft: str, start_from: int) -> Tuple[Optional[int], int]:
        for i in range(start_from, len(headings)):
            if heading_norms[i] == target_norm or heading_softs[i] == target_soft:
                return i, 1
            cnorm, csoft = combined_keys(i)
            if cnorm and (cnorm == target_norm or csoft == target_soft):
                return i, 2
        for i in range(len(headings)):
            if heading_norms[i] == target_norm or heading_softs[i] == target_soft:
                return i, 1
            cnorm, csoft = combined_keys(i)
            if cnorm and (cnorm == target_norm or csoft == target_soft):
                return i, 2
        return None, 0

    def is_toc_heading_at(i: int) -> bool:
        if heading_norms[i] in toc_norm_set or heading_softs[i] in toc_soft_set:
            return True
        cnorm, csoft = combined_keys(i)
        if cnorm and (cnorm in toc_norm_set or csoft in toc_soft_set):
            return True
        return False

    sections: List[Dict] = []
    search_from = 0
    for entry in toc_entries:
        target = norm_key(entry["field"])
        target_soft = soft_key(entry["field"])
        hit_idx, hit_span = find_heading_idx(target, target_soft, search_from)
        if hit_idx is None:
            sections.append(
                {
                    "index": entry["index"],
                    "field": entry["field"],
                    "declared_count": entry["declared_count"],
                    "found_heading": False,
                    "text": "",
                }
            )
            continue

        start = headings[hit_idx][0]
        end = len(text)
        for j in range(hit_idx + hit_span, len(headings)):
            if is_toc_heading_at(j):
                end = headings[j][0]
                break

        sections.append(
            {
                "index": entry["index"],
                "field": entry["field"],
                "declared_count": entry["declared_count"],
                "found_heading": True,
                "text": text[start:end],
            }
        )
        search_from = hit_idx + max(hit_span, 1)

    return sections


def infer_hq_table_columns(rows: List[List[str]]) -> Tuple[set, set, set, set, set]:
    title_cols: set[int] = set()
    level_cols: set[int] = set()
    issn_cols: set[int] = set()
    cn_cols: set[int] = set()
    subfield_cols: set[int] = set()

    for row in rows[:3]:
        for i, cell in enumerate(row):
            c = str(cell or "").strip()
            c_l = c.lower()
            if "期刊名称" in c or "刊名" in c:
                title_cols.add(i)
            if "级别" in c or "分级" in c:
                level_cols.add(i)
            if "issn" in c_l:
                issn_cols.add(i)
            if c.strip().upper() == "CN" or "CN号" in c or "刊号" in c:
                cn_cols.add(i)
            if "学科领域" in c or c == "领域":
                subfield_cols.add(i)
    return title_cols, level_cols, issn_cols, cn_cols, subfield_cols


def is_hq_header_row(cells: List[str]) -> bool:
    hit = 0
    for cell in cells:
        s = str(cell or "").strip()
        sl = s.lower()
        if not s:
            continue
        if s in {"序号", "期刊名称", "期刊", "刊名", "级别", "分级", "学科领域", "备注", "ISSN", "CN", "CN号", "ISSN/EISSN"}:
            hit += 1
            continue
        if any(x in s for x in ("期刊名称", "级别", "分级", "学科领域")):
            hit += 1
            continue
        if re.fullmatch(r"issn(?:/eissn)?", sl):
            hit += 1
            continue
        if re.fullmatch(r"cn号?", s, flags=re.I):
            hit += 1
            continue
    return hit >= 2


def is_probably_journal_title(text: str) -> bool:
    s = str(text or "").strip()
    if not s:
        return False
    if s in {"级别", "分级", "期刊名称", "期刊", "ISSN", "CN", "CN号", "序号", "备注"}:
        return False
    if re.fullmatch(r"\d+", s):
        return False
    if parse_hq_level(s):
        return False
    if normalize_issn(s) or normalize_cn(s):
        return False
    if re.search(r"共\s*\d+\s*[种本]", s):
        return False
    if len(s) > 220:
        return False
    # Accept broader Unicode letters (some entries are not CJK/ASCII).
    return any(ch.isalpha() for ch in s)


def parse_hq_table_records(table_html: str, inherited_level: str) -> Tuple[List[Dict], str]:
    rows = parse_html_table_rows(table_html)
    if not rows:
        return [], inherited_level

    # Skip appendix-like tables that are not part of the official count.
    preview = " | ".join(" | ".join(r) for r in rows[:3])
    if "其他学会已列入分级目录" in preview and "参选期刊" in preview:
        return [], inherited_level

    title_cols, level_cols, issn_cols, cn_cols, subfield_cols = infer_hq_table_columns(rows)
    expected_cols = max((len(r) for r in rows), default=0)
    current_level = inherited_level
    records: List[Dict] = []

    for row in rows:
        cells = [re.sub(r"\s+", " ", str(c or "")).strip() for c in row]
        if expected_cols and len(cells) < expected_cols and level_cols:
            # Compensate rowspan omission: level column may be absent in continuation rows.
            level_idx = min(level_cols)
            while len(cells) < expected_cols:
                cells.insert(level_idx, "")
        if not any(cells):
            continue

        found_level = ""
        for idx in sorted(level_cols):
            if idx < len(cells):
                lv = parse_hq_level(cells[idx])
                if lv:
                    found_level = lv
                    break
        if not found_level:
            for c in cells:
                lv = parse_hq_level(c)
                if lv:
                    found_level = lv
                    break
        if found_level:
            current_level = found_level

        if is_hq_header_row(cells):
            continue
        non_empty = [x for x in cells if x]
        if len(non_empty) == 1 and parse_hq_level(non_empty[0]):
            continue

        row_issn = ""
        row_cn = ""
        row_subfield = ""

        for idx in sorted(issn_cols):
            if idx < len(cells):
                v = normalize_issn(cells[idx])
                if v:
                    row_issn = v
                    break
        if not row_issn:
            for c in cells:
                v = normalize_issn(c)
                if v:
                    row_issn = v
                    break

        for idx in sorted(cn_cols):
            if idx < len(cells):
                v = normalize_cn(cells[idx])
                if v:
                    row_cn = v
                    break
        if not row_cn:
            for c in cells:
                v = normalize_cn(c)
                if v:
                    row_cn = v
                    break

        for idx in sorted(subfield_cols):
            if idx < len(cells):
                v = str(cells[idx]).strip()
                if v and not is_hq_header_row([v]):
                    row_subfield = v
                    break

        titles: List[str] = []
        if title_cols:
            for idx in sorted(title_cols):
                if idx < len(cells):
                    t = cells[idx]
                    if is_probably_journal_title(t):
                        titles.append(t)
        else:
            skip = set(level_cols) | set(issn_cols) | set(cn_cols) | set(subfield_cols)
            for idx, c in enumerate(cells):
                if idx in skip:
                    continue
                if is_probably_journal_title(c):
                    titles.append(c)

        seen_titles: set[str] = set()
        for title in titles:
            key = normalize_title(title)
            if not key or key in seen_titles:
                continue
            seen_titles.add(key)
            records.append(
                {
                    "title": title.strip(),
                    "issn": row_issn,
                    "cn_number": row_cn,
                    "level": current_level,
                    "subfield": row_subfield,
                }
            )

    return records, current_level


def parse_hq_plain_lines(text_block: str, inherited_level: str) -> Tuple[List[Dict], str]:
    # Fallback parser for non-table list text.
    current_level = inherited_level
    records: List[Dict] = []
    for raw in text_block.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        line = line.lstrip("-*• ")
        if line.startswith("#"):
            continue
        if "编制单位" in line or "发布时间" in line:
            continue

        lv = parse_hq_level(line)
        if lv:
            current_level = lv
            continue

        m = re.match(r"^\d+[\.、]\s*(.+)$", line)
        if not m:
            continue
        body = m.group(1).strip()
        if not is_probably_journal_title(body):
            continue
        issn = normalize_issn(body)
        cn = normalize_cn(body)
        title = body
        if issn:
            title = re.sub(ISSN_RE, "", title).strip()
        if cn:
            title = re.sub(CN_RE, "", title).strip()
        title = title.strip(" ,;，；")
        if not is_probably_journal_title(title):
            continue
        records.append(
            {
                "title": title,
                "issn": issn,
                "cn_number": cn,
                "level": current_level,
                "subfield": "",
            }
        )
    return records, current_level


def attach_hq_record(j: Journal, field_name: str, society: str, level: str, subfield: str) -> None:
    j.hq_catalog = True
    if level:
        if not j.hq_level or level_rank(level) < level_rank(j.hq_level):
            j.hq_level = level
    j.hq_records.append(
        {
            "field": field_name.strip(),
            "society": society.strip(),
            "level": level.strip(),
            "subfield": subfield.strip(),
        }
    )


def postprocess_hq_records(field_name: str, records: List[Dict], declared_count: int) -> List[Dict]:
    out: List[Dict] = []
    for rec in records:
        title = str(rec.get("title") or "").strip()
        if not title:
            continue

        # Remove obvious caption rows incorrectly parsed as titles.
        if title.startswith("《") and "目录" in title:
            continue
        if ("领域" in title and "期刊" in title and any(k in title for k in ("排序", "排名", "水平"))):
            continue

        # Field-specific cleanup rules based on source document quirks.
        if "数学领域" in field_name and title in {"理论与应用分析通讯(英文)", "数学与统计通讯(英文)"}:
            continue
        if "材料-综合领域" in field_name and title in {"Materials矿物冶金与材料学报", "for Corrosion and Protection"}:
            continue
        if "图学领域" in field_name and title == "Engineering":
            continue
        if "仪器仪表领域" in field_name and title == "Instrumentation仪器仪表学报(英文版)":
            continue
        if "管理科学领域" in field_name and title in {
            "南方经济",
            "国际经贸探索",
            "金融经济学研究",
            "信息资源管理学报",
            "会计与经济研究",
            "公共管理评论",
            "经济学报",
            "电子政务",
            "管理学研究",
            "信息系统学报",
            "金融学季刊",
            "珞珈管理评论",
            "数量经济研究",
        }:
            continue

        out.append(rec)

    if "地理资源领域" in field_name:
        # This field contains repeated cross-subfield entries. Keep one by soft title key.
        dedup: Dict[str, Dict] = {}
        for rec in out:
            title = str(rec.get("title") or "").strip()
            key = re.sub(r"\s+", "", title).casefold()
            if key not in dedup:
                dedup[key] = rec
        out = list(dedup.values())

        # If still above declared count, drop one starred duplicate where base title exists.
        if len(out) > declared_count:
            title_set = {str(r.get("title") or "").strip() for r in out}
            pruned: List[Dict] = []
            removed = False
            for rec in out:
                title = str(rec.get("title") or "").strip()
                base = title.rstrip("☆").strip()
                if (not removed) and title != base and base in title_set:
                    removed = True
                    continue
                pruned.append(rec)
            out = pruned

    return out


def load_hq_catalog(store: JournalStore) -> List[Dict]:
    file_path = choose_hq_md_file()
    if not file_path:
        return []

    text = file_path.read_text(encoding="utf-8", errors="ignore")
    headings = [(m.start(), m.end(), m.group(1).strip()) for m in re.finditer(r"^#\s*(.+)$", text, flags=re.M)]
    toc_entries = parse_hq_toc_entries(text, headings)
    sections = split_hq_sections(text, headings, toc_entries)

    field_stats: List[Dict] = []
    for sec in sections:
        field_name = sec["field"]
        declared_count = int(sec["declared_count"])
        section_text = sec.get("text", "")
        found_heading = bool(sec.get("found_heading"))

        if not found_heading or not section_text:
            field_stats.append(
                {
                    "index": sec["index"],
                    "field": field_name,
                    "society": "",
                    "declared_count": declared_count,
                    "parsed_count": 0,
                    "parsed_unique_count": 0,
                    "match_by_parsed_count": False,
                    "match_by_unique_count": False,
                    "match_declared": False,
                    "found_heading": found_heading,
                }
            )
            continue

        society = ""
        m_soc = re.search(r"编制单位[:：]\s*([^\n<]+)", section_text)
        if m_soc:
            society = m_soc.group(1).strip()

        records: List[Dict] = []
        current_level = ""
        parts = re.split(r"(<table>.*?</table>)", section_text, flags=re.S | re.I)
        section_has_table = bool(re.search(r"<table>", section_text, flags=re.I))
        for part in parts:
            if not part.strip():
                continue
            if part.lstrip().lower().startswith("<table>"):
                table_records, current_level = parse_hq_table_records(part, current_level)
                records.extend(table_records)
            elif not section_has_table:
                # Use plain-line fallback only for sections without table data.
                line_records, current_level = parse_hq_plain_lines(part, current_level)
                records.extend(line_records)

        records = postprocess_hq_records(field_name=field_name, records=records, declared_count=declared_count)

        parsed_count = len(records)
        unique_keys: set[str] = set()
        for rec in records:
            issn = normalize_issn(rec.get("issn", ""))
            cn = normalize_cn(rec.get("cn_number", ""))
            title_key = normalize_title(rec.get("title", ""))
            key = issn or cn or title_key
            if key:
                unique_keys.add(key)
        parsed_unique_count = len(unique_keys)

        field_stats.append(
            {
                "index": sec["index"],
                "field": field_name,
                "society": society,
                "declared_count": declared_count,
                "parsed_count": parsed_count,
                "parsed_unique_count": parsed_unique_count,
                "match_by_parsed_count": declared_count == parsed_count,
                "match_by_unique_count": declared_count == parsed_unique_count,
                "match_declared": declared_count in {parsed_count, parsed_unique_count},
                "found_heading": found_heading,
            }
        )

        for rec in records:
            title = str(rec.get("title") or "").strip()
            if not title:
                continue
            issn = normalize_issn(rec.get("issn", ""))
            cn = normalize_cn(rec.get("cn_number", ""))
            level = str(rec.get("level") or "").strip()
            subfield = str(rec.get("subfield") or "").strip()

            j = store.get_or_create(title=title, issn=issn, cn_number=cn)
            if title and (not j.title or j.title.startswith("Unknown-")):
                j.title = title
            if issn and not j.issn:
                j.issn = issn
            if cn and not j.cn_number:
                j.cn_number = cn

            attach_hq_record(j, field_name=field_name, society=society, level=level, subfield=subfield)
            j.sources.append(f"md:{file_path.name}:{field_name}")
            store.touch_index(j)

    field_stats.sort(key=lambda x: x["index"])
    return field_stats


def build_search_index(data: List[Dict], meta: Dict[str, object]) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    for row in data:
        item: Dict[str, object] = {k: row.get(k) for k in SEARCH_INDEX_FIELDS}
        tags = item.get("tags")
        item["tags"] = tags if isinstance(tags, list) else []
        rows.append(item)

    return {
        "meta": {
            "generated_at": meta.get("generated_at"),
            "total_journals": len(rows),
            "source_file": OUT_FILE.name,
            "index_fields": SEARCH_INDEX_FIELDS,
        },
        "journals": rows,
    }


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    store = JournalStore()
    showjcr_meta = load_showjcr_data(store)
    load_cscd_md(store)
    hq_field_stats = load_hq_catalog(store)
    cnki_meta = load_cnki_scholar_data(store)

    data = store.finalize()
    hq_catalog_journals = sum(1 for row in data if row.get("hq_catalog"))
    hq_match_count = sum(1 for row in hq_field_stats if row.get("match_declared"))
    payload = {
        "meta": {
            "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
            "root_data_dir": str(DATA_DIR),
            "cas_if_source": "showjcr_db" if showjcr_meta.get("showjcr_db_file") else "showjcr_csv",
            **showjcr_meta,
            **cnki_meta,
            "total_journals": len(data),
            "hq_catalog_journals": hq_catalog_journals,
            "hq_field_count": len(hq_field_stats),
            "hq_field_match_count": hq_match_count,
            "hq_field_stats": hq_field_stats,
        },
        "journals": data,
    }
    search_index_payload = build_search_index(data, payload["meta"])
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    SEARCH_INDEX_FILE.write_text(
        json.dumps(search_index_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    HQ_STATS_FILE.write_text(json.dumps(hq_field_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {OUT_FILE} with {len(data)} journals.")
    print(f"Generated {SEARCH_INDEX_FILE} with {len(search_index_payload['journals'])} journals.")


if __name__ == "__main__":
    build()
