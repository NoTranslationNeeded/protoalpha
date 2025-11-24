import sqlite3
import json
from pathlib import Path

config_path = Path.home() / ".mtga_swapper" / "config.json"
with open(config_path, "r") as f:
    config = json.load(f)

db_path = config["DatabasePath"].strip().replace(">", "\\")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Search for Vivi
cursor.execute("""
    SELECT GrpId, ArtId, Order_Title, ExpansionCode, tags
    FROM Cards
    WHERE LOWER(Order_Title) LIKE '%vivi%'
""")

results = cursor.fetchall()

print(f"Found {len(results)} Vivi card(s):\n")

for grp_id, art_id, name, exp, tags in results:
    print(f"Card Name: {name}")
    print(f"  GrpId: {grp_id}")
    print(f"  ArtId: {art_id}")
    print(f"  Set: [{exp}]")
    
    if tags:
        tag_list = tags.split(',')
        print(f"  Total Tags: {len(tag_list)}")
        
        # Check for Parallax
        if '1696804317' in tag_list:
            print(f"    ✓ Has Parallax Style")
        
        # Show all tags
        print(f"  All Tags:")
        for tag in tag_list:
            tag = tag.strip()
            if tag == '1696804317':
                print(f"    - {tag} (Parallax)")
            else:
                print(f"    - {tag} (Unknown style)")
    else:
        print(f"  Tags: None")
    print()

conn.close()
