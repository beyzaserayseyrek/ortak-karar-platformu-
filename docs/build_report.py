"""Rebuild one-page A4 report and matching HTML. Optional dependency: reportlab."""
import os
from pathlib import Path
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

HERE=Path(__file__).parent
URL='https://github.com/beyzaserayseyrek/ortak-karar-platformu-'
SECTIONS=[
('Amaç ve teknoloji', 'Müzakere, üniversite çalışma gruplarında öğrenme sorularını, kaynakları ve gerekçeli kararları bir araya getiren mobil uyumlu web prototipidir. Python/Flask, SQLite, Jinja, HTML/CSS ve JavaScript kullanır. Kullanıcı araştırması veya öğrenme başarısı ölçümü yapılmamıştır.'),
('Kalıcı iş akışı', 'Kayıt/giriş → konu, alt konu veya düzenleme önerisi → yönetici kapsam incelemesi → sabit seçmenli oylama → sonuç ve kural denetimi → uygulanabilir konuda tartışma. Soru, kaynak, akran açıklaması ve karşı gerekçeler saklanır; düzenleme geçmişi korunur. Yararlı katkı tek kaynak üzerinden puanlanır; puan oy ağırlığını değiştirmez. İtiraz, danışma amaçlı bilirkişi görüşü, bildirim ve sınırlı ilişki grafı vardır.'),
('Projenin seçtiği politika: r = 0,50', 'r minimum katılım oranıdır; varsayılanı 0,50’dir. Açılışta seçmen listesi ve r sabitlenir. Yeterli katılımda kabul/(kabul+ret) > 0,50 gerekir. Çekimser katılıma dahildir; kabul oranının paydasına dahil değildir. Eşitlik ve yalnız çekimser oylar reddedilir; seçmen yoksa katılım yetersizdir. Her ilgili grup ayrıca eşiği sağlamalıdır.'),
('Kabul ile uygulanabilirlik ayrımı', 'R1 özel bilgileri yayımlamayı, R2 grubun katılım hakkını kaldırmayı engeller. Kısıtlayıcı kararlarda en az max(r, 0,67) katılım, en az 2/3 kabul ve farklı yöneticinin gerekçeli incelemesi gerekir. Çoğunluk bu kuralları aşamaz. İçerik gerekçeyle gizlenir; kalıcı gizleme, geçici gizleme üzerinden geri açılamaz. Etki beyanının doğruluğu insan incelemesi ister.'),
('Gerçekten uygulanan tasarım desenleri', 'Strategy: standart ve kısıtlayıcı katılım politikaları aynı arayüzle seçilir. Chain of Responsibility: R1→R2→R4→R3 zinciri bütün ihlalleri toplar. HTTP, oylama, depolama ve AI sınırı ayrı modüllerdedir. Adapter, Observer, Facade ve State değerlendirilmiş; somut ihtiyaç olmadığı için eklenmemiştir. Yedi SVG diyagram ve düzenlenebilir kaynak docs/diagrams altındadır.'),
('AI, PWA ve olay kaydı sınırları', 'AI yardımcıları yerel tam alıntı ve anahtar sözcük demosudur; dış model yoktur. Tür başına sayfalama karşı gerekçelere yer ayırır; kaynak/kapsam/metin doğrulanır, hatada yerel demoya dönülür. AI oy, puan veya gizleme kararı vermez. Hash bağlantılı günlük ve iki yerel dosya kopyası gerçek dağıtık mutabakat değildir. PWA manifesti ve çevrimdışı uyarısı vardır; çevrimdışı işlem ve native uygulama yoktur.'),
('Doğrulama ve kalan işler', '40 otomatik test geçti. Ajan, tarayıcıda kurgusal kayıt, öneri, oylama, kabul, tartışma ve hazır R1 engelini kontrol etti; test süresi ayrı sentetik DB’de hızlandırıldı. 390 px mobil özet ve form hatası denetlendi. Gerçek model/API, fiziksel cihaz kurulumu, yük testi ve bağımsız güvenlik denetimi yapılmadı. Üretim dağıtımı, e-posta/kimlik doğrulama ve parola kurtarma eksiktir.'),
('Yapay zekâ kullanım beyanı', 'Bu revizyonda Codex kaynak incelemesi, kod/refaktör, test üretimi ve çalıştırılması, tarayıcı kontrolü, diyagram ve belge hazırlığında kullanıldı. Bu inceleme ve testleri öğrencinin yaptığı iddia edilmez. Tasarımın açıklanması ve akademik teslim sorumluluğu öğrenciye aittir.'),
]

