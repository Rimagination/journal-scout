from __future__ import annotations

import argparse
import copy
import ipaddress
import json
import os
import re
import time
from collections import OrderedDict
from html.parser import HTMLParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib import error, parse, request


BASE_DIR = Path(__file__).resolve().parent
ELSEVIER_URL = "https://api.elsevier.com/content/serial/title"
MAX_PREVIEW_HTML_BYTES = 1_500_000
PREVIEW_TIMEOUT_SECONDS = 9.0
PREVIEW_CACHE_TTL_SECONDS = 6 * 60 * 60
PREVIEW_CACHE_MAX_ITEMS = 512
PREVIEW_MIN_COVER_SCORE = 90
WEB_PREVIEW_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}
PREVIEW_IMAGE_KEYS = {
    "og:image",
    "og:image:url",
    "og:image:secure_url",
    "twitter:image",
    "twitter:image:src",
    "image",
    "thumbnail",
    "thumbnailurl",
}
_preview_cache: OrderedDict[str, Tuple[float, Dict[str, Any]]] = OrderedDict()


def json_response(handler: SimpleHTTPRequestHandler, status: int, payload: Dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def resolve_api_key(handler: SimpleHTTPRequestHandler) -> str:
    env_key = str(os.environ.get("ELSEVIER_API_KEY") or "").strip()
    if env_key:
        return env_key
    # Dev fallback: allow browser-provided key to avoid hardcoding in server env.
    req_key = str(handler.headers.get("X-Proxy-Elsevier-Key") or "").strip()
    return req_key


def build_elsevier_query(issn: str) -> str:
    q = {
        "issn": issn,
        "view": "STANDARD",
        "field": "citeScoreYearInfoList,SJR,SNIP,subject-area",
    }
    return f"{ELSEVIER_URL}?{parse.urlencode(q)}"


def proxy_elsevier(issn: str, api_key: str, timeout: float = 10.0) -> Tuple[int, Dict]:
    url = build_elsevier_query(issn)
    req = request.Request(
        url=url,
        headers={
            "Accept": "application/json",
            "X-ELS-APIKey": api_key,
        },
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
            return int(resp.status), data
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"raw": raw}
        return int(e.code), {"error": "elsevier_http_error", "details": body}
    except Exception as e:
        return HTTPStatus.BAD_GATEWAY, {"error": "proxy_failed", "message": str(e)}


def normalize_remote_url(raw_url: str) -> str:
    text = str(raw_url or "").strip()
    if not text:
        return ""
    if text.startswith("//"):
        text = f"https:{text}"
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", text):
        text = f"https://{text}"
    try:
        parsed_url = parse.urlsplit(text)
    except Exception:
        return ""
    if parsed_url.scheme.lower() not in {"http", "https"}:
        return ""
    if not parsed_url.netloc:
        return ""
    return parse.urlunsplit(
        (
            parsed_url.scheme.lower(),
            parsed_url.netloc,
            parsed_url.path or "/",
            parsed_url.query,
            "",
        )
    )


def is_private_or_local_hostname(hostname: str) -> bool:
    host = str(hostname or "").strip().lower()
    if not host:
        return True
    if host in {"localhost"}:
        return True
    if host.endswith(".local"):
        return True
    try:
        ip_obj = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        ip_obj.is_loopback
        or ip_obj.is_private
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def is_safe_remote_url(url: str) -> bool:
    try:
        parsed_url = parse.urlsplit(url)
    except Exception:
        return False
    if parsed_url.scheme not in {"http", "https"}:
        return False
    return not is_private_or_local_hostname(parsed_url.hostname or "")


def normalize_image_url(raw_url: str, base_url: str) -> str:
    text = str(raw_url or "").strip().strip("'\"")
    if not text:
        return ""
    text = re.sub(r"^(https?):(https?://)", r"\2", text, flags=re.IGNORECASE)
    text = re.sub(r"^(https?://)(https?://)", r"\2", text, flags=re.IGNORECASE)
    lower = text.lower()
    if lower.startswith(("data:", "javascript:", "blob:")):
        return ""
    absolute = parse.urljoin(base_url, text)
    try:
        parsed_url = parse.urlsplit(absolute)
    except Exception:
        return ""
    if parsed_url.scheme.lower() not in {"http", "https"}:
        return ""
    return parse.urlunsplit(
        (
            parsed_url.scheme.lower(),
            parsed_url.netloc,
            parsed_url.path or "/",
            parsed_url.query,
            "",
        )
    )


class PreviewHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta_candidates: List[Tuple[str, str]] = []
        self.icon_candidates: List[str] = []
        self.image_candidates: List[str] = []

    @staticmethod
    def _attrs_to_dict(attrs: List[Tuple[str, str]]) -> Dict[str, str]:
        return {
            str(k or "").lower().strip(): str(v or "").strip()
            for k, v in attrs
            if k is not None and v is not None
        }

    @staticmethod
    def _src_from_srcset(srcset: str) -> str:
        first = str(srcset or "").split(",")[0].strip()
        if not first:
            return ""
        return first.split(" ")[0].strip()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        attrs_map = self._attrs_to_dict(attrs)
        t = str(tag or "").lower().strip()

        if t == "meta":
            key = (
                attrs_map.get("property")
                or attrs_map.get("name")
                or attrs_map.get("itemprop")
                or ""
            ).lower()
            content = attrs_map.get("content", "")
            if key and content:
                if key in PREVIEW_IMAGE_KEYS or key.endswith(":image"):
                    self.meta_candidates.append((key, content))
            return

        if t == "link":
            rel = attrs_map.get("rel", "").lower()
            href = attrs_map.get("href", "")
            if href and "icon" in rel:
                self.icon_candidates.append(href)
            return

        if t == "img":
            src = attrs_map.get("src") or attrs_map.get("data-src") or ""
            if not src:
                src = self._src_from_srcset(attrs_map.get("srcset", ""))
            if src:
                self.image_candidates.append(src)


def extract_jsonld_blocks(html_text: str) -> List[str]:
    pattern = re.compile(
        r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    return [str(m).strip() for m in pattern.findall(html_text or "") if str(m).strip()]


def collect_jsonld_image_urls(node: Any, output: List[str]) -> None:
    if isinstance(node, str):
        cleaned = node.strip()
        if cleaned:
            output.append(cleaned)
        return
    if isinstance(node, list):
        for item in node:
            collect_jsonld_image_urls(item, output)
        return
    if not isinstance(node, dict):
        return

    for key, value in node.items():
        lower_key = str(key or "").lower()
        if lower_key in {"image", "logo", "thumbnailurl", "imageurl", "contenturl", "url"}:
            if lower_key == "url":
                type_hint = str(node.get("@type", "")).lower()
                if type_hint not in {"imageobject", "mediaobject"}:
                    continue
            if isinstance(value, dict):
                collect_jsonld_image_urls(value.get("url"), output)
                collect_jsonld_image_urls(value.get("contentUrl"), output)
                collect_jsonld_image_urls(value.get("image"), output)
            else:
                collect_jsonld_image_urls(value, output)
        else:
            collect_jsonld_image_urls(value, output)


def extract_jsonld_image_candidates(html_text: str, base_url: str) -> List[str]:
    candidates: List[str] = []
    for block in extract_jsonld_blocks(html_text):
        try:
            parsed_json = json.loads(block)
        except Exception:
            continue
        raw_urls: List[str] = []
        collect_jsonld_image_urls(parsed_json, raw_urls)
        for raw in raw_urls:
            normalized = normalize_image_url(raw, base_url)
            if normalized:
                candidates.append(normalized)
    return candidates


def dedupe_keep_order(items: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    seen: set[str] = set()
    out: List[Dict[str, str]] = []
    for source, url in items:
        key = str(url or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({"source": source, "url": key})
    return out


def score_preview_candidate(source: str, url: str) -> int:
    src = str(source or "").lower()
    target = str(url or "").lower()
    score = 0

    if src.startswith("og:image"):
        score += 160
    elif src.startswith("twitter:image"):
        score += 150
    elif src.startswith("jsonld:image"):
        score += 140
    elif src.startswith("img:src"):
        score += 90
    elif src.startswith("link:icon"):
        score += 30

    positive_tokens = [
        "cover",
        "cover-hires",
        "issue-cover",
        "current-issue",
        "journal",
        "front",
        "issue",
        "volume",
        "vol",
        "thumbnail",
    ]
    negative_tokens = [
        "logo",
        "icon",
        "favicon",
        "sprite",
        "badge",
        "ads",
        "advert",
        "gampad",
        "tracking",
        "pixel",
        "top_item_image",
        "hero",
        "featured",
        "feature",
        "default-social",
        "social-share",
        "news",
        "press-release",
        "articles_",
        "hub-assets/pericles",
    ]
    if any(token in target for token in positive_tokens):
        score += 25
    if any(token in target for token in negative_tokens):
        score -= 40

    if target.endswith((".jpg", ".jpeg", ".png", ".webp", ".avif")):
        score += 12
    if target.endswith(".svg"):
        score -= 10

    if src.startswith("og:image"):
        if "top_item_image" in target:
            score -= 120
        if "cover" not in target and any(
            token in target for token in ["news", "featured", "hero", "social", "share", "default-social"]
        ):
            score -= 70

    if src.startswith("img:src"):
        if any(token in target for token in ["cover-hires", "issue-cover", "current-issue"]):
            score += 70

    return score


def rank_preview_candidates(candidates: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    indexed: List[Tuple[int, Dict[str, str], int]] = []
    for idx, item in enumerate(candidates):
        source = str(item.get("source") or "")
        url = str(item.get("url") or "")
        score = score_preview_candidate(source, url)
        indexed.append((idx, item, score))

    indexed.sort(key=lambda row: (-row[2], row[0]))
    ranked: List[Dict[str, Any]] = []
    for _, item, score in indexed:
        ranked.append({"source": str(item.get("source") or ""), "url": str(item.get("url") or ""), "score": score})
    return ranked


def parse_web_preview_candidates(html_text: str, base_url: str) -> List[Dict[str, Any]]:
    parser_obj = PreviewHTMLParser()
    try:
        parser_obj.feed(html_text)
    except Exception:
        # Best effort; keep any partially collected tags.
        pass
    finally:
        try:
            parser_obj.close()
        except Exception:
            pass

    raw_candidates: List[Tuple[str, str]] = []

    for key, raw_url in parser_obj.meta_candidates:
        normalized = normalize_image_url(raw_url, base_url)
        if normalized:
            raw_candidates.append((key, normalized))

    for raw_url in extract_jsonld_image_candidates(html_text, base_url):
        raw_candidates.append(("jsonld:image", raw_url))

    image_limit = 8
    for raw_url in parser_obj.image_candidates[:image_limit]:
        normalized = normalize_image_url(raw_url, base_url)
        if normalized:
            raw_candidates.append(("img:src", normalized))

    for raw_url in parser_obj.icon_candidates:
        normalized = normalize_image_url(raw_url, base_url)
        if normalized:
            raw_candidates.append(("link:icon", normalized))

    deduped = dedupe_keep_order(raw_candidates)
    return rank_preview_candidates(deduped)


def get_cached_preview(url: str) -> Dict[str, Any] | None:
    key = str(url or "")
    if not key:
        return None
    now = time.time()
    item = _preview_cache.get(key)
    if not item:
        return None
    expires_at, payload = item
    if expires_at <= now:
        _preview_cache.pop(key, None)
        return None
    _preview_cache.move_to_end(key)
    cached_payload = copy.deepcopy(payload)
    cached_payload["cached"] = True
    return cached_payload


def set_cached_preview(url: str, payload: Dict[str, Any]) -> None:
    key = str(url or "")
    if not key:
        return
    _preview_cache[key] = (time.time() + PREVIEW_CACHE_TTL_SECONDS, copy.deepcopy(payload))
    _preview_cache.move_to_end(key)
    while len(_preview_cache) > PREVIEW_CACHE_MAX_ITEMS:
        _preview_cache.popitem(last=False)


def decode_response_bytes(resp: Any, raw: bytes) -> str:
    encoding = None
    try:
        encoding = resp.headers.get_content_charset()  # type: ignore[attr-defined]
    except Exception:
        encoding = None
    if not encoding:
        content_type = str(resp.headers.get("Content-Type") or "")  # type: ignore[attr-defined]
        match = re.search(r"charset=([a-zA-Z0-9_\-]+)", content_type, flags=re.IGNORECASE)
        if match:
            encoding = match.group(1).strip()
    if not encoding:
        encoding = "utf-8"
    try:
        return raw.decode(encoding, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def fetch_web_preview(url: str, timeout: float = PREVIEW_TIMEOUT_SECONDS) -> Dict[str, Any]:
    normalized_url = normalize_remote_url(url)
    if not normalized_url:
        raise ValueError("invalid_url")
    if not is_safe_remote_url(normalized_url):
        raise ValueError("unsafe_url")

    cached = get_cached_preview(normalized_url)
    if cached:
        return cached

    req = request.Request(normalized_url, headers=WEB_PREVIEW_HEADERS, method="GET")
    with request.urlopen(req, timeout=timeout) as resp:
        final_url = normalize_remote_url(resp.geturl() or normalized_url) or normalized_url
        content_type = str(resp.headers.get("Content-Type") or "").lower()
        raw = resp.read(MAX_PREVIEW_HTML_BYTES + 1)

    truncated = False
    if len(raw) > MAX_PREVIEW_HTML_BYTES:
        raw = raw[:MAX_PREVIEW_HTML_BYTES]
        truncated = True

    if content_type.startswith("image/"):
        payload: Dict[str, Any] = {
            "target_url": normalized_url,
            "resolved_url": final_url,
            "cover_url": final_url,
            "preview_candidates": [{"source": "direct:image", "url": final_url}],
            "content_type": content_type,
            "truncated": False,
            "cached": False,
        }
        set_cached_preview(normalized_url, payload)
        return payload

    html_text = decode_response_bytes(resp, raw)
    candidates = parse_web_preview_candidates(html_text, final_url)
    cover_url = ""
    if candidates:
        top = candidates[0]
        top_score = int(top.get("score") or 0)
        if top_score >= PREVIEW_MIN_COVER_SCORE:
            cover_url = str(top.get("url") or "")
    payload = {
        "target_url": normalized_url,
        "resolved_url": final_url,
        "cover_url": cover_url,
        "preview_candidates": candidates[:12],
        "content_type": content_type,
        "truncated": truncated,
        "cached": False,
    }
    set_cached_preview(normalized_url, payload)
    return payload


def proxy_web_preview(url: str) -> Tuple[int, Dict[str, Any]]:
    try:
        return HTTPStatus.OK, fetch_web_preview(url)
    except ValueError as e:
        reason = str(e)
        if reason == "unsafe_url":
            return HTTPStatus.BAD_REQUEST, {
                "error": "unsafe_url",
                "message": "Only public http/https URLs are allowed.",
            }
        return HTTPStatus.BAD_REQUEST, {"error": "invalid_url", "message": "url is invalid"}
    except error.HTTPError as e:
        return HTTPStatus.BAD_GATEWAY, {
            "error": "upstream_http_error",
            "status": int(e.code),
            "message": str(e.reason),
        }
    except Exception as e:
        return HTTPStatus.BAD_GATEWAY, {"error": "preview_failed", "message": str(e)}


class DevHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = parse.urlparse(self.path)
        if parsed.path == "/api/elsevier/serial-title":
            self.handle_elsevier_proxy(parsed)
            return
        if parsed.path == "/api/web/preview-image":
            self.handle_web_preview(parsed)
            return
        super().do_GET()

    def handle_elsevier_proxy(self, parsed: parse.ParseResult) -> None:
        api_key = resolve_api_key(self)
        if not api_key:
            json_response(
                self,
                HTTPStatus.UNAUTHORIZED,
                {
                    "error": "missing_api_key",
                    "message": "Set ELSEVIER_API_KEY env var or pass X-Proxy-Elsevier-Key header.",
                },
            )
            return

        query = parse.parse_qs(parsed.query)
        issn = str((query.get("issn") or [""])[0]).strip()
        if not issn:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": "missing_issn", "message": "issn is required"})
            return

        status, payload = proxy_elsevier(issn=issn, api_key=api_key)
        json_response(self, status, payload)

    def handle_web_preview(self, parsed: parse.ParseResult) -> None:
        query = parse.parse_qs(parsed.query)
        url = str((query.get("url") or [""])[0]).strip()
        if not url:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": "missing_url", "message": "url is required"})
            return

        refresh = str((query.get("refresh") or [""])[0]).strip().lower()
        normalized = normalize_remote_url(url)
        if refresh in {"1", "true", "yes"} and normalized:
            _preview_cache.pop(normalized, None)

        status, payload = proxy_web_preview(url)
        json_response(self, status, payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Keep output concise.
        print(format % args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Journal Scout local server with Elsevier proxy and webpage preview extraction"
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host")
    parser.add_argument("--port", type=int, default=8000, help="bind port")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), DevHandler)
    print(f"Serving on http://{args.host}:{args.port}")
    print("Elsevier proxy endpoint: /api/elsevier/serial-title?issn=xxxx-xxxx")
    print("Preview image endpoint: /api/web/preview-image?url=https://example.com")
    server.serve_forever()


if __name__ == "__main__":
    main()
