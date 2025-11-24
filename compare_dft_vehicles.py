import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

db_path = find_mtga_db_path()
cursor, connection, _ = create_database_connection(db_path)

output = []

# Get column names
cursor.execute("PRAGMA table_info(Cards)")
columns = [col[1] for col in cursor.fetchall()]

output.append("Comparing Burner Rocket (BROKEN) vs Apocalypse Runner (WORKING)")
output.append("Both are DFT set, both are vehicles, both have parallax")
output.append("="*80)

# Get burner rocket data
cursor.execute("SELECT * FROM Cards WHERE GrpId = 94916")
burner_data = cursor.fetchone()
burner = dict(zip(columns, burner_data))

# Get apocalypse runner data
cursor.execute("SELECT * FROM Cards WHERE GrpId = 94990")
apocalypse_data = cursor.fetchone()
apocalypse = dict(zip(columns, apocalypse_data))

output.append(f"\nTotal columns: {len(columns)}\n")

# Find differences
differences = []
for col in columns:
    if burner.get(col) != apocalypse.get(col):
        differences.append(col)
        output.append(f"{col}:")
        output.append(f"  Burner (broken):     {burner.get(col)}")
        output.append(f"  Apocalypse (working): {apocalypse.get(col)}")
        output.append("")

output.append("="*80)
output.append(f"\nTotal different columns: {len(differences)}")
output.append(f"Different columns: {', '.join(differences)}")

# Save to file
output_file = Path(__file__).parent / "column_comparison.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('\n'.join(output))
print(f"\n\nSaved to: {output_file}")

connection.close()
