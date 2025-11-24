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
print("MTGA CARD STYLE & VARIANT SYSTEM ANALYSIS")
print("=" * 70)

# 1. Basic structure
cursor.execute("""
    SELECT 
        COUNT(DISTINCT GrpId) as unique_grpids,
        COUNT(DISTINCT ArtId) as unique_artids,
        COUNT(*) as total_rows
    FROM Cards WHERE Order_Title IS NOT NULL
""")

unique_grpids, unique_artids, total_rows = cursor.fetchone()
print(f"\n[1] DATABASE STRUCTURE:")
print(f"    Total entries: {total_rows}")
print(f"    Unique GrpIds: {unique_grpids}")
print(f"    Unique ArtIds: {unique_artids}")
print(f"    => Each row = One unique card variant")

# 2. Example: Cards with multiple printings
print(f"\n[2] EXAMPLE: Same card name, different printings/styles:")
print("-" * 70)

cursor.execute("""
    SELECT GrpId, ArtId, ExpansionCode, ArtSize, tags
    FROM Cards
    WHERE Order_Title = 'lightning bolt'
    ORDER BY GrpId
""")

print("   'Lightning Bolt' variants:")
for grp_id, art_id, exp, art_size, tags in cursor.fetchall():
    tag_info = f"{len(tags.split(','))} tags" if tags else "no tags"
    print(f"      GrpId:{grp_id:6} ArtId:{art_id:6} Set:[{exp:4}] Size:{art_size} ({tag_info})")

# 3. How styles work
print(f"\n[3] HOW STYLES WORK:")
print("-" * 70)
print("   - Each GrpId is a UNIQUE card entry (specific printing)")
print("   - ArtId points to the actual image file")
print("   - 'tags' column contains style IDs (comma-separated)")
print("   - Adding '1696804317' to tags = Unlocks Parallax style")
print("   - Different GrpIds of same card = Different sets/arts")

# 4. Style unlocking implications
print(f"\n[4] STYLE UNLOCKING IMPLICATIONS:")
print("-" * 70)

cursor.execute("""
    SELECT Order_Title, COUNT(DISTINCT GrpId) as variants
    FROM Cards
    WHERE Order_Title = 'shock'
    GROUP BY Order_Title
""")

result = cursor.fetchone()
if result:
    name, variant_count = result
    print(f"   Example: '{name}' has {variant_count} variants (different sets)")
    
    cursor.execute("""
        SELECT GrpId, ExpansionCode, tags
        FROM Cards
        WHERE Order_Title = ?
    """, (name,))
    
    for grp_id, exp, tags in cursor.fetchall():
        has_parallax = '1696804317' in (tags or '')
        status = "✓ Parallax" if has_parallax else "✗ No Parallax"
        print(f"      GrpId:{grp_id} [{exp}] {status}")
    
    print(f"\n   => Unlocking style affects EACH variant separately!")
    print(f"   => If you own multiple printings, unlock each GrpId")

# 5. What happens when you unlock a style
print(f"\n[5] WHAT HAPPENS WHEN YOU UNLOCK A STYLE:")
print("-" * 70)
print("   1. Your code modifies the 'tags' column for a specific GrpId")
print("   2. Adds '1696804317' to enable Parallax animation")
print("   3. The ArtId (image) stays the SAME")
print("   4. Only the visual EFFECT changes (parallax animation)")
print("   5. Different styles use different tag IDs")

# 6. Alternative art vs styles
print(f"\n[6] ALTERNATIVE ART vs STYLES:")
print("-" * 70)
print("   ALTERNATIVE ART:")
print("      - Different GrpId")
print("      - Different ArtId (different image file)")
print("      - Example: Showcase frame, Borderless, Extended art")
print("      - These are SEPARATE card entries")
print()
print("   STYLES (via tags):")
print("      - Same GrpId")
print("      - Same ArtId (same image)")
print("      - Only adds visual EFFECTS (parallax, animation)")
print("      - Controlled by 'tags' column")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print("✓ Each GrpId = One specific card printing")
print("✓ Styles are EFFECTS applied to existing art (via tags)")
print("✓ Alternative arts are DIFFERENT cards (different GrpId/ArtId)")
print("✓ Unlocking Parallax adds tag '1696804317' to that specific GrpId")
print("✓ If you have multiple printings, each needs separate unlock")
print("=" * 70)

conn.close()
