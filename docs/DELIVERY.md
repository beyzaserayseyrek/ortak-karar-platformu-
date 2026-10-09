# Müzakere — ders revizyonu teslim kaydı

- Hedef: https://github.com/beyzaserayseyrek/ortak-karar-platformu-
- Hedef dal: `main`.
- Başlangıç: `a2adce52e341f532b1dc6cc8c3b4e8dd20eff12a`; mevcut uzak geçmiş korundu.
- Kod/test commit'i: [8fef643](https://github.com/beyzaserayseyrek/ortak-karar-platformu-/commit/8fef64359a4306e91e35de47cf44f44326a75259), main yeniden okunarak doğrulandı.
- Rapor/diyagram/README belgeleri ayrı belge commit'idir; son uzak SHA teslim yanıtında yer alır. Belge kendi commit kimliğini içermek zorunda değildir.
- Shell ağ erişimi olmadığından GitHub bağlantısı kullanıldı; ref güncellemesi beklenen eski SHA ile ve `force=false` yapıldı. Yerel Git commit SHA'ları bağlantının oluşturduğu SHA'lardan farklı olabilir; dosya bütünlüğü tree SHA eşitliğiyle kontrol edilir.
- Kaynak PDF'ler, kitaplar, yerel DB, gerçek kullanıcı bilgileri, `.env`, oturum anahtarı ve çalışma klasörleri gönderilmez.

## Dosyalar

[Rapor](rapor.pdf) tek A4 sayfa ve tıklanabilir gerçek kaynak adresi içerir. [HTML](rapor.html) aynı metni kullanır. [Diyagram galerisi](diagrams/index.html) yedi SVG'ye ve düzenlenebilir kaynağa bağlanır.

[Kurulum](../README.md), [testler](TEST_RESULTS.md), [gereksinim eşleştirmesi](TRACEABILITY.md), [demo sırası](DEMO.md), [AI değerlendirmesi](AI_EVALUATION.md).

## Çalıştırma

`python app.py` ile yerel `http://127.0.0.1:5000`. Bu adres yalnız uygulamanın çalıştığı Mac üzerinde kullanılabilir. Herkese açık canlı demo yayımlanmadı. Sunucu kapandığında yeniden başlatılmalıdır. Mevcut DB üzerinde `seed.py` yeniden çalıştırılmaz; ilk boş kurulum içindir.

Eski ZIP/bundle dosyaları önceki teslimin arşividir; bu revizyon için güncel kaynak GitHub deposudur.
