#!/usr/bin/env python3
import base64
import gzip
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog():
    manifest = load_json(DATA / "manifest.json")
    encoded = "".join((ROOT / path).read_text(encoding="utf-8").strip() for path in manifest.get("catalogFragments", []))
    if not encoded:
        raise RuntimeError("manifest.catalogFragments is empty")
    payload = json.loads(gzip.decompress(base64.b64decode(encoded)).decode("utf-8"))
    if isinstance(payload, list):
        return payload

    mains = payload.get("m", [])
    categories = payload.get("c", [])
    rows = []
    for row in payload.get("r", []):
        product_id, category_index, product_type = row
        main_index, category = categories[category_index]
        rows.append({
            "id": product_id,
            "mainCategory": mains[main_index],
            "category": category,
            "type": product_type,
        })
    return rows


def main():
    catalog = load_catalog()
    summary = load_json(DATA / "compliance-summary.json")

    by_main = defaultdict(lambda: {
        "total": 0,
        "checked": 0,
        "pending": 0,
        "green": 0,
        "yellow": 0,
        "red": 0,
        "pendingItems": [],
    })
    overall = {"total": 0, "checked": 0, "pending": 0, "green": 0, "yellow": 0, "red": 0}

    for product in catalog:
        main_category = product.get("mainCategory", "")
        entry = by_main[main_category]
        entry["total"] += 1
        overall["total"] += 1

        status = (summary.get(str(product["id"])) or {}).get("result", "pending")
        if status in {"green", "yellow", "red"}:
            entry["checked"] += 1
            entry[status] += 1
            overall["checked"] += 1
            overall[status] += 1
        else:
            entry["pending"] += 1
            overall["pending"] += 1
            entry["pendingItems"].append({
                "id": product["id"],
                "category": product.get("category", ""),
                "type": product.get("type", ""),
            })

    result = {
        "version": 1,
        "overall": overall,
        "mainCategories": {},
    }
    for main_category in sorted(by_main):
        entry = by_main[main_category]
        entry["pendingItems"].sort(key=lambda x: (x["category"], x["type"], x["id"]))
        result["mainCategories"][main_category] = entry

    out = DATA / "progress.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Progress: checked {overall['checked']}/{overall['total']}; "
        f"pending {overall['pending']}; GREEN {overall['green']} / "
        f"YELLOW {overall['yellow']} / RED {overall['red']}"
    )


if __name__ == "__main__":
    main()
