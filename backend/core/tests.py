from decimal import Decimal

from django.test import TestCase

from .models import Component, ComponentPrice, CustomsSettings, Laptop, LaptopPrice, Profession, Program, Store, tr
from .services import (
    aggregate_requirements,
    build_pc,
    compare_prices,
    component_fits,
    landed_cost,
    laptop_fits,
    pick_laptops,
    profession_requirements,
)


class ServicesTest(TestCase):
    def setUp(self):
        self.s = CustomsSettings.load()  # 300 / 0.36 / 15 / 1.70 / 12
        self.local = Store.objects.create(name="Kontakt", kind=Store.LOCAL)
        self.glob = Store.objects.create(name="Amazon", kind=Store.GLOBAL)

    def test_customs_formula(self):
        # Baz = 1000 + 2*12 = 1024 > 300 -> gümrük = 724*0.36 + 15 = 275.64
        c = landed_cost(1000, Decimal("2"), self.s)
        self.assertEqual(c["duty_usd"], Decimal("275.64"))
        self.assertEqual(c["total_azn"], Decimal("2209.39"))  # (1024 + 275.64) * 1.70
        # Limit altı: gümrük yok
        self.assertEqual(landed_cost(200, Decimal("1"), self.s)["duty_usd"], Decimal("0.00"))

    def test_aggregate_takes_max(self):
        a = Program.objects.create(name="A", min_cpu_score=10, rec_cpu_score=20, min_gpu_score=5, rec_gpu_score=50,
                                   min_ram_gb=8, rec_ram_gb=16, min_ssd_gb=256, rec_ssd_gb=512)
        b = Program.objects.create(name="B", min_cpu_score=30, rec_cpu_score=15, min_gpu_score=1, rec_gpu_score=9,
                                   min_ram_gb=16, rec_ram_gb=32, min_ssd_gb=128, rec_ssd_gb=1024)
        req = aggregate_requirements([a, b])
        self.assertEqual(req["min"], {"cpu_score": 30, "gpu_score": 5, "ram_gb": 16, "ssd_gb": 256})
        self.assertEqual(req["rec"], {"cpu_score": 20, "gpu_score": 50, "ram_gb": 32, "ssd_gb": 1024})

    def test_compare_prices_and_laptop_tiers(self):
        lp = Laptop.objects.create(name="L1", brand="X", cpu="c", gpu="g", ram_gb=16, ssd_gb=512,
                                   cpu_score=100, gpu_score=100, weight_kg=Decimal("2"))
        LaptopPrice.objects.create(laptop=lp, store=self.local, price=2500, currency="AZN")
        LaptopPrice.objects.create(laptop=lp, store=self.glob, price=1000, currency="USD")
        cmp_ = compare_prices(lp, self.s)
        self.assertEqual(cmp_["best"]["side"], "global")
        self.assertEqual(cmp_["best"]["savings_azn"], Decimal("290.61"))  # 2500 - 2209.39

        req = {"min": {"cpu_score": 50, "gpu_score": 50, "ram_gb": 8, "ssd_gb": 256},
               "rec": {"cpu_score": 100, "gpu_score": 100, "ram_gb": 16, "ssd_gb": 512}}
        picks = pick_laptops(req, self.s)
        self.assertEqual(len(picks), 1)  # tek laptop -> tek öneri, tekrar yok
        self.assertEqual(picks[0]["meets"], "rec")

        # Sadece min'i karşılayan daha ucuz laptop: value olur, önerilen L1'e düşer, pro için aday kalmaz.
        l2 = Laptop.objects.create(name="L2", brand="X", cpu="c", gpu="g", ram_gb=8, ssd_gb=256,
                                   cpu_score=60, gpu_score=60, weight_kg=Decimal("2"))
        LaptopPrice.objects.create(laptop=l2, store=self.local, price=1500, currency="AZN")
        picks = pick_laptops(req, self.s)
        self.assertEqual([(p["tier"], p["laptop"].name, p["meets"]) for p in picks],
                         [("value", "L2", "min"), ("recommended", "L1", "rec")])

    def test_build_pc_is_compatible(self):
        def mk(cat, name, **kw):
            c = Component.objects.create(category=cat, name=name, brand="B", weight_kg=Decimal("1"), **kw)
            ComponentPrice.objects.create(component=c, store=self.local, price=100, currency="AZN")
            return c

        mk(Component.CPU, "cpu-am5", score=100, socket="AM5", tdp_watts=105)
        mk(Component.GPU, "gpu", score=100, tdp_watts=200)
        mk(Component.MOTHERBOARD, "mb-lga", socket="LGA1700", ram_type="DDR4")
        mk(Component.MOTHERBOARD, "mb-am5", socket="AM5", ram_type="DDR5")
        mk(Component.RAM, "ddr4", capacity_gb=32, ram_type="DDR4")
        mk(Component.RAM, "ddr5", capacity_gb=32, ram_type="DDR5")
        mk(Component.SSD, "ssd", capacity_gb=1000)
        mk(Component.CASE_PSU, "weak", psu_watts=400)
        mk(Component.CASE_PSU, "ok", psu_watts=650)

        req = {"min": {"cpu_score": 50, "gpu_score": 50, "ram_gb": 16, "ssd_gb": 512},
               "rec": {"cpu_score": 100, "gpu_score": 100, "ram_gb": 32, "ssd_gb": 1000}}
        parts = {p["category"]: p for p in build_pc(req, self.s)}
        self.assertEqual(parts["motherboard"]["component"].name, "mb-am5")
        self.assertEqual(parts["motherboard"]["compat"], {"socket": "AM5"})
        self.assertEqual(parts["ram"]["component"].name, "ddr5")
        self.assertEqual(parts["case_psu"]["component"].name, "ok")  # 105 + 200 + 150 = 455 W > 400
        self.assertEqual(parts["case_psu"]["compat"], {"psu_min_w": 455})

    def test_fits_and_translation(self):
        prof = Profession.objects.create(name_az="Montajçı", name_en="Editor")
        prog = Program.objects.create(name="P", min_cpu_score=50, rec_cpu_score=100, min_gpu_score=50, rec_gpu_score=100,
                                      min_ram_gb=8, rec_ram_gb=16, min_ssd_gb=256, rec_ssd_gb=512)
        prog.professions.add(prof)
        reqs = profession_requirements()
        lp = Laptop.objects.create(name="L", brand="X", cpu="c", gpu="g", ram_gb=16, ssd_gb=512,
                                   cpu_score=60, gpu_score=100, weight_kg=Decimal("1"))
        self.assertEqual(laptop_fits(lp, reqs), [(prof, "min")])
        cpu = Component.objects.create(category=Component.CPU, name="c", brand="B", score=100, weight_kg=Decimal("1"))
        self.assertEqual(component_fits(cpu, reqs), [(prof, "rec")])
        self.assertEqual(tr(prof, "name", "en"), "Editor")
        self.assertEqual(tr(prof, "name", "ru"), "Montajçı")  # boş -> AZ'ye düşer
