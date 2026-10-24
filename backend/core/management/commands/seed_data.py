"""
python manage.py seed_data

Veritabanını örnek verilerle doldurur (idempotent: isme göre update_or_create).
Fiyatlar örnek niteliğindedir; linkler mağazaların arama sayfalarına gider.
Hiç süper kullanıcı yoksa admin için test/test oluşturur (yalnızca localhost).
"""
from decimal import Decimal
from urllib.parse import quote_plus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Component,
    ComponentPrice,
    CustomsSettings,
    Laptop,
    LaptopPrice,
    Profession,
    ProfessionCategory,
    Program,
    ProgramGroup,
    Store,
)

# name, kind, website, search url template, kg kargo (sadece global), scraper anahtarı (core/scrapers/stores.py)
STORES = [
    ("Kontakt Home", Store.LOCAL, "https://kontakt.az", "https://kontakt.az/search?q={q}", None, ""),  # robots yasak, CSV
    ("İrşad", Store.LOCAL, "https://irshad.az", "https://irshad.az/az/mehsullar?q={q}", None, "irshad_search"),
    ("Baku Electronics", Store.LOCAL, "https://www.bakuelectronics.az", "https://www.bakuelectronics.az/axtaris-neticesi?q={q}", None, "bakuelectronics_sitemap"),
    ("iComp", Store.LOCAL, "https://icomp.az", "https://icomp.az/?search={q}", None, "icomp_sitemap"),
    ("CompStore", Store.LOCAL, "https://compstore.az", "https://compstore.az/?search={q}", None, "compstore_sitemap"),
    ("Amazon", Store.GLOBAL, "https://www.amazon.com", "https://www.amazon.com/s?k={q}", Decimal("12.00"), ""),
    ("eBay", Store.GLOBAL, "https://www.ebay.com", "https://www.ebay.com/sch/i.html?_nkw={q}", Decimal("14.00"), ""),
    ("Newegg", Store.GLOBAL, "https://www.newegg.com", "https://www.newegg.com/p/pl?d={q}", Decimal("13.00"), ""),
    ("B&H", Store.GLOBAL, "https://www.bhphotovideo.com", "https://www.bhphotovideo.com/c/search?q={q}", Decimal("11.00"), ""),
]
SEARCH_URL = {s[0]: s[3] for s in STORES}

# GPU değerleri aşağıdaki tablolarda 3DMark Time Spy ölçeğindedir; kayıt sırasında ts_to_g3d() ile
# PassMark G3D Mark ölçeğine çevrilir (veritabanı ve fetch_benchmarks bu ölçeği kullanır).
# Çapa noktaları: (Time Spy, G3D) — Iris Xe, Radeon 680M, RTX 3050, 4050 Laptop, 4060, 4070, 4080, 4090.
_TS_G3D = [(0, 0), (1700, 2700), (2800, 4300), (6300, 12700), (8500, 14200), (10700, 19500),
           (17800, 26800), (28000, 34400), (36000, 38500), (40000, 41000)]


def ts_to_g3d(v):
    for (x0, y0), (x1, y1) in zip(_TS_G3D, _TS_G3D[1:]):
        if v <= x1:
            return int(round(y0 + (y1 - y0) * (v - x0) / (x1 - x0)))
    x0, y0 = _TS_G3D[-1]
    return int(round(y0 + (v - x0) * 0.6))

# key, icon, (az, ru, en)
CATEGORIES = [
    ("design", "Palette", ("Dizayn və kreativ", "Дизайн и креатив", "Design & creative")),
    ("media", "Clapperboard", ("Video, səs və foto", "Видео, звук и фото", "Video, audio & photo")),
    ("engineering", "Ruler", ("Mühəndislik, memarlıq və 3D", "Инженерия, архитектура и 3D", "Engineering, architecture & 3D")),
    ("software", "Code", ("Proqramlaşdırma və IT", "Программирование и IT", "Software & IT")),
    ("data", "ChartPie", ("Data, maliyyə və ofis", "Данные, финансы и офис", "Data, finance & office")),
    ("gaming", "Gamepad2", ("Oyun və yayım", "Игры и стриминг", "Gaming & streaming")),
]

