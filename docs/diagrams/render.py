"""Editable, dependency-free SVG diagrams. Run: python docs/diagrams/render.py.
UML notation is drawn explicitly; boxes do not imply nonexistent Python classes.
"""
from pathlib import Path
from html import escape
OUT=Path(__file__).parent
class SVG:
    def __init__(self,name,title,subtitle,w=1200,h=800):
        self.name=name;self.w=w;self.h=h
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M1,1 L9,5 L1,9" fill="none" stroke="#172b4d"/></marker><marker id="triangle" markerWidth="13" markerHeight="13" refX="12" refY="6" orient="auto"><path d="M1,1 L12,6 L1,11 Z" fill="white" stroke="#172b4d"/></marker></defs>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#172b4d;font-size:16px}.title{font-size:30px;font-weight:bold}.sub{font-size:15px;fill:#526479}.small{font-size:14px}.bold{font-weight:bold}line,path,rect,ellipse,circle{vector-effect:non-scaling-stroke}</style>',f'<rect width="{w}" height="{h}" fill="#f7f9fc"/>']
        self.text(35,47,title,'title');self.text(35,78,subtitle,'sub')
    def text(self,x,y,lines,cls='',anchor='start'):
        for i,t in enumerate(lines.split('\n')):
            self.parts.append(f'<text x="{x}" y="{y+i*23}" class="{cls}" text-anchor="{anchor}">{escape(t)}</text>')
    def box(self,x,y,w,h,title,body='',rounded=True):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{12 if rounded else 0}" fill="white" stroke="#0f766e" stroke-width="1.6"/>')
        self.text(x+14,y+28,title,'bold')
        if body:self.text(x+14,y+55,body)
    def line(self,x1,y1,x2,y2,dash=False,end='arrow'):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#172b4d" stroke-width="1.4"'+(' stroke-dasharray="6 5"' if dash else '')+(f' marker-end="url(#{end})"' if end else '')+'/>')
    def path(self,points,dash=False,end='arrow'):
        d='M'+' L'.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<path d="{d}" fill="none" stroke="#172b4d" stroke-width="1.4"'+(' stroke-dasharray="6 5"' if dash else '')+(f' marker-end="url(#{end})"' if end else '')+'/>')
    def actor(self,x,y,name):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="13" fill="white" stroke="#172b4d"/>')
        for a,b,c,d in [(x,y+13,x,y+50),(x-25,y+28,x+25,y+28),(x,y+50,x-22,y+78),(x,y+50,x+22,y+78)]:self.line(a,b,c,d,end='')
        self.text(x,y+102,name,'bold','middle')
    def ellipse(self,x,y,w,h,title):
        self.parts.append(f'<ellipse cx="{x}" cy="{y}" rx="{w/2}" ry="{h/2}" fill="white" stroke="#0f766e" stroke-width="1.5"/>')
        self.text(x,y-8 if '\n' in title else y+5,title,'','middle')
    def save(self):
        self.text(35,self.h-22,'Müzakere · Kaynak: bu depodaki uygulama · Ayrıntılar: docs/DESIGN.md','small')
        (OUT/(self.name+'.svg')).write_text('\n'.join(self.parts)+ '</svg>')

# 1. Use case: actors outside system, association lines without arrowheads.
s=SVG('01-use-case','Kullanım durumları','Aktörler kodun rolleridir. Yönetici ve bilirkişi, üye işlevlerini de kullanır.',1200,800)
s.parts.append('<rect x="280" y="110" width="660" height="610" fill="none" stroke="#526479"/>')
s.text(300,136,'Müzakere web uygulaması','bold')
s.actor(130,230,'Üye');s.actor(1060,205,'Yönetici');s.actor(1060,545,'Bilirkişi');s.actor(130,530,'Ziyaretçi')
for y,title in [(185,'Konu / alt konu / düzenleme\nönerisi oluştur'),(290,'Oy kullan / değiştir'),(395,'Tartış / kaynak paylaş /\nyararlı değerlendir'),(500,'Gerekçeyi incele / itiraz et'),(635,'Kayıt ol / giriş yap')]:
 s.ellipse(485,y,330,74,title);s.line(155,290,320,y,end='') if y!=635 else s.line(155,590,320,y,end='')
