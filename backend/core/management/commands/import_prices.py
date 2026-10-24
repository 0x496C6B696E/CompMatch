"""
python manage.py import_prices --template > prices.csv     # doldurulacak şablon (mevcut değerlerle)
python manage.py import_prices prices.csv [--dry-run]        # CSV'den fiyat yükle

CSV sütunları: product,store,price,currency,url,in_stock
  product  : Laptop veya bileşen adı (admin'deki Model alanı, birebir)
  store    : Mağaza adı (admin'deki ad, birebir)
  currency : AZN | USD
  in_stock : 1/0, true/false, evet/hayır
Boş `price` satırları atlanır. Otomasyonu olmayan mağazalar (Kontakt Home, Amazon, eBay, Newegg, B&H) için yol budur.
"""
import csv
import sys

from django.core.management.base import BaseCommand, CommandError

from core.models import Component, ComponentPrice, Laptop, LaptopPrice, Store

COLUMNS = ["product", "store", "price", "currency", "url", "in_stock"]
TRUE = {"1", "true", "yes", "evet", "var", "y"}


class Command(BaseCommand):
    help = "CSV'den mağaza fiyatlarını yükler veya doldurulacak şablonu yazar."

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", help="CSV dosyası")
        parser.add_argument("--template", action="store_true", help="Şablon CSV'yi stdout'a yaz.")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        if opts["template"]:
            return self.template()
        if not opts["path"]:
            raise CommandError("CSV yolu verin veya --template kullanın.")
        self.load(opts["path"], opts["dry_run"])

    def template(self):
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(COLUMNS)
        stores = list(Store.objects.all())
        for model, fk, qs in ((LaptopPrice, "laptop", Laptop.objects.all()), (ComponentPrice, "component", Component.objects.all())):
            for product in qs:
                existing = {p.store_id: p for p in model.objects.filter(**{fk: product})}
                for s in stores:
                    p = existing.get(s.id)
                    w.writerow([product.name, s.name, p.price if p else "", p.currency if p else ("AZN" if s.kind == Store.LOCAL else "USD"),
                                p.url if p else "", int(p.in_stock) if p else 1])

    def load(self, path, dry_run):
        laptops = {l.name: l for l in Laptop.objects.all()}
        components = {c.name: c for c in Component.objects.all()}
        stores = {s.name: s for s in Store.objects.all()}
        ok = skipped = 0
        with open(path, newline="", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.DictReader(f), start=2):
                price = (row.get("price") or "").strip()
                if not price:
                    skipped += 1
                    continue
                name, store_name = (row.get("product") or "").strip(), (row.get("store") or "").strip()
                store = stores.get(store_name)
                product = laptops.get(name) or components.get(name)
                if not store or not product:
                    self.stderr.write(f"satır {i}: {'mağaza' if not store else 'ürün'} bulunamadı: {store_name if not store else name}")
                    skipped += 1
                    continue
                model, fk = (LaptopPrice, "laptop") if name in laptops else (ComponentPrice, "component")
                defaults = dict(
                    price=price.replace(",", "."),
                    currency=(row.get("currency") or ("AZN" if store.kind == Store.LOCAL else "USD")).strip().upper()[:3],
                    url=(row.get("url") or "").strip()[:200],
                    in_stock=(row.get("in_stock") or "1").strip().lower() in TRUE,
                )
                if not dry_run:
                    model.objects.update_or_create(**{fk: product}, store=store, defaults=defaults)
                ok += 1
        self.stdout.write(self.style.SUCCESS(f"{'Önizleme' if dry_run else 'Yüklendi'}: {ok} fiyat, {skipped} satır atlandı."))
