"""
python manage.py fetch_prices [--store "iComp"] [--only laptops|components] [--limit N] [--dry-run]

`scraper` anahtarı tanımlı her mağaza için katalogdaki ürünleri arar, ad eşleşmesi yeterliyse
fiyat/stok/link kaydını günceller (yoksa oluşturur). robots.txt ve Crawl-delay'e uyar; sayfalar
data/cache/ altına önbelleklenir. İrşad robots'ta 30 sn gecikme ister: tam tur ~30 dk sürer.
"""
from django.core.management.base import BaseCommand

from core.models import Component, ComponentPrice, Laptop, LaptopPrice, Store
from core.scrapers import match
from core.scrapers.stores import STRATEGIES


class Command(BaseCommand):
    help = "Mağaza sitelerinden fiyat ve stok çeker."

    def add_arguments(self, parser):
        parser.add_argument("--store", help="Sadece bu mağaza (ad).")
        parser.add_argument("--only", choices=["laptops", "components"])
        parser.add_argument("--category", help="Sadece bu bileşen kategorisi (cpu, gpu, motherboard, ram, ssd).")
        parser.add_argument("--product", help="Adında bu metin geçen ürünler (deneme / tekil yenileme).")
        parser.add_argument("--limit", type=int, default=0, help="Mağaza başına en fazla N ürün (deneme için).")
        parser.add_argument("--threshold", type=float, default=0.75, help="En düşük ad benzerliği (0-1).")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--clear", action="store_true",
                            help="Önce mağazanın mevcut fiyat kayıtlarını sil (örnek verileri gerçek veriyle değiştirmek için).")

    def handle(self, *args, **opts):
        stores = Store.objects.exclude(scraper="")
        if opts["store"]:
            stores = stores.filter(name=opts["store"])
        if not stores:
            self.stderr.write("Scraper tanımlı mağaza yok. Admin > Mağazalar > 'Scraper' alanını seçin.")
            return

        products = []
        if opts["only"] != "components":
            products += [(LaptopPrice, "laptop", lp) for lp in Laptop.objects.all()]
        if opts["only"] != "laptops":
            # Kasa+PSU kayıtları iki ürünün toplamıdır; mağazada tek ürün olarak bulunmaz -> elle / CSV.
            comps = Component.objects.exclude(category=Component.CASE_PSU)
            if opts["category"]:
                comps = comps.filter(category=opts["category"])
            products += [(ComponentPrice, "component", c) for c in comps]
        if opts["product"]:
            products = [p for p in products if opts["product"].lower() in p[2].name.lower()]
        if opts["limit"]:
            products = products[: opts["limit"]]

        total = 0
        for store in stores:
            strategy = STRATEGIES[store.scraper]()
            self.stdout.write(self.style.MIGRATE_HEADING(f"{store.name} ({store.scraper})"))
            if opts["clear"] and not opts["dry_run"]:
                n = LaptopPrice.objects.filter(store=store).delete()[0] + ComponentPrice.objects.filter(store=store).delete()[0]
                self.stdout.write(f"  {n} eski fiyat kaydı silindi")
            for model, fk, product in products:
                offers = strategy(product.name)
                if fk == "component":  # hazır PC / laptop ilanı bileşen fiyatı değildir
                    offers = [o for o in offers if not match.is_system(o.title)]
                verified = next((o for o in offers if o.verified), None)
                offer, sim = (verified, 1.0) if verified else match.best(
                    product.name, offers, key=lambda o: o.title, threshold=opts["threshold"])
                if not offer:
                    self.stdout.write(f"  ?  {product.name}: {len(offers)} aday, eşleşme yok")
                    continue
                stock = "stokta" if offer.in_stock else "stok yok"
                self.stdout.write(f"  ✓  {product.name} -> {offer.title[:70]} | {offer.price} {offer.currency} | {stock} ({sim:.2f})")
                if not opts["dry_run"]:
                    # Stratejiler linki zaten temizler (stores.safe_url); yazarken yine de yalnızca http(s) kabul.
                    url = offer.url[:200] if offer.url.lower().startswith(("http://", "https://")) else ""
                    model.objects.update_or_create(**{fk: product}, store=store, defaults=dict(
                        price=offer.price, currency=offer.currency[:3], url=url, in_stock=offer.in_stock))
                    total += 1
        self.stdout.write(self.style.SUCCESS(f"{'Önizleme bitti' if opts['dry_run'] else f'{total} fiyat kaydı güncellendi'}."))