# key, category, icon, (name az, ru, en), (description az, ru, en)
PROFESSIONS = [
    ("graphic", "design", "Palette",
     ("Qrafik dizayner", "Графический дизайнер", "Graphic designer"),
     ("Poster, loqo, sosial media vizualları", "Постеры, логотипы, визуалы для соцсетей", "Posters, logos, social media visuals")),
    ("uiux", "design", "LayoutDashboard",
     ("UI/UX dizayner", "UI/UX-дизайнер", "UI/UX designer"),
     ("Sayt və tətbiq interfeysləri", "Интерфейсы сайтов и приложений", "Website and app interfaces")),
    ("photo", "media", "Camera",
     ("Fotoqraf", "Фотограф", "Photographer"),
     ("Foto emalı və retuş", "Обработка и ретушь фото", "Photo editing and retouching")),
    ("video", "media", "Clapperboard",
     ("Video montajçı", "Видеомонтажёр", "Video editor"),
     ("Montaj, rəng korreksiyası, YouTube", "Монтаж, цветокоррекция, YouTube", "Editing, color grading, YouTube")),
    ("motion", "media", "Sparkles",
     ("Motion dizayner", "Моушн-дизайнер", "Motion designer"),
     ("Animasiya, VFX, intro-lar", "Анимация, VFX, заставки", "Animation, VFX, intros")),
    ("audio", "media", "Music",
     ("Səs və musiqi prodüseri", "Звукорежиссёр и продюсер", "Audio & music producer"),
     ("Musiqi yazmaq, mix, podkast", "Запись музыки, сведение, подкасты", "Music production, mixing, podcasts")),
    ("3d", "engineering", "Box",
     ("3D modelləmə və animasiya", "3D-моделирование и анимация", "3D modeling & animation"),
     ("Personaj, səhnə, render", "Персонажи, сцены, рендер", "Characters, scenes, rendering")),
    ("arch", "engineering", "Building2",
     ("Memar və interyer dizayneri", "Архитектор и дизайнер интерьера", "Architect & interior designer"),
     ("Layihə, vizualizasiya, BIM", "Проекты, визуализация, BIM", "Plans, visualization, BIM")),
    ("cad", "engineering", "Cog",
     ("Mühəndis (CAD)", "Инженер (CAD)", "Engineer (CAD)"),
     ("Maşın, tikinti, elektrik layihələri", "Машиностроение, строительство, электрика", "Mechanical, civil, electrical design")),
    ("dev", "software", "Code",
     ("Proqramçı", "Программист", "Software developer"),
     ("Veb, backend, mobil", "Веб, бэкенд, мобильные", "Web, backend, mobile")),
    ("mobile", "software", "Smartphone",
     ("Mobil tərtibatçı", "Мобильный разработчик", "Mobile developer"),
     ("Android və iOS tətbiqləri", "Приложения для Android и iOS", "Android and iOS apps")),
    ("gamedev", "software", "Gamepad2",
     ("Oyun tərtibatçısı", "Разработчик игр", "Game developer"),
     ("Unity, Unreal ilə oyun", "Игры на Unity и Unreal", "Games with Unity and Unreal")),
    ("devops", "software", "ShieldCheck",
     ("Sistem administratoru və DevOps", "Сисадмин и DevOps", "Sysadmin & DevOps"),
     ("Serverlər, virtual maşınlar, şəbəkə", "Серверы, виртуальные машины, сети", "Servers, virtual machines, networking")),
    ("analyst", "data", "ChartPie",
     ("Data analitik", "Аналитик данных", "Data analyst"),
     ("Hesabatlar, Power BI, SQL", "Отчёты, Power BI, SQL", "Reports, Power BI, SQL")),
    ("ds", "data", "Brain",
     ("Data alimi və ML mühəndisi", "Data scientist и ML-инженер", "Data scientist & ML engineer"),
     ("Model öyrətmə, Python", "Обучение моделей, Python", "Model training, Python")),
    ("account", "data", "Calculator",
     ("Mühasib və maliyyəçi", "Бухгалтер и финансист", "Accountant & finance"),
     ("1C, Excel, bank sistemləri", "1C, Excel, банковские системы", "1C, Excel, banking systems")),
    ("office", "data", "Briefcase",
     ("Ofis işçisi və tələbə", "Офисный сотрудник и студент", "Office worker & student"),
     ("Sənədlər, Zoom, brauzer", "Документы, Zoom, браузер", "Documents, Zoom, browser")),
    ("gamer", "gaming", "Gamepad2",
     ("Oyunçu", "Геймер", "Gamer"),
     ("Müasir oyunlar yüksək ayarlarda", "Современные игры на высоких настройках", "Modern games on high settings")),
    ("streamer", "gaming", "Radio",
     ("Strimer və kontent yaradıcısı", "Стример и контент-мейкер", "Streamer & content creator"),
     ("OBS, oyun və yayım eyni anda", "OBS, игра и стрим одновременно", "OBS, gaming and streaming at once")),
]

# key, (az, ru, en)
GROUPS = [
    ("photo", ("Foto və qrafika", "Фото и графика", "Photo & graphics")),
    ("vector", ("Vektor, UI və çap", "Вектор, UI и печать", "Vector, UI & print")),
    ("video", ("Video və animasiya", "Видео и анимация", "Video & animation")),
    ("audio", ("Səs və musiqi", "Звук и музыка", "Audio & music")),
    ("threed", ("3D, CAD və render", "3D, CAD и рендер", "3D, CAD & rendering")),
    ("code", ("Kod və tərtibat", "Код и разработка", "Code & development")),
    ("data", ("Data və analitika", "Данные и аналитика", "Data & analytics")),
    ("office", ("Ofis və gündəlik", "Офис и повседневное", "Office & everyday")),
    ("games", ("Oyun və yayım", "Игры и стриминг", "Games & streaming")),
]

