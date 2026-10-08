"""SQLite request storage and transactional event/point/notification writes."""
import sqlite3
import time
from flask import g
from policy import event_digest

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


