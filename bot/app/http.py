from typing import Iterable, Tuple
import httpx
from .config import settings
import logging

log = logging.getLogger("bot.http")

def _unique(seq: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for s in seq:
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out

def _norm_base(u: str) -> str:
    return u.rstrip("/")

def _join(base: str, path: str) -> str:
    return f"{_norm_base(base)}/{path.lstrip('/')}"

def _candidates(path: str) -> list[str]:
    base0 = _norm_base(settings.bff_base_url)
    base_parts = base0.split("/")
    alt_paths = [p.strip() for p in settings.api_alt_paths.split(",") if p.strip()]
    host = "/".join(base_parts[:3])  
    combos = []
    combos.append(_join(base0, path))
    for p in alt_paths:
        combos.append(_join(_join(host, p), path))
    for alt in [u.strip() for u in settings.api_alt_urls.split(",") if u.strip()]:
        combos.append(_join(alt, path))
    return _unique(combos)

async def request_json(method: str, path: str, *, params=None, json=None, timeout=10) -> Tuple[dict | list | None, int]:
    last_code = 0
    last_text = ""
    for url in _candidates(path):
        try:
            async with httpx.AsyncClient(timeout=timeout) as cl:
                r = await cl.request(method, url, params=params, json=json)
            if 200 <= r.status_code < 300:
                try:
                    return r.json(), r.status_code
                except Exception:
                    return None, r.status_code
            last_code = r.status_code
            last_text = r.text
            if r.status_code == 404:
                log.info("fallback 404 on %s %s -> trying next candidate", method, url)
                continue
            log.warning("fallback %s on %s %s: %s", r.status_code, method, url, (r.text[:180] if r.text else ""))
        except httpx.HTTPError as e:
            last_code = 0
            last_text = str(e)
            log.warning("network error on %s %s: %s (try next)", method, url, e)
            continue
    if last_code and last_code != 200:
        log.error("all candidates failed for %s %s: last_code=%s last_text=%s", method, path, last_code, last_text[:200])
    return None, last_code or 0
