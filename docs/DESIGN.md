# Tasarım incelemesi ve karar kayıtları

## Somut inceleme

Dosya + fonksiyon referansları satır kaymalarından bağımsız olarak verilmiştir.

| Bulgu | Uygulanan çözüm / kod | Kalan maliyet |
|---|---|---|
| `app.py` hem HTTP hem kapanış hem SQLite/puan/günlük sorumluluklarını taşıyordu | `voting.py:start_voting,close_voting`; `storage.py:db,event,award,notify`; HTTP `app.py` içinde | Tam repository katmanı kurulmadı. `storage` Flask `g` bağlamına bağlı; servis testinde app context gerekir. |
| Normal ve kısıtlayıcı eşik iki yerde yineleniyordu | `policy.py:VotingPolicy,StandardVotingPolicy,RestrictiveVotingPolicy,policy_for`; oy ve grup denetimi aynı stratejiyi kullanır | İki küçük sınıf; yeni politika eklenince seçim fabrikası bilinçli değişir. |
| Hak kontrolleri tek koşul kümesindeydi | `RuleHandler.check`, `RuleContext`, `build_rule_chain`: R1→R2→R4→R3 | Dört düğüm için sınıf maliyeti vardır; tüm nedenleri toplamak ve kontrolü ayrı değiştirmek gerekçesidir. |
| `start` geçersiz süreyi yakalamadan taslağı yazıyordu; hata yönlendirmesi commit ediyordu | `app.py:start` içinde süre doğrulaması UPDATE'ten önce | Transaction sınırı HTTP durum koduna da bağlı; yeni hata yakalamaları kısmi yazma açısından incelenmeli. |
| Özet son 12 katkıyla eski karşı görüşleri dışlıyordu; 240 karakterde gerekçe kesiliyordu | `app.py:summary`: tür başına 12 + sayfalama; `DemoProvider` tam alıntı; kaynak sayfasını hesaplar | Temsil/önem değerlendirmesi yapmaz. Her türde son 12'nin dışındaki katkılar sonraki sayfada. |
| Sağlayıcı doğrudan route içinde oluşturuluyor, desteklenmeyen ayar başlangıcı durduruyordu | `create_app` yapıcı enjeksiyonu; `SummaryService.validate/summarize`; `UnavailableProvider` geri dönüşü | Dış SDK/time limit yok; gelecekte gerçek sağlayıcının kendi ağ zaman sınırı olmalı. |
| Kalıcı gizli mesaj yeniden geçici gizlenip geri açılabilirdi | `app.py:hide` zaten gizli kaydı reddeder | Veri tabanı yöneticisinin doğrudan müdahalesini önlemez. |
| Konu/graf listeleri tüm konuları belleğe alıyordu | `topics,graph`: SQL JSON üyelik filtresi ve LIMIT/OFFSET | SQLite JSON1 gerekir; diğer dashboard/yönetim listeleri hâlâ büyük ölçek için gözden geçirilmeli. |
| Seed R1 incelemesini kapanıştan sonra yazıyor, karar JSON'unda R3 eski kalıyordu | `seed.py:proposal(review=...)` incelemeyi kapanıştan önce kaydeder | Önceki yerel kayıtların tarihi karar JSON'u değiştirilmedi. Eski örnek 3'te R1 ve R3 birlikte görülebilir. |

## SOLID ve anti-desen değerlendirmesi

- **S:** rotalar, iş akışı, saf kurallar, depolama ve AI sınırı ayrı modüllerdedir. `app.py` hâlâ büyük bir route modülüdür; tam bağımsız mikroservis iddiası yok.
- **O:** eşik algoritması `VotingPolicy` ile değiştirilebilir; kural zincirinin bir koşulu diğer handler kodunu değiştirmeden eklenebilir. Yönetmelik değişikliği yine kod incelemesi gerektirir; sınırsız runtime eklenti sistemi yok.
- **L:** kısıtlayıcı politika standart politikanın sonuç sözlüğü sözleşmesini korur, yalnız threshold metodunu özelleştirir. İki stratejinin sınırları test edilir.
- **I:** `SummaryProvider` tek `summarize` metodu içerir. UI ve oylama, model SDK'sına bağlı değildir.
- **D:** `SummaryService` somut sağlayıcıyı kendi içinde ana yol için yaratmaz; yapıcıdan `SummaryProvider` alır. Fallback açıkça yerel demo olarak seçilir. `create_app` bileşim yeridir.
- God Object riski azaltıldı; rota sayısı sebebiyle tamamen kalkmadı. Singleton, global servis locator, Observer olay otobüsü, gereksiz State sınıfları eklenmedi. Sıkışık Jinja ve bazı tek satırlık yardımcılar okunabilirlik borcudur. Golden hammer / erken soyutlama yerine seçilmiş iki desen kullanıldı.

## ADR-001 — Eşik algoritmasını Strategy ile değiştirme

**Durum:** uygulandı. **Problem:** normal ve hak kısıtlayıcı katılım eşikleri farklı ve aynı karar içinde iki noktada kullanılıyor. **Çözüm:** `VotingPolicy` Protocol; `StandardVotingPolicy.threshold(r)=r`, `RestrictiveVotingPolicy.threshold(r)=max(r,.67)`. `close_voting` seçilmiş nesnenin `evaluate` metodunu çağırır. R4 aynı nesne sözleşmesini kullanır. **Avantaj:** tek eşik tanımı, ayrı sınır testleri. **Maliyet:** iki sınıf ve seçim fabrikası. 2/3 ve bağımsız inceleme R3'te kalır; çoğunluk kabulü ile uygulanabilirliği karıştırmaz.

