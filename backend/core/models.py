from decimal import Decimal

from django.db import models

# Donanım gereksinimi alanları. Program, Laptop ve gereksinim özetleri
# aynı dört alanı paylaşır; services.py bu tuple üzerinden döner.
REQ_FIELDS = ("cpu_score", "gpu_score", "ram_gb", "ssd_gb")


class Profession(models.Model):
    name = models.CharField("Meslek", max_length=100, unique=True)
    icon = models.CharField("Lucide ikon adı", max_length=50, default="Briefcase")
    description = models.CharField("Açıklama", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Meslek"
        verbose_name_plural = "Meslekler"

    def __str__(self):
        return self.name


class Program(models.Model):
    name = models.CharField("Program", max_length=100, unique=True)
    icon = models.CharField("Lucide ikon adı", max_length=50, default="AppWindow")
    professions = models.ManyToManyField(Profession, related_name="programs", verbose_name="Meslekler")

    # CPU/GPU skorları: PassMark CPU Mark ve 3DMark Time Spy ölçeğine yakın değerler.
    min_cpu_score = models.PositiveIntegerField("Min CPU skoru", default=0)
    rec_cpu_score = models.PositiveIntegerField("Önerilen CPU skoru", default=0)
    min_gpu_score = models.PositiveIntegerField("Min GPU skoru", default=0)
    rec_gpu_score = models.PositiveIntegerField("Önerilen GPU skoru", default=0)
    min_ram_gb = models.PositiveIntegerField("Min RAM (GB)", default=8)
    rec_ram_gb = models.PositiveIntegerField("Önerilen RAM (GB)", default=16)
    min_ssd_gb = models.PositiveIntegerField("Min SSD (GB)", default=256)
    rec_ssd_gb = models.PositiveIntegerField("Önerilen SSD (GB)", default=512)

    class Meta:
        ordering = ["name"]
        verbose_name = "Program"
        verbose_name_plural = "Programlar"

    def __str__(self):
        return self.name


class Store(models.Model):
    LOCAL = "local"
    GLOBAL = "global"
    KINDS = [(LOCAL, "Bakü yerel mağaza"), (GLOBAL, "Global platform")]

    name = models.CharField("Mağaza", max_length=100, unique=True)
    kind = models.CharField("Tür", max_length=10, choices=KINDS)
    website = models.URLField("Web sitesi", blank=True)
    shipping_per_kg_usd = models.DecimalField(
        "KG başı kargo (USD)", max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Boş bırakılırsa gümrük ayarlarındaki varsayılan kullanılır (yalnızca global mağazalar).",
    )

    class Meta:
        ordering = ["kind", "name"]
        verbose_name = "Mağaza"
        verbose_name_plural = "Mağazalar"

    def __str__(self):
        return self.name


class Laptop(models.Model):
    name = models.CharField("Model", max_length=150, unique=True)
    brand = models.CharField("Marka", max_length=50)
    cpu = models.CharField("İşlemci", max_length=100)
    gpu = models.CharField("Ekran kartı", max_length=100)
    ram_gb = models.PositiveIntegerField("RAM (GB)")
    ssd_gb = models.PositiveIntegerField("SSD (GB)")
    cpu_score = models.PositiveIntegerField("CPU skoru")
    gpu_score = models.PositiveIntegerField("GPU skoru")
    screen = models.CharField("Ekran", max_length=100, blank=True)
    weight_kg = models.DecimalField("Ağırlık (kg)", max_digits=5, decimal_places=2)
    image_url = models.URLField("Görsel URL", blank=True)

    class Meta:
        ordering = ["brand", "name"]
        verbose_name = "Laptop"
        verbose_name_plural = "Laptoplar"

    def __str__(self):
        return self.name


class Component(models.Model):
    CPU = "cpu"
    GPU = "gpu"
    MOTHERBOARD = "motherboard"
    RAM = "ram"
    SSD = "ssd"
    CASE_PSU = "case_psu"
    CATEGORIES = [
        (CPU, "İşlemci (CPU)"),
        (GPU, "Ekran Kartı (GPU)"),
        (MOTHERBOARD, "Anakart"),
        (RAM, "RAM"),
        (SSD, "SSD"),
        (CASE_PSU, "Kasa + PSU"),
    ]
    # Sonuç ekranındaki gösterim sırası.
    CATEGORY_ORDER = [CPU, GPU, MOTHERBOARD, RAM, SSD, CASE_PSU]

    category = models.CharField("Kategori", max_length=20, choices=CATEGORIES)
    name = models.CharField("Model", max_length=150, unique=True)
    brand = models.CharField("Marka", max_length=50)
    score = models.PositiveIntegerField("Skor", default=0, help_text="CPU/GPU için performans skoru.")
    capacity_gb = models.PositiveIntegerField("Kapasite (GB)", default=0, help_text="RAM/SSD için.")
    socket = models.CharField("Soket", max_length=20, blank=True, help_text="CPU ve anakart için (AM5, LGA1700...).")
    ram_type = models.CharField("RAM tipi", max_length=10, blank=True, help_text="RAM ve anakart için (DDR4, DDR5).")
    tdp_watts = models.PositiveIntegerField("TDP (W)", default=0, help_text="CPU/GPU güç tüketimi.")
    psu_watts = models.PositiveIntegerField("PSU gücü (W)", default=0, help_text="Kasa+PSU için.")
    weight_kg = models.DecimalField("Ağırlık (kg)", max_digits=5, decimal_places=2)
    image_url = models.URLField("Görsel URL", blank=True)

    class Meta:
        ordering = ["category", "brand", "name"]
        verbose_name = "PC Bileşeni"
        verbose_name_plural = "PC Bileşenleri"

    def __str__(self):
        return f"{self.get_category_display()} — {self.name}"


class PriceBase(models.Model):
    AZN = "AZN"
    USD = "USD"
    CURRENCIES = [(AZN, "AZN ₼"), (USD, "USD $")]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name="Mağaza")
    price = models.DecimalField("Fiyat", max_digits=10, decimal_places=2)
    currency = models.CharField("Para birimi", max_length=3, choices=CURRENCIES)
    url = models.URLField("Ürün linki", blank=True)
    in_stock = models.BooleanField("Stokta", default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.store}: {self.price} {self.currency}"


