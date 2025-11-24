import sqlite3
import json
from pathlib import Path
from collections import defaultdict

# Load config
config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get top tag IDs (excluding Parallax which we already know)
cursor.execute("""
    SELECT tags FROM Cards 
    WHERE tags IS NOT NULL 
    AND TRIM(tags) != ''
    AND tags != '1696804317'
    LIMIT 5000
""")
rows = cursor.fetchall()

# Collect tag samples
tag_samples = defaultdict(list)

for row in rows:
    tags_str = row[0]
    if tags_str:
        tag_ids = [tag.strip() for tag in tags_str.split(',')]
        for tag_id in tag_ids:
            if tag_id != '1696804317' and len(tag_samples[tag_id]) < 5:
                # Get card info for this tag
                cursor.execute("""
                    SELECT Order_Title, ExpansionCode, ArtSize, GrpId
                    FROM Cards 
                    WHERE tags LIKE ?
                    LIMIT 1
                """, (f'%{tag_id}%',))
                card = cursor.fetchone()
                if card and card not in tag_samples[tag_id]:
                    tag_samples[tag_id].append(card)

# Display results
print("=== Tag ID Analysis (Sample Cards) ===\n")

# Sort by number of samples (most common first)
sorted_tags = sorted(tag_samples.items(), key=lambda x: len(x[1]), reverse=True)

for i, (tag_id, cards) in enumerate(sorted_tags[:15], 1):
    print(f"\n{i}. Tag ID: {tag_id}")
    print(f"   Sample cards ({len(cards)}):")
    for card in cards[:5]:
        name, set_code, art_size, grp_id = card
        print(f"   - {name:40} [{set_code:5}] ArtSize:{art_size} GrpId:{grp_id}")

# Also check if there are any patterns in ArtSize
print("\n\n=== ArtSize Distribution for Non-Parallax Tags ===")
cursor.execute("""
    SELECT ArtSize, COUNT(*) as count
    FROM Cards
    WHERE tags IS NOT NULL 
    AND TRIM(tags) != ''
    AND tags != '1696804317'
    GROUP BY ArtSize
    ORDER BY count DESC
    LIMIT 10
""")

for art_size, count in cursor.fetchall():
    print(f"ArtSize {art_size}: {count} cards")

conn.close()
