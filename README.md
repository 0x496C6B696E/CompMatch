# CompMatch

Meslek → program → cihaz tipi seçimine göre **darboğazsız sistem gereksinimi** çıkaran, uygun **laptop / PC bileşeni** öneren ve her ürün için **Bakü yerel mağaza fiyatı** ile **Global fiyat + Azerbaycan gümrük maliyetini** yan yana karşılaştıran lokal web uygulaması. Arayüz **Azerbaycanca, Rusça ve İngilizce**; laptop ve PC parça kataloğu markaya göre gezilebilir; bilgisayardan anlamayanlar için seviye etiketleri ("Sadə / Orta / Güclü / Çox güclü") ve sade dilde açıklamalar.

- **Backend:** Python 3.13 · Django 6 · Django REST Framework · SQLite → `http://localhost:8000`
- **Frontend:** React 19 · Vite · TailwindCSS 4 · Axios · Lucide-React (Django tarafından aynı porttan servis edilir)
- **Tasarım:** Ponytale tasarım dili (derin uzay karanlığı, cam katmanlar, neon vurgular, Bento grid)
- **Yol haritası:** [ROADMAP.md](ROADMAP.md)

---

## Klasör Yapısı

```text
CompMatch/
├── backend/
│   ├── manage.py
│   ├── pyproject.toml / uv.lock          # uv ile bağımlılık yönetimi
│   ├── compmatch/
│   │   ├── settings.py                   # DRF + CORS, frontend/dist servis ayarı
│   │   └── urls.py                       # /admin/, /api/, SPA catch-all
│   └── core/
│       ├── models.py                     # ProfessionCategory, Profession, ProgramGroup, Program (az/ru/en alanlar),
│       │                                 # Store, Laptop, Component, LaptopPrice, ComponentPrice, CustomsSettings
│       ├── admin.py                      # TabularInline fiyat yönetimi, singleton ayarlar
│       ├── services.py                   # Gereksinim birleştirme, laptop/PC eşleştirme, gümrük motoru, "uygun meslekler"
│       ├── serializers.py · views.py · urls.py
│       ├── tests.py                      # Gümrük formülü, max() birleştirme, uyumluluk, çeviri testleri
│       └── management/commands/seed_data.py
└── frontend/
    ├── index.html · vite.config.js · package.json
    └── src/
        ├── App.jsx                       # Üst bar (sekmeler + dil), hash yönlendirme
        ├── i18n/ az.js · ru.js · en.js   # Arayüz sözlükleri + LangProvider
        ├── pages/
        │   ├── Wizard.jsx                # 4 adımlı sihirbaz
        │   ├── Laptops.jsx               # Laptop kataloğu (marka filtresi, sıralama, detay)
        │   └── Parts.jsx                 # PC parça kataloğu (kategori + marka)
        ├── components/
        │   ├── Stepper.jsx               # Akışkan ilerleme çubuğu
        │   ├── SelectCard.jsx            # Bento seçim kartı (hover yükselme, neon ring)
        │   ├── RequirementBars.jsx       # Min / Önerilen benchmark çubukları, program tikleri
        │   ├── SpecChips.jsx             # Özellik kutuları + seviye etiketi
        │   ├── Explain.jsx               # "Bu rəqəmlər nə deməkdir?" açılır açıklama
        │   ├── LaptopResults.jsx         # 3 laptop (Fiyat/Perf · Önerilen · Pro) + özet cümle
        │   ├── PcResults.jsx             # 6 uyumlu bileşen + toplam maliyet
        │   ├── PriceCompare.jsx          # Bakü vs Global maliyet çubukları, "Ən sərfəli seçim" rozeti
        │   └── Icon.jsx                  # Admin'den gelen Lucide ikon adını çözer
        └── lib/ levels.js · spec.js      # Seviye eşikleri, özellik/uyumluluk metinleri
```

---

## Lokal Kurulum

