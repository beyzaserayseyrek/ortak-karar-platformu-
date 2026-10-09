# Yardımcı AI sınırı ve sentetik değerlendirme

**Sağlayıcı:** `DemoProvider`, yerel Python. **Model / API / istem:** yok. Bu bir LLM başarım değerlendirmesi değildir. Davranış sürümü, Git commit'i ve testler ile izlenir. Metinsel istem veya dış model adı uydurulmadı.

`tests/test_revision.py:MESSAGES` üç tamamen kurgusal kayıt kullanır: 101 gerekçeli BFS açıklaması, 102 ağırlık varsayımına karşı gerekçe, 103 kuyruk sorusu. Kaydın pedagojik doğruluğunu model puanlamaz; amaç doğrulama sınırının bozulmuş çıktıyı reddetmesidir. Ek uzun-metin örneği sonda önemli bir koşul içerir.

| Durum | Beklenti | Sonuç |
|---|---|---|
| Geçerli tam alıntılar | Aynı kimlik/tür/metin; geri dönüş uyarısı yok | Geçti |
| Açıklamanın “çünkü” gerekçesi silindi | Sağlayıcı çıktısı reddedilir; kaynaklı demo | Geçti |
| Kaynakta olmayan BFS iddiası eklendi | Tam metin eşitliği bozulur; demo | Geçti |
| Karşı gerekçe atlandı | Seçilen kaynak kümesi eksik; demo | Geçti |
| Nesne yerine metin geldi | Şema reddi; demo | Geçti |
| Uydurma kaynak kimliği | Kaynak reddi; demo | Geçti |
| Aynı kaynak tekrarlandı | Tekillik reddi; demo | Geçti |
| Sağlayıcı TimeoutError verdi | Ayrıntı sızmadan demo; ayrı uygulama testi oylamanın sürdüğünü doğrular | Geçti |
| Uzun gerekçenin son koşulu | 240 karakterde kırpılmaz; tamamı korunur | Geçti |

Bunlar dokuz test vakasıdır; “model doğruluğu %100” gibi genelleme yapılmaz. Ek route testinde 25 yeni açıklama eklenmesine rağmen eski karşı gerekçe alıntıda kaldı ve 2. sayfaya kaynak bağlantısı üretildi. Özet isteğinin oy/puan/mesaj/öneri/olay tablolarını değiştirmediği ayrıca karşılaştırıldı (kapanacak oylama bulunmayan fixture).

## Güven sınırı

1. Route yalnız görünür katkıları seçer. Her tür için 12 kayıt + sayfalama vardır; tüm tartışma tek sayfaya sığmış gibi gösterilmez.
2. Sağlayıcıya girdilerin kopyası verilir. Şema, tekil kaynak kimliği, seçilen tüm katkıların bulunması, tür ve tam gövde eşitliği denetlenir.
3. Kaynak bağlantısı gerçek tartışma sayfası ve mesaj ankrajına gider. Oy gerekçeleri karar sayfasına bağlanır.
4. Başarısız/geçersiz sağlayıcı çıktısı kullanıcıya gösterilmez; uyarılı yerel demo kullanılır.
5. Kategori/uyarıların anlamsal doğruluğu kanıtlanmaz; bunlar etiketli anahtar sözcük ipuçlarıdır. AI karar/puan/gizleme otoritesi değildir.

**Gerçek API denemesi:** yapılmadı. Ağ zaman aşımı sınırı ve tekrar politikası uygulanmış gerçek entegrasyon yoktur. Testte exception enjekte edilmiştir; sonsuza dek bloklanan bir dış çağrıyı servis kendi başına durdurmaz. Gerçek entegrasyon gelirse HTTP timeout, maliyet/latans ölçümü, mahremiyet değerlendirmesi ve ayrı model eval seti gerekir.

**Kaynak:** `S02_Temel_Modelleri_Anlamak.pdf`, fiziksel s.44–46 (slayt 38–40), fiziksel s.48–51 (slayt 41–44). Yapılandırılmış çıktı ile doğru içerik farklıdır; kaynak bağlamı doğrulama ihtiyacını kaldırmaz. `YZM_Hafta02_Problem_Cerceveleme.pdf`, fiziksel/slayt s.38: önce basit baseline.
