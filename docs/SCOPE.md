# Gereksinimler, kararlar ve kapsam

## Kesin talepler
Kalıcı uçtan uca akış; Türkçe mobil web; r=0,50 minimum katılım; tek oy;
seçmen dondurma; gizlilik ve roller; alt konu / düzenleme; kural engeli;
azınlık gerekçeleri ve itiraz; öğrenme soruları, kaynak ve açıklama;
tekrarsız katkı puanı; testler; tek sayfalık rapor ve gerçek GitHub adresi.

## Uygulama kararları
Flask + SQLite kurulum ve kod izlemeyi kolaylaştırmak için seçildi.
Öneri sahibi grupları önerir, yönetici kapsamı ve etkiyi onaylar.
Kısıtlayıcı kararda %67 katılım ve 2/3 kabul, bağımsız inceleme gerekir.
Yönetmelik parametresi ikinci yönetici onayıyla değişir. Üyeler kayıt anında bir gruba katılır.
Puan politikası +5 / +3 ve UTC gününde 20 puan; günlük 40 mesajdır.

## Uygulama sırası
1. Kalıcı kimlik ve öneri/oy/sonuç/konu/tartışma akışı.
2. Deterministik kurallar, sabit seçmen, azınlık ve gizleme incelemesi.
3. Öğrenme katkıları, puan, sürümler, bilirkişi, keşif ve demo özet.
4. Otomatik test, masaüstü/mobil kontrol, dokümantasyon ve rapor.
5. GitHub gönderimi ve uzak SHA doğrulaması (entegrasyon yazma erişimi bekleniyor).

## Karşılanma özeti
- 1–4: Mobil web ve temel akışlar çalışır; native yok.
- 5: Grup katılımı, hak kuralları, itiraz ve sıkı inceleme çalışır; tam hak garantisi değildir.
- 6: Mesaj gizleme / geçmiş / acil inceleme çalışır; öneri tarihindeki tüm bölüm için de kaldırma oylaması var.
- 7: JSON kavram/ilişki modeli ve Python kuralları çalışır; tam ontoloji çıkarımı yok.
- 8: Kişisel dashboard ve katkılar var; konu takibi yeni katkı bildirimi üretir.
- 9: Filtreli ilişki şeması + liste var; fizik simülasyonlu graf değil.
- 10: Uzmanlık, tarih, çıkar çatışması, gerekçeli görüş ve talep var.
- 11: Yerel alıntı özeti ve kelime eşleşmeli benzer başlık uyarısı var. Gerçek model yok;
  kategori ve çelişki ipuçları yalnız sözcük eşleştiren demo sağlayıcıdadır. Karşı görüşler alıntılara dahil edilir;
  son 12 kayıt sınırı nedeniyle tüm çoğunluk/azınlık görüşlerini kapsama garantisi yok.
- 12: Eklemeli hash zinciri ve iki dosyalı yerel kopyalama var; bağımsız düğümler/mutabakat yok.
- 13–15: Testler, örnek senaryolar, belge ve ortak görsel dil var. Ayrıntılar TEST_RESULTS.md.
- 16: Gerçek depo erişimi doğrulandı; yazma 403 nedeniyle yükleme bekliyor.
