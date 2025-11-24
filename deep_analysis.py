import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

def check_missing_and_deeper_analysis():
    db_path = find_mtga_db_path()
    cursor, connection, _ = create_database_connection(db_path)
    
    output = []
    
    # Check for agonasaur
    output.append("Searching for 'agonasaur rex':")
    cursor.execute("""
        SELECT GrpId, Order_Title, SubTypes, tags 
        FROM Cards 
        WHERE Order_Title LIKE '%agonasaur%'
    """)
    
    cursor.execute(f"SELECT * FROM Cards WHERE GrpId = 94916")  # burner rocket
    burner = dict(zip(columns, cursor.fetchone()))
    
    cursor.execute(f"SELECT * FROM Cards WHERE GrpId = 94990")  # apocalypse runner
    apocalypse = dict(zip(columns, cursor.fetchone()))
    
    output.append("\nDifferences found:")
    differences = []
    for col in columns:
        if burner.get(col) != apocalypse.get(col):
            differences.append(col)
            output.append(f"  {col}:")
            output.append(f"    Burner (broken): {burner.get(col)}")
            output.append(f"    Apocalypse (working): {apocalypse.get(col)}")
    
    output.append(f"\nTotal different columns: {len(differences)}")
    output.append(f"Different columns: {', '.join(differences)}")
    
    # Write output
    output_file = Path(__file__).parent / "deep_vehicle_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print('\n'.join(output))
    print(f"\n\nAnalysis saved to: {output_file}")
    
    connection.close()

if __name__ == "__main__":
    check_missing_and_deeper_analysis()
