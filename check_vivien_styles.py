import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

def check_liliana_styles():
    # Find database
    db_path = find_mtga_db_path()
    if not db_path:
        print("Database not found.")
        return
    
    print(f"Using database: {db_path}\n")
    
    # Connect to database
    cursor, connection, _ = create_database_connection(db_path)
    
    # Search for Liliana, Dreadhorde General
    query = """
        SELECT 
            GrpId,
            Order_Title,
            ExpansionCode,
            ArtId,
            tags,
            ArtSize
        FROM Cards
        WHERE Order_Title LIKE '%liliana%dreadhorde%'
           OR Order_Title LIKE '%liliana%general%'
        ORDER BY GrpId
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} 'Liliana, Dreadhorde General' variants:\n")
    
    if len(rows) == 0:
        # Try a broader search
        print("No exact match found. Searching for all Liliana cards...\n")
        query = """
            SELECT 
                GrpId,
                Order_Title,
                ExpansionCode,
                ArtId,
                tags,
                ArtSize
            FROM Cards
            WHERE Order_Title LIKE '%liliana%'
            ORDER BY Order_Title, GrpId
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} Liliana cards total:\n")
    
    for row in rows:
        grp_id, name, set_code, art_id, tags, art_size = row
        print(f"\n{'='*80}")
        print(f"Name: {name}")
        print(f"GrpId: {grp_id}")
        print(f"Set Code: {set_code}")
        print(f"ArtId: {art_id}")
        print(f"Art Size: {art_size}")
        print(f"Tags: {tags if tags else '(none/기본 스타일만)'}")
        
        # Decode tags if present
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            print(f"Number of styles: {len(tag_list)}")
            print(f"Style tags: {', '.join(tag_list)}")
            
            # Interpret common tags
            style_names = []
            for tag in tag_list:
                if tag == '1696804317':
                    style_names.append('Parallax/Depth')
                elif tag == '-166024499':
                    style_names.append('Showcase')
                elif tag == '1070957949':
                    style_names.append('Extended Art')
                elif tag == '-837447456':
                    style_names.append('Borderless')
                elif tag == '-938816491':
                    style_names.append('Full Art')
                else:
                    style_names.append(f'Unknown ({tag})')
            
            print(f"Style names: {', '.join(style_names)}")
    
    connection.close()

if __name__ == "__main__":
    check_liliana_styles()
