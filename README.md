# Ortak — Akran öğrenmesi ve ortak karar platformu

Türkçe, mobil uyumlu bir üniversite ders projesi. Öğrenciler öğrenme soruları önerir, sabit seçmen listesiyle oy kullanır, kabul edilen konularda kaynak ve gerekçeli akran açıklamaları paylaşır.

**Teslim durumu:** Kaynak kod, testler, kurulum dosyaları ve rapor GitHub `main` dalına gönderildi. Kaynak teslim commit'i: `226ebe2703b3ee314602d42653be62ff570ef0ac`. Yerel ve uzak Git ağaçları eşleştirilerek dosya bütünlüğü doğrulandı. Sonraki belge commit'i rapordaki bekleme notunu kaldırır.

**Kaynak deposu:** https://github.com/beyzaserayseyrek/ortak-karar-platformu-

**Canlı demo:** Yayımlanmadı. `http://127.0.0.1:5000` yalnız yerel çalıştırma adresidir.

## Kurulum ve başlatma

Python 3.11+ önerilir (test ortamı: Python 3.13.5). Node.js uygulama için gerekmez.

```bash
# Bu klasörde:
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env
python seed.py
python app.py
```

Tarayıcıda http://127.0.0.1:5000 açılır. Windows'ta `.env.example` dosyasını `.env` olarak kopyalayın. `seed.py` yalnız boş veritabanında çalışır; mevcut veriyi silmez. Normal yeniden başlatmada yalnız `python app.py` gerekir. Yerel SQLite verileri `instance/ortak.sqlite` içinde kalır.

`SECRET_KEY` boş bırakılırsa yalnız bu makinede, `instance/session.key` altında rastgele anahtar oluşturulur (dosya izinleri 0600). Dış ortama kurarken özgün güçlü bir değer ayarlayın. `DATABASE`, `HOST`, `PORT`, `COOKIE_SECURE`, `AI_PROVIDER` alanları `.env.example` içindedir. HTTPS kurulumunda `COOKIE_SECURE=1` olmalıdır. Flask geliştirme sunucusu ve örnek hesaplar halka açık üretim kullanımı için değildir.

## Örnek hesaplar

Tamamı kurgusaldır. Ortak demo şifresi: **`Ortak-Demo-2026!`**. Bu bir hizmet anahtarı veya gerçek kullanıcının parolası değildir; yalnız `seed.py` tarafından yerel oluşturulur.

| Kullanıcı adı | Rol | Grup |
|---|---|---|
| `ada`, `deniz`, `ege` | Üye | Algoritmalar |
| `yonetici` | Yönetici / moderatör | Algoritmalar |
| `inceleme` | İkinci yönetici | İstatistik |
| `bilirkişi` | Bilirkişi | İstatistik |
| `selin`, `can` | Üye | İstatistik |

Kayıt formu ad, doğum tarihi, adres, takma ad, grup ve giriş bilgilerini alır. Üyelere yalnız takma ad, grup ve rol bilgisi gösterilir. Şifreler Werkzeug scrypt ile hash'lenir. Özel profil alanları veritabanında şifrelenmez; dosya erişimini koruyun ve sunumda gerçek bilgi kullanmayın. Roller kendi kendine kayıtla yükseltilemez.

## Ders gösterimi — temel akış

1. `ada` ile girin veya kurgusal yeni hesap oluşturun. **Konu öner** → başlık, öğrenme sorusu, kategori, grup, etiket ve etki → **Önizle** → taslak kaydet.
2. `yonetici` ile **Yönetim → İnceleme bekleyen taslaklar** bölümünü açın. İlgili grupları ve beyan edilen etkiyi inceleyin, süreyi seçin ve başlatın. Süre 1–168 saattir; web arayüzü erken kapatamaz.
3. İlgili grubun açılış anındaki üyeleri oy kullanır. Oy süre bitene kadar değiştirilebilir. Katılım görünür; oy dağılımı ve başkalarının gerekçeleri kapanınca açılır.
4. Süre dolunca bir sonraki oturumlu istekte işlem atomik olarak sonuçlandırılır. Kabul, uygulama için yeterli değildir: grup katılımı ve kurallar ayrıca denetlenir.
5. Uygulanan konuya girip öğrenme sorusu, kaynak URL'si, açıklama veya karşı gerekçe paylaşın. Yararlı değerlendirmesi puanı bir kez kazandırır. Düzenleme geçmişi kalır.

