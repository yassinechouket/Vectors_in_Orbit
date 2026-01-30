import json

input_file = "public/data/reference_catalog_clean.jsonl"
output_file = "public/data/reference_catalog_clean.json"

items = []
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        items.append(json.loads(line))

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"✅ Converted {len(items)} products to {output_file}")
