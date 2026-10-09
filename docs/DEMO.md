# Derste kısa demo — 5–7 dakika

**Adres:** yerel uygulama `http://127.0.0.1:5000`. Bu adres internet yayını değildir. **Tüm örnek hesapların şifresi:** `Ortak-Demo-2026!` (kurgusal).

1. **Ada / başlangıç (45 sn):** `ada` ile giriş. Müzakere adını, kişisel dashboard'u ve her kişinin bir oy hakkı olduğunu göster. İstersen ayrı kurgusal kayıt aç; gerçek ad/adres kullanma.
2. **Öneri (1 dk):** “Kuyruk kullanımı BFS sırasını nasıl etkiler?” başlığı, öğrenme sorusu, ilgili grup → Önizle → Taslağı kaydet. `yonetici` kapsam/etki/süreyi denetleyip başlatır. Oy dağılımı kapanana kadar gizlidir.
3. **Kabul ve azınlık (1 dk):** Yeni oylama 1–168 saat sürer; sunum için **Öneri 1** hazır kapanmış örneğini aç. r=0,50 katılım; çoğunluk kabulü; karşı gerekçe ve itirazı göster. **Öneri 2** katılım yetersizliğidir.
4. **Hak denetimi (1 dk):** **Öneri 3**: kabul oyları olsa da “Bu karar uygulanamaz”, R1. İnceleme hak ihlalini geçersiz kılamaz. Eski kurulumlarda R3 de görünebilir; eski seed kapanıştan sonra inceleme eklemişti, bu revizyon yeni seed'i düzeltti.
5. **Akran öğrenmesi (1 dk):** **Konu 1**: soru, açıklama, kaynak, karşı görüş ve bilirkişi danışma görüşü. `deniz` açıklamasını `ada` yararlı bulabilir; tekrar puan kazandırmaz. Geçmiş ve kaldırma gerekçesini göster.
6. **AI / tasarım (1 dk):** Demo özetinde tam kaynak alıntısı ve karşı görüş bölümü; bunun gerçek model olmadığını söyle. [Mimari](diagrams/07-architecture.svg) ve [sınıf diyagramında](diagrams/02-classes.svg) Strategy ile Chain of Responsibility'yi açıkla.
7. **Son (30 sn):** Yönetim günlüğü hash doğrulaması; iki JSON kopyası gerçek dağıtık sistem değildir. [Tek sayfalık rapor](rapor.pdf) ve [test sonuçlarını](TEST_RESULTS.md) aç.

## Sunumda doğru anlatım

- r tanımı ve kısıtlayıcı eşikler projenin seçtiği politikalardır.
- Puan öğrenme başarısını ölçmez ve oy ağırlığını değiştirmez.
- Gerçek AI, native mobil ve herkese açık canlı dağıtım yok.
- Açık örnek 7–8 yalnız seed'den itibaren 24 saat açıktır; sonra kapanmaları normaldir. Mevcut DB'yi yeniden seed ederek silmeye çalışmayın.
- Tarayıcı E2E'de süre yalnız ayrı sentetik test DB'sinde hızlandırıldı. Ürün arayüzünde erken kapatma bulunmaz.
