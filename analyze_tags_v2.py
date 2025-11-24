import sqlite3
import json
from pathlib import Path
from collections import Counter

# Load config
config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get top 10 most common non-Parallax tags
print("=== Top 10 Non-Parallax Style Tags ===\n")

cursor.execute("""
    SELECT tags FROM Cards 
    WHERE tags IS NOT NULL 
    AND TRIM(tags) != ''
""")

all_tags = []
for row in cursor.fetchall():
    tags_str = row[0]
    if tags_str:
        tag_ids = [tag.strip() for tag in tags_str.split(',') if tag.strip() != '1696804317']
        all_tags.extend(tag_ids)

tag_counts = Counter(all_tags)

for i, (tag_id, count) in enumerate(tag_counts.most_common(10), 1):
    print(f"{i}. Tag ID: {tag_id:15} ({count:5} cards)")
    
    # Get 3 sample cards for this tag
    cursor.execute("""
        SELECT Order_Title, ExpansionCode, ArtSize
        FROM Cards 
        WHERE tags LIKE ?
        LIMIT 3
    """, (f'%{tag_id}%',))
    
    samples = cursor.fetchall()
    for name, set_code, art_size in samples:
        print(f"   - {name[:35]:35} [{set_code}] ArtSize:{art_size}")
    print()

# Check ArtSize correlation
print("\n=== ArtSize Analysis ===")
print("(ArtSize might indicate different card styles)\n")

for art_size in [0, 1, 2, 3]:
    cursor.execute("""
        SELECT COUNT(*) FROM Cards 
        WHERE ArtSize = ? AND tags IS NOT NULL AND tags != '1696804317'
    """, (art_size,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        cursor.execute("""
            SELECT Order_Title, ExpansionCode
            FROM Cards 
            WHERE ArtSize = ? AND tags IS NOT NULL AND tags != '1696804317'
            LIMIT 2
        """, (art_size,))
        samples = cursor.fetchall()
        
        print(f"ArtSize {art_size}: {count} cards")
        for name, set_code in samples:
            print(f"  - {name[:40]:40} [{set_code}]")
        print()

conn.close()
