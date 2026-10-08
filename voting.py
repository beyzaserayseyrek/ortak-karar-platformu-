"""Voting lifecycle; called inside the request transaction or a seed transaction."""
import json
from policy import policy_for, check_rules, LABELS
from storage import one, allrows, run, now, event, award, notify

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
    voting_policy = policy_for(p['restrictive'])
    result = voting_policy.evaluate([v['choice'] for v in votes], len(voters), p['r'])
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