Beklemeden sunum için seed verilerindeki kapanmış kararları kullanın:

| Kayıt | Gösterim |
|---|---|
| Öneri 1 | Yeterli katılım, kabul, azınlık gerekçesi ve itiraz |
| Öneri 2 | Katılım yetersizliği |
| Öneri 3 | Oybirliğine rağmen R1 nedeniyle uygulanamayan karar |
| Öneri 4 | Kabul edilmiş alt konu |
| Öneri 5 | Kabul edilmiş düzenleme; eski / yeni karşılaştırması |
| Öneri 6 | Sıkı eşik ve bağımsız incelemeyle mesaj gizleme |
| Öneri 7–8 | Açık oylamalar |
| Konu 1 | Sorular, kaynaklar, açıklamalar, karşı görüş, uzman görüşü, demo özet |

## Oylama ve hak politikası

**Nihai proje kararı: r minimum katılım oranıdır; varsayılan r = 0,50.** Bu, proje kapsamında seçilmiş politikadır; hocanın doğrulanmış tanımı olduğu iddia edilmez.

- Katılım = oy kullanan uygun kişi / açılışta sabitlenen uygun kişi.
- Katılım `< r` ise katılım yetersiz. Seçmen yoksa da yetersiz.
- Kabul / (kabul + ret) `> 0,50` ise çoğunluk kabulü. Eşitlikte ret.
- Çekimser katılıma dahil; kabul oranının paydasına dahil değil. Yalnız çekimser varsa ret.
- Örnek: 20 seçmen, 6 kabul + 3 ret + 1 çekimser → katılım %50; kabul oranı 6/9 ≈ %66,7 → kabul. Kurallar ayrıca sağlanmalı.
- Her ilgili grubun katılımı ayrıca aynı eşiğe ulaşır; azınlık grubu tümüyle devre dışı bırakılarak karar uygulanamaz.
- Hak kısıtlayan / içerik gizleyen kararlarda katılım en az `max(r, 0,67)`, kabul oranı en az `2/3`, öneri sahibinden farklı yöneticinin gerekçeli incelemesi gerekir. Eşikler proje politikasıdır.
- Yönetici kapsamı onaylar; öneri sahibi bireysel seçmen seçemez. Kullanıcı grubu kayıt sırasında seçilir, arayüzde sonradan değiştirilemez. Kimlik / gerçek grup üyeliği doğrulaması yapılmadığı için çoklu sahte hesap saldırısına tam koruma yoktur.
- Puanlar hiçbir zaman oy ağırlığını değiştirmez.

Gerekçeler ve itirazlar kararın yanında kalır. Yönetici itiraza yanıt verebilir; kabul edilmiş kararın içeriği bir yanıtla değiştirilmez, yeni oylama gerekir. Acil gizleme gerekçesiyle kayıt oluşturulur ve kaldırma incelemesi taslağı açılır. Yönetici geçici gizlemeyi gerekçeyle kaldırabilir. Kabul edilmiş kaldırma içeriği silmez; normal görünümden gizler. Gizli içerik ve geçmiş yalnız yöneticilere açıktır.

## Teknoloji ve mimari

- **Python / Flask:** Okunabilir sunucu rotaları, sunucu tarafı HTML ve yetki denetimi.
- **SQLite:** Kurulum gerektirmeyen kalıcı ilişkisel veri; yabancı anahtarlar, tek oy / yararlı değerlendirmesi kısıtları.
- **Jinja / HTML / CSS / az miktarda JavaScript:** Türkçe duyarlı arayüz, önizleme, benzer başlık uyarısı, klavye odağı, durum metinleri. PWA manifesti ve çevrimdışı bağlantı uyarısı.
- `app.py`: HTTP rotaları, yetki, veri işlemleri ve kapanış akışı.
- `policy.py`: Deterministik oy hesabı, R1–R4 ve hash doğrulaması.
- `schema.sql`: İlişkiler, sürümler, sabit seçmenler, denetim ve puan kayıtları.
- `ai.py`: Değiştirilebilir `SummaryProvider` arayüzü ve yerel `DemoProvider`.
- `docs/ontology.json`: Kavramlar, ilişkiler, değerlendirilebilir kural tanımları. SQL yabancı anahtarları ile uygulanır; tam RDF/OWL çıkarım motoru değildir.

