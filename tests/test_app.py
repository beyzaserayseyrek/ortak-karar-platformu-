import json
import tempfile
import time
import unittest
from pathlib import Path
from flask import g
from app import create_app, db, run, one, start_voting, close_voting, event, award
from policy import tally, verify_events, check_rules
from seed import seed, DEMO_PASSWORD

class PolicyTests(unittest.TestCase):
    def test_votes_and_boundaries(self):
        self.assertEqual(tally(['accept'],4,.5)['status'],'insufficient')
        self.assertEqual(tally(['accept','abstain'],4,.5)['status'],'accepted')
        self.assertEqual(tally(['accept','reject'],4,.5)['status'],'rejected')
        self.assertEqual(tally(['abstain','abstain'],4,.5)['status'],'rejected')
        self.assertEqual(tally([],0,.5)['status'],'insufficient')
        self.assertEqual(tally(['accept','accept','reject'],4,.5)['status'],'accepted')
    def test_group_and_restrictive_rules(self):
        p=dict(effect='learning',r=.5,restrictive=0,review=None,reviewer=None)
        self.assertIn('R4',check_rules(p,[1,.25],{'accept':3,'reject':0}))
        p.update(effect='hide_content',restrictive=1)
        self.assertIn('R3',check_rules(p,[1],{'accept':4,'reject':0}))