def font_path(env, names):
    if os.getenv(env): return os.environ[env]
    for name in names:
        if Path(name).is_file(): return name
    raise SystemExit(f'Türkçe font bulunamadı; {env} ile TTF dosyası belirtin.')
regular=font_path('REPORT_FONT',['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/arial.ttf'])
bold=font_path('REPORT_FONT_BOLD',['/System/Library/Fonts/Supplemental/Arial Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf'])
pdfmetrics.registerFont(TTFont('Report',regular));pdfmetrics.registerFont(TTFont('ReportBold',bold))
navy=colors.HexColor('#172b4d');teal=colors.HexColor('#0f766e')
body=ParagraphStyle('body',fontName='Report',fontSize=9.25,leading=12.2,textColor=navy,spaceAfter=3)
heading=ParagraphStyle('heading',fontName='ReportBold',fontSize=10,leading=12.8,textColor=teal,spaceBefore=7,spaceAfter=3)
title=ParagraphStyle('title',fontName='ReportBold',fontSize=27,leading=32,textColor=navy)
small=ParagraphStyle('small',parent=body,fontSize=8.2,leading=11)
story=[Paragraph('Müzakere',title),Paragraph('Akran öğrenmesi ve katılımcı karar alma · Ders revizyonu · 9 Ekim 2026',small),Spacer(1,7),HRFlowable(width='100%',thickness=2,color=teal)]
for h,p in SECTIONS:story += [Paragraph(escape(h),heading),Paragraph(escape(p),body)]
story += [Spacer(1,6),HRFlowable(width='100%',thickness=.5,color=teal),Spacer(1,6),Paragraph('Canlı demo: yayımlanmadı. Yerel önizleme internet yayını değildir.',small),Paragraph(f'Kaynak kod ve kurulum: <link href="{URL}" color="#0f766e">{URL}</link>',small)]
SimpleDocTemplate(str(HERE/'rapor.pdf'),pagesize=A4,rightMargin=39,leftMargin=39,topMargin=32,bottomMargin=30,title='Müzakere — Ders Revizyon Raporu',author='Müzakere proje belgeleri').build(story)
html='''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Müzakere · Tek sayfalık rapor</title><style>@page{size:A4;margin:12mm}body{font:9.25pt/1.32 Arial,sans-serif;color:#172b4d;max-width:180mm;margin:20px auto;padding:0 12px}h1{font-size:27pt;margin:0}h2{color:#0f766e;font-size:10pt;margin:9pt 0 3pt}p{margin:0 0 4pt}header{border-bottom:2px solid #0f766e;padding-bottom:8pt}footer{border-top:1px solid #0f766e;margin-top:8pt;padding-top:6pt;font-size:8.2pt}a{color:#0f766e}</style><header><h1>Müzakere</h1><p>Akran öğrenmesi ve katılımcı karar alma · Ders revizyonu · 9 Ekim 2026</p></header>'''
for h,p in SECTIONS: html+=f'<h2>{escape(h)}</h2><p>{escape(p)}</p>'
html+=f'<footer><p>Canlı demo: yayımlanmadı. Yerel önizleme internet yayını değildir.</p><p>Kaynak kod ve kurulum: <a href="{URL}">{URL}</a></p></footer></html>'
(HERE/'rapor.html').write_text(html)
print('rapor.pdf and rapor.html generated')
