#!/usr/bin/env python3
import json
import build_furniture as furniture

INDEX = furniture.ROOT / 'data-src' / 'furniture-index.json'


def load_verified_furniture_rows():
    obj = json.loads(INDEX.read_text(encoding='utf-8'))
    out = obj.get('items', [])
    out.sort(key=lambda x: int(x['id']))
    if len(out) != 227:
        raise SystemExit(f'Furniture index mismatch: expected 227, got {len(out)}')
    if int(out[0]['id']) != 4042 or int(out[-1]['id']) != 4268:
        raise SystemExit(f"Furniture ID range mismatch: {out[0]['id']}..{out[-1]['id']}")
    if len({int(x['id']) for x in out}) != 227:
        raise SystemExit('Furniture duplicate IDs detected')
    return [{'id': int(x['id']), 'name': x['name'], 'category': x['category']} for x in out]


if __name__ == '__main__':
    furniture.load_catalog_rows = load_verified_furniture_rows
    furniture.main()
