import sqlite3
import json
from pathlib import Path

config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("TOKEN CARD ANALYSIS")
print("=" * 70)

# Find token cards (Rarity = 0)
cursor.execute("""
    SELECT COUNT(*) FROM Cards
    WHERE Rarity = 0
""")

total_tokens = cursor.fetchone()[0]
print(f"\nTotal token cards: {total_tokens}")

# Check how many tokens have Parallax style
cursor.execute("""
    SELECT COUNT(*) FROM Cards
    WHERE Rarity = 0 AND tags LIKE '%1696804317%'
""")

tokens_with_parallax = cursor.fetchone()[0]
print(f"Tokens with Parallax style: {tokens_with_parallax}")
print(f"Tokens without Parallax: {total_tokens - tokens_with_parallax}")

# Sample tokens with Parallax
print(f"\n{'=' * 70}")
print("Sample tokens WITH Parallax style:")
print("=" * 70)

cursor.execute("""
    SELECT Order_Title, GrpId, ArtId, ExpansionCode, tags
    FROM Cards
    WHERE Rarity = 0 AND tags LIKE '%1696804317%'
    LIMIT 10
""")

for name, grp_id, art_id, exp, tags in cursor.fetchall():
    if name:
        tag_count = len(tags.split(',')) if tags else 0
        print(f"{name[:40]:40} [{exp}] GrpId:{grp_id} ({tag_count} tags)")

# Sample tokens WITHOUT Parallax
print(f"\n{'=' * 70}")
print("Sample tokens WITHOUT Parallax style:")
print("=" * 70)

cursor.execute("""
    SELECT Order_Title, GrpId, ArtId, ExpansionCode, tags
    FROM Cards
    WHERE Rarity = 0 AND (tags IS NULL OR tags NOT LIKE '%1696804317%')
    LIMIT 10
""")

for name, grp_id, art_id, exp, tags in cursor.fetchall():
    if name:
        tag_info = f"{len(tags.split(','))} tags" if tags else "no tags"
        print(f"{name[:40]:40} [{exp}] GrpId:{grp_id} ({tag_info})")

# Check specific token example
print(f"\n{'=' * 70}")
print("Example: Checking specific token types")
print("=" * 70)

# Look for common token types
token_types = ['soldier', 'zombie', 'goblin', 'elf', 'dragon']

for token_type in token_types:
    cursor.execute("""
        SELECT COUNT(*) FROM Cards
        WHERE Rarity = 0 AND LOWER(Order_Title) LIKE ?
    """, (f'%{token_type}%',))
    
    count = cursor.fetchone()[0]
    
    if count > 0:
        cursor.execute("""
            SELECT COUNT(*) FROM Cards
            WHERE Rarity = 0 
            AND LOWER(Order_Title) LIKE ?
            AND tags LIKE '%1696804317%'
        """, (f'%{token_type}%',))
        
        with_parallax = cursor.fetchone()[0]
        
        print(f"{token_type.capitalize():10} tokens: {count:4} total, {with_parallax:4} with Parallax ({with_parallax*100//count if count > 0 else 0}%)")

print(f"\n{'=' * 70}")
print("CONCLUSION:")
print("=" * 70)
print(f"✓ Token cards CAN have Parallax style")
print(f"✓ Current status: {tokens_with_parallax}/{total_tokens} tokens have Parallax")
print(f"✓ You can unlock Parallax for the remaining {total_tokens - tokens_with_parallax} tokens")
print("=" * 70)

conn.close()
