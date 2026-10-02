"""Ortak: a small, server-rendered Flask application backed by SQLite."""
import json
import os
import secrets
import sqlite3
import time
from datetime import date
from contextlib import closing
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from policy import RULES, EFFECTS, tally, check_rules, event_digest, verify_events
from ai import DemoProvider

ROOT = Path(__file__).parent
LABELS = {'draft': '✎ Taslak', 'voting': '◷ Oylamada', 'accepted': '✓ Kabul', 'rejected': '× Ret', 'insufficient': '! Katılım yetersiz'}


def db():
    if 'db' not in g:
        g.db = sqlite3.connect(g.app_db, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def one(sql, args=()): return db().execute(sql, args).fetchone()
def allrows(sql, args=()): return db().execute(sql, args).fetchall()
def run(sql, args=()): return db().execute(sql, args)
def now(): return time.time()


def event(kind, object_id):
    previous = one('SELECT digest FROM events ORDER BY id DESC LIMIT 1')
    previous = previous['digest'] if previous else '0' * 64
    stamp = now()
    run('INSERT INTO events(kind,object_id,stamp,previous,digest) VALUES(?,?,?,?,?)',
        (kind, object_id, stamp, previous, event_digest(kind, object_id, stamp, previous)))


def award(user_id, source, reason, amount):
    earned = one('SELECT COALESCE(SUM(amount),0) n FROM points WHERE user_id=? AND created>=?', (user_id, int(now() // 86400) * 86400))['n']
    amount = min(amount, max(0, 20 - earned))
    if amount: run('INSERT OR IGNORE INTO points(user_id,source,reason,amount,created) VALUES(?,?,?,?,?)', (user_id, source, reason, amount, now()))


def notify(user_id, body, link):
    run('INSERT INTO notifications(user_id,body,link,created) VALUES(?,?,?,?)', (user_id, body, link, now()))


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not g.user: return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user['role'] != 'admin': abort(403)
        return fn(*args, **kwargs)
    return wrapped


def must_text(key, minimum=1, maximum=5000):
    value = request.form.get(key, '').strip()
    if not minimum <= len(value) <= maximum: raise ValueError(f'{key}: {minimum}–{maximum} karakter girin.')
    return value


def get_proposal(pid):
    p = one('SELECT p.*,u.nickname FROM proposals p JOIN users u ON u.id=p.author WHERE p.id=?', (pid,))
    if not p: abort(404)
    if p['status'] == 'draft' and g.user['id'] != p['author'] and g.user['role'] != 'admin': abort(403)
    return p


def start_voting(pid, hours=24):
    p = one('SELECT * FROM proposals WHERE id=?', (pid,))
    if p['status'] != 'draft': raise ValueError('Yalnız taslaklar oylamaya açılır.')
    group_ids = json.loads(p['group_ids'])
    # Only the administrator freezes eligibility; author cannot choose individual voters.
    for gid in group_ids:
        run('INSERT INTO electorate SELECT ?,id,group_id FROM users WHERE group_id=?', (pid, gid))
    r = one('SELECT r FROM settings WHERE id=1')['r']
    run("UPDATE proposals SET status='voting',deadline=?,r=? WHERE id=?", (now() + hours * 3600, r, pid))
    for voter in allrows('SELECT user_id FROM electorate WHERE proposal_id=?', (pid,)):
        notify(voter['user_id'], f'Oylama açıldı: {p["title"]}', f'/proposal/{pid}')
    event('voting_started', pid)


def close_voting(pid):
    p = one('SELECT * FROM proposals WHERE id=?', (pid,))
    if p['status'] != 'voting': return
    if p['deadline'] > now(): raise ValueError('Oylama süresi henüz bitmedi.')
    voters = allrows('SELECT * FROM electorate WHERE proposal_id=?', (pid,))
    votes = allrows('SELECT * FROM votes WHERE proposal_id=?', (pid,))
    threshold = max(p['r'], .67) if p['restrictive'] else p['r']
    result = tally([v['choice'] for v in votes], len(voters), threshold)
    rates = []
    for gid in json.loads(p['group_ids']):
        ids = {v['user_id'] for v in voters if v['group_id'] == gid}
        rates.append(sum(v['user_id'] in ids for v in votes) / len(ids) if ids else 0)
    violations = check_rules(p, rates, result['counts'])
    result['violations'] = violations
    applied = result['status'] == 'accepted' and not violations
    # Concurrent edits never silently overwrite a newer version: compare stored base.
    if applied and p['kind'] == 'edit':
        payload = json.loads(p['body'])
        target = one('SELECT * FROM topics WHERE id=?', (p['target'],))
        if target['body'] != payload['old_body'] or target['title'] != payload['old_title']:
            applied = False
            result['violations'].append('SÜRÜM')
    run('UPDATE proposals SET status=?,decision=?,applied=? WHERE id=?', (result['status'], json.dumps(result), int(applied), pid))
    event('vote_result', pid)
    event('rule_check', pid)
    if applied:
        if p['kind'] in ('topic', 'subtopic'):
            tid = run('INSERT INTO topics(title,body,category,group_ids,parent,proposal_id) VALUES(?,?,?,?,?,?)',
                      (p['title'], p['body'], p['category'], p['group_ids'], p['parent'], pid)).lastrowid
            run('INSERT INTO topic_versions(topic_id,proposal_id,title,body,created) VALUES(?,?,?,?,?)', (tid, pid, p['title'], p['body'], now()))
        elif p['kind'] == 'edit':
            payload = json.loads(p['body'])
            run('UPDATE topics SET title=?,body=? WHERE id=?', (p['title'], payload['new_body'], p['target']))
            run('INSERT INTO topic_versions(topic_id,proposal_id,title,body,created) VALUES(?,?,?,?,?)', (p['target'], pid, p['title'], payload['new_body'], now()))
            event('edit_accepted', pid)
        elif p['kind'] == 'remove_section':
            run('UPDATE messages SET hidden=1,hidden_reason=? WHERE topic_id=? AND created<=?', (p['body'], p['target'], p['created']))
            event('discussion_hidden', p['target'])
        elif p['kind'] == 'remove':
            run('UPDATE messages SET hidden=1,hidden_reason=? WHERE id=?', (p['body'], p['target']))
            event('content_hidden', p['target'])
        award(p['author'], f'proposal:{pid}', 'Kabul edilip uygulanan öneri', 5)
    for voter in voters: notify(voter['user_id'], f'Karar: {p["title"]} — {LABELS[result["status"]]}', f'/proposal/{pid}')


def create_app(test_config=None):
    # Minimal .env loader, no subprocess and no secret printing.
    envfile = ROOT / '.env'
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())
    if os.getenv('AI_PROVIDER','demo') != 'demo':
        raise RuntimeError('Bu teslim yalnız AI_PROVIDER=demo destekler. Gerçek sağlayıcı önce uygulanmalıdır.')
    app = Flask(__name__)
    instance = ROOT / 'instance'
    instance.mkdir(exist_ok=True)
    secret = os.getenv('SECRET_KEY')
    if not secret:
        secretfile = instance / 'session.key'
        if not secretfile.exists():
            fd = os.open(secretfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w') as handle: handle.write(secrets.token_hex(32))
        secret = secretfile.read_text()
    app.config.update(SECRET_KEY=secret, DATABASE=str(ROOT / os.getenv('DATABASE', 'instance/ortak.sqlite')),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE') == '1',
                      MAX_CONTENT_LENGTH=64 * 1024, PERMANENT_SESSION_LIFETIME=3600)
    if test_config: app.config.update(test_config)
    with closing(sqlite3.connect(app.config['DATABASE'])) as conn:
        conn.executescript((ROOT / 'schema.sql').read_text()); conn.commit()

    @app.before_request
    def prepare():
        g.app_db = app.config['DATABASE']
        g.user = one('SELECT * FROM users WHERE id=?', (session.get('uid'),)) if session.get('uid') else None
        session.setdefault('csrf', secrets.token_hex(32))
        if request.method == 'POST' and not secrets.compare_digest(session['csrf'], request.form.get('csrf', '')): abort(400, 'İstek doğrulanamadı. Sayfayı yenileyin.')
        if request.method == 'POST': db().execute('BEGIN IMMEDIATE')
        # Close elapsed votes once, atomically. No early closing shortcut.
        if g.user:
            due = allrows("SELECT id FROM proposals WHERE status='voting' AND deadline<=?", (now(),))
            if due:
                if not db().in_transaction: db().execute('BEGIN IMMEDIATE')
                for item in due: close_voting(item['id'])
                db().commit()
                if request.method == 'POST': db().execute('BEGIN IMMEDIATE')

    @app.after_request
    def secure(response):
        if 'db' in g:
            if response.status_code < 400: g.db.commit()
            else: g.db.rollback()
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.teardown_appcontext
    def cleanup(error):
        connection = g.pop('db', None)
        if connection: connection.close()

    @app.context_processor
    def context():
        return dict(labels=LABELS, rules=RULES, effects=EFFECTS, groups=allrows('SELECT * FROM groups'), csrf=session.get('csrf'), json=json)

    @app.template_filter('date')
    def datefmt(value):
        import datetime
        return datetime.datetime.fromtimestamp(value, datetime.timezone.utc).strftime('%d.%m.%Y %H:%M UTC') if value else ''

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error): return render_template('error.html', error=error), error.code

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            user = one('SELECT * FROM users WHERE username=?', (request.form.get('username', '').strip(),))
            if user and check_password_hash(user['password'], request.form.get('password', '')):
                session.clear(); session.update(uid=user['id'], csrf=secrets.token_hex(32)); session.permanent = True
                return redirect(url_for('index'))
            error = 'Kullanıcı adı veya şifre hatalı.'
        return render_template('auth.html', register=False, error=error)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = None
        if request.method == 'POST':
            try:
                username = must_text('username', 3, 40)
                nickname = must_text('nickname', 2, 50)
                password = must_text('password', 10, 128)
                birth = date.fromisoformat(must_text('birthdate'))
                if birth >= date.today() or birth.year < 1900: raise ValueError('Doğum tarihini kontrol edin.')
                gid = int(request.form.get('group_id', '0'))
                if not one('SELECT id FROM groups WHERE id=?', (gid,)): raise ValueError('Geçerli bir grup seçin.')
                uid = run('INSERT INTO users(username,nickname,password,fullname,birthdate,address,group_id) VALUES(?,?,?,?,?,?,?)',
                    (username, nickname, generate_password_hash(password), must_text('fullname', 3, 100), str(birth), must_text('address', 3, 300), gid)).lastrowid
                session.clear(); session.update(uid=uid, csrf=secrets.token_hex(32)); session.permanent = True
                flash('Hesabın oluşturuldu. Herkese yalnız takma adın gösterilir.')
                return redirect(url_for('index'))
            except (ValueError, sqlite3.IntegrityError): error = 'Alanları kontrol edin: kullanıcı/takma ad benzersiz, şifre en az 10 karakter ve tarih geçerli olmalı.'
        return render_template('auth.html', register=True, error=error)

    @app.post('/logout')
    def logout(): session.clear(); return redirect(url_for('login'))

    @app.get('/')
    @login_required
    def index():
        pending = allrows("SELECT p.* FROM proposals p JOIN electorate e ON p.id=e.proposal_id WHERE e.user_id=? AND p.status='voting' ORDER BY p.deadline LIMIT 8", (g.user['id'],))
        mine = allrows('SELECT * FROM proposals WHERE author=? ORDER BY id DESC LIMIT 8', (g.user['id'],))
        notices = allrows('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 8', (g.user['id'],))
        points = one('SELECT COALESCE(SUM(amount),0) n FROM points WHERE user_id=?', (g.user['id'],))['n']
        return render_template('index.html', pending=pending, mine=mine, notices=notices, points=points)

    @app.get('/proposals')
    @login_required
    def proposals():
        q = request.args.get('q', '')[:100]; status = request.args.get('status', '')
        page = max(1, request.args.get('page', 1, type=int)); gid = request.args.get('group', '', type=str)
        rows = allrows("SELECT * FROM proposals WHERE (status!='draft' OR author=? OR ?='admin') AND title LIKE ? AND (?='' OR status=?) ORDER BY id DESC", (g.user['id'], g.user['role'], f'%{q}%', status, status))
        if gid: rows = [r for r in rows if gid in [str(v) for v in json.loads(r['group_ids'])]]
        return render_template('proposals.html', items=rows[(page-1)*12:page*12], page=page, more=len(rows)>page*12, q=q, status=status)

    @app.route('/proposal/new', methods=['GET', 'POST'])
    @login_required
    def new_proposal():
        error = None
        target_id = request.values.get('target', type=int)
        kind = request.values.get('kind', 'topic')
        if kind not in ('topic', 'subtopic', 'edit', 'remove', 'remove_section'): abort(400)
        target = None
        if kind in ('edit', 'subtopic', 'remove_section'):
            target = one('SELECT * FROM topics WHERE id=?', (target_id,))
            if not target: abort(404)
        if kind == 'remove':
            target = one('SELECT m.*,t.group_ids,t.category FROM messages m JOIN topics t ON t.id=m.topic_id WHERE m.id=?', (target_id,))
            if not target: abort(404)
        if request.method == 'POST':
            try:
                title = must_text('title', 5, 180); body = must_text('body', 15)
                gids = [int(v) for v in request.form.getlist('groups')]
                valid = {v['id'] for v in allrows('SELECT id FROM groups')}
                if not gids or not set(gids) <= valid: raise ValueError('En az bir geçerli ilgili grup seçin.')
                if target: gids = json.loads(target['group_ids'])
                effect = request.form.get('effect', 'learning')
                if effect not in EFFECTS: raise ValueError('Geçerli bir etki seçin.')
                if kind in ('remove','remove_section'): effect = 'hide_content'
                if kind == 'edit': body = json.dumps(dict(old_title=target['title'], old_body=target['body'], new_body=body), ensure_ascii=False)
                pid = run('INSERT INTO proposals(author,kind,title,body,category,tags,group_ids,target,parent,restrictive,effect,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                    (g.user['id'], kind, title, body, must_text('category', 2, 80), request.form.get('tags','')[:150], json.dumps(sorted(set(gids))), target_id if kind in ('edit','remove','remove_section') else None, target_id if kind=='subtopic' else None, int(effect!='learning'), effect, now())).lastrowid
                event('proposal_created', pid)
                flash('Taslak kaydedildi. Yönetici kapsamı inceleyip seçmen listesini sabitleyerek oylamayı başlatacak.')
                return redirect(url_for('proposal', pid=pid))
            except ValueError as exc: error = str(exc)
        similar = allrows('SELECT id,title FROM topics ORDER BY id DESC LIMIT 20')
        return render_template('new.html', kind=kind, target=target, target_id=target_id, error=error, similar=similar)

    @app.get('/proposal/<int:pid>')
    @login_required
    def proposal(pid):
        p = get_proposal(pid)
        total = one('SELECT COUNT(*) n FROM electorate WHERE proposal_id=?', (pid,))['n']
        cast = one('SELECT COUNT(*) n FROM votes WHERE proposal_id=?', (pid,))['n']
        eligible = one('SELECT * FROM electorate WHERE proposal_id=? AND user_id=?', (pid,g.user['id']))
        myvote = one('SELECT * FROM votes WHERE proposal_id=? AND user_id=?', (pid,g.user['id']))
        decision = json.loads(p['decision']) if p['decision'] else None
        reasons = allrows('SELECT v.*,u.nickname FROM votes v JOIN users u ON u.id=v.user_id WHERE proposal_id=? AND reason!=\'\'', (pid,)) if decision else []
        appeals = allrows('SELECT a.*,u.nickname FROM appeals a JOIN users u ON u.id=a.author WHERE proposal_id=?', (pid,))
        topic = one('SELECT id FROM topics WHERE proposal_id=?', (pid,))
        electorate = allrows('SELECT u.nickname,g.name FROM electorate e JOIN users u ON e.user_id=u.id JOIN groups g ON e.group_id=g.id WHERE proposal_id=?', (pid,))
        return render_template('proposal.html', p=p, total=total, cast=cast, eligible=eligible, myvote=myvote, decision=decision, reasons=reasons, appeals=appeals, topic=topic, electorate=electorate)

    @app.post('/proposal/<int:pid>/start')
    @admin_required
    def start(pid):
        p = get_proposal(pid)
        try:
            if p['status'] != 'draft': raise ValueError('Oylama zaten başlatılmış.')
            gids = sorted(set(int(v) for v in request.form.getlist('groups')))
            if not gids or not set(gids) <= {v['id'] for v in allrows('SELECT id FROM groups')}: raise ValueError('Grupları kontrol edin.')
            if p['target'] or p['parent']:
                if set(gids) != set(json.loads(p['group_ids'])): raise ValueError('Bağlı konunun etkilenen grupları korunmalıdır.')
            effect=request.form.get('effect',p['effect'])
            if effect not in EFFECTS: raise ValueError('Geçerli bir etki seçin.')
            if p['kind'] in ('remove','remove_section'): effect='hide_content'
            run('UPDATE proposals SET group_ids=?,effect=?,restrictive=? WHERE id=?', (json.dumps(gids),effect,int(effect!='learning'),pid))
            hours = int(request.form.get('hours',24))
            if not 1 <= hours <= 168: raise ValueError('Süre 1–168 saat olmalı.')
            start_voting(pid, hours); flash('Oylama açıldı; seçmen listesi ve r değeri sabitlendi.')
        except ValueError as exc: flash(str(exc))
        return redirect(url_for('proposal',pid=pid))

    @app.post('/proposal/<int:pid>/vote')
    @login_required
    def vote(pid):
        p = get_proposal(pid)
        if p['status'] != 'voting' or p['deadline'] <= now(): abort(400, 'Oylama kapanmış.')
        if not one('SELECT 1 FROM electorate WHERE proposal_id=? AND user_id=?', (pid,g.user['id'])): abort(403)
        choice = request.form.get('choice')
        if choice not in ('accept','reject','abstain'): abort(400)
        reason = request.form.get('reason','').strip()[:2000]
        run('INSERT INTO votes VALUES(?,?,?,?) ON CONFLICT(proposal_id,user_id) DO UPDATE SET choice=excluded.choice,reason=excluded.reason', (pid,g.user['id'],choice,reason))
        event('vote_recorded',pid)
        flash('Oyun kaydedildi. Süre bitene kadar değiştirebilirsin.')
        return redirect(url_for('proposal',pid=pid))

    @app.post('/proposal/<int:pid>/review')
    @admin_required
    def review(pid):
        p = get_proposal(pid)
        if p['status'] != 'voting' or p['author'] == g.user['id']: abort(403)
        try: reviewtext = must_text('review', 20, 2000)
        except ValueError as exc: abort(400,str(exc))
        run('UPDATE proposals SET review=?,reviewer=? WHERE id=?', (reviewtext,g.user['id'],pid)); event('review_recorded',pid)
        return redirect(url_for('proposal',pid=pid))

    @app.post('/proposal/<int:pid>/appeal')
    @login_required
    def appeal(pid):
        p = get_proposal(pid)
        if p['status'] in ('draft','voting'): abort(400)
        try: body = must_text('body',15,2000)
        except ValueError as exc: abort(400,str(exc))
        run('INSERT INTO appeals(proposal_id,author,body,created) VALUES(?,?,?,?)',(pid,g.user['id'],body,now())); event('appeal_created',pid)
        flash('İtirazın kaydedildi. Yönetici gerekçeli yanıt verebilir; yeniden karar için yeni oylama gerekir.')
        return redirect(url_for('proposal',pid=pid))

    @app.post('/appeal/<int:aid>/respond')
    @admin_required
    def respond(aid):
        a = one('SELECT * FROM appeals WHERE id=?',(aid,))
        if not a: abort(404)
        try: body=must_text('response',15,2000)
        except ValueError as exc: abort(400,str(exc))
        run("UPDATE appeals SET response=?,status='reviewed' WHERE id=?",(body,aid)); event('appeal_reviewed',aid)
        notify(a['author'],'İtirazınıza yanıt verildi.',f'/proposal/{a["proposal_id"]}')
        return redirect(url_for('proposal',pid=a['proposal_id']))

    @app.get('/topics')
    @login_required
    def topics():
        q=request.args.get('q','')[:100]; gid=request.args.get('group','')
        page=max(1,request.args.get('page',1,type=int))
        rows=allrows('SELECT * FROM topics WHERE title LIKE ? ORDER BY id DESC',(f'%{q}%',))
        if gid: rows=[t for t in rows if gid in [str(x) for x in json.loads(t['group_ids'])]]
        return render_template('topics.html',items=rows[(page-1)*12:page*12],page=page,more=len(rows)>page*12,q=q)

    @app.get('/topic/<int:tid>')
    @login_required
    def topic(tid):
        t=one('SELECT * FROM topics WHERE id=?',(tid,))
        if not t: abort(404)
        page=max(1,request.args.get('page',1,type=int))
        messages=allrows('SELECT m.*,u.nickname,(SELECT COUNT(*) FROM helpful h WHERE h.message_id=m.id) helpful FROM messages m JOIN users u ON u.id=m.author WHERE topic_id=? ORDER BY m.id LIMIT 21 OFFSET ?',(tid,(page-1)*20))
        opinions=allrows('SELECT o.*,u.nickname,u.expertise FROM opinions o JOIN users u ON u.id=o.expert WHERE topic_id=?',(tid,))
        versions=allrows('SELECT * FROM topic_versions WHERE topic_id=? ORDER BY id DESC',(tid,))
        requests=allrows('SELECT * FROM expert_requests WHERE topic_id=?',(tid,))
        children=allrows('SELECT id,title FROM topics WHERE parent=?',(tid,))
        return render_template('topic.html',t=t,messages=messages[:20],more=len(messages)>20,page=page,opinions=opinions,versions=versions,requests=requests,children=children,following=one('SELECT 1 FROM follows WHERE user_id=? AND topic_id=?',(g.user['id'],tid)))

    @app.post('/topic/<int:tid>/follow')
    @login_required
    def follow(tid):
        if not one('SELECT id FROM topics WHERE id=?',(tid,)): abort(404)
        if one('SELECT 1 FROM follows WHERE user_id=? AND topic_id=?',(g.user['id'],tid)):
            run('DELETE FROM follows WHERE user_id=? AND topic_id=?',(g.user['id'],tid))
            flash('Konu takibi kapatıldı.')
        else:
            run('INSERT INTO follows VALUES(?,?)',(g.user['id'],tid));flash('Konu takip ediliyor. Yeni katkılar genel bakışta görünecek.')
        return redirect(url_for('topic',tid=tid))

    @app.post('/topic/<int:tid>/message')
    @login_required
    def message(tid):
        if not one('SELECT id FROM topics WHERE id=?',(tid,)): abort(404)
        try:
            body=must_text('body',10,4000); kind=request.form.get('kind','explanation')
            if kind not in ('question','resource','explanation','counter'): raise ValueError('Katkı türü geçersiz.')
            link=request.form.get('url','').strip()
            if link and (urlparse(link).scheme not in ('http','https') or not urlparse(link).netloc): raise ValueError('Kaynak bağlantısı http veya https olmalı.')
            if kind=='resource' and not link: raise ValueError('Kaynak paylaşımına bağlantı ekleyin.')
            if one('SELECT id FROM messages WHERE author=? AND body=?',(g.user['id'],body)): raise ValueError('Aynı katkı tekrar eklenemez.')
            if one('SELECT COUNT(*) n FROM messages WHERE author=? AND created>?',(g.user['id'],now()-86400))['n'] >= 40: raise ValueError('Günlük 40 katkı sınırına ulaştın.')
            reply=request.form.get('reply_to',type=int)
            if reply and not one('SELECT id FROM messages WHERE id=? AND topic_id=?',(reply,tid)): raise ValueError('Yanıt aynı konudaki mesaja bağlanmalı.')
            run('INSERT INTO messages(topic_id,author,kind,body,url,reply_to,created) VALUES(?,?,?,?,?,?,?)',(tid,g.user['id'],kind,body,link,reply,now()))
            for follower in allrows('SELECT user_id FROM follows WHERE topic_id=? AND user_id!=?',(tid,g.user['id'])):
                notify(follower['user_id'],'Takip ettiğin konuya yeni katkı eklendi.',f'/topic/{tid}')
            flash('Katkın kaydedildi.')
        except ValueError as exc:
            flash(str(exc))
            return render_template('message_retry.html',tid=tid,error=str(exc)),400
        return redirect(url_for('topic',tid=tid))

    @app.route('/message/<int:mid>/edit',methods=['GET','POST'])
    @login_required
    def edit_message(mid):
        m=one('SELECT * FROM messages WHERE id=?',(mid,))
        if not m: abort(404)
        if m['author']!=g.user['id'] or m['hidden']: abort(403)
        if request.method=='POST':
            try: body=must_text('body',10,4000)
            except ValueError as exc: return render_template('edit_message.html',m=m,error=str(exc)),400
            run('INSERT INTO message_versions(message_id,body,created) VALUES(?,?,?)',(mid,m['body'],now()))
            run('UPDATE messages SET body=?,edited=? WHERE id=?',(body,now(),mid))
            return redirect(url_for('topic',tid=m['topic_id']))
        return render_template('edit_message.html',m=m)

    @app.get('/message/<int:mid>/history')
    @login_required
    def history(mid):
        m=one('SELECT * FROM messages WHERE id=?',(mid,))
        if not m: abort(404)
        if m['hidden'] and g.user['role']!='admin': abort(403)
        return render_template('history.html',m=m,versions=allrows('SELECT * FROM message_versions WHERE message_id=? ORDER BY id DESC',(mid,)))

    @app.post('/message/<int:mid>/helpful')
    @login_required
    def helpful(mid):
        m=one('SELECT * FROM messages WHERE id=?',(mid,))
        if not m: abort(404)
        if m['author']==g.user['id'] or m['hidden']: abort(403)
        run('INSERT OR IGNORE INTO helpful VALUES(?,?)',(mid,g.user['id']))
        if m['kind'] in ('explanation','resource','counter'): award(m['author'],f'helpful:{mid}','Yararlı bulunan gerekçeli katkı',3)
        flash('Yararlı değerlendirmesi kaydedildi; aynı katkı yalnız bir kez puan kazanır.')
        return redirect(url_for('topic',tid=m['topic_id']))

    @app.post('/message/<int:mid>/hide')
    @admin_required
    def hide(mid):
        m=one('SELECT m.*,t.group_ids,t.category FROM messages m JOIN topics t ON t.id=m.topic_id WHERE m.id=?',(mid,))
        if not m: abort(404)
        try: reason=must_text('reason',15,2000)
        except ValueError as exc: abort(400,str(exc))
        run('UPDATE messages SET hidden=1,hidden_reason=? WHERE id=?',(f'Geçici gizleme; inceleme bekliyor: {reason}',mid)); event('temporary_hidden',mid)
        pid=run("INSERT INTO proposals(author,kind,title,body,category,tags,group_ids,target,restrictive,effect,created) VALUES(?,'remove',?,?,?,'',?,?,1,'hide_content',?)",(g.user['id'],f'Mesaj #{mid} gizleme incelemesi',reason,m['category'],m['group_ids'],mid,now())).lastrowid
        event('proposal_created',pid)
        flash('Mesaj geçici gizlendi; gerekçeli inceleme taslağı oluşturuldu.')
        return redirect(url_for('proposal',pid=pid))

    @app.post('/message/<int:mid>/restore')
    @admin_required
    def restore(mid):
        m=one('SELECT * FROM messages WHERE id=?',(mid,))
        if not m: abort(404)
        try: must_text('reason',15,2000)
        except ValueError as exc: abort(400,str(exc))
        if not (m['hidden_reason'] or '').startswith('Geçici gizleme;'): abort(403)
        run('UPDATE messages SET hidden=0,hidden_reason=? WHERE id=?',(f'Geçici gizleme kaldırıldı: {request.form["reason"]}',mid));event('temporary_restored',mid)
        return redirect(url_for('topic',tid=m['topic_id']))

    @app.post('/topic/<int:tid>/expert')
    @login_required
    def expert(tid):
        if not one('SELECT id FROM topics WHERE id=?',(tid,)): abort(404)
        try: body=must_text('body',15,3000)
        except ValueError as exc: abort(400,str(exc))
        if request.form.get('mode')=='opinion':
            if g.user['role']!='expert': abort(403)
            run('INSERT INTO opinions(topic_id,expert,body,conflict,created) VALUES(?,?,?,?,?)',(tid,g.user['id'],body,request.form.get('conflict','Yok')[:1000],now()))
        else:
            run('INSERT INTO expert_requests(topic_id,author,body,created) VALUES(?,?,?,?)',(tid,g.user['id'],body,now()))
            for u in allrows("SELECT id FROM users WHERE role='expert'"): notify(u['id'],'Bilirkişi görüşü istendi.',f'/topic/{tid}')
        flash('Bilirkişi kaydı eklendi. Görüşler danışma amaçlıdır; oy ağırlığını değiştirmez.')
        return redirect(url_for('topic',tid=tid))

    @app.get('/topic/<int:tid>/summary')
    @login_required
    def summary(tid):
        current=one('SELECT * FROM topics WHERE id=?',(tid,))
        if not current: abort(404)
        messages=[dict(m) for m in allrows('SELECT id,body,kind FROM messages WHERE topic_id=? AND hidden=0 ORDER BY id DESC LIMIT 12',(tid,))]
        return render_template('summary.html',summary=DemoProvider().summarize(messages,dict(current),[dict(t) for t in allrows('SELECT id,title FROM topics WHERE id!=? ORDER BY id DESC LIMIT 50',(tid,))]),tid=tid)

    @app.get('/contributions')
    @login_required
    def contributions():
        return render_template('contributions.html',points=allrows('SELECT * FROM points WHERE user_id=? ORDER BY id DESC',(g.user['id'],)),votes=allrows('SELECT p.id,p.title,p.status,v.choice FROM votes v JOIN proposals p ON v.proposal_id=p.id WHERE v.user_id=? ORDER BY p.id DESC',(g.user['id'],)),appeals=allrows('SELECT * FROM appeals WHERE author=?',(g.user['id'],)))

    @app.get('/groups')
    @login_required
    def groups_page(): return render_template('groups.html',members=allrows('SELECT nickname,group_id,role,expertise FROM users ORDER BY nickname'))

    @app.get('/graph')
    @login_required
    def graph():
        gid=request.args.get('group',g.user['group_id'],type=int)
        tid=request.args.get('topic',type=int)
        members=allrows('SELECT id,nickname FROM users WHERE group_id=? LIMIT 30',(gid,))
        topics=[t for t in allrows('SELECT * FROM topics ORDER BY id DESC') if gid in json.loads(t['group_ids']) and (not tid or tid==t['id'])][:12]
        ids=[t['id'] for t in topics]
        contributions=[]
        for t in topics:
            contributions += allrows('SELECT DISTINCT u.nickname,m.topic_id FROM messages m JOIN users u ON m.author=u.id WHERE m.topic_id=? AND m.hidden=0 LIMIT 20',(t['id'],))
        return render_template('graph.html',gid=gid,members=members,topics=topics,edges=contributions)

    @app.route('/admin',methods=['GET','POST'])
    @admin_required
    def admin():
        if request.method=='POST':
            try:
                value=float(request.form.get('r',''))
                if not 0<value<=1: raise ValueError('r, 0 ile 1 arasında olmalı (0 hariç).')
                reason=must_text('reason',20,2000)
                run('INSERT INTO policy_changes(author,r,reason,created) VALUES(?,?,?,?)',(g.user['id'],value,reason,now()))
                flash('Politika değişikliği ikinci bir yöneticinin onayına sunuldu.')
            except ValueError as exc: flash(str(exc))
        ok,bad=verify_events(allrows('SELECT * FROM events ORDER BY id'))
        return render_template('admin.html',r=one('SELECT r FROM settings')['r'],changes=allrows('SELECT * FROM policy_changes ORDER BY id DESC'),ok=ok,bad=bad,events=allrows('SELECT * FROM events ORDER BY id DESC LIMIT 30'))

    @app.post('/policy/<int:cid>/approve')
    @admin_required
    def approve_policy(cid):
        change=one('SELECT * FROM policy_changes WHERE id=?',(cid,))
        if not change: abort(404)
        if change['author']==g.user['id'] or change['approved_by']: abort(403)
        run('UPDATE settings SET r=? WHERE id=1',(change['r'],));run('UPDATE policy_changes SET approved_by=? WHERE id=?',(g.user['id'],cid));event('policy_changed',cid)
        flash('Politika onaylandı. Yalnız bundan sonra açılan oylamalara uygulanır.')
        return redirect(url_for('admin'))

    @app.get('/manifest.webmanifest')
    def manifest(): return app.send_static_file('manifest.webmanifest')
    @app.get('/sw.js')
    def sw(): return app.send_static_file('sw.js')
    return app

if __name__=='__main__':
    create_app().run(host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','5000')),debug=False)
