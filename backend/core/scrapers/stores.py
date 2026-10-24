"""
Mağaza stratejileri. Her strateji `offers(product_name) -> list[Offer]` verir.

- irshad_search:   İrşad'ın AJAX ürün listesi (/az/products/list?q=), HTML kartlar. robots: Crawl-delay 30.
- jsonld_sitemap:  Sitemap'ten ürün URL'leri -> ad eşleşen sayfalar -> JSON-LD Product/Offer.
                   iComp, CompStore (sitemap-posts.xml) ve Baku Electronics (sitemap-0..3, /mehsul/).
Kontakt Home: robots.txt aramayı yasaklıyor ve bot koruması var -> otomasyon yok, CSV ile girin.
Amazon / eBay / Newegg / B&H: bot koruması -> CSV ile girin (ROADMAP: eBay API).
"""
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import quote_plus, urljoin, urlsplit

from bs4 import BeautifulSoup

from . import match
from .http import fetch

# Sitemap'ler üçüncü taraf XML'i: XXE/billion-laughs riskine girmemek için ayrıştırıcı yok, sadece <loc> regex'i.
LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")


@dataclass
class Offer:
    title: str
    price: Decimal
    currency: str
    url: str
    in_stock: bool = True
    verified: bool = False  # strateji ürünü kendi doğruladı (ad benzerliği tekrar aranmaz)


def safe_url(candidate, base):
    """Çekilen linki güvenli hale getirir: göreli ise base'e göre çözülür; http(s) değilse ya da
    başka bir host'a gidiyorsa (javascript:, data:, üçüncü taraf) sayfanın kendi URL'si kullanılır."""
    u = urljoin(base, (candidate or "").strip())
    p, b = urlsplit(u), urlsplit(base)
    return u if p.scheme in ("http", "https") and p.hostname == b.hostname else base


def _decimal(text):
    m = re.search(r"\d[\d\s.,]*", str(text))
    if not m:
        return None
    s = m.group(0).replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(",", "")          # 1,599.99
    elif "," in s:
        s = s.replace(",", ".")         # 1599,99
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


# --------------------------------------------------------------------------- #
# İrşad: arama (+ ürün sayfasından CPU/GPU doğrulama)
# --------------------------------------------------------------------------- #
def _verifiable(product_name):
    """Sayfada aranacak model token'ları (13420h, 4050, m3, macbook...). Boşsa doğrulama yapılamaz."""
    toks = [t for t in match.tokens(product_name) if t not in match.STOP]
    return match.required(toks, capacity=False)


def page_has_required(page, product_name):
    """Ürün sayfası metni adımızın model token'larını içeriyor mu? Hiç token yoksa False (boş doğrulama yok)."""
    req = _verifiable(product_name)
    if not req:
        return False
    text = re.sub(r"<[^>]+>", " ", page or "")
    page_tokens, flat = set(match.tokens(text)), match.flat(text)
    return all(r in page_tokens or (sum(c.isdigit() for c in r) >= 3 and r in flat) for r in req)


def irshad_search(product_name, max_pages=3):
    """
    İrşad başlıkları model kodu taşır (ANV15-51-76ER), CPU/GPU taşımaz. Başlık yetmezse
    en ucuz adayların ürün sayfası açılıp "Prosessor : ... / Qrafik yaddaş : ..." satırları kontrol edilir.
    """
    url = f"https://irshad.az/az/products/list?q={quote_plus(match.query_for(product_name))}"
    page = fetch(url, ttl_hours=12, delay=30, headers={"X-Requested-With": "XMLHttpRequest"})
    if not page:
        return []
    soup = BeautifulSoup(page, "html.parser")
    offers = []
    for card in soup.select("div.product"):
        a = card.select_one("a.product__name")
        # İndirimde: <span class="old-price"> + <p class="new-price">; yoksa tek fiyat metni.
        price_el = card.select_one(".product__price__current .new-price") or card.select_one(".product__price__current")
        price = _decimal(price_el.get_text(" ", strip=True)) if price_el else None
        if a and price:
            offers.append(Offer(a.get_text(" ", strip=True), price, "AZN", safe_url(a.get("href"), url)))

    by_title = [o for o in offers if match.similarity(product_name, o.title) >= 0.75]
    if by_title or not _verifiable(product_name):
        return by_title
    # Seri adı tutan adaylar (parantezsiz sorguya göre), ucuzdan pahalıya
    series = match.query_for(product_name)
    candidates = sorted((o for o in offers if match.similarity(series, o.title) >= 0.6), key=lambda o: o.price)
    verified = []
    for o in candidates[:max_pages]:
        if page_has_required(fetch(o.url, ttl_hours=24, delay=30), product_name):
            verified.append(Offer(o.title, o.price, o.currency, o.url, o.in_stock, verified=True))
            break
    return verified


# --------------------------------------------------------------------------- #
# JSON-LD Product (sitemap tabanlı)
# --------------------------------------------------------------------------- #
def sitemap_urls(sitemaps, contains=""):
    urls = []
    for sm in sitemaps:
        xml = fetch(sm, ttl_hours=24, delay=2)
        urls += [u for u in LOC.findall(xml or "") if contains in u]
    return urls


def jsonld_product(page):
    """Sayfadaki ilk schema.org Product bloğunu dict olarak döndürür."""
    for block in re.findall(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", page or "", re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Product":
                return item
    return None


def offer_from_jsonld(product, url):
    offers = product.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = _decimal(offers.get("price") or offers.get("lowPrice") or "")
    if not price:  # 0 = mağaza fiyat yayınlamıyor
        return None
    availability = str(offers.get("availability", "")).lower()
    in_stock = "outofstock" not in availability and "soldout" not in availability
    return Offer(product.get("name", ""), price, offers.get("priceCurrency") or "AZN", safe_url(offers.get("url"), url), in_stock)


def jsonld_sitemap(sitemaps, contains="", max_pages=2):
    def offers(product_name):
        urls = sitemap_urls(sitemaps, contains)
        slug = lambda u: u.rstrip("/").rsplit("/", 1)[-1]
        scored = sorted(
            ((u, match.similarity(product_name, slug(u))) for u in urls),
            key=lambda us: (-us[1], len(us[0])),
        )
        found = []
        for u, score in scored[:max_pages]:
            if score < 0.6:
                break
            page = fetch(u, ttl_hours=12, delay=2)
            product = jsonld_product(page)
            offer = offer_from_jsonld(product, u) if product else None
            if offer:
                found.append(offer)
        return found

    return offers


# Store.scraper anahtarı -> strateji. Yeni mağaza: buraya bir satır + admin'de anahtarı seç.
STRATEGIES = {
    "irshad_search": lambda: irshad_search,
    "icomp_sitemap": lambda: jsonld_sitemap(["https://icomp.az/sitemap-posts.xml"], ".html"),
    "compstore_sitemap": lambda: jsonld_sitemap(["https://compstore.az/sitemap-posts.xml"], ".html"),
    "bakuelectronics_sitemap": lambda: jsonld_sitemap(
        [f"https://bakuelectronics.az/sitemap-{i}.xml" for i in range(4)], "/mehsul/"),
}
SCRAPER_CHOICES = [("", "— yok (elle / CSV) —")] + [(k, k) for k in STRATEGIES]
