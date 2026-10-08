"""Explicit, deterministic classroom policy; no AI decisions."""
import hashlib
import json
from typing import Protocol
from dataclasses import dataclass
from collections.abc import Callable

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


class VotingPolicy(Protocol):
    def threshold(self, r: float) -> float: ...
    def evaluate(self, choices: list[str], eligible: int, r: float) -> dict: ...


class StandardVotingPolicy:
    def threshold(self, r): return r

    def evaluate(self, choices, eligible, r):
        return tally(choices, eligible, self.threshold(r))


class RestrictiveVotingPolicy(StandardVotingPolicy):
    def threshold(self, r): return max(r, .67)


def policy_for(restrictive) -> VotingPolicy:
    return RestrictiveVotingPolicy() if restrictive else StandardVotingPolicy()


@dataclass
class RuleContext:
    proposal: object
    group_rates: list[float]
    counts: dict


@dataclass
class RuleHandler:
    """A collecting chain: every handler delegates, even after a violation."""
    code: str
    fails: Callable[[RuleContext], bool]
    successor: 'RuleHandler | None' = None

    def check(self, context: RuleContext) -> list[str]:
        result = [self.code] if self.fails(context) else []
        if self.successor:
            result.extend(self.successor.check(context))
        return result


def review_missing(context):
    p, counts = context.proposal, context.counts
    decisive = counts['accept'] + counts['reject']
    return bool(p['restrictive'] and (
        not p['review'] or not p['reviewer'] or not decisive
        or counts['accept'] * 3 < decisive * 2))


def build_rule_chain():
    review = RuleHandler('R3', review_missing)
    participation = RuleHandler('R4', lambda c: any(
        rate < policy_for(c.proposal['restrictive']).threshold(c.proposal['r'])
        for rate in c.group_rates), review)
    exclusion = RuleHandler('R2', lambda c: c.proposal['effect'] == 'exclude_group', participation)
    return RuleHandler('R1', lambda c: c.proposal['effect'] == 'publish_private', exclusion)


RULE_CHAIN = build_rule_chain()


def check_rules(proposal, group_rates, counts):
    return RULE_CHAIN.check(RuleContext(proposal, group_rates, counts))


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


LABELS = {'draft': '✎ Taslak', 'voting': '◷ Oylamada', 'accepted': '✓ Kabul', 'rejected': '× Ret', 'insufficient': '! Katılım yetersiz'}
