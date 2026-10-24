"""
python manage.py fetch_benchmarks [--dry-run] [--threshold 0.5]

PassMark CPU Mark ve G3D Mark listelerini indirir (haftalık önbellek), laptop ve bileşen
skorlarını ada göre eşleştirip günceller. Eşleşmeyenleri listeler.
"""
from django.core.management.base import BaseCommand

from core.models import Component, Laptop
from core.scrapers import passmark


class Command(BaseCommand):
    help = "PassMark'tan CPU/GPU skorlarını çekip laptop ve bileşenlere yazar."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Sadece göster, kaydetme.")
        parser.add_argument("--threshold", type=float, default=0.6, help="En düşük benzerlik (0-1).")

    def handle(self, *args, **opts):
        cpu, gpu = passmark.load("cpu"), passmark.load("gpu")
        if not cpu or not gpu:
            self.stderr.write("PassMark listeleri indirilemedi (ağ / robots). Çıkılıyor.")
            return
        self.stdout.write(f"PassMark: {len(cpu)} CPU, {len(gpu)} GPU")
        th = opts["threshold"]
        updated = missed = 0

        def apply(obj, field, table, name, laptop):
            nonlocal updated, missed
            hit, score, sim = passmark.lookup(table, name, laptop=laptop, threshold=th)
            if not hit:
                missed += 1
                self.stdout.write(f"  ?  {obj} | {name}: eşleşme yok")
                return
            old = getattr(obj, field)
            self.stdout.write(f"  {'=' if old == score else '~'}  {obj} | {name} -> {hit} = {score} (önce {old}, benzerlik {sim:.2f})")
            if old != score and not opts["dry_run"]:
                setattr(obj, field, score)
                obj.save(update_fields=[field])
                updated += 1

        self.stdout.write("Laptoplar:")
        for lp in Laptop.objects.all():
            apply(lp, "cpu_score", cpu, lp.cpu, laptop=True)
            apply(lp, "gpu_score", gpu, lp.gpu, laptop=True)

        self.stdout.write("Bileşenler:")
        for c in Component.objects.filter(category__in=[Component.CPU, Component.GPU]):
            apply(c, "score", cpu if c.category == Component.CPU else gpu, c.name, laptop=False)

        self.stdout.write(self.style.SUCCESS(
            f"{'Önizleme' if opts['dry_run'] else 'Güncellendi'}: {updated} skor; eşleşmeyen: {missed}"))
