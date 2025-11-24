import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

def check_card_styles(card_name_pattern, output_lines):
    # Find database
    db_path = find_mtga_db_path()
    if not db_path:
        output_lines.append("Database not found.")
        return
    
    output_lines.append(f"Searching for: {card_name_pattern}\n")
    
    # Connect to database
    cursor, connection, _ = create_database_connection(db_path)
    
    query = """
        SELECT 
            GrpId,
            Order_Title,
            ExpansionCode,
            ArtId,
            tags,
            ArtSize
        FROM Cards
        WHERE Order_Title LIKE ?
        ORDER BY GrpId
    """
    
    cursor.execute(query, (f'%{card_name_pattern}%',))
    rows = cursor.fetchall()
    
    output_lines.append(f"Found {len(rows)} card variants:\n")
    
    for i, row in enumerate(rows, 1):
        grp_id, name, set_code, art_id, tags, art_size = row
        output_lines.append(f"\n[Variant {i}]")
        output_lines.append(f"Name: {name}")
        output_lines.append(f"GrpId: {grp_id}")
        output_lines.append(f"Set: {set_code}")
        output_lines.append(f"ArtId: {art_id}")
        
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            output_lines.append(f"Tags: {tags}")
            output_lines.append(f"Available Styles ({len(tag_list)} + base):")
            
            # Map common tag IDs to style names
            tag_map = {
                '1696804317': 'Parallax/Depth Art',
                '-166024499': 'Showcase',
                '1070957949': 'Extended Art',
                '-837447456': 'Borderless',
                '-938816491': 'Full Art',
                '-1882537866': 'Alt Art',
                '520216861': 'Phyrexian',
                '1414245915': 'Stained Glass',
            }
            
            output_lines.append("  - Base/Default style")
            for tag in tag_list:
                style_name = tag_map.get(tag, f'Unknown style (tag: {tag})')
                output_lines.append(f"  - {style_name}")
        else:
            output_lines.append("Tags: (none)")
            output_lines.append("Available Styles:")
            output_lines.append("  - Base/Default style only")
        
        output_lines.append("-" * 60)
    
    connection.close()

if __name__ == "__main__":
    output_lines = []
    
    # Search for both cards
    output_lines.append("="*60)
    output_lines.append("Liliana, Dreadhorde General")
    output_lines.append("="*60)
    check_card_styles("liliana%dreadhorde", output_lines)
    
    output_lines.append("\n\n")
    output_lines.append("="*60)
    output_lines.append("Vivien, Champion of the Wilds")
    output_lines.append("="*60)
    check_card_styles("vivien%champion", output_lines)
    
    # Write to file
    output_file = Path(__file__).parent / "card_styles_result.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Results written to: {output_file}")
    print("\nSummary:")
    print('\n'.join(output_lines))
