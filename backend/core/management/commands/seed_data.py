"""
python manage.py seed_data

Veritabanını örnek verilerle doldurur (idempotent: isme göre update_or_create).
Fiyatlar örnek niteliğindedir; linkler mağazaların arama sayfalarına gider.
"""
from decimal import Decimal
from urllib.parse import quote_plus

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Component,
    ComponentPrice,
    CustomsSettings,
    Laptop,
    LaptopPrice,
    Profession,
    Program,
    Store,
)

# name, kind, website, search url template, kg kargo (sadece global)
STORES = [
    ("Kontakt Home", Store.LOCAL, "https://kontakt.az", "https://kontakt.az/search?q={q}", None),
    ("İrşad", Store.LOCAL, "https://irshad.az", "https://irshad.az/search?q={q}", None),
    ("Baku Electronics", Store.LOCAL, "https://www.bakuelectronics.az", "https://www.bakuelectronics.az/search?q={q}", None),
    ("iComp", Store.LOCAL, "https://icomp.az", "https://icomp.az/search?q={q}", None),
    ("CompStore", Store.LOCAL, "https://compstore.az", "https://compstore.az/search?q={q}", None),
    ("Amazon", Store.GLOBAL, "https://www.amazon.com", "https://www.amazon.com/s?k={q}", Decimal("12.00")),
    ("eBay", Store.GLOBAL, "https://www.ebay.com", "https://www.ebay.com/sch/i.html?_nkw={q}", Decimal("14.00")),
    ("Newegg", Store.GLOBAL, "https://www.newegg.com", "https://www.newegg.com/p/pl?d={q}", Decimal("13.00")),
    ("B&H", Store.GLOBAL, "https://www.bhphotovideo.com", "https://www.bhphotovideo.com/c/search?q={q}", Decimal("11.00")),
]
SEARCH_URL = {s[0]: s[3] for s in STORES}

# name, icon, description
PROFESSIONS = [
    ("Grafik / UI Dizayner", "Palette", "Photoshop, Illustrator, Figma ile görsel tasarım"),
    ("Video Editör", "Clapperboard", "Premiere, After Effects, DaVinci ile kurgu ve renk"),
    ("Data Analist", "PieChart", "Power BI, Excel, Python ile veri analizi"),
    ("3D Mimar / Modelleme", "Box", "Blender, AutoCAD, 3ds Max ile modelleme ve render"),
    ("Yazılımcı", "Code", "VS Code, Docker, Android Studio ile geliştirme"),
]

# name, icon, professions, (min_cpu, rec_cpu, min_gpu, rec_gpu, min_ram, rec_ram, min_ssd, rec_ssd)
PROGRAMS = [
    ("Adobe Photoshop", "Image", ["Grafik / UI Dizayner", "Video Editör"], (8000, 18000, 1500, 5000, 8, 16, 256, 512)),
    ("Adobe Illustrator", "PenTool", ["Grafik / UI Dizayner"], (7000, 15000, 1000, 3000, 8, 16, 256, 512)),
    ("Figma", "Figma", ["Grafik / UI Dizayner"], (6000, 15000, 1000, 3000, 8, 16, 256, 512)),
    ("Adobe Premiere Pro", "Film", ["Video Editör"], (12000, 25000, 4000, 10000, 16, 32, 512, 1000)),
    ("Adobe After Effects", "Sparkles", ["Video Editör"], (14000, 28000, 5000, 12000, 16, 32, 512, 1000)),
    ("DaVinci Resolve", "Video", ["Video Editör"], (14000, 28000, 6000, 15000, 16, 32, 512, 1000)),
    ("Blender", "Box", ["3D Mimar / Modelleme"], (10000, 28000, 6000, 15000, 16, 32, 512, 1000)),
    ("AutoCAD", "Ruler", ["3D Mimar / Modelleme"], (8000, 20000, 2500, 8000, 8, 16, 256, 512)),
    ("3ds Max", "Shapes", ["3D Mimar / Modelleme"], (12000, 26000, 5000, 12000, 16, 32, 512, 1000)),
    ("Microsoft Power BI", "Activity", ["Data Analist"], (7000, 15000, 500, 2000, 8, 16, 256, 512)),
    ("Python / Jupyter", "FlaskConical", ["Data Analist", "Yazılımcı"], (7000, 18000, 500, 2000, 8, 16, 256, 512)),
    ("Microsoft Excel", "Table", ["Data Analist"], (6000, 14000, 500, 1500, 8, 16, 256, 512)),
    ("VS Code", "Code", ["Yazılımcı", "Data Analist"], (6000, 15000, 500, 1500, 8, 16, 256, 512)),
    ("Docker Desktop", "Container", ["Yazılımcı"], (12000, 25000, 500, 1500, 16, 32, 512, 1000)),
    ("Android Studio", "Smartphone", ["Yazılımcı"], (12000, 25000, 1000, 3000, 16, 32, 512, 1000)),
]

