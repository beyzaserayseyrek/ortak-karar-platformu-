# Müzakere — problem çerçevesi ve riskler

## Kapsam ve varsayımlar

| Konu | Bu revizyondaki karar |
|---|---|
| İşlev kapsamı | İlk proje gereksinimleri korunur. Yeni slayt örnekleri ürün özelliği sayılmaz. |
| Kullanıcı | Üniversite ders çalışma grubu; gerçek kullanıcı araştırması yapılmadı. |
| r | Projenin seçtiği minimum katılım oranı; varsayılan 0,50. |
| Teslim | Mobil uyumlu Flask web uygulaması; manifest ve çevrimdışı uyarısı. Native uygulama yok. |
| AI | Yerel, deterministik alıntı / kelime eşleşmesi demosu; dış model yok. |
| Ders notları | Belirsiz “bazı analizler” ifadesinden yeni hoca zorunluluğu çıkarılmaz. |
| Veriler | Sentetik örnekler; eski yerel veritabanı ve bağlantılar korunur. |

## Problem → karar → değer

Hedef kullanıcı öğrencidir. Moderatör kapsamı ve hak etkilerini inceler; bilirkişi danışma görüşü verir. Öğretim elemanı sunumu ve gerekçeleri değerlendirebilir; ayrı öğretmen rolü uygulanmamıştır. Veri sahibi öğrenciler ve bakım yapan geliştirici de paydaştır.

Varsayılan problem: sohbet içinde öğrenme soruları, kaynaklar ve karşı gerekçeler kaybolur; kararın kimlerin katılımıyla oluştuğu takip edilemez. Bu bir **tasarım varsayımıdır**, araştırmayla doğrulanmış bulgu değildir.

Öğrenci çalışma konusunu önerir; etkilenen grubun açılıştaki üyeleri kabul / ret / çekimser oy kullanır. Yazılım katılım ve çoğunluğu hesaplar, kural ihlali varsa uygulamayı engeller. Kabul edilen uygulanabilir konu kalıcı tartışma alanına dönüşür. Beklenen değer: gerekçeli öğrenme katkılarının ve karar izinin aynı yerde bulunması. Öğrenme başarısında artış henüz ölçülmedi.

## Gereksinimler ve veri

- İşlevler: kayıt, sabit seçmen, tek güncel oy, açıklanabilir sonuç, sürümler, kaynak / soru / karşı gerekçe, yararlılık, itiraz, moderasyon, bilirkişi, bildirim, graf ve denetim günlüğü.
- Kalite: kalıcılık, işlem atomikliği, sunucu tarafı yetki, CSRF, HTML kaçışlama, mobil yerleşim, klavyeyle temel akış, hatada form verisinin korunması.
- Kaynaklar: kayıt formları, oylar, tartışma metinleri ve sentetik `seed.py`. Ders PDF metinleri uygulamaya veya AI girişine alınmaz.
- Özel profil alanları normal görünümde yayımlanmaz; demo sağlayıcıya kullanıcı kaydı gönderilmez. SQLite dosyasında özel profil alanları şifreli değildir. Sunumda yalnız kurgu kullanılır.
- AI'a seçilmiş görünür mesajların kimliği, türü ve gövdesi; konunun kimliği/başlığı; en fazla 50 aday başlığı verilir. Dış servise gönderim yoktur.

## Deterministik çekirdek ve baseline

Oylama ve R1–R4, bilinmekte olan kurallardır; bunları modelden tahmin etmesini istemek gereksiz belirsizlik yaratır. Baseline, oylama hesabı + açık kural zinciri + kaynaklı tam alıntılardır. AI benzeri yardımcı yalnız kategori / ilişki / olası çelişki ipucu verir. “Karar” ve “tahmin” birbirinden ayrıdır. Daha karmaşık modelin gerekli olduğuna ilişkin karşılaştırmalı kanıt yok; eğitim, fine-tuning ve RAG eklenmedi.

Özet tam anlamsal özet değildir. Her türden sayfa başına en fazla 12 katkı seçilir; karşı görüşler yeni açıklamalar yüzünden kota dışında kalmaz. Diğer alıntılara sayfalama vardır. Seçilen bir gerekçe kırpılamaz veya kaynağı değiştirilemez. Kapalı oylamadaki kabul/ret gerekçeleri ayrıca karar sayfasına bağlanır.

## Başarı ölçütleri

Aşağıdaki hedefler proje kabul ölçütleridir; dersin zorunlu eşikleri veya saha sonucu değildir.

