"""Replaceable demonstration provider; public discussion data only."""
from typing import Protocol
import re

class SummaryProvider(Protocol):
    def summarize(self, messages: list[dict], topic: dict, candidates: list[dict]) -> dict: ...

class DemoProvider:
    def summarize(self, messages, topic, candidates):
        text=' '.join([topic['title']]+[m['body'] for m in messages]).lower()
        words=set(re.findall(r'\w{4,}',topic['title'].lower()))
        related=[]
        for candidate in candidates:
            overlap=words & set(re.findall(r'\w{4,}',candidate['title'].lower()))
            if overlap: related.append(candidate)
        category='İstatistik' if any(w in text for w in ('olasılık','hipotez','dağılım')) else 'Bilgisayar Bilimleri' if any(w in text for w in ('arama','algoritma','dizi','kod')) else 'Genel çalışma'
        flags=[]
        if any(w in text for w in ('adres','kişisel bilgi','doğum tarihi')): flags.append('R1 ile olası ilişki: kişisel bilgi ifadeleri var. İnsan incelemesi gerekir.')
        if any(w in text for w in ('dışla','katılım hakkı','grubu çıkar')): flags.append('R2 ile olası ilişki: katılım hakkı ifadeleri var. İnsan incelemesi gerekir.')
        return {'label':'Demo yapay zekâ özeti (yerel, alıntı tabanlı)',
                'items':[{'id':m['id'],'text':m['body'][:240],'kind':m['kind']} for m in messages[:12]],
                'category':category,'related':related[:3],'flags':flags,
                'note':'Gerçek model çağrısı yapılmaz. Son 12 görünür katkıdan alıntılar, anahtar sözcükle kategori/çelişki ipuçları ve benzer başlıklar sunar. Kesin karar veya kural denetimi değildir.'}
