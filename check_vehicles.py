import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

def get_vehicle_info():
    db_path = find_mtga_db_path()
    cursor, connection, _ = create_database_connection(db_path)
    
    # Find V vehicle subtype ID by checking known vehicle
    cursor.execute("""
        SELECT Loc FROM Localizations_enUS WHERE LocId IN (235, 331, 337)
    """)
    rows = cursor.fetchall()
    
    output = []
    output.append("SubType IDs found in Greasefang (235, 337) and Skysovereign (331):")
    for row in rows:
        output.append(f"  - {row[0]}")
    
    # Now count vehicles with each possible ID
    for test_id in [235, 331, 337]:
        cursor.execute(f"""
            SELECT COUNT(*) FROM Cards 
            WHERE SubTypes LIKE '%{test_id}%'
        """)
        count = cursor.fetchone()[0]
        output.append(f"\nCards with SubType {test_id}: {count}")
        
        # Get sample
        cursor.execute(f"""
            SELECT Order_Title, GrpId FROM Cards 
            WHERE SubTypes LIKE '%{test_id}%'
            LIMIT 5
        """)
        samples = cursor.fetchall()
        for name, grp_id in samples:
            output.append(f"  - {name} ({grp_id})")
    
    # Write to file
    output_file = Path(__file__).parent / "vehicle_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print('\n'.join(output))
    print(f"\n\nResults saved to: {output_file}")
    
    connection.close()

if __name__ == "__main__":
    get_vehicle_info()
