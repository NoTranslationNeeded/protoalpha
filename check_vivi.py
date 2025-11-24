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
print("VIVI ORNITIER - STYLE ANALYSIS")
print("=" * 70)

# Search for Vivi
cursor.execute("""
    SELECT GrpId, ArtId, Order_Title, ExpansionCode, ArtSize, tags
    FROM Cards
    WHERE LOWER(Order_Title) LIKE '%vivi%'
    ORDER BY GrpId
""")

results = cursor.fetchall()

if not results:
    print("\nNo cards found matching 'Vivi'")
else:
    print(f"\nFound {len(results)} Vivi variant(s):\n")
    
    for grp_id, art_id, name, exp_code, art_size, tags in results:
        print(f"Card: {name}")
        print(f"  GrpId: {grp_id}")
        print(f"  ArtId: {art_id}")
        print(f"  Set: [{exp_code}]")
        print(f"  ArtSize: {art_size}")
        
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            print(f"  Tags ({len(tag_list)} total):")
            
            # Check for known styles
            has_parallax = '1696804317' in tag_list
            other_tags = [t for t in tag_list if t != '1696804317']
            
            if has_parallax:
                print(f"    ✓ Parallax Style (1696804317)")
            
            if other_tags:
                print(f"    Other style tags:")
                for tag in other_tags:
                    print(f"      - {tag}")
            
            print(f"  Raw tags: {tags}")
        else:
            print(f"  Tags: None (no styles)")
        
        print()

# Check if there are any other FF-themed cards
print("\n" + "=" * 70)
print("OTHER FINAL FANTASY CARDS (for comparison):")
print("=" * 70)

cursor.execute("""
    SELECT DISTINCT Order_Title, COUNT(*) as count
    FROM Cards
    WHERE (LOWER(Order_Title) LIKE '%cloud%' 
       OR LOWER(Order_Title) LIKE '%squall%'
       OR LOWER(Order_Title) LIKE '%lightning%'
       OR LOWER(Order_Title) LIKE '%sephiroth%')
    AND ExpansionCode LIKE '%SLD%'
    GROUP BY Order_Title
    LIMIT 5
""")

ff_cards = cursor.fetchall()
if ff_cards:
    print("\nOther FF Secret Lair cards found:")
    for name, count in ff_cards:
        print(f"  - {name} ({count} variant(s))")
        
        # Get tag info for first variant
        cursor.execute("""
            SELECT tags FROM Cards
            WHERE Order_Title = ?
            LIMIT 1
        """, (name,))
        
        result = cursor.fetchone()
        if result and result[0]:
            tag_count = len(result[0].split(','))
            print(f"    Tags: {tag_count} style(s)")
else:
    print("\nNo other FF cards found in Secret Lair sets")

conn.close()

print("\n" + "=" * 70)
print("SUMMARY:")
print("=" * 70)
print("Check the output above to see:")
print("  1. How many Vivi variants exist")
print("  2. What style tags each variant has")
print("  3. Whether there are styles beyond Parallax")
print("=" * 70)
