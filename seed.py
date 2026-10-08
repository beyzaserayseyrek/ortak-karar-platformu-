"""Create fictional classroom examples in an EMPTY database only."""
import argparse
import json
import time
from flask import g
from werkzeug.security import generate_password_hash
from app import create_app, db, run, one, event, start_voting, close_voting, award

DEMO_PASSWORD = 'Ortak-Demo-2026!'

def seed(app):
    with app.app_context():
        g.app_db=app.config['DATABASE']
        if one('SELECT id FROM users LIMIT 1'):
            raise SystemExit('Veritabanı boş değil; mevcut veriler korunuyor. Örnek veri eklenmedi.')
        run("INSERT INTO groups VALUES(1,'Algoritmalar Çalışma Grubu'),(2,'İstatistik Atölyesi')")
        accounts=[('ada','Ada','member',1,''),('deniz','Deniz','member',1,''),('ege','Ege','member',1,''),('yonetici','Moderatör','admin',1,''),('inceleme','İnceleme','admin',2,''),('bilirkişi','Uzman','expert',2,'İstatistik, bilimsel yöntem'),('selin','Selin','member',2,''),('can','Can','member',2,'')]
        hashed=generate_password_hash(DEMO_PASSWORD)
        for username,nickname,role,gid,expertise in accounts:
            run('INSERT INTO users(username,nickname,password,fullname,birthdate,address,group_id,role,expertise) VALUES(?,?,?,?,?,?,?,?,?)',(username,nickname,hashed,'Örnek Öğrenci','2003-01-01','Kurgusal Kampüs / Demo',gid,role,expertise))
        def proposal(title,body,gid=1,kind='topic',effect='learning',target=None,parent=None,votes=None,finish=True,review=None):
            pid=run('INSERT INTO proposals(author,kind,title,body,category,tags,group_ids,target,parent,restrictive,effect,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(1,kind,title,body,'Algoritmalar' if gid==1 else 'İstatistik','ders, çalışma grubu',json.dumps([gid]),target,parent,int(effect!='learning'),effect,time.time()-90000)).lastrowid
            event('proposal_created',pid);start_voting(pid,24)
            for uid,choice,reason in votes or []: run('INSERT INTO votes VALUES(?,?,?,?)',(pid,uid,choice,reason));event('vote_recorded',pid)
            if review:
                run('UPDATE proposals SET review=?,reviewer=5 WHERE id=?',(review,pid))
            if finish:
                run('UPDATE proposals SET deadline=? WHERE id=?',(time.time()-1,pid));close_voting(pid)
            return pid
        p1=proposal('İkili aramayı birlikte çözelim','İkili arama neden sıralı dizi gerektirir? Haftalık çalışma grubunda örnekler ve karmaşıklık analiziyle inceleyelim.',votes=[(1,'accept','Birlikte örnek çözmek kavramı netleştirecek.'),(2,'accept','Önce doğrusal aramayla karşılaştıralım.'),(3,'reject','Önce özyineleme konusundaki eksikleri gidermeliyiz.')])
        tid=one('SELECT id FROM topics WHERE proposal_id=?',(p1,))['id']
        p2=proposal('Olasılık dağılımları için soru saati','Binom ve normal dağılımın hangi koşullarda kullanılacağını ders örnekleriyle tartışalım.',gid=2,votes=[(5,'accept','Ders tekrarına katkı sağlayabilir.')])
        p3=proposal('Grup üyelerinin adreslerini ortak listede açalım','Ders gösterimi için kurala aykırı örnek: özel adreslerin herkese açılması. Gerçek kişisel bilgi içermez.',effect='publish_private',votes=[(1,'accept','Kurgusal test oyu.'),(2,'accept','Kurgusal test oyu.'),(3,'accept','Kurgusal test oyu.'),(4,'accept','Kurgusal test oyu.')],review='İnceleme kaydı: özel bilgilerin açılması R1 ile yasaktır.')
        # Review does not bypass hard rights rules.
        sub=proposal('Özyinelemeli ikili arama','Taban durumu ve özyinelemeli çağrılar nasıl tasarlanır? Bir çağrı ağacı çizerek birlikte çözelim.',kind='subtopic',parent=tid,votes=[(1,'accept','Örnek kodu açıklayabiliriz.'),(2,'accept','Çağrı ağacı faydalı olur.')])
        editbody=json.dumps({'old_title':'İkili aramayı birlikte çözelim','old_body':one('SELECT body FROM topics WHERE id=?',(tid,))['body'],'new_body':'İkili arama neden sıralı dizi gerektirir? Önce doğrusal aramayla karşılaştırıp sonra adım sayısını hesaplayalım. Her öğrenci gerekçeli bir örnek paylaşsın.'},ensure_ascii=False)
        proposal('İkili arama: karşılaştırarak öğrenelim',editbody,kind='edit',target=tid,votes=[(1,'accept','Karşılaştırma öğrenmeyi kolaylaştırır.'),(2,'accept','Adım sayısını ölçelim.')])
        message_data=[(1,'question','Dizi sıralı değilse ortadaki elemanı karşılaştırıp yarısını elemek neden güvenilir olmaz?',''),(2,'explanation','Sıralılık, aranan değerin hangi yarıda bulunabileceğini garanti eder. Örneğin [2, 4, 8, 16] dizisinde 8 aranırken 4 ile karşılaştırmak sol yarıyı elememizi sağlar. Sırasız dizide bu çıkarımı yapamayız.',''),(3,'counter','Küçük bir diziyi yalnız bir kez arayacaksak önce sıralama maliyeti doğrusal aramadan yüksek olabilir. Kullanım sıklığını da tartışmalıyız.',''),(2,'resource','Python belgelerindeki bisect modülü sıralı dizilerde aramanın sınırlarını anlamak için bir kaynak olabilir.','https://docs.python.org/3/library/bisect.html'),(1,'explanation','Kaldırma akışını göstermek için hazırlanmış, kişisel bilgi içermeyen örnek mesaj.','')]
        for author,kind,body,url in message_data:
            run('INSERT INTO messages(topic_id,author,kind,body,url,created) VALUES(?,?,?,?,?,?)',(tid,author,kind,body,url,time.time()))
        run('INSERT INTO helpful VALUES(2,1)');award(2,'helpful:2','Yararlı bulunan gerekçeli katkı',3)
        remove=proposal('Örnek mesajın gizlenmesini değerlendirelim','Ders gösterimi: bu mesaj konu dışı olduğundan normal görünümden gizlenmesi öneriliyor.',kind='remove',effect='hide_content',target=5,votes=[(1,'accept','Konu dışı örneği gizleyelim.'),(2,'accept','Gerekçe yerinde gösterilsin.'),(3,'accept','Denetim kaydı korunsun.')],finish=False)
        run('UPDATE proposals SET review=?,reviewer=5,deadline=? WHERE id=?',('Mesaj kimseyi hedef almıyor; ders gösterimindeki konu dışı örnek. Gerekçe korunarak gizlenmesi orantılıdır.',time.time()-1,remove));close_voting(remove)
        run('INSERT INTO appeals(proposal_id,author,body,created) VALUES(?,?,?,?)',(p1,3,'Özyineleme konusunda destek isteyen öğrenciler için ön hazırlık kaynağı eklenmesini talep ediyorum.',time.time()))
        run('INSERT INTO opinions(topic_id,expert,body,conflict,created) VALUES(?,?,?,?,?)',(tid,6,'Karşılaştırma yaparken girdi boyutunu ve sıralama maliyetini belirtin. Bu yöntem istatistiksel ölçüm için de önemlidir.','Kurgusal ders örneği; çıkar çatışması yok.',time.time()))
        proposal('Sınav öncesi grafik algoritmaları oturumu','BFS ve DFS hangi problemler için uygundur? Küçük bir kampüs haritası üzerinde birlikte yol bulalım.',votes=[(2,'accept','Küçük örnekler üzerinde izleyelim.')],finish=False)
        proposal('Hipotez testinde p değeri ne söyler?','p değerinin hipotezin doğru olma olasılığı olmadığını örnek araştırma sonuçları üzerinden tartışalım.',gid=2,votes=[(5,'accept','Yaygın yanlış yorumları inceleyelim.')],finish=False)
        db().commit()
        print('8 kurgusal hesap, 2 grup ve 8 oylama senaryosu oluşturuldu. Şifre için README dosyasına bakın.')

if __name__=='__main__': seed(create_app())