> Gereksinimler: [uv](https://docs.astral.sh/uv/) (Python'u kendisi indirir) ve Node.js 20+.

### Tek port (önerilen) — her şey `localhost:8000`

```powershell
cd frontend
npm install
npm run build                             # frontend/dist -> Django /static/ ve index.html

cd ../backend
uv sync                                   # .venv oluşturur, Django + DRF + CORS kurar
uv run python manage.py migrate
uv run python manage.py seed_data         # örnek veriler; süper kullanıcı yoksa test/test oluşturur
uv run python manage.py runserver
```

- Uygulama: <http://localhost:8000/> (sekmeler: Mənə uyğun olanı tap · Noutbuklar · PC hissələri; dil: AZ / RU / EN)
- Admin: <http://localhost:8000/admin/> → `test` / `test` (yalnızca lokal)
- API (gezilebilir): <http://localhost:8000/api/>

Frontend'de değişiklik yaptıysan tekrar `npm run build` çalıştır.

### Geliştirme modu (hot reload) — `localhost:5173`

Backend 8000'de çalışırken ikinci terminalde:

```powershell
cd frontend
npm run dev                               # /api istekleri 8000'e proxy'lenir
```

### Testler

```powershell
cd backend
uv run python manage.py test
```

---

## API

Tüm uçlar `?lang=az|ru|en` alır (yoksa `Accept-Language`, o da yoksa `az`).

| Uç | Açıklama |
| --- | --- |
| `GET /api/professions/` | Meslekler, her biri `category` ile (başlık altında gruplamak için) |
| `GET /api/programs/?profession=<id>` | Mesleğe göre programlar; `group` ve sade dilde `blurb` ile |
| `GET /api/laptops/` | Tüm laptoplar + fiyat karşılaştırması + `fits` (hangi meslekler için uygun) |
| `GET /api/components/?category=cpu` | PC parçaları + fiyat karşılaştırması + `fits` |
| `POST /api/match/` | `{"program_ids": [1,4], "device_type": "laptop" \| "pc"}` → gereksinimler + öneriler + fiyat/gümrük |
| `GET /api/settings/` | Aktif gümrük parametreleri |

## Gerçek Veri Çekme (scraper)

Tüm komutlar `backend/` içinde `uv run python manage.py ...` ile çalışır. Hepsi `--dry-run` ile önce önizleme yapar.

| Komut | Ne yapar |
| --- | --- |
| `fetch_benchmarks` | PassMark CPU Mark ve G3D Mark listelerini indirir (haftalık önbellek), laptop ve parça skorlarını ada göre günceller. |
| `fetch_prices [--store X] [--only laptops\|components] [--category gpu] [--product Nitro] [--limit N] [--clear]` | `Scraper` alanı dolu mağazalar için fiyat, stok ve link çeker. `--clear` mağazanın eski (örnek) kayıtlarını önce siler. |
| `import_prices --template > prices.csv` | Tüm ürün × mağaza kombinasyonlarını mevcut değerlerle CSV'ye yazar. |
| `import_prices prices.csv` | Doldurulmuş CSV'yi yükler (`product,store,price,currency,url,in_stock`). |

**Mağaza stratejileri** (admin → Mağazalar → *Scraper*; kod: `core/scrapers/stores.py`):

| Mağaza | Yöntem | Not |
| --- | --- | --- |
| iComp, CompStore | `sitemap-posts.xml` → ad eşleşen ürün sayfası → JSON-LD `Product/Offer` | CPU/GPU/RAM/SSD/anakart iyi eşleşir; laptop başlıkları model kodu olduğu için seyrek. |
| Baku Electronics | `sitemap-0..3.xml` (`/mehsul/`) → JSON-LD | Laptop başlıklarında CPU/GPU var, iyi eşleşir. |
| İrşad | `/az/products/list?q=` araması → başlık yetmezse ürün sayfasında "Prosessor / Qrafik yaddaş" doğrulaması | robots.txt `Crawl-delay: 30` → tam tur ~1 saat; `--product` ile tekil yenileyin. |
| Kontakt Home | — | robots.txt aramayı yasaklıyor, bot koruması var → CSV. |
| Amazon, eBay, Newegg, B&H | — | Bot koruması → CSV (ROADMAP: eBay API). |

Kurallar: `core/scrapers/http.py` her istekte robots.txt'e bakar (izin yoksa atlar), `Crawl-delay`'e uyar, sayfaları `backend/data/cache/` altında önbellekler (sitemap 24 sa, ürün sayfası 12 sa, PassMark 7 gün). Ad eşleştirme (`core/scrapers/match.py`) CPU/GPU model numaralarını zorunlu tutar, Ti/Super/XT/Pro gibi varyantları ve markayı ayrı sayar; emin olmadığında fiyat yazmaz. Kasa+PSU kayıtları paket olduğu için otomatik çekilmez.

Önerilen düzen: haftada bir `fetch_benchmarks`, gecede bir `fetch_prices --clear` (İrşad'ı ayrı ve uzun bir pencerede).

## Azerbaycan Gümrük Formülü

```text
Baz Maliyet (USD)   = Ürün Fiyatı + Ağırlık (kg) × KG Kargo Ücreti
Gümrük (USD)        = Baz > Limit ? (Baz − Limit) × Oran + Sabit Beyanname : 0
Bakü Teslim (AZN)   = (Baz + Gümrük) × USD/AZN Kuru
```

Varsayılanlar (admin → **Gümrük ayarları**): limit **300 USD**, oran **%36**, beyanname **15 USD**, kur **1.70**, kargo **12 USD/kg** (mağaza bazında ezilebilir).

## Admin'den Yönetilebilenler

- Meslek kategorileri, meslekler (ad ve açıklama AZ/RU/EN), program grupları, programlar (grup, sade açıklama AZ/RU/EN, min/önerilen CPU skoru, GPU skoru, RAM, SSD)
- Laptoplar ve PC bileşenleri (`weight_kg` dahil); ürün sayfasının içinde **TabularInline** ile mağaza fiyatları, para birimi (AZN/USD), stok ve satış linki
- Yerel (Bakü) ve global mağazalar, mağaza bazlı kg kargo ücreti
- `CustomsSettings`: gümrük limiti, vergi oranı, beyanname ücreti, kur, varsayılan kargo

Örnek veri: 6 kategori, 19 meslek, 9 grup, 52 program, 28 laptop (ASUS, Lenovo, HP, Acer, MSI, Dell, Apple, Huawei, Samsung), 39 PC parçası, 9 mağaza, 341 fiyat.

> Not: `seed_data` fiyatları örnektir; linkler mağazaların arama sayfasına gider. Gerçek fiyatları admin'den güncelleyin.
