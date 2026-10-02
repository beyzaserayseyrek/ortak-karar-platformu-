# Doğrulama sonuçları

Tarih: 2 Ekim 2026. Python 3.13.5, Flask 3.1.2, SQLite; yerel macOS ortamı.

## Otomatik testler

Komut: `python -m unittest discover -s tests -v`

**19 test geçti, 0 başarısız.** Son çalışma yaklaşık 1,47 saniye.

- Tüm ana sayfaların ve örnek kararların oluşturulması
- Günlük katkı puanı sınırı
- Süre sonu ve iki yöneticiyle politika değişikliği
- Demo AI işaretleri ve karşı gerekçeler
- Acil gizleme ve inceleme taslağı
- Öneri → sabit seçmen → oy → kapanış → konu → kalıcı tartışma
- Hash zincirinde değişiklik tespiti, SQL güncelleme engeli
- Yararlı katkının tekrarlı puanlanmaması ve kendi katkısını puanlayamama
- Devam eden oy dağılımının ve gizlenen içeriğin korunması
- Çoğunluk kabulüne rağmen R1 engeli
- Mesaj kalıcılığı, düzenleme geçmişi ve HTML kaçışlama
- Sunucu tarafı roller, CSRF, seçmen ve bilirkişi yetkisi
- Kayıt, şifre hash'i, özel alanlar ve seçmen listesinin sabit kalması
- Bölüm gizlemede sonradan eklenen mesajların kapsam dışı kalması
- Çakışan konu düzenlemesinin eski içeriği ezmemesi
- Konu takibi ve bildirim
- Tek oy ve oy güncelleme
- Grup katılımı / kısıtlayıcı karar incelemesi
- Kabul, ret, eşitlik, çekimser, seçmensiz ve yetersiz katılım sınırları

## Ek denetim

`python scripts/verify_ledger.py --demo-tamper`: orijinal zincir `(True, None)`;
yalnız bellekte bozulan kopya `(False, 25)`. Veritabanına bozuk veri yazılmadı.

`python scripts/replicate_ledger.py`: node-a ve node-b dosyalarında 49 olayın
aynı zincirle doğrulanması başarılı. Bu kayıt sayısı kontrol anına aittir;
yeni işlemlerle artar. Bu test gerçek dağıtık mutabakat kanıtı değildir.

## Tarayıcı kontrolü

Codex iç tarayıcısında gerçek yerel Flask sunucusuyla kontrol edildi.

- Giriş, konu önerisi önizlemesi ve kalıcı taslak kaydı başarılı.
- Mobil görünümde kabul oyu kaydı ve tartışma katkısı başarılı.
- Oy değiştirme (çekimser) ve ikinci tartışma katkısı başarılı.
- 390 px ve 334 px dar görünümde, 1440 px masaüstü görünümde
  `/proposal/new`, `/proposal/7`, `/proposal/3`, `/topic/1`, `/graph` için
  belge genişliği ekran genişliğine eşit; yatay taşma saptanmadı.
- Masaüstü genel bakış / öneri / tartışma ve mobil oylama / karar
  ekranları görsel olarak incelendi.
- Kararda “Kabul” ile “Bu karar uygulanamaz” ayrımı doğrulandı.
- Kontrol verileri yalnız yerel, Git dışında tutulan kurgusal veritabanındadır.

Fiziksel telefon kurulumu, ekran okuyucu denetimi, farklı tarayıcı matrisi,
üretim yük testi ve güvenlik denetimi yapılmadı. Otomatik Playwright işlemi
macOS işlem kısıtıyla başlamadı; arayüz kontrolleri iç tarayıcı üzerinden tamamlandı.

## GitHub

Depo API ile doğrulandı; bağlı hesabın `push: true` yetkisi göründü.
Gerçek Contents API yazımı `403 Resource not accessible by integration` döndürdü.
Yerel `git push` ise kayıtlı GitHub kimliği olmadığı için gönderemedi.
Uzak `main` üzerinde son commit doğrulanamadı. **Gönderim tamamlanmadı.**
