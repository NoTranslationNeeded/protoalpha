import sqlite3
import json
from pathlib import Path
from collections import defaultdict

config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

target_tag = "-166024499"

print("=" * 70)
print(f"Cards using style tag: {target_tag}")
print("=" * 70)

# Get all cards with this tag
cursor.execute("""
    SELECT Order_Title, GrpId, ArtId, ExpansionCode, tags
    FROM Cards
    WHERE tags LIKE ?
    ORDER BY ExpansionCode, Order_Title
    LIMIT 100
""", (f'%{target_tag}%',))

results = cursor.fetchall()

print(f"\nFound {len(results)} cards (showing first 100):\n")

# Group by expansion
by_expansion = defaultdict(list)

for name, grp_id, art_id, exp, tags in results:
    if name and exp:  # Check for None
        by_expansion[exp].append((name, grp_id, art_id, tags or ""))

# Display by expansion
for exp in sorted(by_expansion.keys()):
    cards = by_expansion[exp]
    print(f"\n[{exp}] - {len(cards)} cards:")
    
    for name, grp_id, art_id, tags in cards[:15]:  # Show max 15 per set
        tag_count = len(tags.split(',')) if tags else 0
        has_parallax = '1696804317' in tags
        parallax_str = " + Parallax" if has_parallax else ""
        
        print(f"  {name[:35]:35} GrpId:{grp_id:6} ({tag_count} tags{parallax_str})")
    
    if len(cards) > 15:
        print(f"  ... and {len(cards) - 15} more")

# Get total count
cursor.execute("""
    SELECT COUNT(*) FROM Cards
    WHERE tags LIKE ?
""", (f'%{target_tag}%',))

total = cursor.fetchone()[0]

print(f"\n{'=' * 70}")
print(f"TOTAL: {total} cards use style tag {target_tag}")
print("=" * 70)

# Check what sets use this tag most
cursor.execute("""
    SELECT ExpansionCode, COUNT(*) as count
    FROM Cards
    WHERE tags LIKE ?
    GROUP BY ExpansionCode
    ORDER BY count DESC
""", (f'%{target_tag}%',))

print(f"\nSets using this style:")
for exp, count in cursor.fetchall():
    print(f"  [{exp}]: {count} cards")

conn.close()
