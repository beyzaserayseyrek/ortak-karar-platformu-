# Doğrulama sonuçları — 9 Ekim 2026

Ortam: yerel macOS, Python 3.13.5, Flask 3.1.2, SQLite. Kontroller Codex ajanı tarafından yapıldı; öğrencinin yaptığı ileri sürülmez.

## Otomatik testler

```bash
python -m unittest discover -s tests -v
```

**40 test geçti; 0 başarısız / 0 hata.** Son koşu 2,148 saniye. Bu süre uygulamanın performans ölçümü değildir. Başlangıçtaki 19 test de değişiklikten önce geçti; 21 anlamlı regresyon/sınır testi eklendi. Seed inceleme sırası düzeltildikten ve R2 beklentisi eklendikten sonra son koşu yapıldı.

- Katılımın hemen altı/eşitliği/üstü: 49/100, 50/100, 51/100; kısıtlayıcı 66/100,67/100; tam 2/3 kabul.
- Sıfır seçmen, yalnız çekimser, eşitlik, tek güncel oy, oy değiştirme, seçmen dondurma, kapanış sonrası oy reddi ve tek kapanış olayı.
- Yetki/CSRF, özel profil gizliliği, XSS kaçışlama, bilirkişi yetkisi.
- R1/R2/R3/R4 zinciri; birden fazla ihlal birlikte döner. İnceleme olsa da R1 kabul edilen kararı engeller.
- Yanlış süreyle oylama başlatmada taslağın değişmeden kalması; kalıcı gizlemeyi geçiciye çevirerek geri açma yolunun engellenmesi.
- Düzenleme geçmişi, eski içeriğe dayanan düzenleme engeli, bölüm kaldırmada sonradan gelen mesajın korunması, itiraz/yanıt yetkileri.
- Tekrarlı yararlılıkta tek puan kaynağı, kendi katkısını değerlendirme engeli, günlük puan sınırı, aynı metni tekrar ekleme reddi, bildirim.
- AI sağlayıcı hatasında oylama devamı; desteklenmeyen yapılandırmada girişin açılması; eski karşı gerekçe ve doğru kaynak sayfası; 9 sentetik çıktı durumu.

Eşleştirme: [TRACEABILITY.md](TRACEABILITY.md). AI ayrımı: [AI_EVALUATION.md](AI_EVALUATION.md).

### Testlerin kendisinin incelemesi

Beklentiler politika tanımından türetildi; uygulama çıktısı kopyalanarak beklenen sonuç üretilmedi. Süre sonu testi ilk yazıldığında seed'deki eski oyu yok sayıyordu: beklenti, mevcut oyların korunup yeni/geç oyun eklenmemesi olarak düzeltildi. SQLite test bağlantıları açık kalmayacak şekilde kapatıldı. Seed R1 senaryosunda inceleme kapanıştan önce kaydedildi; artık R1 engeli sürerken R3 yokluğu da doğrulanır. Seçilmiş testler geniş davranışları kapsar; test adedi tam kapsama veya güvenlik garantisi değildir.

## Ajanın tarayıcı kontrolleri

Codex iç tarayıcısında gerçek yerel Flask sunucusu; **ayrı sentetik SQLite dosyası**, port 5001. Mevcut kullanıcı veritabanı yeniden oluşturulmadı.

| Senaryo | Gözlenen sonuç |
|---|---|
| Kurgusal kayıt | Yeni “Sınama” hesabı oluştu; boş dashboard ve öneri bağlantısı göründü. |
| Yeni öneri | BFS başlığı/gerekçesi → Önizle → taslak 9 kalıcı kaydedildi. |
| Yönetici başlatma | 1 saat seçildi; 5 kişilik seçmen listesi sabitlendi; en az 3 katılımcı gösterildi. |
| Farklı rollerle giriş ve oy | Yönetici + Ada kabul, Deniz ret; gerekçeler kaydoldu. Oylama sürerken dağılım gizliydi. |
| Kapanış | Yalnız bu test DB'sinde deadline geçmişe alındı. Sonraki istek %60 katılım, 2 kabul /1 ret, “Uygulandı” ve konu 3 bağlantısı gösterdi. Bir saat gerçek zaman beklenmedi. |
| Kalıcı tartışma | Konu 3'e ağırlıklı graf varsayımını sorgulayan karşı gerekçe eklendi; sayfada göründü. |
| Kural engeli | Hazır seed önerisi 3 tarayıcıda “Kabul” ile “Bu karar uygulanamaz” ve R1'i birlikte gösterdi. Bu satır yeni baştan tarayıcıyla oylanmış ayrı vaka değildir. |
| Mobil / hata | 390×844 özet ekranında belge/ekran genişliği 390 px; yatay taşma yok. Kaynaksız kaynak paylaşımı hata verdi, girilen metin/tür korundu. |
| Klavye | Kayıt, öneri, önizleme, oy ve katkı adımları Enter/Space ile yürütüldü. Tam ekran okuyucu/Tab sırası denetimi yapılmadı. |
| Konsol | Kontrol sonunda tarayıcı hata günlüğünde kayıt yoktu. |

Tarayıcı aracının mouse click işlemleri bazı adımlarda etki yaratmadı; görünen durumu okuyup klavye ile devam edildi. Bu gözlem uygulamada fare hatası bulunduğu şeklinde genellenmez. Uzun süren bir dış API isteği bulunmadığından AI yükleme animasyonu senaryosu yok; sunucu sayfa yanıtı verir.

## Günlük, diyagram ve rapor

- `python scripts/verify_ledger.py --demo-tamper`: orijinal `(True, None)`, bellekte değiştirilen kopya `(False, 29)`. Asıl veri bozulmadı.
- `python scripts/replicate_ledger.py`: 56 olaylı node-a ve node-b kopyaları doğrulandı. Sayı kontrol anına aittir; gerçek ağ/mutabakat testi değildir.
- 7 SVG tarayıcıda açılıp okunabilirlik/taşma açısından incelendi. Sınıf çizgisinin kutuya girişi ve durum geçişi koşulları düzeltilerek yeniden kontrol edildi.
- `rapor.pdf`: **1 sayfa, A4 (595,28 × 841,89 pt)**. Türkçe metinler ve alt bilgi görsel olarak kontrol edildi. PDF link annotasyonu tam repository URL'sidir; okunabilir metinle eşleşir. HTML ve PDF aynı kaynak metninden üretilir.
- `git diff --check` temiz. Yerel DB, özel anahtar, kaynak ders PDF'leri ve ortam dosyaları teslim ağacına dahil edilmedi.

## Yapılmayan kontroller ve sınırlar

Gerçek AI/API testi, fiziksel telefon PWA kurulumu, çevrimdışı gerçek cihaz testi, ekran okuyucu incelemesi, çok tarayıcı matrisi, yük testi, bağımsız güvenlik denetimi, kullanıcı araştırması ve öğrenme başarı ölçümü yapılmadı. GitHub Actions sonucu bu yerel test sonucu yerine geçirilmez; bu rapor CI'nin geçtiğini iddia etmez.

## GitHub kaynak doğrulaması

Kod ve test revizyonu `main` dalında yeniden okunarak doğrulandı:
[8fef64359a4306e91e35de47cf44f44326a75259](https://github.com/beyzaserayseyrek/ortak-karar-platformu-/commit/8fef64359a4306e91e35de47cf44f44326a75259).
Yerel/uzak kod ağacı: `815e6363c92552a0fa27b07a19727568c39c07b8`.
Belgeler ve rapor bunu izleyen ayrı commit'te teslim edilir; son commit doğrulaması teslim yanıtında verilir. Force push kullanılmadı.