Yazma istekleri SQLite `BEGIN IMMEDIATE` işlemlerinde yürür. CSRF, HttpOnly/SameSite oturum çerezi, içerik güvenlik politikası, HTML kaçışlama ve URL şema denetimi vardır. Oturum süresi 1 saattir. Kimlik bilgileri dış servise gönderilmez.

## Özellikler ve katkı puanı

- Kalıcı kayıt / giriş; üye, yönetici ve bilirkişi rolleri.
- Taslak → oylama → kabul / ret / yetersiz; alt konu ve sürüm karşılaştırmalı düzenleme. Eski sürüme dayanan çakışan teklif uygulanmaz.
- Kabul edilen uygulanabilir öneri: +5; başka üyenin yararlı bulduğu açıklama / kaynak / karşı gerekçe: +3. Her kaynak olayı yalnız bir defa puanlanır. Günlük UTC sınırı 20; sınır aşılırsa yalnız kalan puan verilir. Kendi katkısını değerlendirme, aynı metni tekrar paylaşma engellenir; günlük 40 mesaj sınırı vardır.
- Dashboard: bekleyen oylar, kendi önerileri, bildirimler, puan, oy geçmişi ve itirazlar. Bilirkişi görüşleri ilgili konuda; bilirkişiye talepler bildirim olarak gider.
- Başlık arama, grup / durum filtresi, konu ve oylama sayfalaması; tartışma 20 mesajlık sayfalarda.
- Grup filtreli ilişki şeması, açılır düğüm bilgisi ve eşdeğer erişilebilir liste. Puan sıralaması yoktur.
- İki yöneticinin ayrı onayıyla r değişikliği; mevcut oylamanın r değeri değişmez. Sabit R1–R4 değişikliği kod incelemesi ve test gerektirir; sıradan konu oylaması yönetmeliği değiştiremez.

## Yapay zekâ, olay günlüğü ve PWA sınırları

**Demo AI:** Dış model çağrısı yoktur. Özet, son 12 görünür mesajdan bağlantılı alıntıdır; karşı görüşler de aynı kuralla alınır. Görüş dağılımının eksiksiz veya anlamsal özeti değildir. Gerçek sağlayıcı eklemek için `SummaryProvider` uygulanmalı; yalnız görünür mesajların `id`, `body`, `kind` alanları sınırı geçer. `AI_PROVIDER=demo` desteklenir. Gerçek API anahtarı gerekmez ve örnek dosyada bulunmaz. Benzer konu uyarısı başlık kelime eşleşmesidir. Demo sağlayıcı anahtar sözcüklerle sınıflandırma ve olası kural çelişkisi ipuçları sunar; gerçek model analizi değildir. Kesin kurallar ayrı ve deterministiktir.

**Olay günlüğü:** Öneri, oy işlemi, sonuç, kural denetimi, düzenleme ve gizleme olayları hash bağlantılıdır. Olay türü, nesne kimliği, zaman, önceki hash tutulur; mesaj, özel profil bilgisi veya oy tercihi yazılmaz. Günlük uygulama seviyesinde eklemelidir; SQLite tetikleyicileri güncelleme / silmeyi engeller. Tam veritabanını kontrol eden saldırgan zinciri yeniden yazabilir veya son kısmını silebilir. Dış güvenilir hash sabitlemesi yoktur; bu çözüm tam değiştirilemezlik garantisi vermez.

```bash
python scripts/verify_ledger.py --demo-tamper
python scripts/replicate_ledger.py
```

