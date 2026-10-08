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
                'items':[{'id':m['id'],'text':m['body'],'kind':m['kind']} for m in messages],
                'category':category,'related':related[:3],'flags':flags,
                'note':'Gerçek model çağrısı yapılmaz. Her türden sayfa başına en fazla 12 görünür katkının tam alıntıları, anahtar sözcükle kategori/çelişki ipuçları ve benzer başlıklar sunar. Kesin karar veya kural denetimi değildir.'}


class UnavailableProvider:
    def summarize(self, messages, topic, candidates):
        raise RuntimeError('Sağlayıcı bu teslimde uygulanmadı.')


class SummaryService:
    """Read-only provider boundary. Validate evidence before rendering any output."""
    def __init__(self, provider: SummaryProvider):
        self.provider = provider

    def summarize(self, messages, topic, candidates):
        from copy import deepcopy
        try:
            result = self.provider.summarize(deepcopy(messages), deepcopy(topic), deepcopy(candidates))
            self.validate(result, messages, candidates)
            return result
        except Exception:
            # No exception details or provider-generated text reaches the user.
            result = DemoProvider().summarize(messages, topic, candidates)
            result['warning'] = 'Sağlayıcı kullanılamadı veya çıktısı doğrulanamadı. Yerel alıntı demosu gösteriliyor; oylama ve tartışma çalışmaya devam eder.'
            return result

    @staticmethod
    def validate(result, messages, candidates):
        if not isinstance(result, dict): raise ValueError('Nesne bekleniyor')
        for key in ('label','category','note'):
            if not isinstance(result.get(key), str) or not 1 <= len(result[key]) <= 1000:
                raise ValueError('Metin alanı geçersiz')
        if not isinstance(result.get('flags'),list) or any(not isinstance(f,str) or len(f)>1000 for f in result['flags']):
            raise ValueError('Uyarı alanı geçersiz')
        expected = {m['id']: m for m in messages}
        items = result.get('items')
        if not isinstance(items,list) or len(items)!=len(expected):
            raise ValueError('Eksik gerekçe')
        seen=set()
        for item in items:
            if not isinstance(item,dict) or type(item.get('id')) is not int: raise ValueError('Kaynak yok')
            mid=item['id']
            if mid in seen or mid not in expected: raise ValueError('Kaynak yok veya tekrar')
            source=expected[mid]
            if item.get('text')!=source['body'] or item.get('kind')!=source['kind']:
                raise ValueError('Kaynakla uyuşmayan açıklama')
            seen.add(mid)
        related=result.get('related')
        if not isinstance(related,list) or len(related)>3 or any(c not in candidates for c in related):
            raise ValueError('İlgili konu kaynağı geçersiz')