# name, icon, group, [profession keys], (blurb az, ru, en),
# (min_cpu, rec_cpu, min_gpu, rec_gpu, min_ram, rec_ram, min_ssd, rec_ssd)
PROGRAMS = [
    # --- foto və qrafika ---
    ("Adobe Photoshop", "Image", "photo", ["graphic", "photo", "uiux", "video", "motion"],
     ("Foto emalı və kollaj", "Обработка фото и коллажи", "Photo editing and compositing"),
     (8000, 18000, 1500, 5000, 8, 16, 256, 512)),
    ("Adobe Lightroom", "Aperture", "photo", ["photo", "graphic"],
     ("Toplu foto emalı", "Пакетная обработка фото", "Batch photo editing"),
     (8000, 18000, 1500, 4000, 8, 16, 256, 512)),
    ("Capture One", "Camera", "photo", ["photo"],
     ("Peşəkar RAW emalı", "Профессиональная обработка RAW", "Professional RAW processing"),
     (10000, 20000, 2000, 5000, 16, 32, 256, 512)),
    ("Affinity Photo", "Image", "photo", ["graphic", "photo"],
     ("Photoshop-a ucuz alternativ", "Доступная альтернатива Photoshop", "Affordable Photoshop alternative"),
     (7000, 15000, 1000, 3000, 8, 16, 256, 512)),
    ("Canva", "LayoutTemplate", "photo", ["graphic", "office", "streamer"],
     ("Sadə dizayn, brauzerdə", "Простой дизайн в браузере", "Simple design in the browser"),
     (5000, 10000, 500, 1500, 8, 8, 128, 256)),
    # --- vektor, UI, çap ---
    ("Adobe Illustrator", "PenTool", "vector", ["graphic", "uiux"],
     ("Loqo və vektor qrafika", "Логотипы и векторная графика", "Logos and vector graphics"),
     (7000, 15000, 1000, 3000, 8, 16, 256, 512)),
    ("CorelDRAW", "PenTool", "vector", ["graphic"],
     ("Vektor və çap dizaynı", "Вектор и дизайн для печати", "Vector and print design"),
     (7000, 15000, 1000, 3000, 8, 16, 256, 512)),
    ("Adobe InDesign", "BookOpen", "vector", ["graphic"],
     ("Jurnal, kitab, kataloq", "Журналы, книги, каталоги", "Magazines, books, catalogs"),
     (7000, 15000, 1000, 2500, 8, 16, 256, 512)),
    ("Figma", "LayoutDashboard", "vector", ["uiux", "graphic", "dev"],
     ("İnterfeys dizaynı, komanda ilə", "Дизайн интерфейсов в команде", "Interface design with your team"),
     (6000, 15000, 1000, 3000, 8, 16, 256, 512)),
    ("Adobe XD", "Layers", "vector", ["uiux"],
     ("Prototip və UI", "Прототипы и UI", "Prototyping and UI"),
     (6000, 14000, 1000, 3000, 8, 16, 256, 512)),
    # --- video və animasiya ---
    ("Adobe Premiere Pro", "Film", "video", ["video", "motion", "streamer"],
     ("Video montaj", "Видеомонтаж", "Video editing"),
     (12000, 25000, 4000, 10000, 16, 32, 512, 1000)),
    ("Adobe After Effects", "Sparkles", "video", ["motion", "video"],
     ("Animasiya və VFX", "Анимация и VFX", "Animation and VFX"),
     (14000, 28000, 5000, 12000, 16, 32, 512, 1000)),
    ("DaVinci Resolve", "Video", "video", ["video", "motion"],
     ("Montaj və rəng korreksiyası", "Монтаж и цветокоррекция", "Editing and color grading"),
     (14000, 28000, 6000, 15000, 16, 32, 512, 1000)),
    ("CapCut", "Scissors", "video", ["video", "streamer", "office"],
     ("Sürətli, sadə montaj", "Быстрый простой монтаж", "Quick, simple editing"),
     (6000, 12000, 1000, 3000, 8, 16, 256, 512)),
    ("Adobe Audition", "AudioWaveform", "video", ["audio", "video"],
     ("Səs təmizləmə və montaj", "Очистка и монтаж звука", "Audio cleanup and editing"),
     (7000, 15000, 500, 1500, 8, 16, 256, 512)),
    # --- səs və musiqi ---
    ("FL Studio", "Music", "audio", ["audio"],
     ("Bit və musiqi istehsalı", "Биты и продакшн музыки", "Beats and music production"),
     (8000, 18000, 500, 1500, 8, 16, 256, 512)),
    ("Ableton Live", "Music", "audio", ["audio"],
     ("Canlı ifa və prodakşn", "Живое выступление и продакшн", "Live performance and production"),
     (8000, 18000, 500, 1500, 8, 16, 256, 512)),
    ("Cubase / Pro Tools", "Mic", "audio", ["audio"],
     ("Studiya yazısı", "Студийная запись", "Studio recording"),
     (10000, 20000, 500, 1500, 16, 32, 512, 1000)),
    # --- 3D, CAD, render ---
    ("Blender", "Box", "threed", ["3d", "motion", "gamedev"],
     ("3D modelləmə və render", "3D-моделирование и рендер", "3D modeling and rendering"),
     (10000, 28000, 6000, 15000, 16, 32, 512, 1000)),
    ("Cinema 4D", "Box", "threed", ["motion", "3d"],
     ("Motion üçün 3D", "3D для моушна", "3D for motion design"),
     (12000, 28000, 6000, 15000, 16, 32, 512, 1000)),
    ("Autodesk Maya", "Box", "threed", ["3d"],
     ("Personaj animasiyası", "Анимация персонажей", "Character animation"),
     (12000, 28000, 6000, 15000, 16, 32, 512, 1000)),
    ("3ds Max", "Shapes", "threed", ["3d", "arch"],
     ("Arxitektura vizualizasiyası", "Архитектурная визуализация", "Architectural visualization"),
     (12000, 26000, 5000, 12000, 16, 32, 512, 1000)),
    ("ZBrush", "Brush", "threed", ["3d"],
     ("Rəqəmsal heykəltəraşlıq", "Цифровая скульптура", "Digital sculpting"),
     (10000, 22000, 3000, 8000, 16, 32, 512, 1000)),
    ("AutoCAD", "Ruler", "threed", ["arch", "cad"],
     ("2D çertyoj", "2D-чертежи", "2D drafting"),
     (8000, 20000, 2500, 8000, 8, 16, 256, 512)),
    ("Revit", "Building2", "threed", ["arch"],
     ("BIM layihələndirmə", "BIM-проектирование", "BIM design"),
     (12000, 26000, 4000, 10000, 16, 32, 512, 1000)),
    ("ArchiCAD", "Building2", "threed", ["arch"],
     ("Memarlıq BIM", "Архитектурный BIM", "Architectural BIM"),
     (12000, 26000, 4000, 10000, 16, 32, 512, 1000)),
    ("SketchUp", "PenTool", "threed", ["arch"],
     ("Sürətli 3D eskiz", "Быстрые 3D-эскизы", "Quick 3D sketches"),
     (7000, 15000, 2000, 6000, 8, 16, 256, 512)),
    ("Lumion / Twinmotion", "Sun", "threed", ["arch"],
     ("Real vaxt render", "Рендер в реальном времени", "Real-time rendering"),
     (14000, 28000, 8000, 18000, 16, 32, 512, 1000)),
    ("SolidWorks", "Cog", "threed", ["cad"],
     ("Maşınqayırma 3D CAD", "Машиностроительный 3D CAD", "Mechanical 3D CAD"),
     (12000, 26000, 4000, 10000, 16, 32, 512, 1000)),
    ("Fusion 360", "Cog", "threed", ["cad"],
     ("CAD/CAM, 3D çap", "CAD/CAM, 3D-печать", "CAD/CAM, 3D printing"),
     (10000, 22000, 3000, 8000, 16, 32, 512, 1000)),
    # --- kod və tərtibat ---
    ("VS Code", "Code", "code", ["dev", "mobile", "gamedev", "devops", "analyst", "ds"],
     ("Kod redaktoru", "Редактор кода", "Code editor"),
     (6000, 15000, 500, 1500, 8, 16, 256, 512)),
    ("IntelliJ IDEA / PyCharm", "Code", "code", ["dev", "mobile"],
     ("Java, Kotlin, Python IDE", "IDE для Java, Kotlin, Python", "Java, Kotlin, Python IDE"),
     (10000, 22000, 500, 1500, 16, 32, 512, 1000)),
    ("Visual Studio", "Code", "code", ["dev", "gamedev"],
     ("C#, C++, .NET", "C#, C++, .NET", "C#, C++, .NET"),
     (10000, 22000, 500, 2000, 16, 32, 512, 1000)),
    ("Android Studio", "Smartphone", "code", ["mobile", "dev"],
     ("Android tətbiqləri və emulyator", "Android-приложения и эмулятор", "Android apps and emulator"),
     (12000, 25000, 1000, 3000, 16, 32, 512, 1000)),
    ("Docker Desktop", "Container", "code", ["dev", "devops"],
     ("Konteynerlər", "Контейнеры", "Containers"),
     (12000, 25000, 500, 1500, 16, 32, 512, 1000)),
    ("VirtualBox / VMware", "Server", "code", ["devops", "dev"],
     ("Virtual maşınlar", "Виртуальные машины", "Virtual machines"),
     (12000, 25000, 500, 1500, 16, 32, 512, 1000)),
    ("Unity", "Gamepad2", "code", ["gamedev"],
     ("2D/3D oyun mühərriki", "2D/3D игровой движок", "2D/3D game engine"),
     (12000, 25000, 4000, 10000, 16, 32, 512, 1000)),
    ("Unreal Engine 5", "Gamepad2", "code", ["gamedev", "arch", "motion"],
     ("Yüksək keyfiyyətli 3D oyun və vizual", "Высококачественные 3D-игры и визуалы", "High-end 3D games and visuals"),
     (18000, 32000, 10000, 20000, 32, 64, 1000, 2000)),
    # --- data və analitika ---
    ("Python / Jupyter", "FlaskConical", "data", ["ds", "analyst", "dev"],
     ("Data analizi və skriptlər", "Анализ данных и скрипты", "Data analysis and scripts"),
     (7000, 18000, 500, 2000, 8, 16, 256, 512)),
    ("PyTorch / TensorFlow", "Brain", "data", ["ds"],
     ("Model öyrətmə, GPU vacibdir", "Обучение моделей, важен GPU", "Model training, GPU matters"),
     (14000, 28000, 8000, 18000, 16, 32, 512, 1000)),
    ("Microsoft Power BI", "Activity", "data", ["analyst", "account"],
     ("İnteraktiv hesabatlar", "Интерактивные отчёты", "Interactive reports"),
     (7000, 15000, 500, 2000, 8, 16, 256, 512)),
    ("Tableau", "Activity", "data", ["analyst"],
     ("Vizual analitika", "Визуальная аналитика", "Visual analytics"),
     (8000, 16000, 1000, 2500, 8, 16, 256, 512)),
    ("SQL (DBeaver, SSMS)", "Database", "data", ["analyst", "dev", "ds"],
     ("Verilənlər bazası sorğuları", "Запросы к базам данных", "Database queries"),
     (6000, 14000, 500, 1500, 8, 16, 256, 512)),
    ("MATLAB", "Sigma", "data", ["cad", "ds"],
     ("Mühəndislik hesablamaları", "Инженерные расчёты", "Engineering computation"),
     (10000, 22000, 1000, 3000, 16, 32, 512, 1000)),
    # --- ofis və gündəlik ---
    ("Microsoft Excel", "Table", "office", ["analyst", "account", "office"],
     ("Cədvəllər və hesabatlar", "Таблицы и отчёты", "Spreadsheets and reports"),
     (6000, 14000, 500, 1500, 8, 16, 256, 512)),
    ("Microsoft Office (Word, PowerPoint)", "FileText", "office", ["office", "account"],
     ("Sənəd və təqdimat", "Документы и презентации", "Documents and presentations"),
     (5000, 10000, 500, 1000, 8, 8, 128, 256)),
    ("1C", "Calculator", "office", ["account"],
     ("Mühasibat uçotu", "Бухгалтерский учёт", "Accounting"),
     (7000, 15000, 500, 1000, 8, 16, 256, 512)),
    ("Zoom / Teams", "Video", "office", ["office", "dev", "analyst"],
     ("Video görüşlər", "Видеозвонки", "Video calls"),
     (5000, 10000, 500, 1000, 8, 8, 128, 256)),
    ("Chrome / Web", "Globe", "office", ["office", "dev", "uiux", "analyst"],
     ("Çox tab, veb tətbiqlər", "Много вкладок, веб-приложения", "Many tabs, web apps"),
     (5000, 12000, 500, 1000, 8, 16, 128, 256)),
    # --- oyun və yayım ---
    ("AAA games (Cyberpunk, GTA)", "Gamepad2", "games", ["gamer", "streamer"],
     ("Yüksək ayarlar, 1080p–1440p", "Высокие настройки, 1080p–1440p", "High settings, 1080p–1440p"),
     (12000, 26000, 8000, 18000, 16, 32, 512, 1000)),
    ("eSports (CS2, Valorant, Dota 2)", "Crosshair", "games", ["gamer", "streamer"],
     ("Yüksək FPS, rəqabətli", "Высокий FPS, соревновательные", "High FPS, competitive"),
     (10000, 20000, 4000, 9000, 16, 16, 256, 512)),
    ("OBS Studio", "Radio", "games", ["streamer"],
     ("Yayım və ekran yazısı", "Стрим и запись экрана", "Streaming and screen recording"),
     (10000, 22000, 3000, 8000, 16, 32, 512, 1000)),
]