## ADR-002 — Kural ihlallerini toplayan Chain of Responsibility

**Durum:** uygulandı. **Problem:** birden fazla hak/katılım ihlalinin hepsini gerekçede göstermek gerekiyor. **Çözüm:** `RuleHandler` kendi predicate'ini değerlendirir ve `successor.check` çağrısıyla devam eder. Somut zincir R1, R2, R4, R3; ilk ihlalde kesilmez. **Avantaj:** ihlaller kaybolmaz, kuralların sorumlulukları bağımsızdır. **Maliyet:** basit if dizisine göre daha fazla yapı; yalnız bu dört sıralı denetimde kullanılır. Ders kaynağındaki hata toplama biçimiyle uyumludur.

## ADR-003 — Sağlayıcı sınırı ve kanıt doğrulaması

**Durum:** uygulandı; **GoF Adapter olarak etiketlenmedi**. Ortada uyumsuz harici SDK yoktur. Protocol tek başına Adapter sayılmaz. `SummaryService` id/kind/tam metin ve seçilen kaynak kümesinin kapsamını doğrular; hatada açık uyarılı yerel alıntı döner. Girdiler kopyalanarak sağlayıcının doğrulama tabanını değiştirmesi engellenir. Serbest kategori/uyarı alanlarında tür ve uzunluk denetimi vardır; bunların anlamsal doğruluğu garanti edilmez. Bu nedenle gerçek sağlayıcı doğrudan eklenmiş sayılmaz.

## ADR-004 — Değerlendirilen, eklenmeyen desenler

| Desen | Karar ve gerekçe |
|---|---|
| Adapter | Ertelendi: uyumsuz gerçek sağlayıcı API'si yok. Entegrasyon gelirse açık giriş/çıkış dönüşümü yazılabilir. |
| Observer | Eklenmedi: DB bildirimi ve olay kaydı aynı transaction içinde doğrudan yazılır. Bağımsız subscriber/publisher sistemi yok. `notify` yardımcı fonksiyonuna Observer denmez. |
| Facade | Eklenmedi: modül ayırma ve `SummaryService` sınırlı sorumluluk taşır; karmaşık birden fazla alt sistemi gizleyen ayrı cephe gereksinimi yok. |
| State | Eklenmedi: beş durum ve açık geçiş korumaları mevcut ölçek için yeterli. Durum diyagramı olması State deseni uygulandığı anlamına gelmez. |

## ADR-005 — Veriyi ve teslim sınırlarını koruma

Ürün adı Müzakere; depo adı, URL'ler, `instance/ortak.sqlite` ve mevcut demo şifresi değişmedi. Şema göçü veya yeniden seed yok. Tarayıcı E2E ayrı sentetik SQLite dosyasında yapıldı. Ders kaynakları depoya kopyalanmadı. AI karar, puan veya gizleme işleminin otoritesi değildir. PWA ve yerel ledger kopyaları açıkça sınırlı demo olarak anlatılır.

## Diyagramlar

[Galeri](diagrams/index.html) · [Düzenlenebilir Python kaynağı](diagrams/render.py)

1. [Use case](diagrams/01-use-case.svg): sistem sınırı, çöp adam aktörler, elips kullanım durumları ve ok başsız ilişkiler.
2. [UML sınıfları](diagrams/02-classes.svg): gerçek Protocol/sınıflar; boş üçgen kalıtım, kesik boş üçgen yapısal gerçekleştirme; successor öz ilişkisi.
3. [Öneri / oylama sekansı](diagrams/03-proposal-sequence.svg).
4. [Kural engeli sekansı](diagrams/04-blocked-sequence.svg).
5. [Durum diyagramı](diagrams/05-lifecycle.svg): `accepted` ve `applied` ayrı.
6. [Kavramsal SQL grafı](diagrams/06-graph.svg): Python sınıfı olarak sunulmaz.
7. [Mimari](diagrams/07-architecture.svg).

Vektör çizimi için standart SVG kullanıldı. Kaynak, yerleşim ve UML işaretlerini açıkça üreten bağımlılıksız Python betiğidir; `python docs/diagrams/render.py` ile yeniden üretilir. SVG'ler ayrıca vektör editöründe düzenlenebilir.

## Ders dayanakları

- `tasarim_desenleri.pdf`, fiziksel s.8 (UML/Protocol), s.9 (SOLID), s.12 (bağımlılık tersine çevirme), s.24 (Adapter), s.28 (Facade), s.36 (Strategy), s.38 (Observer), s.43 (State), s.44 (hata toplayan zincir), s.57–58 (anti-desenler ve seçim). Slayt numaraları fiziksel sayfalarla aynıdır.
- `S02_Temel_Modelleri_Anlamak.pdf`, fiziksel s.44–46 (slayt 38–40): yapılandırılmış çıktı içerik doğruluğu garantisi değildir; s.48–51 (slayt 41–44): tutarsızlık, halüsinasyon, kaynak bağlamı.
- `S01_YZ_Muhendisligine_Giris.pdf`, fiziksel s.54–55 (slayt 46–47): üretilen testlerin de doğrulanması ve insan/AI iş bölümü.