| Tür | Ölçüt / hedef | Bu revizyonda gözlem |
|---|---|---|
| Ürün | Öğrenci temel akışı yardımsız tamamlayabilsin | Kullanıcı çalışması yapılmadı; ajan tarayıcı senaryosu tamamlandı. |
| Öğrenme | Gerekçeli katkıların yararlılığı; öğrenme ön/son değerlendirmesi | Ölçülmedi; katkı puanı öğrenme başarısının vekili sayılmaz. |
| Teknik | Tanımlı kritik regresyonlarda hata olmaması | 40 otomatik test geçti; kapsam ve sınırlamalar TEST_RESULTS.md. |
| Koruyucu | Sentetik R1/R2 ihlallerinin çoğunlukla aşılamaması | Deterministik testler geçti; serbest metin hak ihlallerini tam tespit etmez. |
| Koruyucu | Seçilen AI kanıtında kaynaksız / eksik gerekçe olmaması | Sentetik bozuk çıktılar geri dönüşe alındı; gerçek model skoru değildir. |
| Güvenlik | Normal görünümde özel profil sızıntısı olmaması | Seçilmiş sayfalar otomatik denetlendi; bağımsız güvenlik denetimi yapılmadı. |
| Performans | Ders gösteriminde etkileşimlerin kullanılabilir olması | Yük testi, p95 gecikme veya eşzamanlı kullanıcı kapasitesi ölçülmedi. |
| Maliyet | Dış AI API maliyeti olmaması | Bu sürüm hiçbir dış model çağrısı yapmaz; cihaz/enerji maliyeti ölçülmedi. |

Katılımı tek başarı ölçütü yapmayın: çok hesap açarak oran artırılabilir. Katkı adedini tek ölçüt yapmayın: spam teşvik edebilir. Tekil kaynak puanı, günlük sınırlar, hak denetimi ve gerekçe kalitesi koruyucu ölçütlerdir.

## Kısıtlar ve ön-otopsi

Bir ders prototipi, tek bilgisayar, Flask geliştirme sunucusu ve SQLite kullanılır. Kesin ders son tarihi / bütçe verilmedi; uydurulmadı. Üretim dağıtımı veya sürekli işletim taahhüdü yoktur.

| Olası başarısızlık | Nitel risk | Önlem / kalan sınır |
|---|---|---|
| Çoğunluk azınlığın hakkını kaldırır | Yüksek etki | Grup katılımı + R1/R2 + itiraz; yanlış etki beyanı insan incelemesi ister. |
| Özet karşı gerekçeyi saklar | Yüksek etki | Tür başına kota, tam alıntı, kapsam doğrulaması ve kaynak bağlantısı; anlamsal temsil garantisi yok. |
| Sağlayıcı hatası uygulamayı durdurur | Orta etki | Enjekte edilen sağlayıcı sınırı; hata/geçersiz çıktı yerel demoya döner. Gerçek ağ zaman aşımı entegrasyonu yok. |
| Süre hatası taslağı kısmen değiştirir | Orta etki | Tüm süre/kapsam doğrulaması SQL yazmasından önce; regresyon testi. |
| Kalıcı gizleme geçici gizlemeye çevrilir | Yüksek etki | Zaten gizli içeriği yeniden geçici gizleme 409; kalıcı geri açma 403. |
| Özel bilgi / hizmet anahtarı depoya girer | Yüksek etki | `.gitignore`, kurgusal seed, gönderim dosya incelemesi; gerçek veriler yüklenmez. |
| Çoklu sahte hesap / kötü niyetli yönetici | Yüksek etki | Tek oy, r değişikliğinde iki yönetici; kimlik/üyelik doğrulaması ve yöneticinin bütün kötüye kullanımları çözümlenmedi. |
| Tek cihaz veya disk bozulur | Yüksek etki | Üretimde yedek/izleme gerekir; iki JSON kopyası demosu yedekleme sistemi değildir. |

Risk etiketleri olasılık ölçümü değil, ön-otopsi için nitel tasarım değerlendirmesidir.

## Ders dayanakları

- `YZM_Hafta02_Problem_Cerceveleme.pdf`, fiziksel s.8–12: yeterli en basit yaklaşım; s.16–17: amaç/karar ayrımı; s.25,34–35: farklı metrikler ve koruyucu ölçüt; s.38: baseline; s.45,47–48: kısıtlar, ön-otopsi ve problem çerçevesi. Bu dosyada basılı slayt numaraları fiziksel sayfalarla aynıdır.
- `S01_YZ_Muhendisligine_Giris.pdf`, fiziksel s.40 (slayt 34): kalite boyutları; s.42–43 (slayt 36–37): demo/ürün ayrımı ve bakım; s.55 (slayt 47): tanımla–üret–doğrula–entegre et–izle.
- Kaynakların mini laboratuvarları uygulama kapsamına aktarılmadı. Sunumlardaki kitap kapakları/kaynakçalar, kitapların bağımsız okunmuş içeriği olarak kullanılmadı.