# name, brand, cpu, gpu, ram, ssd, cpu_score, gpu_score, screen, weight, (local AZN, global USD)
LAPTOPS = [
    # ASUS
    ("ASUS Vivobook 15 (i5-1335U)", "ASUS", "Intel Core i5-1335U", "Intel Iris Xe",
     16, 512, 15000, 1800, '15.6" FHD', "1.70", (1150, 580)),
    ("ASUS TUF Gaming A15 (R7 7735HS / RTX 4050)", "ASUS", "AMD Ryzen 7 7735HS", "NVIDIA RTX 4050 6GB",
     16, 512, 24000, 8500, '15.6" FHD 144Hz', "2.20", (1700, 900)),
    ("ASUS TUF Gaming F15 (i7-13620H / RTX 4060)", "ASUS", "Intel Core i7-13620H", "NVIDIA RTX 4060 8GB",
     16, 1000, 25000, 10500, '15.6" FHD 144Hz', "2.20", (2300, 1150)),
    ("ASUS ROG Zephyrus G14 (R9 8945HS / RTX 4070)", "ASUS", "AMD Ryzen 9 8945HS", "NVIDIA RTX 4070 8GB",
     32, 1000, 31000, 12500, '14" 3K OLED 120Hz', "1.50", (3800, 1900)),
    ("ASUS ROG Strix G16 (i9-14900HX / RTX 4070)", "ASUS", "Intel Core i9-14900HX", "NVIDIA RTX 4070 8GB",
     32, 1000, 44000, 13500, '16" QHD+ 240Hz', "2.50", (4300, 2100)),
    ("ASUS ProArt P16 (R9 HX 370 / RTX 4070)", "ASUS", "AMD Ryzen AI 9 HX 370", "NVIDIA RTX 4070 8GB",
     32, 2000, 36000, 13000, '16" 4K OLED', "1.85", (5200, 2600)),
    # Lenovo
    ("Lenovo IdeaPad Slim 3 (R5 7530U)", "Lenovo", "AMD Ryzen 5 7530U", "AMD Radeon Graphics",
     16, 512, 15500, 1600, '15.6" FHD', "1.60", (950, 480)),
    ("Lenovo IdeaPad Slim 5 14 (R7 7735HS)", "Lenovo", "AMD Ryzen 7 7735HS", "AMD Radeon 680M",
     16, 512, 24000, 2800, '14" 2.8K OLED 90Hz', "1.46", (1250, 650)),
    ("Lenovo LOQ 15 (i5-13450HX / RTX 4050)", "Lenovo", "Intel Core i5-13450HX", "NVIDIA RTX 4050 6GB",
     16, 512, 22000, 8500, '15.6" FHD 144Hz', "2.40", (1600, 850)),
    ("Lenovo Legion 5 15 (R7 7745HX / RTX 4060)", "Lenovo", "AMD Ryzen 7 7745HX", "NVIDIA RTX 4060 8GB",
     16, 1000, 32000, 10800, '15.6" WQHD 165Hz', "2.40", (2600, 1300)),
    ("Lenovo Legion Pro 7 16 (i9-14900HX / RTX 4080)", "Lenovo", "Intel Core i9-14900HX", "NVIDIA RTX 4080 12GB",
     32, 1000, 44000, 18500, '16" WQXGA 240Hz', "2.80", (6000, 2900)),
    ("Lenovo ThinkPad E14 Gen 5 (i7-1355U)", "Lenovo", "Intel Core i7-1355U", "Intel Iris Xe",
     16, 512, 16000, 1800, '14" WUXGA', "1.40", (1500, 800)),
    # HP
    ("HP 15 (i3-1315U)", "HP", "Intel Core i3-1315U", "Intel UHD Graphics",
     8, 512, 10000, 1000, '15.6" FHD', "1.60", (750, 400)),
    ("HP Pavilion 15 (R7 7730U)", "HP", "AMD Ryzen 7 7730U", "AMD Radeon Graphics",
     16, 512, 19000, 2200, '15.6" FHD', "1.75", (1200, 620)),
    ("HP Victus 16 (i5-13500H / RTX 4060)", "HP", "Intel Core i5-13500H", "NVIDIA RTX 4060 8GB",
     16, 512, 23000, 10500, '16.1" FHD 144Hz', "2.40", (2000, 1000)),
    ("HP OMEN 16 (R9 8945HS / RTX 4070)", "HP", "AMD Ryzen 9 8945HS", "NVIDIA RTX 4070 8GB",
     32, 1000, 31000, 13000, '16.1" QHD 240Hz', "2.40", (3600, 1800)),
    # Acer
    ("Acer Aspire 5 (i5-1235U)", "Acer", "Intel Core i5-1235U", "Intel Iris Xe",
     16, 512, 13500, 1700, '15.6" FHD', "1.75", (1000, 520)),
    ("Acer Nitro V 15 (i5-13420H / RTX 4050)", "Acer", "Intel Core i5-13420H", "NVIDIA RTX 4050 6GB",
     16, 512, 18000, 8500, '15.6" FHD 144Hz', "2.10", (1500, 800)),
    ("Acer Predator Helios 16 (i7-13700HX / RTX 4080)", "Acer", "Intel Core i7-13700HX", "NVIDIA RTX 4080 12GB",
     32, 1000, 36000, 18000, '16" WQXGA 240Hz', "2.60", (5000, 2500)),
    # MSI
    ("MSI Modern 15 (R7 7730U)", "MSI", "AMD Ryzen 7 7730U", "AMD Radeon Graphics",
     16, 512, 19000, 2200, '15.6" FHD', "1.70", (1150, 600)),
    ("MSI Katana 15 (i7-13620H / RTX 4060)", "MSI", "Intel Core i7-13620H", "NVIDIA RTX 4060 8GB",
     16, 1000, 25000, 10500, '15.6" FHD 144Hz', "2.25", (2250, 1100)),
    ("MSI Raider GE78 HX (i9-14900HX / RTX 4080)", "MSI", "Intel Core i9-14900HX", "NVIDIA RTX 4080 12GB",
     32, 2000, 44000, 18500, '17" QHD+ 240Hz', "3.10", (6500, 3200)),
    # Dell
    ("Dell Inspiron 15 (i5-1335U)", "Dell", "Intel Core i5-1335U", "Intel Iris Xe",
     16, 512, 15000, 1800, '15.6" FHD', "1.65", (1150, 600)),
    ("Dell XPS 15 (i7-13700H / RTX 4060)", "Dell", "Intel Core i7-13700H", "NVIDIA RTX 4060 6GB",
     32, 1000, 29000, 10000, '15.6" 3.5K OLED', "1.90", (4200, 2100)),
    # Apple
    ("Apple MacBook Air 13 (M3, 16/512)", "Apple", "Apple M3", "Apple M3 10-core GPU",
     16, 512, 18000, 4500, '13.6" Liquid Retina', "1.24", (2600, 1300)),
    ("Apple MacBook Pro 14 (M3 Pro, 18/512)", "Apple", "Apple M3 Pro", "Apple M3 Pro 18-core GPU",
     18, 512, 29000, 9000, '14.2" Liquid Retina XDR', "1.61", (4300, 2000)),
    # Huawei / Samsung
    ("Huawei MateBook D16 (i5-13420H)", "Huawei", "Intel Core i5-13420H", "Intel UHD Graphics",
     16, 512, 18000, 1500, '16" FHD', "1.72", (1300, 650)),
    ("Samsung Galaxy Book4 Pro (Ultra 7 155H)", "Samsung", "Intel Core Ultra 7 155H", "Intel Arc Graphics",
     16, 512, 24000, 3500, '14" 3K AMOLED', "1.23", (2800, 1400)),
]