class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.dbpath=str(Path(cls.tmp.name)/'base.sqlite')
        cls.app=create_app({'TESTING':True,'DATABASE':cls.dbpath,'SECRET_KEY':'test-secret-only'})
        seed(cls.app)
        cls.snapshot=Path(cls.dbpath).read_bytes()
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def setUp(self):
        Path(self.dbpath).write_bytes(self.snapshot)
        self.client=self.app.test_client()
    def login(self,name='ada'):
        self.client.get('/login')
        return self.post('/login',{'username':name,'password':DEMO_PASSWORD})
    def post(self,path,data=None):
        with self.client.session_transaction() as s: token=s.get('csrf','')
        return self.client.post(path,data=dict(data or {},csrf=token))
    def context(self):
        ctx=self.app.app_context();ctx.push();g.app_db=self.dbpath
        self.addCleanup(ctx.pop)
    def test_all_pages(self):
        self.login('yonetici')
        for path in ['/','/proposals','/topics','/groups','/graph','/contributions','/admin','/proposal/new','/manifest.webmanifest','/sw.js']+[f'/proposal/{i}' for i in range(1,9)]+['/topic/1','/topic/1/summary','/message/2/history']:
            with self.subTest(path=path):
                response=self.client.get(path)
                self.assertEqual(response.status_code,200)
                response.close()
    def test_unique_vote_and_update(self):
        self.login()
        self.assertEqual(self.post('/proposal/7/vote',dict(choice='accept',reason='Birlikte öğrenelim.')).status_code,302)
        self.post('/proposal/7/vote',dict(choice='reject',reason='Ön hazırlık gerekir.'))
        self.context()
        self.assertEqual(one('SELECT COUNT(*) n FROM votes WHERE proposal_id=7 AND user_id=1')['n'],1)
        self.assertEqual(one('SELECT choice FROM votes WHERE proposal_id=7 AND user_id=1')['choice'],'reject')
    def test_permissions_and_csrf(self):
        self.login()
        self.assertEqual(self.client.get('/admin').status_code,403)
        self.assertEqual(self.post('/proposal/7/start',dict(hours=1,groups='1')).status_code,403)
        self.assertEqual(self.client.post('/proposal/7/vote',data=dict(choice='accept')).status_code,400)
        self.assertEqual(self.post('/proposal/8/vote',dict(choice='accept')).status_code,403)
        self.assertEqual(self.post('/topic/1/expert',dict(mode='opinion',body='Yetkisiz bilirkişi görüşü.')).status_code,403)
    def test_registration_snapshot_and_privacy(self):
        self.client.get('/register')
        response=self.post('/register',dict(username='new-user',nickname='Yeni',password='Test-Only-12345',fullname='Gizli Tam Ad',birthdate='2002-01-01',address='Gizli adres örneği',group_id=1))
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.post('/proposal/7/vote',dict(choice='accept')).status_code,403)
        for path in ['/groups','/graph','/proposal/7']:
            body=self.client.get(path).get_data(as_text=True)
            self.assertNotIn('Gizli Tam Ad',body);self.assertNotIn('Gizli adres',body)
        self.context()
        self.assertNotEqual(one("SELECT password FROM users WHERE username='new-user'")['password'],'Test-Only-12345')
    def test_hidden_distribution_and_no_hidden_leak(self):
        self.login()
        page=self.client.get('/proposal/7').get_data(as_text=True)
        self.assertNotIn('vote-counts',page)
        self.assertEqual(self.client.get('/message/5/history').status_code,403)
        self.assertNotIn('kişisel bilgi içermeyen örnek mesaj',self.client.get('/topic/1').get_data(as_text=True))
        self.assertNotIn('kişisel bilgi içermeyen örnek mesaj',self.client.get('/topic/1/summary').get_data(as_text=True))
    def test_majority_cannot_override_rule(self):
        self.context()
        p=one('SELECT * FROM proposals WHERE id=3')
        self.assertEqual(p['status'],'accepted');self.assertFalse(p['applied'])
        self.assertIn('R1',json.loads(p['decision'])['violations'])
        self.assertIsNone(one('SELECT * FROM topics WHERE proposal_id=3'))
    def test_helpfulness_dedup_and_self_rating(self):
        self.login()
        for _ in range(3): self.post('/message/2/helpful')
        self.assertEqual(self.post('/message/1/helpful').status_code,403)
        self.login('ege');self.post('/message/2/helpful')
        self.context()
        self.assertEqual(one("SELECT COUNT(*) n FROM points WHERE source='helpful:2'")['n'],1)
        self.assertEqual(one('SELECT COUNT(*) n FROM helpful WHERE message_id=2')['n'],2)
    def test_message_persistence_history_and_escape(self):
        self.login()
        content='<script>alert(1)</script> Öğrenme sorusu örneği'
        self.assertEqual(self.post('/topic/1/message',dict(body=content,kind='question')).status_code,302)
        html=self.client.get('/topic/1').get_data(as_text=True)
        self.assertIn('&lt;script&gt;',html);self.assertNotIn('<script>alert',html)
        self.assertEqual(self.post('/message/1/edit',dict(body='Sırasız dizide hangi çıkarım geçersiz olur?')).status_code,302)
        self.context()
        self.assertEqual(one('SELECT COUNT(*) n FROM message_versions WHERE message_id=1')['n'],1)
    def test_hash_chain_tampering(self):
        self.context()
        rows=[dict(x) for x in db().execute('SELECT * FROM events ORDER BY id')]
        self.assertTrue(verify_events(rows)[0])
        rows[1]['object_id']+=1
        self.assertFalse(verify_events(rows)[0])
        with self.assertRaises(Exception): run("UPDATE events SET kind='tamper' WHERE id=1")
    def test_end_to_end_proposal_vote_close_discussion(self):
        self.login()
        response=self.post('/proposal/new',dict(title='Dinamik programlama öğrenme oturumu',body='Alt problemlerin sonuçlarını neden saklarız? Birlikte örnek çözelim.',category='Algoritmalar',groups='1',effect='learning',kind='topic'))
        self.assertEqual(response.status_code,302)
        pid=int(response.location.rsplit('/',1)[1])
        self.login('yonetici');self.post(f'/proposal/{pid}/start',dict(groups='1',hours=1))
        self.login();self.post(f'/proposal/{pid}/vote',dict(choice='accept'))
        self.login('deniz');self.post(f'/proposal/{pid}/vote',dict(choice='abstain'))
        with self.app.app_context():
            g.app_db=self.dbpath
            run('UPDATE proposals SET deadline=? WHERE id=?',(time.time()-1,pid));db().commit()
        self.client.get(f'/proposal/{pid}')
        with self.app.app_context():
            g.app_db=self.dbpath
            topic=one('SELECT id FROM topics WHERE proposal_id=?',(pid,))
            self.assertIsNotNone(topic);tid=topic['id']
        self.assertEqual(self.post(f'/topic/{tid}/message',dict(kind='explanation',body='Aynı alt problemi yeniden çözmek yerine sonucu saklarız.')).status_code,302)
        with self.app.app_context():
            g.app_db=self.dbpath
            self.assertEqual(one('SELECT COUNT(*) n FROM messages WHERE topic_id=?',(tid,))['n'],1)
    def test_deadline_and_policy_two_admins(self):
        self.login();self.assertEqual(self.post('/proposal/1/vote',dict(choice='accept')).status_code,400)
        self.login('yonetici');self.post('/admin',dict(r=.6,reason='Ders grupları için daha yüksek katılım isteniyor.'))
        self.assertEqual(self.post('/policy/1/approve').status_code,403)
        self.login('inceleme');self.assertEqual(self.post('/policy/1/approve').status_code,302)
        self.context();self.assertEqual(one('SELECT r FROM settings')['r'],.6)
        self.assertEqual(one('SELECT r FROM proposals WHERE id=7')['r'],.5)
    def test_emergency_hide_and_review(self):
        self.login('yonetici')
        self.assertEqual(self.post('/message/2/hide',dict(reason='Kurgusal acil gizleme incelemesi için örnek.')).status_code,302)
        self.context()
        self.assertTrue(one('SELECT hidden FROM messages WHERE id=2')['hidden'])
        self.assertIsNotNone(one("SELECT id FROM proposals WHERE kind='remove' AND target=2 AND status='draft'"))
    def test_topic_follow_notification(self):
        self.login('deniz');self.post('/topic/1/follow')
        self.login('ege');self.post('/topic/1/message',dict(kind='explanation',body='Takip bildirimini sınayan özgün bir açıklama.'))
        self.context()
        self.assertIsNotNone(one("SELECT id FROM notifications WHERE user_id=2 AND body LIKE 'Takip ettiğin%'"))
    def test_daily_points_cap(self):
        self.context()
        for i in range(10): award(3,f'test:{i}','Test katkısı',3)
        self.assertEqual(one('SELECT SUM(amount) n FROM points WHERE user_id=3')['n'],20)
    def test_section_removal_keeps_later_messages(self):
        self.login()
        response=self.post('/proposal/new',dict(kind='remove_section',target=1,title='Örnek bölümün kaldırılması',body='Kurgusal bölüm kaldırma testi ve yeterli gerekçe.',category='Algoritmalar',groups='1',effect='learning'))
        self.assertEqual(response.status_code,302)
        pid=int(response.location.rsplit('/',1)[1])
        self.context()
        start_voting(pid)
        run('UPDATE proposals SET review=?,reviewer=5,deadline=0 WHERE id=?',('Orantılı kaldırma talebi incelendi ve onaylandı.',pid))
        for uid in (1,2,3): run("INSERT INTO votes VALUES(?,?,'accept','')",(pid,uid))
        mid=run("INSERT INTO messages(topic_id,author,kind,body,created) VALUES(1,1,'question','Sonradan gelen soru kapsam dışıdır.',?)",(time.time()+1,)).lastrowid
        close_voting(pid)
        self.assertTrue(one('SELECT hidden FROM messages WHERE id=1')['hidden'])
        self.assertFalse(one('SELECT hidden FROM messages WHERE id=?',(mid,))['hidden'])
    def test_demo_ai_never_decides(self):
        self.login()
        text=self.client.get('/topic/1/summary').get_data(as_text=True)
        self.assertIn('Sınıflandırma önerisi',text)
        self.assertIn('Karşı gerekçeler',text)
        self.assertIn('Gerçek model çağrısı yapılmaz',text)
    def test_stale_edit_cannot_overwrite(self):
        self.context()
        body=json.dumps(dict(old_title='Eski başlık',old_body='Eski gövde',new_body='Yeni içerik'))
        pid=run("INSERT INTO proposals(author,kind,title,body,category,tags,group_ids,target,created) VALUES(1,'edit','Çakışan sürüm',?,'Ders','','[1]',1,?)",(body,time.time())).lastrowid
        start_voting(pid)
        run("INSERT INTO votes VALUES(?,1,'accept','')",(pid,));run("INSERT INTO votes VALUES(?,2,'accept','')",(pid,))
        run('UPDATE proposals SET deadline=0 WHERE id=?',(pid,));close_voting(pid)
        self.assertFalse(one('SELECT applied FROM proposals WHERE id=?',(pid,))['applied'])
        self.assertIn('SÜRÜM',json.loads(one('SELECT decision FROM proposals WHERE id=?',(pid,))['decision'])['violations'])

if __name__=='__main__': unittest.main()
