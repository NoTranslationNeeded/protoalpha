import sqlite3
import json
from pathlib import Path

# Load config
config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count total cards with names
cursor.execute("SELECT COUNT(*) FROM Cards WHERE Order_Title IS NOT NULL AND TRIM(Order_Title) != ''")
total = cursor.fetchone()[0]
print(f"Total cards with names: {total}")

# Count basic lands (case-insensitive)
basic_lands = ["island", "forest", "mountain", "plains", "swamp", "wastes"]
basic_count = 0
for land in basic_lands:
    cursor.execute(f"SELECT COUNT(*) FROM Cards WHERE LOWER(Order_Title) LIKE '{land}%'")
    count = cursor.fetchone()[0]
    print(f"  {land.capitalize()}: {count}")
    basic_count += count

print(f"\nTotal basic lands: {basic_count}")
print(f"Unlockable cards (excluding basic lands): {total - basic_count}")

conn.close()