class LaptopPrice(PriceBase):
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE, related_name="prices")

    class Meta:
        verbose_name = "Laptop fiyatı"
        verbose_name_plural = "Laptop fiyatları"
        constraints = [models.UniqueConstraint(fields=["laptop", "store"], name="uniq_laptop_store")]


class ComponentPrice(PriceBase):
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name="prices")

    class Meta:
        verbose_name = "Bileşen fiyatı"
        verbose_name_plural = "Bileşen fiyatları"
        constraints = [models.UniqueConstraint(fields=["component", "store"], name="uniq_component_store")]


class CustomsSettings(models.Model):
    """Tek satırlık ayar tablosu: Azerbaycan gümrük ve kargo parametreleri."""

    duty_free_limit_usd = models.DecimalField(
        "Aylık gümrüksüz limit (USD)", max_digits=8, decimal_places=2, default=Decimal("300.00"))
    duty_rate = models.DecimalField(
        "Gümrük vergisi oranı", max_digits=5, decimal_places=4, default=Decimal("0.36"), help_text="0.36 = %36")
    declaration_fee_usd = models.DecimalField(
        "Sabit beyanname ücreti (USD)", max_digits=8, decimal_places=2, default=Decimal("15.00"))
    usd_azn_rate = models.DecimalField(
        "USD/AZN kuru", max_digits=6, decimal_places=4, default=Decimal("1.70"))
    shipping_per_kg_usd = models.DecimalField(
        "Varsayılan KG başı kargo (USD)", max_digits=8, decimal_places=2, default=Decimal("12.00"))

    class Meta:
        verbose_name = "Gümrük ayarları"
        verbose_name_plural = "Gümrük ayarları"

    def __str__(self):
        return "Azerbaycan gümrük ayarları"

    def save(self, *args, **kwargs):
        self.pk = 1  # ponytail: singleton via sabit pk
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