# name, brand, cpu, gpu, ram, ssd, cpu_score, gpu_score, screen, weight, (local AZN, global USD)
LAPTOPS = [
    ("Lenovo IdeaPad Slim 5 14 (R7 7735HS)", "Lenovo", "AMD Ryzen 7 7735HS", "AMD Radeon 680M",
     16, 512, 24000, 2800, '14" 2.8K OLED 90Hz', "1.46", (1250, 650)),
    ("Acer Nitro V 15 (i5-13420H / RTX 4050)", "Acer", "Intel Core i5-13420H", "NVIDIA RTX 4050 6GB",
     16, 512, 18000, 8500, '15.6" FHD 144Hz', "2.10", (1500, 800)),
    ("ASUS TUF Gaming A15 (R7 7735HS / RTX 4050)", "ASUS", "AMD Ryzen 7 7735HS", "NVIDIA RTX 4050 6GB",
     16, 512, 24000, 8500, '15.6" FHD 144Hz', "2.20", (1700, 900)),
    ("Lenovo Legion 5 15 (R7 7745HX / RTX 4060)", "Lenovo", "AMD Ryzen 7 7745HX", "NVIDIA RTX 4060 8GB",
     16, 1000, 32000, 10800, '15.6" WQHD 165Hz', "2.40", (2600, 1300)),
    ("ASUS ROG Zephyrus G14 (R9 8945HS / RTX 4070)", "ASUS", "AMD Ryzen 9 8945HS", "NVIDIA RTX 4070 8GB",
     32, 1000, 31000, 12500, '14" 3K OLED 120Hz', "1.50", (3800, 1900)),
    ("MSI Raider GE78 HX (i9-14900HX / RTX 4080)", "MSI", "Intel Core i9-14900HX", "NVIDIA RTX 4080 12GB",
     32, 2000, 44000, 18500, '17" QHD+ 240Hz', "3.10", (6500, 3200)),
]

# category, name, brand, extra fields, weight, (local AZN, global USD)
COMPONENTS = [
    (Component.CPU, "AMD Ryzen 5 7600", "AMD", dict(score=27000, socket="AM5", tdp_watts=65), "0.30", (420, 190)),
    (Component.CPU, "AMD Ryzen 7 7800X3D", "AMD", dict(score=34000, socket="AM5", tdp_watts=120), "0.30", (780, 370)),
    (Component.CPU, "Intel Core i5-14400F", "Intel", dict(score=25000, socket="LGA1700", tdp_watts=100), "0.30", (380, 170)),
    (Component.CPU, "Intel Core i7-14700K", "Intel", dict(score=52000, socket="LGA1700", tdp_watts=253), "0.30", (790, 360)),

    (Component.GPU, "NVIDIA GeForce RTX 4060 8GB", "NVIDIA", dict(score=10700, tdp_watts=115), "1.20", (620, 300)),
    (Component.GPU, "NVIDIA GeForce RTX 4070 Super 12GB", "NVIDIA", dict(score=19500, tdp_watts=220), "1.50", (1250, 600)),
    (Component.GPU, "AMD Radeon RX 7800 XT 16GB", "AMD", dict(score=19800, tdp_watts=263), "1.60", (1050, 500)),
    (Component.GPU, "NVIDIA GeForce RTX 4090 24GB", "NVIDIA", dict(score=36000, tdp_watts=450), "2.50", (3600, 1700)),

    (Component.MOTHERBOARD, "MSI PRO B650M-A WiFi", "MSI", dict(socket="AM5", ram_type="DDR5"), "1.00", (300, 140)),
    (Component.MOTHERBOARD, "ASUS ROG Strix X670E-E", "ASUS", dict(socket="AM5", ram_type="DDR5"), "1.50", (700, 330)),
    (Component.MOTHERBOARD, "Gigabyte B760M DS3H DDR4", "Gigabyte", dict(socket="LGA1700", ram_type="DDR4"), "1.00", (240, 110)),
    (Component.MOTHERBOARD, "ASUS TUF Gaming Z790-Plus WiFi", "ASUS", dict(socket="LGA1700", ram_type="DDR5"), "1.40", (520, 240)),

    (Component.RAM, "Kingston Fury Beast 16GB DDR5-5600", "Kingston", dict(capacity_gb=16, ram_type="DDR5"), "0.10", (110, 55)),
    (Component.RAM, "Corsair Vengeance 32GB (2x16) DDR5-6000", "Corsair", dict(capacity_gb=32, ram_type="DDR5"), "0.15", (210, 100)),
    (Component.RAM, "Kingston Fury Beast 32GB (2x16) DDR4-3200", "Kingston", dict(capacity_gb=32, ram_type="DDR4"), "0.15", (150, 70)),
    (Component.RAM, "G.Skill Trident Z5 64GB (2x32) DDR5-6000", "G.Skill", dict(capacity_gb=64, ram_type="DDR5"), "0.20", (400, 200)),

    (Component.SSD, "Kingston NV2 500GB NVMe", "Kingston", dict(capacity_gb=500), "0.05", (90, 40)),
    (Component.SSD, "Samsung 980 1TB NVMe", "Samsung", dict(capacity_gb=1000), "0.05", (160, 75)),
    (Component.SSD, "WD Black SN850X 2TB NVMe", "WD", dict(capacity_gb=2000), "0.05", (340, 160)),

    (Component.CASE_PSU, "Montech X3 Mesh + 600W Bronze", "Montech", dict(psu_watts=600), "7.00", (260, 130)),
    (Component.CASE_PSU, "NZXT H5 Flow + 750W Gold", "NZXT", dict(psu_watts=750), "8.00", (420, 220)),
    (Component.CASE_PSU, "Lian Li Lancool 216 + 1000W Gold", "Lian Li", dict(psu_watts=1000), "9.00", (650, 340)),
]

