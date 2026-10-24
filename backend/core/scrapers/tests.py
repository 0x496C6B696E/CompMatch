"""Ağ gerektirmeyen scraper testleri: eşleştirme, PassMark satır ayrıştırma, JSON-LD teklif, İrşad doğrulama."""
from decimal import Decimal

from django.test import SimpleTestCase

from . import match, passmark
from .stores import jsonld_product, offer_from_jsonld, page_has_required, safe_url


class MatchTest(SimpleTestCase):
    def test_required_tokens_must_appear_even_when_glued(self):
        name = "ASUS TUF Gaming F15 (i7-13620H / RTX 4060)"
        self.assertGreater(match.similarity(name, "notebook-asus-tuf-gaming-f15-fx507-i7-13620h16gb1-tb-rtx-4060-8gb-211506"), 0.7)
        self.assertEqual(match.similarity(name, "notebook-asus-tuf-gaming-f15-fx507-i7-13700h16gb1-tb-rtx-4060-8gb"), 0.0)  # başka CPU

    def test_suffix_variants_are_different_products(self):
        self.assertEqual(match.similarity("AMD Ryzen 5 7600", "AMD Ryzen 5 7600X (5.3 GHz)"), 0.0)        # 7600 ≠ 7600X
        self.assertEqual(match.similarity("AMD Ryzen 5 7600", "AMD Ryzen 5 7600 (5.1 GHz) Processor"), 1.0)
        self.assertEqual(match.similarity("AMD Ryzen 7 7735HS", "AMD R7 7735HS"), 1.0)                    # ryzen 7 -> r7
        self.assertEqual(match.similarity("NVIDIA GeForce RTX 4060 8GB", "MSI Ventus 2x RTX 4060 Ti (8GB)"), 0.0)  # Ti
        self.assertEqual(match.similarity("NVIDIA GeForce RTX 4060 8GB", "MSI GeForce RTX 4060 Ventus 2X OC 8G"), 1.0)  # 8G = 8GB
        self.assertEqual(match.similarity("Apple MacBook Pro 14 (M3 Pro)", "Apple MacBook Air 13 M3"), 0.0)  # pro/air

    def test_capacity_and_memory_type_are_required_for_stores(self):
        self.assertEqual(match.similarity("Samsung 990 Pro 4TB NVMe", "NVMe SSD Samsung 990 PRO 2 TB"), 0.0)
        self.assertEqual(match.similarity("Samsung 990 Pro 4TB NVMe", "M.2 SSD Samsung 990 PRO 4TB"), 1.0)
        self.assertEqual(match.similarity("Kingston Fury Beast 16GB DDR4-3200", "DDR4 Kingston Fury Beast 8 GB 3200 MHz"), 0.0)
        self.assertEqual(match.similarity("Kingston Fury Beast 16GB DDR4-3200", "Kingston FURY Beast 16GB (1x16GB) DDR4 3200"), 1.0)
        self.assertEqual(match.similarity("Gigabyte B760M DS3H DDR4", "Gigabyte B760M DS3H GEN5 Mainboard"), 0.0)  # DDR4 yok

    def test_series_words_brand_and_bare_numbers(self):
        self.assertEqual(match.similarity("Lenovo IdeaPad Slim 3 (R5 7530U)", "Lenovo IdeaPad Flex 5 14ABR8 R5-7530U"), 0.0)   # slim ≠ flex
        self.assertEqual(match.similarity("Lenovo IdeaPad Slim 3 (R5 7530U)", "LENOVO IdeaPad Slim 3 15ABR8 R5-7530U/8GB"), 1.0)
        self.assertEqual(match.similarity("Dell Inspiron 15 (i5-1335U)", "Notbuk HP 250G10 i5-1335U 15 8GB"), 0.0)             # marka
        self.assertEqual(match.similarity("Apple M3 10-core GPU", "Radeon Vega 10 Mobile"), 0.0)                              # "10" sayılmaz
        self.assertEqual(match.similarity("Apple M3", "Intel Atom 330 @ 1.60GHz"), 0.0)                                       # "m3" ⊄ "atom330"

    def test_strict_mode_for_benchmark_names(self):
        self.assertGreater(match.similarity("NVIDIA RTX 4050 6GB", "GeForce RTX 4050 Laptop GPU", strict=True), 0.6)  # 6GB serbest
        self.assertEqual(match.similarity("Intel UHD Graphics", "Intel UHD 630", strict=True), 0.0)
        self.assertEqual(match.similarity("Intel Iris Xe", "Intel Iris Xe", strict=True), 1.0)
        self.assertEqual(match.similarity("AMD Ryzen 7 7735HS", "AMD Ryzen 7 7735HS", strict=True), 1.0)

    def test_best_prefers_shorter_on_tie_and_system_listings(self):
        hit, score = match.best("Intel Core i7-14700K", ["Intel Core i7-14700K", "Intel Core i7-14700K Processor"])
        self.assertEqual((hit, score), ("Intel Core i7-14700K", 1.0))
        self.assertTrue(match.is_system("Desktop DarkFlash DLM21 B760M Intel Core i5 14400F"))
        self.assertTrue(match.is_system("Notbuk HP Victus 15 i5-13420H RTX 3050"))
        self.assertFalse(match.is_system("PNY GeForce RTX 4060 8GB Verto Dual Fan"))

    def test_query_for_drops_parentheses_and_noise(self):
        self.assertEqual(match.query_for("NVIDIA GeForce RTX 4060 8GB"), "rtx 4060 8gb")
        self.assertEqual(match.query_for("ASUS TUF Gaming A15 (R7 7735HS / RTX 4050)"), "asus tuf a15")


