"""
CompMatch iş mantığı:
  - aggregate_requirements: seçilen programların darboğaz yaratmayacak max değerleri
  - landed_cost / compare_prices: Bakü yerel vs global + Azerbaycan gümrük hesabı
  - pick_laptops: 3 laptop (fiyat/perf, önerilen, pro)
  - build_pc: birbiriyle uyumlu PC bileşen seti
  - profession_requirements / laptop_fits / component_fits: katalogda "hangi işler için uygun"
"""
from decimal import ROUND_HALF_UP, Decimal

from .models import REQ_FIELDS, Component, CustomsSettings, Laptop, Profession, Store

TWO = Decimal("0.01")
PSU_HEADROOM_W = 150  # anakart + RAM + SSD + fanlar için pay


def _q(x):
    return Decimal(x).quantize(TWO, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- #
# Gereksinimler
# --------------------------------------------------------------------------- #
def aggregate_requirements(programs):
    """Her alan için programlar arasındaki en yüksek değer -> darboğaz yok."""
    programs = list(programs)
    return {
        "min": {f: max((getattr(p, f"min_{f}") for p in programs), default=0) for f in REQ_FIELDS},
        "rec": {f: max((getattr(p, f"rec_{f}") for p in programs), default=0) for f in REQ_FIELDS},
    }


def meets(obj, level):
    return all(getattr(obj, f) >= level[f] for f in REQ_FIELDS)


def profession_requirements():
    """{profession: req} — programı olan her meslek için, katalog 'uygun işler' etiketi için."""
    out = {}
    for prof in Profession.objects.prefetch_related("programs").order_by("order", "name_az"):
        programs = list(prof.programs.all())
        if programs:
            out[prof] = aggregate_requirements(programs)
    return out


def _level(value_of, req):
    if all(value_of(f) >= req["rec"][f] for f in REQ_FIELDS):
        return "rec"
    if all(value_of(f) >= req["min"][f] for f in REQ_FIELDS):
        return "min"
    return None


def laptop_fits(laptop, prof_reqs):
    """[(profession, 'rec'|'min')] — laptop'un karşıladığı meslekler, rec önce."""
    found = []
    for prof, req in prof_reqs.items():
        level = _level(lambda f: getattr(laptop, f), req)
        if level:
            found.append((prof, level))
    found.sort(key=lambda x: x[1] != "rec")
    return found


# Bileşen kategorisi -> hangi gereksinim alanıyla ve hangi özelliğiyle karşılaştırılır.
COMPONENT_FIELD = {
    Component.CPU: ("cpu_score", "score"),
    Component.GPU: ("gpu_score", "score"),
    Component.RAM: ("ram_gb", "capacity_gb"),
    Component.SSD: ("ssd_gb", "capacity_gb"),
}


def component_fits(component, prof_reqs):
    """Tek alanlı karşılaştırma: CPU skoru, GPU skoru, RAM veya SSD kapasitesi."""
    pair = COMPONENT_FIELD.get(component.category)
    if not pair:
        return []
    req_field, attr = pair
    value = getattr(component, attr)
    found = []
    for prof, req in prof_reqs.items():
        if value >= req["rec"][req_field]:
            found.append((prof, "rec"))
        elif value >= req["min"][req_field]:
            found.append((prof, "min"))
    found.sort(key=lambda x: x[1] != "rec")
    return found


# --------------------------------------------------------------------------- #
# Gümrük & fiyat karşılaştırma
# --------------------------------------------------------------------------- #
def landed_cost(price_usd, weight_kg, settings, shipping_per_kg_usd=None):
    """
    Baz Maliyet = Fiyat + Ağırlık × KG kargo
    Baz > limit ise Gümrük = (Baz - limit) × oran + beyanname
    Toplam AZN = (Baz + Gümrük) × kur
    """
    price_usd = Decimal(price_usd)
    weight_kg = Decimal(weight_kg)
    per_kg = Decimal(shipping_per_kg_usd if shipping_per_kg_usd is not None else settings.shipping_per_kg_usd)

    shipping_usd = weight_kg * per_kg
    base_usd = price_usd + shipping_usd
    duty_usd = Decimal(0)
    if base_usd > settings.duty_free_limit_usd:
        duty_usd = (base_usd - settings.duty_free_limit_usd) * settings.duty_rate + settings.declaration_fee_usd
    total_usd = base_usd + duty_usd
    return {
        "price_usd": _q(price_usd),
        "shipping_usd": _q(shipping_usd),
        "base_usd": _q(base_usd),
        "duty_usd": _q(duty_usd),
        "total_usd": _q(total_usd),
        "total_azn": _q(total_usd * settings.usd_azn_rate),
    }


def compare_prices(product, settings):
    """product: `prices` ilişkisi ve `weight_kg` alanı olan Laptop veya Component."""
    local, global_ = [], []
    for p in product.prices.all():
        store = p.store
        if store.kind == Store.LOCAL:
            price_azn = p.price if p.currency == "AZN" else p.price * settings.usd_azn_rate
            local.append({
                "store": store.name, "url": p.url, "in_stock": p.in_stock,
                "price_azn": _q(price_azn),
            })
        else:
            price_usd = p.price if p.currency == "USD" else p.price / settings.usd_azn_rate
            cost = landed_cost(price_usd, product.weight_kg, settings, store.shipping_per_kg_usd)
            global_.append({"store": store.name, "url": p.url, "in_stock": p.in_stock, **cost})

    local.sort(key=lambda o: (not o["in_stock"], o["price_azn"]))
    global_.sort(key=lambda o: (not o["in_stock"], o["total_azn"]))

    best_local = next((o for o in local if o["in_stock"]), None)
    best_global = next((o for o in global_ if o["in_stock"]), None)

    best = None
    if best_local and best_global:
        if best_local["price_azn"] <= best_global["total_azn"]:
            best = {"side": "local", "store": best_local["store"], "total_azn": best_local["price_azn"],
                    "savings_azn": _q(best_global["total_azn"] - best_local["price_azn"])}
        else:
            best = {"side": "global", "store": best_global["store"], "total_azn": best_global["total_azn"],
                    "savings_azn": _q(best_local["price_azn"] - best_global["total_azn"])}
    elif best_local:
        best = {"side": "local", "store": best_local["store"], "total_azn": best_local["price_azn"], "savings_azn": None}
    elif best_global:
        best = {"side": "global", "store": best_global["store"], "total_azn": best_global["total_azn"], "savings_azn": None}

    return {"local": local, "global": global_, "best": best}


def _cost(product, settings):
    """Sıralama için: en ucuz teslim AZN; fiyatı yoksa sona at."""
    best = compare_prices(product, settings)["best"]
    return best["total_azn"] if best else Decimal("Infinity")


# --------------------------------------------------------------------------- #
# Laptop eşleştirme
# --------------------------------------------------------------------------- #
def pick_laptops(req, settings):
    laptops = list(Laptop.objects.prefetch_related("prices__store"))
    for lp in laptops:
        lp._cost = _cost(lp, settings)
        lp._perf = lp.cpu_score + lp.gpu_score

    min_ok = [l for l in laptops if meets(l, req["min"])]
    rec_ok = [l for l in laptops if meets(l, req["rec"])]
    by_cost = lambda pool: sorted(pool, key=lambda l: l._cost)
    by_perf = lambda pool: sorted(pool, key=lambda l: -l._perf)

    picks, used = [], set()

    def take(tier, candidates):
        """Aday listesinde (öncelik sırasıyla) henüz seçilmemiş ilk laptopu al."""
        for c in candidates:
            if c.pk not in used:
                used.add(c.pk)
                picks.append({"tier": tier, "laptop": c, "meets": "rec" if meets(c, req["rec"]) else "min"})
                return

    take("value", by_cost(min_ok))
    take("recommended", by_cost(rec_ok) + by_cost(min_ok))
    take("pro", by_perf(rec_ok) + by_perf(min_ok))
    return picks


# --------------------------------------------------------------------------- #
# PC toplama
# --------------------------------------------------------------------------- #
def _cheapest(items, predicate):
    pool = [c for c in items if predicate(c)]
    return min(pool, key=lambda c: c._cost) if pool else None


def _pick_scored(items, min_score, rec_score):
    """Önerilen skoru karşılayan en ucuz; yoksa min; yoksa en güçlü."""
    for level, score in (("rec", rec_score), ("min", min_score)):
        c = _cheapest(items, lambda x: x.score >= score)
        if c:
            return c, level
    return max(items, key=lambda x: x.score, default=None), "below"


def _pick_capacity(items, min_gb, rec_gb, extra=lambda x: True):
    for level, gb in (("rec", rec_gb), ("min", min_gb)):
        c = _cheapest(items, lambda x: x.capacity_gb >= gb and extra(x))
        if c:
            return c, level
    return max((x for x in items if extra(x)), key=lambda x: x.capacity_gb, default=None), "below"


def build_pc(req, settings):
    comps = list(Component.objects.prefetch_related("prices__store"))
    for c in comps:
        c._cost = _cost(c, settings)
    by_cat = {cat: [c for c in comps if c.category == cat] for cat in Component.CATEGORY_ORDER}

    cpu, cpu_level = _pick_scored(by_cat[Component.CPU], req["min"]["cpu_score"], req["rec"]["cpu_score"])
    gpu, gpu_level = _pick_scored(by_cat[Component.GPU], req["min"]["gpu_score"], req["rec"]["gpu_score"])

    mb = _cheapest(by_cat[Component.MOTHERBOARD], lambda m: cpu is not None and m.socket == cpu.socket)
    ram_type = mb.ram_type if mb else ""
    ram, ram_level = _pick_capacity(
        by_cat[Component.RAM], req["min"]["ram_gb"], req["rec"]["ram_gb"],
        extra=lambda r: not ram_type or r.ram_type == ram_type,
    )
    ssd, ssd_level = _pick_capacity(by_cat[Component.SSD], req["min"]["ssd_gb"], req["rec"]["ssd_gb"])

    need_w = (cpu.tdp_watts if cpu else 0) + (gpu.tdp_watts if gpu else 0) + PSU_HEADROOM_W
    case = _cheapest(by_cat[Component.CASE_PSU], lambda k: k.psu_watts >= need_w)

    # compat: frontend'in kendi dilinde yazacağı yapısal not
    parts = [
        (Component.CPU, cpu, cpu_level, None),
        (Component.GPU, gpu, gpu_level, None),
        (Component.MOTHERBOARD, mb, "rec" if mb else "below", {"socket": cpu.socket} if cpu else None),
        (Component.RAM, ram, ram_level, {"ram_type": ram_type} if ram_type else None),
        (Component.SSD, ssd, ssd_level, None),
        (Component.CASE_PSU, case, "rec" if case else "below", {"psu_min_w": need_w}),
    ]
    return [
        {"category": cat, "component": comp, "meets": level, "compat": note}
        for cat, comp, level, note in parts
    ]


# --------------------------------------------------------------------------- #
# Giriş noktası
# --------------------------------------------------------------------------- #
def match(programs, device_type):
    settings = CustomsSettings.load()
    req = aggregate_requirements(programs)
    result = {"requirements": req, "device_type": device_type, "settings": settings}
    if device_type == "laptop":
        result["laptops"] = [
            {**p, "prices": compare_prices(p["laptop"], settings)} for p in pick_laptops(req, settings)
        ]
    else:
        result["components"] = [
            {**p, "prices": compare_prices(p["component"], settings) if p["component"] else None}
            for p in build_pc(req, settings)
        ]
    return result