# Ürün sırasına göre hangi mağazalara hangi çarpanla fiyat girileceği.
# ponytail: deterministik varyasyon; gerçek fiyat çekme (scraper) kapsam dışı.
LOCAL_PLANS = [
    [("Kontakt Home", "1.00"), ("İrşad", "1.04"), ("Baku Electronics", "1.02")],
    [("Kontakt Home", "1.03"), ("iComp", "0.98"), ("CompStore", "1.01")],
    [("İrşad", "1.00"), ("iComp", "0.97"), ("Baku Electronics", "1.05")],
]
GLOBAL_PLANS = [
    [("Amazon", "1.00"), ("eBay", "0.94")],
    [("Amazon", "1.02"), ("Newegg", "0.98")],
    [("Newegg", "1.00"), ("B&H", "1.01"), ("eBay", "0.92")],
]


def _url(store_name, query):
    return SEARCH_URL[store_name].format(q=quote_plus(query))


class Command(BaseCommand):
    help = "CompMatch örnek verilerini yükler (meslek, program, laptop, PC bileşeni, mağaza, fiyat, gümrük ayarı)."

    @transaction.atomic
    def handle(self, *args, **options):
        CustomsSettings.load()

        stores = {}
        for name, kind, website, _tpl, ship in STORES:
            stores[name], _ = Store.objects.update_or_create(
                name=name, defaults=dict(kind=kind, website=website, shipping_per_kg_usd=ship))

        professions = {}
        for order, (name, icon, desc) in enumerate(PROFESSIONS):
            professions[name], _ = Profession.objects.update_or_create(
                name=name, defaults=dict(icon=icon, description=desc, order=order))

        for name, icon, profs, req in PROGRAMS:
            mc, rc, mg, rg, mr, rr, ms, rs = req
            program, _ = Program.objects.update_or_create(name=name, defaults=dict(
                icon=icon,
                min_cpu_score=mc, rec_cpu_score=rc, min_gpu_score=mg, rec_gpu_score=rg,
                min_ram_gb=mr, rec_ram_gb=rr, min_ssd_gb=ms, rec_ssd_gb=rs,
            ))
            program.professions.set([professions[p] for p in profs])

        for i, (name, brand, cpu, gpu, ram, ssd, cs, gs, screen, weight, (azn, usd)) in enumerate(LAPTOPS):
            laptop, _ = Laptop.objects.update_or_create(name=name, defaults=dict(
                brand=brand, cpu=cpu, gpu=gpu, ram_gb=ram, ssd_gb=ssd, cpu_score=cs, gpu_score=gs,
                screen=screen, weight_kg=Decimal(weight),
            ))
            self._prices(LaptopPrice, "laptop", laptop, stores, i, azn, usd, name)

        for i, (cat, name, brand, extra, weight, (azn, usd)) in enumerate(COMPONENTS):
            comp, _ = Component.objects.update_or_create(name=name, defaults=dict(
                category=cat, brand=brand, weight_kg=Decimal(weight), **extra))
            self._prices(ComponentPrice, "component", comp, stores, i, azn, usd, name)

        self.stdout.write(self.style.SUCCESS(
            f"Seed tamam: {Profession.objects.count()} meslek, {Program.objects.count()} program, "
            f"{Laptop.objects.count()} laptop, {Component.objects.count()} bileşen, "
            f"{Store.objects.count()} mağaza, "
            f"{LaptopPrice.objects.count() + ComponentPrice.objects.count()} fiyat."
        ))

    def _prices(self, model, fk, product, stores, i, azn, usd, query):
        for store_name, mult in LOCAL_PLANS[i % len(LOCAL_PLANS)]:
            model.objects.update_or_create(**{fk: product}, store=stores[store_name], defaults=dict(
                price=(Decimal(azn) * Decimal(mult)).quantize(Decimal("1")), currency="AZN",
                url=_url(store_name, query), in_stock=(i % 5 != 3),
            ))
        for store_name, mult in GLOBAL_PLANS[i % len(GLOBAL_PLANS)]:
            model.objects.update_or_create(**{fk: product}, store=stores[store_name], defaults=dict(
                price=(Decimal(usd) * Decimal(mult)).quantize(Decimal("1")), currency="USD",
                url=_url(store_name, query), in_stock=True,
            ))
