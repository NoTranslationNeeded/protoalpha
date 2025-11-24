import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

db_path = find_mtga_db_path()
cursor, connection, _ = create_database_connection(db_path)

# Check all the reported vehicles
vehicles = {
    'BROKEN': [
        ('mobilizermech', 79489),
        ('dreadmobile', 90936),
        ('burnerrocket', 94916),
        ('esikaschariot', 75214)
    ],
    'WORKING': [
        ('ribskiff', 83940),
        ('soulshredder', 95366),
        ('apocalypserunner', 94990),
        ('carriageofdreams', 97988)
    ]
}

output = []
output.append("="*80)
output.append("HYPOTHESIS: Checking if mono-colored vs multi-colored matters")
output.append("="*80)

for status, card_list in vehicles.items():
    output.append(f"\n{status} VEHICLES:")
    for name, grp_id in card_list:
        cursor.execute("""
            SELECT Order_Title, Colors, ColorIdentity, AdditionalFrameDetails
            FROM Cards
            WHERE GrpId = ?
        """, (grp_id,))
        result = cursor.fetchone()
        if result:
            card_name, colors, color_id, frame = result
            color_count = len(str(colors).split(',')) if colors else 0
            output.append(f"  {card_name}:")
            output.append(f"    Colors: {colors} ({color_count} colors)")
            output.append(f"    Frame: '{frame if frame else '(mono-colored)'}'")

output.append("\n" + "="*80)
output.append("PATTERN ANALYSIS")
output.append("="*80)

# Check broken vehicles
broken_mono = 0
broken_multi = 0
for name, grp_id in vehicles['BROKEN']:
    cursor.execute("SELECT Colors, AdditionalFrameDetails FROM Cards WHERE GrpId = ?", (grp_id,))
    colors, frame = cursor.fetchone()
    color_count = len(str(colors).split(',')) if colors else 0
    if color_count <= 1 or not frame:
        broken_mono += 1
    else:
        broken_multi += 1

# Check working vehicles  
working_mono = 0
working_multi = 0
for name, grp_id in vehicles['WORKING']:
    cursor.execute("SELECT Colors, AdditionalFrameDetails FROM Cards WHERE GrpId = ?", (grp_id,))
    colors, frame = cursor.fetchone()
    color_count = len(str(colors).split(',')) if colors else 0
    if color_count <= 1 or not frame:
        working_mono += 1
    else:
        working_multi += 1

output.append(f"\nBROKEN vehicles:")
output.append(f"  Mono-colored: {broken_mono}")
output.append(f"  Multi-colored: {broken_multi}")

output.append(f"\nWORKING vehicles:")
output.append(f"  Mono-colored: {working_mono}")
output.append(f"  Multi-colored: {working_multi}")

if broken_mono > 0 and broken_multi == 0 and working_multi > 0:
    output.append("\n⚠️  PATTERN FOUND!")
    output.append("  ALL broken vehicles are MONO-COLORED")
    output.append("  WORKING vehicles include MULTI-COLORED cards")
    output.append("\n  💡 HYPOTHESIS CONFIRMED:")
    output.append("  Parallax bug affects MONO-COLORED vehicles!")

# Save
output_file = Path(__file__).parent / "color_pattern_analysis.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('\n'.join(output))
print(f"\n\nSaved to: {output_file}")

connection.close()
