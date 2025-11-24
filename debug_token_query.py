import sqlite3
import json
from pathlib import Path

config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Checking token card query...")
print("=" * 60)

# Check what Rarity values exist
print("\n1. Checking Rarity values in database:")
cursor.execute("SELECT DISTINCT Rarity, COUNT(*) FROM Cards GROUP BY Rarity ORDER BY Rarity")
for rarity, count in cursor.fetchall():
    print(f"   Rarity {rarity}: {count} cards")

# Check if there are cards with Order_Title
print("\n2. Checking cards with Order_Title:")
cursor.execute("SELECT COUNT(*) FROM Cards WHERE Order_Title IS NOT NULL AND TRIM(Order_Title) != ''")
with_title = cursor.fetchone()[0]
print(f"   Cards with Order_Title: {with_title}")

# Try the exact query from our endpoint
print("\n3. Testing our token query:")
query = """
    SELECT COUNT(*)
    FROM Cards
    WHERE Rarity = 0
    AND Order_Title IS NOT NULL
    AND TRIM(Order_Title) != ''
"""
cursor.execute(query)
count = cursor.fetchone()[0]
print(f"   Result: {count} cards")

# Check without the Order_Title filter
print("\n4. Checking Rarity = 0 without Order_Title filter:")
cursor.execute("SELECT COUNT(*) FROM Cards WHERE Rarity = 0")
count_no_filter = cursor.fetchone()[0]
print(f"   Result: {count_no_filter} cards")

# Sample some Rarity = 0 cards
print("\n5. Sample Rarity = 0 cards:")
cursor.execute("SELECT GrpId, Order_Title, ArtId FROM Cards WHERE Rarity = 0 LIMIT 5")
for grp_id, title, art_id in cursor.fetchall():
    print(f"   GrpId:{grp_id} Title:'{title}' ArtId:{art_id}")

# Check schema
print("\n6. Checking Cards table schema:")
cursor.execute("PRAGMA table_info(Cards)")
columns = cursor.fetchall()
print("   Columns:")
for col in columns:
    print(f"     - {col[1]} ({col[2]})")

conn.close()
