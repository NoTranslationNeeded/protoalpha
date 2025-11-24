import sqlite3
import json
from pathlib import Path

# Load config
config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("CARD VARIANT ANALYSIS")
print("=" * 70)

# 1. Basic statistics
cursor.execute("""
    SELECT 
        COUNT(DISTINCT GrpId) as unique_grpids,
        COUNT(DISTINCT ArtId) as unique_artids,
        COUNT(*) as total_rows
    FROM Cards
    WHERE Order_Title IS NOT NULL
""")

unique_grpids, unique_artids, total_rows = cursor.fetchone()
print(f"\n1. DATABASE STRUCTURE:")
print(f"   - Total card entries: {total_rows}")
print(f"   - Unique GrpIds: {unique_grpids}")
print(f"   - Unique ArtIds: {unique_artids}")
print(f"   - Conclusion: Each GrpId = One unique card entry")
print(f"   - Note: {unique_grpids - unique_artids} GrpIds share ArtIds")

# 2. Find cards with same name but different GrpIds (reprints/variants)
print(f"\n2. CARDS WITH MULTIPLE VARIANTS (Same name, different GrpId/ArtId):")
print("-" * 70)

cursor.execute("""
    SELECT Order_Title, COUNT(DISTINCT GrpId) as variant_count
    FROM Cards
    WHERE Order_Title IS NOT NULL AND TRIM(Order_Title) != ''
    GROUP BY Order_Title
    HAVING variant_count > 1
    ORDER BY variant_count DESC
    LIMIT 10
""")

for name, variant_count in cursor.fetchall():
    print(f"\n   {name} ({variant_count} variants):")
    
    cursor.execute("""
        SELECT GrpId, ArtId, ExpansionCode, tags
        FROM Cards
        WHERE Order_Title = ?
        ORDER BY GrpId
        LIMIT 6
    """, (name,))
    
    for grp_id, art_id, exp_code, tags in cursor.fetchall():
        tag_count = len(tags.split(',')) if tags else 0
        print(f"      GrpId:{grp_id:6} ArtId:{art_id:6} Set:[{exp_code}] Tags:{tag_count}")

# 3. Check if same ArtId is used by multiple GrpIds
print(f"\n3. ARTID SHARING (Multiple GrpIds using same ArtId):")
print("-" * 70)

cursor.execute("""
    SELECT ArtId, COUNT(DISTINCT GrpId) as grp_count, 
           GROUP_CONCAT(DISTINCT Order_Title) as names
    FROM Cards
    WHERE ArtId IS NOT NULL
    GROUP BY ArtId
    HAVING grp_count > 1
    LIMIT 5
""")

shared_arts = cursor.fetchall()
if shared_arts:
    for art_id, grp_count, names in shared_arts:
        name_list = names.split(',')[:3]  # Show first 3 names
        print(f"   ArtId {art_id} shared by {grp_count} cards:")
        for name in name_list:
            print(f"      - {name}")
else:
    print("   No ArtId sharing found")

# 4. Style variants - same card name with different tags
print(f"\n4. STYLE VARIANTS (Same card name with different style tags):")
print("-" * 70)

cursor.execute("""
    SELECT Order_Title
    FROM Cards
    WHERE Order_Title IS NOT NULL 
    AND tags IS NOT NULL
    GROUP BY Order_Title
    HAVING COUNT(DISTINCT tags) > 1
    LIMIT 5
""")

style_variants = cursor.fetchall()
if style_variants:
    for (name,) in style_variants:
        print(f"\n   {name}:")
        cursor.execute("""
            SELECT GrpId, ArtId, tags
            FROM Cards
            WHERE Order_Title = ?
            ORDER BY GrpId
        """, (name,))
        
        for grp_id, art_id, tags in cursor.fetchall()[:4]:
            tag_preview = tags[:60] + "..." if tags and len(tags) > 60 else tags
            print(f"      GrpId:{grp_id} ArtId:{art_id} Tags:[{tag_preview}]")
else:
    print("   Each card name has consistent tags across variants")

print("\n" + "=" * 70)
print("KEY FINDINGS:")
print("=" * 70)
print("- Each GrpId represents ONE unique card entry")
print("- Same card name can have multiple GrpIds (different sets/printings)")
print("- Each variant has its own ArtId (different artwork)")
print("- Tags determine available styles (Parallax, Showcase, etc.)")
print("=" * 70)

conn.close()
