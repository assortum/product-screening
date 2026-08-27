#!/usr/bin/env python3
import base64
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digits(value):
    return re.sub(r'\D', '', str(value or ''))


def load_catalog():
    manifest = load(DATA / 'manifest.json')
    encoded = ''.join((ROOT / path).read_text(encoding='utf-8').strip() for path in manifest.get('catalogFragments', []))
    payload = json.loads(gzip.decompress(base64.b64decode(encoded)).decode('utf-8'))
    if isinstance(payload, list):
        return {str(x['id']): x for x in payload}
    mains = payload.get('m', [])
    categories = payload.get('c', [])
    out = {}
    for row in payload.get('r', []):
        pid, category_index, product_type = row
        main_index, category = categories[category_index]
        out[str(pid)] = {
            'id': pid,
            'mainCategory': mains[main_index],
            'category': category,
            'type': product_type,
        }
    return out


def rule_codes(rule):
    match = rule.get('match', {})
    values = []
    values.extend(match.get('tnvedPrefixes', []))
    values.extend(match.get('tnved', []))
    return [digits(x) for x in values if digits(x)]


def code_intersects(product_code, rule_code):
    p = digits(product_code)
    r = digits(rule_code)
    if len(p) < 4 or len(r) < 4:
        return False
    return p.startswith(r) or r.startswith(p)


def main():
    summary = load(DATA / 'compliance-summary.json')
    registry = load(DATA / 'regulations.json')
    catalog = load_catalog()

    report = {
        'version': 1,
        'generatedFromRegistryReview': registry.get('lastReviewed'),
        'rules': {},
        'totalPotentialMatches': 0,
        'note': 'Potential match is a review queue, not an automatic legal conclusion. Rules requiring OKPD2/name/age remain potential until those conditions are confirmed.'
    }

    for rule_id, rule in registry.get('rules', {}).items():
        codes = rule_codes(rule)
        matches = []
        if not codes:
            continue
        logic = rule.get('match', {}).get('logic', 'tnved')
        for pid, item in summary.items():
            product_codes = item.get('tnvedCodes') or []
            matched = []
            for pcode in product_codes:
                for rcode in codes:
                    if code_intersects(pcode, rcode):
                        matched.append({'productCode': pcode, 'ruleCode': rcode})
            if not matched:
                continue
            row = catalog.get(pid, {})
            confidence = 'direct-code-candidate' if logic in {'tnved', 'tnved-prefix'} else 'potential-requires-extra-fields'
            matches.append({
                'id': int(pid),
                'type': row.get('type', ''),
                'mainCategory': row.get('mainCategory', ''),
                'category': row.get('category', ''),
                'currentScreeningResult': item.get('result', 'pending'),
                'confidence': confidence,
                'matched': matched[:6]
            })
        report['rules'][rule_id] = {
            'label': rule.get('label'),
            'status': rule.get('status'),
            'logic': logic,
            'count': len(matches),
            'products': matches
        }
        report['totalPotentialMatches'] += len(matches)

    (DATA / 'regulatory-impact.json').write_text(json.dumps(report, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f"Regulatory impact built: {report['totalPotentialMatches']} potential rule/product matches across {len(report['rules'])} rules")


if __name__ == '__main__':
    main()
