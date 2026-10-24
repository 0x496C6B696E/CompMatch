"""
Kibar HTTP istemcisi: robots.txt'e uyar, Crawl-delay'e saygı duyar, diske önbellekler.

Her fetch:
  1. host'un robots.txt'ini (bir kez) okur; izin yoksa None döner.
  2. aynı host'a ardışık isteklerde en az `delay` (veya robots Crawl-delay) saniye bekler.
  3. yanıtı data/cache/<sha1>.html'e yazar; `ttl_hours` dolmadıysa ağa çıkmaz.
"""
import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests
from django.conf import settings

log = logging.getLogger("compmatch.scrapers")

UA = "CompMatch/1.0 (local price comparison tool; respects robots.txt)"
CACHE_DIR = Path(settings.BASE_DIR) / "data" / "cache"

_robots: dict[str, RobotFileParser | None] = {}
_last_hit: dict[str, float] = {}


def _host(url):
    p = urlsplit(url)
    return p.scheme, p.netloc


def _robot(url):
    scheme, host = _host(url)
    if host not in _robots:
        # RobotFileParser.read() varsayılan "Python-urllib" UA'sını kullanır; bazı siteler onu 403'ler ve
        # parser her şeyi yasak sayar. robots.txt'i kendi UA'mızla çekip parse ediyoruz.
        rp = RobotFileParser()
        try:
            resp = requests.get(f"{scheme}://{host}/robots.txt", headers={"User-Agent": UA}, timeout=20)
            if resp.status_code == 404:
                rp.allow_all = True
            elif resp.status_code >= 400:
                rp.disallow_all = True
            else:
                rp.parse(resp.text.splitlines())
        except requests.RequestException as e:
            log.warning("robots.txt okunamadı (%s): %s", host, e)
            rp = None
        _robots[host] = rp
    return _robots[host]


def allowed(url):
    rp = _robot(url)
    return True if rp is None else rp.can_fetch(UA, url)


def crawl_delay(url, default):
    rp = _robot(url)
    d = rp.crawl_delay("*") if rp else None
    return max(default, float(d or 0))


def _cache_path(url):
    return CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest() + ".html")


def fetch(url, *, ttl_hours=12, delay=2.0, headers=None, use_cache=True):
    """Sayfa metni; robots izin vermiyorsa veya hata olursa None."""
    if not allowed(url):
        log.warning("robots.txt izin vermiyor, atlandı: %s", url)
        return None

    path = _cache_path(url)
    if use_cache and path.exists() and time.time() - path.stat().st_mtime < ttl_hours * 3600:
        return path.read_text(encoding="utf-8")

    _, host = _host(url)
    wait = _last_hit.get(host, 0) + crawl_delay(url, delay) - time.time()
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()

    try:
        resp = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "az,ru,en", **(headers or {})}, timeout=40)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning("İstek başarısız %s: %s", url, e)
        return None

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8")
    return resp.text
