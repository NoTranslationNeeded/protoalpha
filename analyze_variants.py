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

print("=== Cards with Multiple Styles (Same GrpId, Different ArtId) ===\n")

# Find cards that have the same name but different ArtIds
cursor.execute("""
    SELECT Order_Title, COUNT(DISTINCT ArtId) as art_count, 
           COUNT(DISTINCT GrpId) as grp_count,
           GROUP_CONCAT(DISTINCT GrpId) as grp_ids
    FROM Cards
    WHERE Order_Title IS NOT NULL AND TRIM(Order_Title) != ''
    GROUP BY Order_Title
    HAVING art_count > 1
    ORDER BY art_count DESC
    LIMIT 20
""")

print("Top 20 cards with multiple art variants:\n")
for name, art_count, grp_count, grp_ids in cursor.fetchall():
    print(f"{name[:40]:40} - {art_count} different arts, {grp_count} GrpIds")
    
    # Get details for each variant
    cursor.execute("""
        SELECT GrpId, ArtId, ExpansionCode, ArtSize, tags
        FROM Cards
        WHERE Order_Title = ?
        ORDER BY GrpId
    """, (name,))
    
    variants = cursor.fetchall()
    for grp_id, art_id, exp_code, art_size, tags in variants[:5]:  # Show max 5 variants
        tag_list = tags.split(',') if tags else []
        # Check for special styles
        has_parallax = '1696804317' in tag_list
        other_tags = [t for t in tag_list if t != '1696804317']
        
        style_info = []
        if has_parallax:
            style_info.append("Parallax")
        if other_tags:
            style_info.append(f"{len(other_tags)} other tags")
        
        style_str = f" [{', '.join(style_info)}]" if style_info else ""
        
        print(f"  GrpId:{grp_id:6} ArtId:{art_id:6} [{exp_code}] ArtSize:{art_size}{style_str}")
    
    if len(variants) > 5:
        print(f"  ... and {len(variants) - 5} more variants")
    print()

# Now check: same GrpId but different styles
print("\n=== Same Card (GrpId) with Multiple Style Entries ===\n")

cursor.execute("""
    SELECT GrpId, COUNT(*) as count
    FROM Cards
    GROUP BY GrpId
    HAVING count > 1
    LIMIT 10
""")

duplicate_grpids = cursor.fetchall()
if duplicate_grpids:
    print(f"Found {len(duplicate_grpids)} GrpIds with multiple entries:\n")
    
    for grp_id, count in duplicate_grpids[:5]:
        cursor.execute("""
            SELECT Order_Title, ArtId, ExpansionCode, ArtSize, tags
            FROM Cards
            WHERE GrpId = ?
        """, (grp_id,))
        
        print(f"GrpId {grp_id} ({count} entries):")
        for name, art_id, exp_code, art_size, tags in cursor.fetchall():
            print(f"  {name[:35]:35} ArtId:{art_id} [{exp_code}] Tags:{tags[:50] if tags else 'None'}")
        print()
else:
    print("No duplicate GrpIds found - each GrpId is unique!\n")

# Check the relationship between GrpId and ArtId
print("\n=== GrpId vs ArtId Relationship ===\n")

cursor.execute("""
    SELECT 
        COUNT(DISTINCT GrpId) as unique_grpids,
        COUNT(DISTINCT ArtId) as unique_artids,
        COUNT(*) as total_rows
    FROM Cards
    WHERE Order_Title IS NOT NULL
""")

unique_grpids, unique_artids, total_rows = cursor.fetchone()
print(f"Unique GrpIds: {unique_grpids}")
print(f"Unique ArtIds: {unique_artids}")
print(f"Total card rows: {total_rows}")
print(f"\nConclusion: {'Each row is a unique card variant' if total_rows == unique_grpids else 'Multiple rows can share the same GrpId'}")

conn.close()
