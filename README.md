# CompMatch

Meslek → program → cihaz tipi seçimine göre **darboğazsız sistem gereksinimi** çıkaran, uygun **laptop / PC bileşeni** öneren ve her ürün için **Bakü yerel mağaza fiyatı** ile **Global fiyat + Azerbaycan gümrük maliyetini** yan yana karşılaştıran lokal web uygulaması.

- **Backend:** Python 3.13 · Django 6 · Django REST Framework · SQLite → `http://localhost:8000`
- **Frontend:** React 19 · Vite · TailwindCSS 4 · Axios · Lucide-React → `http://localhost:5173`
- **Tasarım:** Ponytale tasarım dili (derin uzay karanlığı, cam katmanlar, neon vurgular, Bento grid)

---

## Klasör Yapısı

```text
CompMatch/
├── backend/
│   ├── manage.py
│   ├── pyproject.toml / uv.lock          # uv ile bağımlılık yönetimi
│   ├── compmatch/
│   │   ├── settings.py                   # DRF + CORS (localhost:5173)
│   │   └── urls.py                       # /admin/, /api/
│   └── core/
│       ├── models.py                     # Profession, Program, Store, Laptop, Component,
│       │                                 # LaptopPrice, ComponentPrice, CustomsSettings
│       ├── admin.py                      # TabularInline fiyat yönetimi, singleton ayarlar
│       ├── services.py                   # Gereksinim birleştirme, laptop/PC eşleştirme, gümrük motoru
│       ├── serializers.py · views.py · urls.py
│       ├── tests.py                      # Gümrük formülü, max() birleştirme, uyumluluk testleri
│       └── management/commands/seed_data.py
└── frontend/
    ├── index.html · vite.config.js · package.json
    └── src/
        ├── main.jsx · App.jsx            # 4 adımlı sihirbaz state'i
        ├── api.js                        # Axios istemcisi + ₼/$ formatlayıcılar
        ├── index.css                     # Tailwind 4 @theme: Ponytale renkleri, animasyonlar
        └── components/
            ├── Stepper.jsx               # Akışkan ilerleme çubuğu
            ├── SelectCard.jsx            # Bento seçim kartı (hover yükselme, neon ring)
            ├── RequirementsCard.jsx      # Min / Önerilen gereksinim tablosu
            ├── LaptopResults.jsx         # 3 laptop (Fiyat/Perf · Önerilen · Pro)
            ├── PcResults.jsx             # 6 uyumlu bileşen + toplam maliyet
            ├── PriceCompare.jsx          # Bakü vs Global + gümrük tablosu, "En Karlı Seçenek" rozeti
            └── Icon.jsx                  # Admin'den gelen Lucide ikon adını çözer
```

## Yol Haritası (tamamlandı)

1. Django projesi, modeller, migration, admin (inline fiyatlar, singleton `CustomsSettings`)
2. `services.py`: `max()` tabanlı gereksinim birleştirme · 3 katmanlı laptop seçimi · soket/RAM tipi/PSU uyumlu PC toplama · Azerbaycan gümrük formülü
3. DRF uçları: `/api/professions/`, `/api/programs/?profession=`, `/api/match/`, `/api/settings/`
4. `seed_data`: 5 meslek, 15 program, 6 laptop, 22 PC bileşeni, 9 mağaza, 149 fiyat
5. React + Tailwind 4 arayüz: Stepper → Meslek → Programlar → Cihaz → Sonuç & maliyet
6. Testler (`manage.py test`) ve bu rehber

---

## Lokal Kurulum

> Gereksinimler: [uv](https://docs.astral.sh/uv/) (Python'u kendisi indirir) ve Node.js 20+.

### Tek port (önerilen) — her şey `localhost:8000`

Frontend build edilir, Django hem API'yi hem React uygulamasını aynı porttan servis eder.

```powershell
cd frontend
npm install
npm run build                             # frontend/dist -> Django /static/ ve index.html

cd ../backend
uv sync                                   # .venv oluşturur, Django + DRF + CORS kurar
uv run python manage.py migrate
uv run python manage.py seed_data         # örnek veriler (tekrar çalıştırmak güvenlidir)
uv run python manage.py createsuperuser   # admin paneli için kullanıcı
uv run python manage.py runserver
```

- Uygulama: <http://localhost:8000/>
- Admin: <http://localhost:8000/admin/>
- API (gezilebilir): <http://localhost:8000/api/>

Frontend'de değişiklik yaptıysan tekrar `npm run build` çalıştır.

### Geliştirme modu (hot reload) — `localhost:5173`

Backend yukarıdaki gibi 8000'de çalışırken ikinci terminalde:

```powershell
cd frontend
npm run dev                               # /api istekleri 8000'e proxy'lenir
```

Tarayıcıda <http://localhost:5173> adresini aç.

### Testler

```powershell
cd backend
uv run python manage.py test
```

---

## API

| Uç | Açıklama |
| --- | --- |
| `GET /api/professions/` | Meslek listesi |
| `GET /api/programs/?profession=<id>` | Mesleğe göre programlar (min/önerilen skorlarla) |
| `POST /api/match/` | `{"program_ids": [1,4], "device_type": "laptop" \| "pc"}` → gereksinimler + öneriler + fiyat/gümrük karşılaştırması |
| `GET /api/settings/` | Aktif gümrük parametreleri |

## Azerbaycan Gümrük Formülü

```text
Baz Maliyet (USD)   = Ürün Fiyatı + Ağırlık (kg) × KG Kargo Ücreti
Gümrük (USD)        = Baz > Limit ? (Baz − Limit) × Oran + Sabit Beyanname : 0
Bakü Teslim (AZN)   = (Baz + Gümrük) × USD/AZN Kuru
```

Varsayılanlar (admin → **Gümrük ayarları** üzerinden değiştirilebilir): limit **300 USD**, oran **%36**, beyanname **15 USD**, kur **1.70**, kargo **12 USD/kg** (mağaza bazında ezilebilir).

## Admin'den Yönetilebilenler

- Meslekler, programlar (min/önerilen CPU skoru, GPU skoru, RAM, SSD) ve meslek-program ilişkisi
- Laptoplar ve PC bileşenleri (`weight_kg` dahil); ürün sayfasının içinde **TabularInline** ile mağaza fiyatları, para birimi (AZN/USD), stok ve satış linki
- Yerel (Bakü) ve global mağazalar, mağaza bazlı kg kargo ücreti
- `CustomsSettings`: gümrük limiti, vergi oranı, beyanname ücreti, kur, varsayılan kargo

> Not: `seed_data` fiyatları örnektir; linkler mağazaların arama sayfasına gider. Gerçek fiyatları admin'den güncelleyin.