s.ellipse(790,245,250,80,'Kapsamı onayla /\noylamayı aç');s.line(1035,260,915,245,end='')
s.ellipse(790,380,250,80,'İncele / geçici gizle /\nitiraza yanıt ver');s.line(1035,260,915,380,end='')
s.ellipse(790,550,250,80,'Danışma görüşü ver');s.line(1035,600,915,550,end='')
s.text(300,704,'R1–R4 denetimi kapanışta sistemce yürütülür; ayrı insan aktör değildir.','small');s.save()

# 2. Actual classes/protocols; hollow triangle for realization/inheritance.
s=SVG('02-classes','Gerçek Python sınıfları ve arayüzleri','Kavramsal kullanıcı / konu sınıfları yoktur; bunlar SQL tablolarıdır (bkz. graf modeli).',1400,990)
def cls(x,y,w,h,title,fields,methods):
 s.box(x,y,w,h,title,rounded=False);s.line(x,y+40,x+w,y+40,end='');s.text(x+12,y+64,fields,'small');off=y+82+23*(len(fields.split('\n'))-1);s.line(x,off,x+w,off,end='');s.text(x+12,off+24,methods,'small')
cls(50,140,340,150,'«Protocol» VotingPolicy','policy.py','+ threshold(r): float\n+ evaluate(choices, eligible, r): dict')
cls(50,380,340,150,'StandardVotingPolicy','policy.py','+ threshold(r): r\n+ evaluate(...): tally(...)')
cls(50,630,340,135,'RestrictiveVotingPolicy','policy.py','+ threshold(r): max(r, .67)')
s.line(220,380,220,290,True,'triangle');s.text(230,335,'yapısal gerçekleştirme','small')
s.line(220,630,220,530,False,'triangle');s.text(230,583,'kalıtım','small')
cls(500,140,350,150,'RuleContext','+ proposal: object\n+ group_rates: list[float]\n+ counts: dict','')
cls(500,395,350,185,'RuleHandler','+ code: str\n+ fails: Callable\n+ successor: RuleHandler | None','+ check(context): list[str]')
s.line(670,395,670,290,True);s.text(680,338,'parametre','small')
s.path([(850,455),(900,455),(900,550),(850,550)],end='arrow');s.text(905,492,'0..1','small');s.text(862,585,'successor','small')
s.text(510,642,'Zincir nesneleri: R1 → R2 → R4 → R3','small');s.text(510,672,'Her düğüm kendi koşulunu denetler;\nih­lalde de sonraki düğüme aktarır.','small')
cls(990,140,355,150,'«Protocol» SummaryProvider','ai.py','+ summarize(messages, topic,\n  candidates): dict')
cls(990,365,355,130,'DemoProvider','ai.py','+ summarize(...): dict')
cls(990,590,355,130,'UnavailableProvider','ai.py','+ summarize(...): raises')
s.line(1100,365,1100,290,True,'triangle')
s.path([(1345,650),(1370,650),(1370,220),(1345,220)],True,'triangle')
cls(550,775,460,145,'SummaryService','+ provider: SummaryProvider','+ summarize(...): validated dict / fallback\n+ validate(result, messages, candidates)')
s.path([(945,775),(945,320),(990,250)],end='arrow');s.text(705,756,'sağlayıcı yapıcıdan enjekte edilir','small')
s.text(45,854,'Kesik + boş üçgen: Protocol uyumu\nDüz + boş üçgen: kalıtım\nOk: kullanım / yönlü ilişki','small');s.save()

# Sequence helper: lifelines, ordered messages, return dashed.
def sequence(name,title,subtitle,heads,steps,h=1000):
 s=SVG(name,title,subtitle,1300,h);xs=[100+i*275 for i in range(len(heads))]
 for x,label in zip(xs,heads):
  s.box(x-75,115,190,65,label);s.line(x+20,180,x+20,h-100,True,end='')
 for y,a,b,text,ret in steps:
  xa,xb=xs[a]+20,xs[b]+20
  if a==b:s.path([(xa,y),(xa+100,y),(xa+100,y+35),(xa,y+35)]);s.text(xa+30,y-12,text,'small')
  else:s.line(xa,y,xb,y,ret);s.text(min(xa,xb)+12,y-13,text,'small')
 s.save()
