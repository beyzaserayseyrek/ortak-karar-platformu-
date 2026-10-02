"""Explicit, deterministic classroom policy; no AI decisions."""
import hashlib
import json

RULES = {
    'R1': 'Kişisel bilgilerin herkese açılmasına izin verilmez.',
    'R2': 'Bir grubun öğrenme ve katılım hakkı kaldırılamaz.',
    'R3': 'İçerik gizleme ve hak kısıtlayan kararlar gerekçeli yönetici incelemesi ister.',
    'R4': 'Doğrudan etkilenen her grubun katılımı ayrıca eşiği sağlamalıdır.',
}
EFFECTS = {'learning': 'Öğrenme / içerik düzenleme', 'publish_private': 'Özel bilgileri yayımlama', 'exclude_group': 'Grubun katılım hakkını kaldırma', 'hide_content': 'İçerik gizleme'}


def tally(choices, eligible, r):
    counts = {key: choices.count(key) for key in ('accept', 'reject', 'abstain')}
    participation = len(choices) / eligible if eligible else 0
    if not eligible or participation < r:
        status, reason = 'insufficient', 'Seçmen yok veya minimum katılım oranı sağlanmadı.'
    elif counts['accept'] + counts['reject'] == 0:
        status, reason = 'rejected', 'Kabul veya ret oyu yok; yalnız çekimser oylarla kabul oluşmaz.'
    elif counts['accept'] > counts['reject']:
        status, reason = 'accepted', 'Katılım yeterli ve kabul oyları kabul + ret oylarının yarısından fazla.'
    else:
        status, reason = 'rejected', 'Kabul çoğunluğu oluşmadı; eşitlikte öneri reddedilir.'
    return dict(status=status, reason=reason, counts=counts, participation=participation, eligible=eligible)


def check_rules(proposal, group_rates, counts):
    violations = []
    if proposal['effect'] == 'publish_private': violations.append('R1')
    if proposal['effect'] == 'exclude_group': violations.append('R2')
    threshold = max(proposal['r'], .67) if proposal['restrictive'] else proposal['r']
    if any(rate < threshold for rate in group_rates): violations.append('R4')
    if proposal['restrictive']:
        decisive = counts['accept'] + counts['reject']
        if not proposal['review'] or not proposal['reviewer'] or not decisive or counts['accept'] / decisive < 2 / 3:
            violations.append('R3')
    return violations


def event_digest(kind, object_id, stamp, previous):
    value = json.dumps([kind, object_id, stamp, previous], separators=(',', ':'))
    return hashlib.sha256(value.encode()).hexdigest()


def verify_events(rows):
    previous = '0' * 64
    for row in rows:
        expected = event_digest(row['kind'], row['object_id'], row['stamp'], previous)
        if row['previous'] != previous or row['digest'] != expected:
            return False, row['id']
        previous = expected
    return True, None