# category, name, brand, extra fields, weight, (local AZN, global USD)
COMPONENTS = [
    (Component.CPU, "AMD Ryzen 5 7600", "AMD", dict(score=27000, socket="AM5", tdp_watts=65), "0.30", (420, 190)),
    (Component.CPU, "AMD Ryzen 7 7800X3D", "AMD", dict(score=34000, socket="AM5", tdp_watts=120), "0.30", (780, 370)),
    (Component.CPU, "AMD Ryzen 9 7950X", "AMD", dict(score=63000, socket="AM5", tdp_watts=170), "0.30", (1050, 500)),
    (Component.CPU, "Intel Core i5-12400F", "Intel", dict(score=19500, socket="LGA1700", tdp_watts=65), "0.30", (280, 130)),
    (Component.CPU, "Intel Core i5-14400F", "Intel", dict(score=25000, socket="LGA1700", tdp_watts=100), "0.30", (380, 170)),
    (Component.CPU, "Intel Core i7-14700K", "Intel", dict(score=52000, socket="LGA1700", tdp_watts=253), "0.30", (790, 360)),
    (Component.CPU, "Intel Core i9-14900K", "Intel", dict(score=60000, socket="LGA1700", tdp_watts=253), "0.30", (1100, 520)),

    (Component.GPU, "NVIDIA GeForce RTX 3050 8GB", "NVIDIA", dict(score=6300, tdp_watts=130), "1.00", (450, 210)),
    (Component.GPU, "NVIDIA GeForce RTX 4060 8GB", "NVIDIA", dict(score=10700, tdp_watts=115), "1.20", (620, 300)),
    (Component.GPU, "NVIDIA GeForce RTX 4060 Ti 8GB", "NVIDIA", dict(score=13500, tdp_watts=160), "1.30", (820, 400)),
    (Component.GPU, "AMD Radeon RX 7700 XT 12GB", "AMD", dict(score=16500, tdp_watts=245), "1.50", (900, 430)),
    (Component.GPU, "NVIDIA GeForce RTX 4070 Super 12GB", "NVIDIA", dict(score=19500, tdp_watts=220), "1.50", (1250, 600)),
    (Component.GPU, "AMD Radeon RX 7800 XT 16GB", "AMD", dict(score=19800, tdp_watts=263), "1.60", (1050, 500)),
    (Component.GPU, "NVIDIA GeForce RTX 4080 Super 16GB", "NVIDIA", dict(score=28000, tdp_watts=320), "2.20", (2200, 1000)),
    (Component.GPU, "NVIDIA GeForce RTX 4090 24GB", "NVIDIA", dict(score=36000, tdp_watts=450), "2.50", (3600, 1700)),

    (Component.MOTHERBOARD, "MSI PRO B650M-A WiFi", "MSI", dict(socket="AM5", ram_type="DDR5"), "1.00", (300, 140)),
    (Component.MOTHERBOARD, "Gigabyte B650 Gaming X AX", "Gigabyte", dict(socket="AM5", ram_type="DDR5"), "1.20", (380, 180)),
    (Component.MOTHERBOARD, "ASUS ROG Strix X670E-E", "ASUS", dict(socket="AM5", ram_type="DDR5"), "1.50", (700, 330)),
    (Component.MOTHERBOARD, "Gigabyte B760M DS3H DDR4", "Gigabyte", dict(socket="LGA1700", ram_type="DDR4"), "1.00", (240, 110)),
    (Component.MOTHERBOARD, "MSI PRO B760-P WiFi DDR4", "MSI", dict(socket="LGA1700", ram_type="DDR4"), "1.20", (300, 140)),
    (Component.MOTHERBOARD, "ASUS TUF Gaming Z790-Plus WiFi", "ASUS", dict(socket="LGA1700", ram_type="DDR5"), "1.40", (520, 240)),

    (Component.RAM, "Kingston Fury Beast 16GB DDR5-5600", "Kingston", dict(capacity_gb=16, ram_type="DDR5"), "0.10", (110, 55)),
    (Component.RAM, "Corsair Vengeance 32GB (2x16) DDR5-6000", "Corsair", dict(capacity_gb=32, ram_type="DDR5"), "0.15", (210, 100)),
    (Component.RAM, "G.Skill Trident Z5 64GB (2x32) DDR5-6000", "G.Skill", dict(capacity_gb=64, ram_type="DDR5"), "0.20", (400, 200)),
    (Component.RAM, "Kingston Fury Beast 16GB DDR4-3200", "Kingston", dict(capacity_gb=16, ram_type="DDR4"), "0.10", (80, 40)),
    (Component.RAM, "Kingston Fury Beast 32GB (2x16) DDR4-3200", "Kingston", dict(capacity_gb=32, ram_type="DDR4"), "0.15", (150, 70)),
    (Component.RAM, "Corsair Vengeance LPX 64GB (2x32) DDR4-3200", "Corsair", dict(capacity_gb=64, ram_type="DDR4"), "0.20", (300, 140)),

    (Component.SSD, "Kingston NV2 500GB NVMe", "Kingston", dict(capacity_gb=500), "0.05", (90, 40)),
    (Component.SSD, "Kingston NV2 1TB NVMe", "Kingston", dict(capacity_gb=1000), "0.05", (140, 65)),
    (Component.SSD, "Samsung 980 1TB NVMe", "Samsung", dict(capacity_gb=1000), "0.05", (160, 75)),
    (Component.SSD, "Samsung 990 Pro 2TB NVMe", "Samsung", dict(capacity_gb=2000), "0.05", (380, 180)),
    (Component.SSD, "WD Black SN850X 2TB NVMe", "WD", dict(capacity_gb=2000), "0.05", (340, 160)),
    (Component.SSD, "Samsung 990 Pro 4TB NVMe", "Samsung", dict(capacity_gb=4000), "0.05", (700, 330)),

    (Component.CASE_PSU, "Montech X3 Mesh + 600W Bronze", "Montech", dict(psu_watts=600), "7.00", (260, 130)),
    (Component.CASE_PSU, "DeepCool CC560 + 650W Bronze", "DeepCool", dict(psu_watts=650), "7.50", (300, 150)),
    (Component.CASE_PSU, "NZXT H5 Flow + 750W Gold", "NZXT", dict(psu_watts=750), "8.00", (420, 220)),
    (Component.CASE_PSU, "Lian Li Lancool 216 + 850W Gold", "Lian Li", dict(psu_watts=850), "8.50", (520, 270)),
    (Component.CASE_PSU, "Fractal North + 1000W Gold", "Fractal", dict(psu_watts=1000), "9.00", (650, 340)),
    (Component.CASE_PSU, "Corsair 5000D + 1200W Platinum", "Corsair", dict(psu_watts=1200), "10.00", (900, 470)),
]

