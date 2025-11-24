import sqlite3
import json
from pathlib import Path

config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("TOKEN CARD ANALYSIS")
print("=" * 60)

# Total tokens
cursor.execute("SELECT COUNT(*) FROM Cards WHERE Rarity = 0")
total_tokens = cursor.fetchone()[0]
print(f"\nTotal token cards: {total_tokens}")

# Tokens with Parallax
cursor.execute("SELECT COUNT(*) FROM Cards WHERE Rarity = 0 AND tags LIKE '%1696804317%'")
tokens_with_parallax = cursor.fetchone()[0]
print(f"Tokens with Parallax: {tokens_with_parallax}")
print(f"Tokens without Parallax: {total_tokens - tokens_with_parallax}")

# Percentage
percentage = (tokens_with_parallax * 100 // total_tokens) if total_tokens > 0 else 0
print(f"Percentage with Parallax: {percentage}%")

# Sample tokens WITH Parallax
print(f"\nSample tokens WITH Parallax (5 examples):")
cursor.execute("""
    SELECT Order_Title, GrpId, ExpansionCode
    FROM Cards
    WHERE Rarity = 0 AND tags LIKE '%1696804317%'
    AND Order_Title IS NOT NULL
    LIMIT 5
""")

for name, grp_id, exp in cursor.fetchall():
    print(f"  - {name[:35]:35} [{exp}] GrpId:{grp_id}")

# Sample tokens WITHOUT Parallax
print(f"\nSample tokens WITHOUT Parallax (5 examples):")
cursor.execute("""
    SELECT Order_Title, GrpId, ExpansionCode
    FROM Cards
    WHERE Rarity = 0 
    AND (tags IS NULL OR tags NOT LIKE '%1696804317%')
    AND Order_Title IS NOT NULL
    LIMIT 5
""")

for name, grp_id, exp in cursor.fetchall():
    print(f"  - {name[:35]:35} [{exp}] GrpId:{grp_id}")

print(f"\n{'=' * 60}")
print("CONCLUSION:")
print(f"  YES - Token cards CAN have Parallax style!")
print(f"  Currently {tokens_with_parallax}/{total_tokens} tokens have it")
print(f"  You can unlock it for the remaining {total_tokens - tokens_with_parallax} tokens")
print("=" * 60)

conn.close()