sequence('03-proposal-sequence','Öneriden kalıcı tartışmaya','Kapanış erken yapılamaz. Süre dolduktan sonraki oturumlu istek prepare() üzerinden kapatır.',
 ['Üye / Yönetici','app.py rotaları','voting.py / policy','storage / SQLite'],[
 (230,0,1,'Üye: POST /proposal/new + CSRF',False),(280,1,3,'taslak INSERT + proposal_created',False),
 (330,0,1,'Yönetici: POST /start (grup / etki / süre)',False),(380,1,2,'start_voting(pid, hours)',False),
 (430,2,3,'seçmen listesi + r + deadline sabitlenir',False),(485,0,1,'Uygun üye: POST /vote',False),
 (530,1,3,'tekil oy UPSERT + event',False),(600,0,1,'Süre sonrası oturumlu GET',False),
 (645,1,2,'BEGIN IMMEDIATE; close_voting(pid)',False),(695,2,2,'policy.evaluate → check_rules',False),
 (770,2,3,'karar; uygunsa konu / sürüm / puan',False),(815,2,3,'olaylar + bildirimler (prepare commit eder)',False),
 (865,1,0,'karar gerekçesi + konu bağlantısı',True),(920,0,1,'POST /topic/<id>/message → kalıcı katkı',False)],1050)
sequence('04-blocked-sequence','Kabul edildi; uygulanması engellendi','Somut senaryo: effect=publish_private; yeterli katılım ve kabul çoğunluğu var.',
 ['Oturumlu üye','prepare / close','Politika / kural zinciri','SQLite'],[
 (230,0,1,'Süre sonrası GET /proposal/<id>',False),(290,1,3,'seçmenler, oylar, öneri okunur',False),
 (350,1,2,'RestrictiveVotingPolicy.evaluate(...)',False),(410,2,1,'status=accepted (oylama sonucu)',True),
 (470,1,2,'check_rules(proposal, rates, counts)',False),(530,2,2,'R1 başarısız → R2 → R4 → R3',False),
 (610,2,1,'violations=[R1, ...]',True),(670,1,3,'status=accepted, applied=0, decision JSON',False),
 (730,1,3,'vote_result + rule_check + bildirimler',False),(805,1,0,'“Bu karar uygulanamaz” + R1 gerekçesi',True)],940)

s=SVG('05-lifecycle','Öneri ve karar yaşam döngüsü','Durum ile uygulanabilirlik ayrı alanlardır. Alt kutular görsel bileşiktir; yeni SQL durumları değildir.',1250,830)
s.parts.append('<circle cx="80" cy="195" r="10" fill="#172b4d"/>');s.line(90,195,150,195)
s.box(150,150,230,90,'draft','Öneri kaydedildi');s.line(380,195,525,195);s.text(393,163,'admin / start','small')
s.box(525,150,260,90,'voting','Seçmen + r + süre sabit');s.path([(650,150),(650,113),(810,113),(810,190),(785,190)]);s.text(835,135,'oy kullan / değiştir\n[süre devam ediyor]','small')
s.line(650,240,650,335);s.text(675,295,'[deadline doldu] / close_voting','small')
s.parts.append('<path d="M650,335 L690,375 L650,415 L610,375 Z" fill="white" stroke="#172b4d"/>')
s.box(55,465,300,100,'insufficient','Seçmen yok / katılım yetersiz');s.path([(610,375),(205,375),(205,465)]);s.text(80,358,'[katılım koşulu sağlanmadı]','small')
s.box(450,465,320,100,'rejected','Eşitlik / yalnız çekimser / ret');s.line(650,415,650,465);s.text(395,423,'[katılım yeterli;\nçoğunluk yok]','small')
s.box(880,465,310,100,'accepted','Oy çoğunluğu kabul etti');s.path([(690,375),(1035,375),(1035,465)]);s.text(895,330,'[katılım yeterli ve\nkabul > ret]','small')
s.box(500,660,330,85,'applied = 0','Kural / sürüm engeli');s.box(880,660,310,85,'applied = 1','Etki uygulandı');s.path([(970,565),(970,610),(665,610),(665,660)]);s.text(545,601,'[ihlaller var / eski düzenleme]','small');s.line(1060,565,1060,660);s.text(1070,611,'[engel yok]','small')
s.text(45,700,'Kapanan karara itiraz eklenebilir.\nİtiraz mevcut kararı değiştirmez;\nyeni karar için yeni öneri gerekir.','small');s.save()

