#!/usr/bin/env python3
import json
from pathlib import Path
import build_furniture as furniture

DATA = furniture.DATA


def load_all_furniture_rows():
    d = json.loads((DATA / 'catalog-dict.json').read_text(encoding='utf-8'))
    cats = d['c']
    out = []
    for path in sorted((DATA / 'catalog').glob('part-*.json')):
        rows = json.loads(path.read_text(encoding='utf-8'))
        for pid, cat_idx, name in rows:
            if furniture.START_ID <= int(pid) <= furniture.END_ID and cats[cat_idx][0] == furniture.FURNITURE_MAIN_INDEX:
                out.append({'id': int(pid), 'name': name, 'category': cats[cat_idx][1]})
    out.sort(key=lambda x: x['id'])
    if len(out) != 227:
        raise SystemExit(f'Furniture catalog mismatch: expected 227, got {len(out)}')
    if out[0]['id'] != 4042 or out[-1]['id'] != 4268:
        raise SystemExit(f"Furniture ID range mismatch: {out[0]['id']}..{out[-1]['id']}")
    return out


if __name__ == '__main__':
    furniture.load_catalog_rows = load_all_furniture_rows
    furniture.main()
