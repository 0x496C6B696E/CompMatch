# CompMatch Yol Haritası

## Faz 1 — Çok dilli, geniş katalog, herkes için anlaşılır (bu sürüm)

- [x] **3 dil:** Azerbaycanca (varsayılan), Rusça, İngilizce. Arayüz metinleri sözlükten, admin'den girilen başlıklar (`*_az / *_ru / *_en` alanları) API'den dile göre gelir. Dil seçimi üst barda, tarayıcıda hatırlanır.
- [x] **Meslekler başlıklar altında:** 6 kategori (Dizayn, Video/Səs/Foto, Mühəndislik/Memarlıq/3D, Proqramlaşdırma/IT, Data/Maliyyə/Ofis, Oyun/Yayım), 19 meslek.
- [x] **Programlar gruplar altında:** 9 grup, 52 program; her programın sade dilde bir satır açıklaması var.
- [x] **Laptop kataloğu:** 28 laptop, markaya göre filtre, fiyata/güce göre sıralama. Her kartta "hangi işler için uygun" (meslek bazlı) ve "en ucuz nerede". Kart açılınca Bakü vs Global karşılaştırması.
- [x] **PC parça kataloğu:** 39 parça, kategori sekmeleri + marka filtresi; her kategorinin ne işe yaradığı sade dille yazılı.
- [x] **Bilgisayardan anlamayanlar için:** sayısal skorların yanında "Sadə / Orta / Güclü / Çox güclü" seviye etiketi, "Bu rəqəmlər nə deməkdir?" açılır açıklama, her öneri için tek cümlelik özet, mağaza/gümrük kırılımı düz cümle.
- [x] **Mobil:** iki satırlı üst bar, kaydırılabilir sekmeler, tek sütun kartlar, dar ekranda kısaltılmış stepper.

## Faz 2 — Gerçek veri

- [ ] Mağaza fiyatlarını CSV/Excel'den toplu içe aktarma (admin aksiyonu).
- [ ] Kontakt, İrşad, iComp için fiyat/stok çekici (scraper) komutları; "son güncelleme" zamanı.
- [ ] USD/AZN kurunu Mərkəzi Bank'tan otomatik çekme (`update_rates` komutu).
- [ ] Ürün görselleri ve resmi ürün sayfası linkleri.

## Faz 3 — Kullanıcı özellikleri

- [ ] İki laptopu / iki parçayı yan yana karşılaştırma.
- [ ] Sonucu link olarak paylaşma (seçimler URL'de).
- [ ] Favoriler ve "fiyat düşünce haber ver" (e-posta).
- [ ] Hazır (prebuilt) PC setleri ve "bütçeye göre topla" modu.

## Faz 4 — Yayına hazırlık

- [ ] Ortam değişkenleriyle ayarlar, PostgreSQL, statik dosya sunumu (WhiteNoise), HTTPS.
- [ ] Arama (laptop/parça adı), sayfalama.
- [ ] Basit kullanım istatistikleri (hangi meslek/program seçiliyor).
- [ ] PWA (ana ekrana ekle, çevrimdışı son sonuç).