s=SVG('06-graph','Kavramsal veri ve ilişki grafı','Bu kutular SQL varlıklarıdır; Python sınıf diyagramı değildir. Ok yönü yabancı anahtar / ilişki yönüdür.',1250,860)
s.box(55,140,290,120,'users · kullanıcı','nickname, role, group_id\nÖzel alanlar grafa çıkmaz');s.box(490,140,280,120,'groups · grup','id, name');s.line(345,195,490,195);s.text(365,178,'N → 1','small')
s.box(490,360,280,120,'topics · konu','title, group_ids, parent\nproposal_id');s.line(635,360,635,260);s.text(645,311,'N ↔ N · JSON grup kimlikleri','small')
s.box(55,360,290,120,'messages · katkı','author, topic_id, kind\nbody, hidden, reply_to');s.line(200,360,200,260);s.text(210,310,'N → 1 · yazar','small');s.line(345,417,490,417);s.text(355,400,'N → 1','small')
s.box(920,360,280,120,'proposals · öneri','author, status, applied\ngroup_ids, decision');s.line(770,417,920,417);s.text(785,400,'1 → 1 · köken','small')
s.box(55,640,290,120,'helpful / points','Tekil değerlendirme\nTekil puan kaynağı');s.line(200,640,200,480);s.text(210,558,'mesaj + kullanıcı\nsource=helpful:<id>','small')
s.box(490,640,280,120,'electorate / votes','Öneri + kullanıcı tekil\nAçılış grubu sabittir');s.path([(920,450),(840,450),(840,695),(770,695)]);s.text(850,565,'önerinin\nseçmenleri / oyları','small')
s.path([(490,710),(405,710),(405,290),(345,230)],True);s.text(415,611,'user_id','small')
s.text(920,165,'/graph görünümü\nGrup başına ≤30 üye\n≤12 konu; konu başına\n≤20 katkıcı ilişkisi\nÖzel profil metni yok.','small');s.save()

s=SVG('07-architecture','Çalışan mimari','Tek süreç + SQLite; dış model, dağıtık mutabakat veya native mobil uygulama yok.',1250,850)
s.box(55,130,330,115,'Tarayıcı','Jinja HTML + CSS + JS\nManifest / çevrimdışı uyarısı');s.box(520,130,360,115,'app.py · Flask','Oturum / CSRF / rol kontrolü\nHTTP rotaları ve transaction sınırı');s.line(385,185,520,185);s.text(400,165,'HTTP','small')
s.box(60,360,350,110,'voting.py','start_voting / close_voting\nDeterministik iş akışı');s.line(520,235,330,360);s.box(60,625,350,120,'policy.py','VotingPolicy Strategy\nR1 → R2 → R4 → R3 zinciri');s.line(230,470,230,625)
s.box(520,360,360,110,'storage.py','SQLite erişimi / event\naward / notify');s.line(695,245,695,360);s.line(410,417,520,417)
s.box(520,625,360,120,'SQLite · schema.sql','users / proposals / votes / topics\nmessages / versions / points\nevents: hash bağlantılı olaylar');s.line(695,470,695,625);s.text(710,550,'tek dosya; atomik yazma','small')
s.box(940,360,260,160,'ai.py','SummaryService\n→ SummaryProvider\n→ DemoProvider\nHata: yerel alıntı dönüşü');s.path([(880,200),(1070,200),(1070,360)]);s.text(915,175,'görünür veri seçimi','small');s.text(930,585,'AI veritabanına yazmaz.\nOy / puan / gizleme kararı\nAI çıktısına bağlı değildir.','small')
s.text(515,793,'scripts/replicate_ledger.py → iki yerel JSON kopyası (yalnız demo)','small');s.save()
print('7 SVG generated')