class PassmarkTest(SimpleTestCase):
    def test_parse_chart_rows(self):
        page = (
            '<li id="rk6641"><span class="more_details"></span><a href="/cpu.php?cpu=X"><span class="prdname">AMD Ryzen 9 9955HX3D</span>'
            '<div><span class="index pink" style="width: 86%">(86%)</span></div><span class="count">62,114</span><span class="price-neww">NA</span></a></li>'
            '<li id="rk5706"> <a href="gpu.php?gpu=Y"> <span class="prdname" >GeForce RTX 4060</span> <div></div> <span class="count">19,479</span> </a> </li>'
        )
        self.assertEqual(passmark.parse(page), {"AMD Ryzen 9 9955HX3D": 62114, "GeForce RTX 4060": 19479})

    def test_lookup_prefers_laptop_gpu_for_laptops(self):
        table = {"GeForce RTX 4060": 19479, "GeForce RTX 4060 Laptop GPU": 17000}
        self.assertEqual(passmark.lookup(table, "NVIDIA RTX 4060 8GB", laptop=True)[0], "GeForce RTX 4060 Laptop GPU")
        self.assertEqual(passmark.lookup(table, "NVIDIA GeForce RTX 4060 8GB", laptop=False)[0], "GeForce RTX 4060")


class IrshadVerifyTest(SimpleTestCase):
    def test_product_page_must_mention_cpu_and_gpu(self):
        page = "<div>Prosessor : Intel® Core™ i5-13420H</div><div>Qrafik yaddaş : NVIDIA® GeForce RTX™ 4050</div>"
        self.assertTrue(page_has_required(page, "Acer Nitro V 15 (i5-13420H / RTX 4050)"))
        self.assertFalse(page_has_required(page, "Acer Nitro V 15 (i7-13620H / RTX 4050)"))


class JsonLdTest(SimpleTestCase):
    def test_offer_from_product_block(self):
        page = ('<script type="application/ld+json">{"@type":"WebSite"}</script>'
                '<script type="application/ld+json">{"@type":"Product","name":"X","offers":{"@type":"Offer",'
                '"price":"2999.99","priceCurrency":"AZN","availability":"https://schema.org/OutOfStock"}}</script>')
        offer = offer_from_jsonld(jsonld_product(page), "https://example.az/p")
        self.assertEqual((offer.price, offer.currency, offer.in_stock, offer.url), (Decimal("2999.99"), "AZN", False, "https://example.az/p"))
        self.assertIsNone(offer_from_jsonld({"offers": {"price": "0"}}, "u"))  # 0 = fiyat yok

    def test_scraped_urls_are_sanitized(self):
        base = "https://icomp.az/p.html"
        self.assertEqual(safe_url("javascript:alert(1)", base), base)
        self.assertEqual(safe_url("https://evil.example/x", base), base)
        self.assertEqual(safe_url("/mehsullar/abc", base), "https://icomp.az/mehsullar/abc")
        self.assertEqual(safe_url(None, base), base)
        offer = offer_from_jsonld({"name": "X", "offers": {"price": "5", "url": "data:text/html,hi"}}, base)
        self.assertEqual(offer.url, base)
