"""
PassMark skorları: CPU Mark (cpubenchmark.net) ve G3D Mark (videocardbenchmark.net).
Tam listeler "chart" sayfalarında (high/mid/low end); cpu_list.php eksik olduğu için onlar kullanılır.
robots.txt: User-agent * için Allow: /, Content-Signal use=reference. Haftada bir indirilir.
"""
import html
import re

from . import match
from .http import fetch

PAGES = {
    "cpu": [f"https://www.cpubenchmark.net/{p}.html" for p in ("high_end_cpus", "mid_range_cpus", "low_end_cpus")],
    "gpu": [f"https://www.videocardbenchmark.net/{p}.html" for p in ("high_end_gpus", "mid_range_gpus", "low_end_gpus")],
}

# <li id="rk6641"> ... <span class="prdname">AMD Ryzen 9 9955HX3D</span> ... <span class="count">62,114</span>
ROW = re.compile(r'<li id="rk\d+"[^>]*>.*?<span class="prdname"\s*>(.*?)</span>.*?<span class="count"\s*>\s*([\d,]+)\s*</span>', re.I | re.S)

MOBILE_WORDS = ("laptop", "mobile", "max-q", "notebook")


def parse(page):
    table = {}
    for name, score in ROW.findall(page or ""):
        name = html.unescape(re.sub(r"<[^>]+>", "", name)).strip()
        table[name] = int(score.replace(",", ""))
    return table


def load(kind):
    """kind: 'cpu' | 'gpu' -> {ad: skor}. Boş sözlük = hiçbir sayfa indirilemedi."""
    table = {}
    for url in PAGES[kind]:
        table.update(parse(fetch(url, ttl_hours=24 * 7, delay=3)))
    return table


def lookup(table, name, *, laptop=False, threshold=0.5):
    """(passmark_adı, skor, benzerlik). Laptop GPU'ları için 'Laptop GPU' girdileri önce denenir."""
    names = list(table)
    is_mobile = lambda n: any(w in n.lower() for w in MOBILE_WORDS)
    pools = [[n for n in names if is_mobile(n)], names] if laptop else [[n for n in names if not is_mobile(n)]]
    for pool in pools:
        hit, score = match.best(name, pool, threshold=threshold, strict=True)
        if hit:
            return hit, table[hit], score
    return None, None, 0.0