İlk komut orijinali doğrular, yalnız bellekteki kopyayı bozup saptar. İkinci komut `instance/node-a` ve `node-b` altında aynı olayların iki yerel dosya kopyasını doğrular. Bu bağımsız çalışan ağ düğümleri veya gerçek dağıtık mutabakat değildir.

**PWA:** Manifest ve service worker vardır. Çevrimdışıyken anlaşılır uyarı gösterir; özel sayfalar ve oylar önbelleğe alınmaz. Çevrimdışı oy / mesaj yoktur. Tarayıcıya göre kurulum desteği değişir; mobil cihazda yükleme ayrıca denenmelidir. Ayrı native uygulama kapsam dışıdır; dersteki “uygulama + web sitesi” beklentisi ayrıca doğrulanmalıdır.

## Test ve doğrulama

```bash
python -m unittest discover -s tests -v
python scripts/verify_ledger.py --demo-tamper
```

Testler geçici SQLite dosyası ve kurgusal veriler kullanır. Oy hesabı sınırları, tek oy güncellemesi, CSRF / yetki / seçmen denetimi, donmuş seçmen listesi, özel bilgilerin gizliliği, çoğunluğa karşı kural engeli, puan tekilliği, geçmiş / XSS kaçışlama, zincir bozulması, uçtan uca temel akış, iki yönetici politikası, acil gizleme ve çakışan düzenleme denetlenir. Sonuçlar `docs/TEST_RESULTS.md` içinde.

## Bilinen sınırlamalar

Bu bir ders prototipidir. E-posta doğrulama, şifre sıfırlama, giriş denemesi hız sınırlaması, üyelik onayı, çoklu hesap engeli, at-rest profil şifreleme, yedekleme yönetimi, üretim dağıtımı ve yük testi yoktur. Kural motoru serbest metni semantik olarak okuyamaz; etki alanındaki yanlış beyanı yönetici yakalamalıdır. Moderatörün kötüye kullanımını tamamen önlemez; azınlık haklarını kesin garanti etmez.

Konu takibi açıldığında yeni katkılar dashboard bildirimi üretir. Soru ve kaynak akışı çalışır; öneri taslağını sonradan düzenleme ekranı yoktur. Metin araması yalnız başlıklardadır. Graf görünümü sınırlı ilişki şemasıdır. Mesaj veya öneri anındaki tüm tartışma bölümü için kaldırma oylaması vardır; sonradan eklenen mesajlar bölüm önerisinin kapsamı dışında kalır. Yeni grup oluşturma ve rol atama için yönetim arayüzü yoktur. Otomatik zamanlayıcı yerine sonraki oturumlu istekte kapanış yapılır. Geniş listelerin bir kısmı uygulama içinde filtrelendiğinden büyük ölçeğe uygun değildir.

## GitHub'a gönderme

`.gitignore`, `.env`, yerel veritabanı, anahtarlar ve üretilen dosyaları dışlar. `seed.py` yalnız kurgusal hesaplar içerir. Göndermeden önce `git status --short` ve `git diff --cached` kontrol edilir. Gönderim GitHub bağlantısı üzerinden tamamlandı. Yerel terminal için ayrıca Git kimlik doğrulaması gerekebilir.

GitHub bağlantısının hedef depo için **Contents: read and write** izni gerekir. Hesabın yönetici olması entegrasyonun yazma izni olduğu anlamına gelmez. Entegrasyon erişimini güncelledikten veya Git için kendi hesabınla kimlik doğruladıktan sonra:

```bash
git remote -v
git fetch origin
# Uzak main varsa önce incele; farklı geçmişleri körlemesine birleştirme.
git log --oneline --all --decorate -8
git push -u origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Son iki SHA eşleşmeden gönderim tamamlanmış sayılmaz. Uzak dalda yeni değişiklik varsa önce koruyarak birleştirin; **force push kullanmayın**. İlk gönderim doğrulandı; rapor ve README teslim durumu güncellendi.

## Rapor

`docs/rapor.pdf`: Türkçe tek A4; en altta okunabilir, tıklanabilir gerçek repository adresi. `docs/rapor.html`: tarayıcıdan açılabilir eşdeğer rapor. GitHub kaynak adresi canlı uygulama adresi olarak sunulmaz.