# Ürün sırasına göre hangi mağazalara hangi çarpanla fiyat girileceği.
# ponytail: deterministik varyasyon; gerçek fiyat çekme (scraper) kapsam dışı (ROADMAP Faz 2).
LOCAL_PLANS = [
    [("Kontakt Home", "1.00"), ("İrşad", "1.04"), ("Baku Electronics", "1.02")],
    [("Kontakt Home", "1.03"), ("iComp", "0.98"), ("CompStore", "1.01")],
    [("İrşad", "1.00"), ("iComp", "0.97"), ("Baku Electronics", "1.05")],
    [("CompStore", "0.99"), ("Kontakt Home", "1.02")],
]
GLOBAL_PLANS = [
    [("Amazon", "1.00"), ("eBay", "0.94")],
    [("Amazon", "1.02"), ("Newegg", "0.98")],
    [("Newegg", "1.00"), ("B&H", "1.01"), ("eBay", "0.92")],
]


def _url(store_name, query):
    return SEARCH_URL[store_name].format(q=quote_plus(query))


def _named(prefix, triple):
    az, ru, en = triple
    return {f"{prefix}_az": az, f"{prefix}_ru": ru, f"{prefix}_en": en}


class Command(BaseCommand):
    help = "CompMatch örnek verilerini yükler (kategori, meslek, grup, program, laptop, PC bileşeni, mağaza, fiyat, gümrük)."

    @transaction.atomic
    def handle(self, *args, **options):
        CustomsSettings.load()

        stores = {}
        for name, kind, website, tpl, ship, scraper in STORES:
            stores[name], _ = Store.objects.update_or_create(
                name=name, defaults=dict(kind=kind, website=website, search_url=tpl, shipping_per_kg_usd=ship, scraper=scraper))

        categories = {}
        for order, (key, icon, names) in enumerate(CATEGORIES):
            categories[key], _ = ProfessionCategory.objects.update_or_create(
                name_az=names[0], defaults=dict(**_named("name", names), icon=icon, order=order))

        professions = {}
        for order, (key, cat, icon, names, descs) in enumerate(PROFESSIONS):
            professions[key], _ = Profession.objects.update_or_create(
                name_az=names[0], defaults=dict(
                    **_named("name", names), **_named("description", descs),
                    category=categories[cat], icon=icon, order=order))

        groups = {}
        for order, (key, names) in enumerate(GROUPS):
            groups[key], _ = ProgramGroup.objects.update_or_create(
                name_az=names[0], defaults=dict(**_named("name", names), order=order))

        for name, icon, group, profs, blurbs, req in PROGRAMS:
            mc, rc, mg, rg, mr, rr, ms, rs = req
            mg, rg = ts_to_g3d(mg), ts_to_g3d(rg)
            program, _ = Program.objects.update_or_create(name=name, defaults=dict(
                icon=icon, group=groups[group], **_named("blurb", blurbs),
                min_cpu_score=mc, rec_cpu_score=rc, min_gpu_score=mg, rec_gpu_score=rg,
                min_ram_gb=mr, rec_ram_gb=rr, min_ssd_gb=ms, rec_ssd_gb=rs,
            ))
            program.professions.set([professions[p] for p in profs])

        for i, (name, brand, cpu, gpu, ram, ssd, cs, gs, screen, weight, (azn, usd)) in enumerate(LAPTOPS):
            laptop, _ = Laptop.objects.update_or_create(name=name, defaults=dict(
                brand=brand, cpu=cpu, gpu=gpu, ram_gb=ram, ssd_gb=ssd, cpu_score=cs, gpu_score=ts_to_g3d(gs),
                screen=screen, weight_kg=Decimal(weight),
            ))
            self._prices(LaptopPrice, "laptop", laptop, stores, i, azn, usd, name)

        for i, (cat, name, brand, extra, weight, (azn, usd)) in enumerate(COMPONENTS):
            if cat == Component.GPU:
                extra = {**extra, "score": ts_to_g3d(extra["score"])}
            comp, _ = Component.objects.update_or_create(name=name, defaults=dict(
                category=cat, brand=brand, weight_kg=Decimal(weight), **extra))
            self._prices(ComponentPrice, "component", comp, stores, i, azn, usd, name)

        # Yalnızca DEBUG (localhost) modunda ve hiç süper kullanıcı yokken: geliştirme hesabı test/test.
        # DJANGO_DEBUG=0 ile çalışan bir kurulumda asla oluşturulmaz; orada `createsuperuser` kullanın.
        User = get_user_model()
        if settings.DEBUG and not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser("test", "", "test")  # ponytail: localhost geliştirme hesabı
            self.stdout.write("Geliştirme admin hesabı oluşturuldu (kullanıcı adı: test; şifre README'de).")

        self.stdout.write(self.style.SUCCESS(
            f"Seed tamam: {ProfessionCategory.objects.count()} kategori, {Profession.objects.count()} meslek, "
            f"{ProgramGroup.objects.count()} grup, {Program.objects.count()} program, "
            f"{Laptop.objects.count()} laptop, {Component.objects.count()} bileşen, "
            f"{Store.objects.count()} mağaza, "
            f"{LaptopPrice.objects.count() + ComponentPrice.objects.count()} fiyat."
        ))

    def _prices(self, model, fk, product, stores, i, azn, usd, query):
        for store_name, mult in LOCAL_PLANS[i % len(LOCAL_PLANS)]:
            model.objects.update_or_create(**{fk: product}, store=stores[store_name], defaults=dict(
                price=(Decimal(azn) * Decimal(mult)).quantize(Decimal("1")), currency="AZN",
                url=_url(store_name, query), in_stock=(i % 7 != 3),
            ))
        for store_name, mult in GLOBAL_PLANS[i % len(GLOBAL_PLANS)]:
            model.objects.update_or_create(**{fk: product}, store=stores[store_name], defaults=dict(
                price=(Decimal(usd) * Decimal(mult)).quantize(Decimal("1")), currency="USD",
                url=_url(store_name, query), in_stock=True,
            ))
