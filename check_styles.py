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

# Get all unique tag values
cursor.execute("SELECT tags FROM Cards WHERE tags IS NOT NULL AND TRIM(tags) != ''")
rows = cursor.fetchall()

# Parse all individual tag IDs
all_tags = []
for row in rows:
    tags_str = row[0]
    if tags_str:
        # Split by comma and strip whitespace
        tag_ids = [tag.strip() for tag in tags_str.split(',')]
        all_tags.extend(tag_ids)

# Count occurrences
tag_counts = Counter(all_tags)

print("=== Style Tag IDs found in database ===\n")
print(f"Total unique tag IDs: {len(tag_counts)}\n")

# Sort by frequency
for tag_id, count in tag_counts.most_common(20):
    print(f"Tag ID: {tag_id:15} - Used in {count:5} cards")

# Check for known style IDs
print("\n=== Known Style IDs ===")
known_styles = {
    "1696804317": "Parallax Style",
    "1696804318": "Showcase Style", 
    "1696804319": "Borderless Style",
    "1696804320": "Extended Art"
}

for style_id, style_name in known_styles.items():
    count = tag_counts.get(style_id, 0)
    print(f"{style_name:20} ({style_id}): {count} cards")

conn.close()
