#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def load(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def main():
    sources = load('sources.json').get('sources', {})
    registry = load('regulations.json')
    allowed = set(registry.get('statuses', []))
    errors = []
    warnings = []

    rules = registry.get('rules', {})
    if not rules:
        errors.append('regulations.json: rules is empty')

    for rule_id, rule in rules.items():
        status = rule.get('status')
        if status not in allowed:
            errors.append(f'{rule_id}: invalid status {status!r}')
        source_ids = rule.get('sourceIds', [])
        if not source_ids:
            errors.append(f'{rule_id}: no sourceIds')
        for source_id in source_ids:
            if source_id not in sources:
                errors.append(f'{rule_id}: missing source {source_id}')
        if not rule.get('reviewedAt'):
            errors.append(f'{rule_id}: reviewedAt is required')
        if not rule.get('match'):
            errors.append(f'{rule_id}: match definition is required')
        if not rule.get('effect'):
            errors.append(f'{rule_id}: effect definition is required')

        until = rule.get('effectiveUntil')
        if until:
            try:
                days = (date.fromisoformat(until) - date.today()).days
                if days < 0 and status not in {'expired', 'review'}:
                    warnings.append(f'{rule_id}: effectiveUntil {until} has passed; review status')
                elif days <= 30:
                    warnings.append(f'{rule_id}: effectiveUntil {until} is within 30 days')
            except ValueError:
                errors.append(f'{rule_id}: invalid effectiveUntil {until!r}')

        future = rule.get('effectiveFrom')
        if status == 'future' and not future:
            errors.append(f'{rule_id}: future rule requires effectiveFrom')

    if errors:
        print('REGULATORY DATA VALIDATION FAILED')
        for item in errors:
            print(f'ERROR: {item}')
        raise SystemExit(1)

    print(f'Regulatory registry OK: {len(rules)} rules, {len(sources)} sources')
    for item in warnings:
        print(f'WARNING: {item}')


if __name__ == '__main__':
    main()
