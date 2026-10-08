"""Synthetic regression cases: no real model calls or real user information."""
from contextlib import closing
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import g
from ai import DemoProvider, SummaryService
from app import create_app, db, run, one
from policy import policy_for, check_rules
from seed import seed, DEMO_PASSWORD

MESSAGES = [
    {'id':101,'body':'Önce BFS çalışalım; çünkü katman sırası en kısa yolu açıklar.','kind':'explanation'},
    {'id':102,'body':'Katılmıyorum; negatif ağırlık varsa bu çıkarım doğru değildir.','kind':'counter'},
    {'id':103,'body':'Neden kuyruk kullanıyoruz?','kind':'question'},
]
TOPIC={'id':1,'title':'Algoritma çalışma grubu'}

class ChangedProvider:
    def __init__(self, change): self.change=change
    def summarize(self, messages, topic, candidates):
        result=DemoProvider().summarize(messages,topic,candidates)
        return self.change(result)

class SummaryTests(unittest.TestCase):
    def test_valid_exact_quotes(self):
        result=SummaryService(DemoProvider()).summarize(MESSAGES,TOPIC,[])
        self.assertNotIn('warning',result)
        self.assertEqual([i['text'] for i in result['items']],[m['body'] for m in MESSAGES])
    def test_missing_reason_is_rejected(self):
        def mutate(r): r['items'][0]['text']='Önce BFS çalışalım.';return r
        self.assert_fallback(mutate)
    def test_unsupported_claim_is_rejected(self):
        def mutate(r): r['items'][0]['text']='BFS her tür ağırlıklı graf için doğrudur.';return r
        self.assert_fallback(mutate)
    def test_minority_omission_is_rejected(self):
        def mutate(r): r['items']=[i for i in r['items'] if i['kind']!='counter'];return r
        self.assert_fallback(mutate)
    def test_invalid_output_is_rejected(self): self.assert_fallback(lambda r:'not-json')
    def test_unknown_source_is_rejected(self):
        def mutate(r): r['items'][0]['id']=999;return r
        self.assert_fallback(mutate)
    def test_duplicate_source_is_rejected(self):
        def mutate(r): r['items'][1]=dict(r['items'][0]);return r
        self.assert_fallback(mutate)
    def test_timeout_is_isolated(self):
        def fail(r): raise TimeoutError('private provider error')
        result=self.assert_fallback(fail)
        self.assertNotIn('private provider error',json.dumps(result))
    def test_long_reason_not_cut_off(self):
        messages=[{'id':1,'body':'Örnek gerekçe. '*30+'Ancak bu varsayım yalnız sıralı dizide geçerlidir.','kind':'counter'}]
        result=SummaryService(DemoProvider()).summarize(messages,TOPIC,[])
        self.assertEqual(result['items'][0]['text'],messages[0]['body'])
    def assert_fallback(self,mutate):
        result=SummaryService(ChangedProvider(mutate)).summarize(MESSAGES,TOPIC,[])
        self.assertIn('warning',result)
        self.assertEqual([i['id'] for i in result['items']],[101,102,103])
        self.assertEqual(result['items'][0]['text'],MESSAGES[0]['body'])
        return result

class PolicyRevisionTests(unittest.TestCase):
    def test_threshold_below_equal_above(self):
        for n,status in [(49,'insufficient'),(50,'accepted'),(51,'accepted')]:
            with self.subTest(voters=n):
                self.assertEqual(policy_for(False).evaluate(['accept']*n,100,.5)['status'],status)
    def test_strategies_differ_at_restrictive_boundary(self):
        self.assertEqual(policy_for(False).evaluate(['accept']*66,100,.5)['status'],'accepted')
        self.assertEqual(policy_for(True).evaluate(['accept']*66,100,.5)['status'],'insufficient')
        self.assertEqual(policy_for(True).evaluate(['accept']*67,100,.5)['status'],'accepted')
    def test_chain_collects_multiple_failures(self):
        p=dict(effect='publish_private',r=.5,restrictive=True,review=None,reviewer=None)
        self.assertEqual(check_rules(p,[.5],{'accept':2,'reject':1}),['R1','R4','R3'])
        p['effect']='exclude_group'
        self.assertEqual(check_rules(p,[.5],{'accept':2,'reject':1}),['R2','R4','R3'])
    def test_two_thirds_exact_boundary(self):
        p=dict(effect='hide_content',r=.5,restrictive=True,review='İncelendi',reviewer=5)
        self.assertEqual(check_rules(p,[1],{'accept':2,'reject':1}),[])
        self.assertIn('R3',check_rules(p,[1],{'accept':3,'reject':2}))

class RevisionAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.path=str(Path(cls.tmp.name)/'test.sqlite')
        cls.app=create_app({'TESTING':True,'DATABASE':cls.path,'SECRET_KEY':'synthetic-test'})
        seed(cls.app);cls.snapshot=Path(cls.path).read_bytes()
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def setUp(self):
        Path(self.path).write_bytes(self.snapshot)
        self.client=self.app.test_client()
    def post(self,path,data=None):
        with self.client.session_transaction() as s: token=s.get('csrf','')
        return self.client.post(path,data=dict(data or {},csrf=token))
    def login(self,user='ada'):
        self.client.get('/login');return self.post('/login',{'username':user,'password':DEMO_PASSWORD})
    def sql(self,sql,args=()):
        with closing(sqlite3.connect(self.path)) as c, c:
            c.row_factory=sqlite3.Row
            cur=c.execute(sql,args)
            return [dict(r) for r in cur.fetchall()]
    def draft(self):
        self.login()
        response=self.post('/proposal/new',dict(title='Revizyon sınama önerisi',body='Gerekçeli öğrenme sorusu ve sentetik öneri içeriği.',category='Algoritmalar',groups='1',effect='learning',kind='topic'))
        return int(response.location.rsplit('/',1)[1])
    def test_invalid_start_is_atomic(self):
        pid=self.draft();before=self.sql('SELECT * FROM proposals WHERE id=?',(pid,))
        self.login('yonetici')
        self.post(f'/proposal/{pid}/start',{'groups':'2','effect':'publish_private','hours':'0'})
        self.assertEqual(self.sql('SELECT * FROM proposals WHERE id=?',(pid,)),before)
        self.assertEqual(self.sql('SELECT * FROM electorate WHERE proposal_id=?',(pid,)),[])
    def test_permanent_hide_cannot_become_temporary(self):
        self.login('yonetici');before=self.sql('SELECT * FROM messages WHERE id=5')
        self.assertEqual(self.post('/message/5/hide',{'reason':'Tekrar gizleyerek kalıcı kararı aşma denemesi.'}).status_code,409)
        self.assertEqual(self.post('/message/5/restore',{'reason':'Kalıcı gizlemeyi doğrudan kaldırma denemesi.'}).status_code,403)
        self.assertEqual(self.sql('SELECT * FROM messages WHERE id=5'),before)
    def test_appeal_and_response_permissions(self):
        self.login();self.assertEqual(self.post('/proposal/7/appeal',{'body':'Oylama bitmeden itiraz kabul edilmemeli.'}).status_code,400)
        self.assertEqual(self.post('/proposal/3/appeal',{'body':'Bu kararın gerekçesi yeniden değerlendirilsin.'}).status_code,302)
        aid=self.sql('SELECT max(id) id FROM appeals')[0]['id']
        self.assertEqual(self.post(f'/appeal/{aid}/respond',{'response':'Üyenin yetkisiz yanıt verme denemesi.'}).status_code,403)
        self.login('yonetici');self.assertEqual(self.post(f'/appeal/{aid}/respond',{'response':'Hak koruması nedeniyle karar uygulanmayacaktır.'}).status_code,302)
        self.assertEqual(self.sql('SELECT applied FROM proposals WHERE id=3')[0]['applied'],0)
    def test_old_minority_and_paginated_source_survive(self):
        self.sql("INSERT INTO messages(topic_id,author,kind,body,created) VALUES(1,2,'counter','Eski azınlık gerekçesi: varsayım açıkça sınırlandırılmalı.',1)")
        for i in range(25): self.sql("INSERT INTO messages(topic_id,author,kind,body,created) VALUES(1,1,'explanation',?,1)",(f'Yeni açıklama {i}: bağımsız sentetik gerekçe.',))
        self.login();response=self.client.get('/topic/1/summary').get_data(as_text=True)
        self.assertIn('Eski azınlık gerekçesi',response)
        self.assertIn('?page=2#message-',response)
        self.assertIn('Diğer alıntılar',response)
    def test_provider_failure_keeps_voting_working_and_summary_read_only(self):
        def fail(r): raise TimeoutError('synthetic')
        with patch.dict(self.app.extensions,{'summary_service':SummaryService(ChangedProvider(fail))}):
            self.login();before={t:self.sql(f'SELECT * FROM {t}') for t in ['votes','points','messages','proposals','events']}
            response=self.client.get('/topic/1/summary')
            self.assertIn('Sağlayıcı kullanılamadı',response.get_data(as_text=True))
            after={t:self.sql(f'SELECT * FROM {t}') for t in before}
            self.assertEqual(before,after)
            self.assertEqual(self.post('/proposal/7/vote',{'choice':'accept'}).status_code,302)
            self.assertEqual(self.sql('SELECT choice FROM votes WHERE proposal_id=7 AND user_id=1')[0]['choice'],'accept')
    def test_unsupported_config_does_not_prevent_login(self):
        with patch.dict(os.environ,{'AI_PROVIDER':'not-implemented'}):
            app=create_app({'TESTING':True,'DATABASE':self.path,'SECRET_KEY':'synthetic-test'})
        self.assertEqual(app.test_client().get('/login').status_code,200)
        result=app.extensions['summary_service'].summarize(MESSAGES,TOPIC,[])
        self.assertIn('warning',result)
    def test_expired_vote_closes_once_and_rejects_late_vote(self):
        self.login();before=self.sql('SELECT * FROM votes WHERE proposal_id=7');self.sql('UPDATE proposals SET deadline=0 WHERE id=7')
        self.assertEqual(self.post('/proposal/7/vote',{'choice':'accept'}).status_code,400)
        self.client.get('/proposal/7');self.client.get('/proposal/7')
        self.assertEqual(self.sql("SELECT COUNT(*) n FROM events WHERE kind='vote_result' AND object_id=7")[0]['n'],1)
        self.assertEqual(self.sql('SELECT * FROM votes WHERE proposal_id=7'),before)
    def test_spam_and_hidden_edit_permissions(self):
        self.login();body='Tekrarlanan sentetik çalışma sorusu neden geçersiz?'
        self.assertEqual(self.post('/topic/1/message',dict(kind='question',body=body)).status_code,302)
        self.assertEqual(self.post('/topic/1/message',dict(kind='question',body=body)).status_code,400)
        self.assertEqual(self.post('/message/2/edit',dict(body='Başkasının katkısını değiştirme denemesi.')).status_code,403)
        self.assertEqual(self.post('/message/5/edit',dict(body='Gizlenmiş katkıyı değiştirme denemesi.')).status_code,403)
        self.assertEqual(self.sql('SELECT COUNT(*) n FROM messages WHERE body=?',(body,))[0]['n'],1)

if __name__=='__main__': unittest.main()
