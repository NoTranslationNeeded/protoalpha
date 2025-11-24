import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

def compare_vehicles():
    """
    Compare broken vs working vehicles to find the pattern
    """
    db_path = find_mtga_db_path()
    cursor, connection, _ = create_database_connection(db_path)
    
    # Broken vehicles (black text)
    broken = [
        'mobilizer%mech',
        'dreadmobile',
        'burner%rocket',
        'esika%chariot'
    ]
    
    # Working vehicles (white text)
    working = [
        'ribskiff',
        'soul%shredder',
        'apocalypse%runner',
        'agonasaur%rex',
        'carriage%dreams'
    ]
    
    output = []
    output.append("="*80)
    output.append("VEHICLE COMPARISON: BROKEN vs WORKING")
    output.append("="*80)
    
    # Get details for broken vehicles
    output.append("\n" + "="*80)
    output.append("BROKEN VEHICLES (Black rules text)")
    output.append("="*80)
    
    broken_data = []
    for pattern in broken:
        query = """
            SELECT 
                GrpId, Order_Title, ExpansionCode, ArtId, 
                SubTypes, tags, ArtSize, Rarity
            FROM Cards
            WHERE Order_Title LIKE ? AND SubTypes LIKE '%331%'
        """
        cursor.execute(query, (pattern,))
        result = cursor.fetchone()
        if result:
            broken_data.append(result)
            grp_id, name, set_code, art_id, subtypes, tags, art_size, rarity = result
            output.append(f"\n{name}")
            output.append(f"  GrpId: {grp_id}")
            output.append(f"  Set: {set_code}")
            output.append(f"  ArtId: {art_id}")
            output.append(f"  SubTypes: {subtypes}")
            output.append(f"  Tags: {tags}")
            output.append(f"  ArtSize: {art_size}")
            output.append(f"  Rarity: {rarity}")
    
    # Get details for working vehicles
    output.append("\n" + "="*80)
    output.append("WORKING VEHICLES (White rules text)")
    output.append("="*80)
    
    working_data = []
    for pattern in working:
        query = """
            SELECT 
                GrpId, Order_Title, ExpansionCode, ArtId, 
                SubTypes, tags, ArtSize, Rarity
            FROM Cards
            WHERE Order_Title LIKE ? AND SubTypes LIKE '%331%'
        """
        cursor.execute(query, (pattern,))
        result = cursor.fetchone()
        if result:
            working_data.append(result)
            grp_id, name, set_code, art_id, subtypes, tags, art_size, rarity = result
            output.append(f"\n{name}")
            output.append(f"  GrpId: {grp_id}")
            output.append(f"  Set: {set_code}")
            output.append(f"  ArtId: {art_id}")
            output.append(f"  SubTypes: {subtypes}")
            output.append(f"  Tags: {tags}")
            output.append(f"  ArtSize: {art_size}")
            output.append(f"  Rarity: {rarity}")
    
    # Pattern analysis
    output.append("\n" + "="*80)
    output.append("PATTERN ANALYSIS")
    output.append("="*80)
    
    # Compare sets
    broken_sets = [v[2] for v in broken_data]
    working_sets = [v[2] for v in working_data]
    
    output.append(f"\nBroken sets: {', '.join(broken_sets)}")
    output.append(f"Working sets: {', '.join(working_sets)}")
    
    # Compare ArtSize
    broken_artsizes = [v[6] for v in broken_data]
    working_artsizes = [v[6] for v in working_data]
    
    output.append(f"\nBroken ArtSize values: {broken_artsizes}")
    output.append(f"Working ArtSize values: {working_artsizes}")
    
    # Compare Rarity
    broken_rarities = [v[7] for v in broken_data]
    working_rarities = [v[7] for v in working_data]
    
    output.append(f"\nBroken Rarity values: {broken_rarities}")
    output.append(f"Working Rarity values: {working_rarities}")
    
    # Compare tag counts
    broken_tag_counts = [len(v[5].split(',')) if v[5] else 0 for v in broken_data]
    working_tag_counts = [len(v[5].split(',')) if v[5] else 0 for v in working_data]
    
    output.append(f"\nBroken tag counts: {broken_tag_counts}")
    output.append(f"Working tag counts: {working_tag_counts}")
    
    # Check for other styles
    output.append("\n" + "="*80)
    output.append("OTHER STYLES ANALYSIS")
    output.append("="*80)
    
    for name_pattern, data in [("BROKEN", broken_data), ("WORKING", working_data)]:
        output.append(f"\n{name_pattern}:")
        for vehicle in data:
            name = vehicle[1]
            tags = vehicle[5]
            if tags:
                tag_list = tags.split(',')
                other_tags = [t for t in tag_list if t.strip() != '1696804317']
                if other_tags:
                    output.append(f"  {name}: Has {len(other_tags)} other style(s) - {', '.join(other_tags)}")
                else:
                    output.append(f"  {name}: Parallax only")
            else:
                output.append(f"  {name}: No tags")
    
    # Key finding
    output.append("\n" + "="*80)
    output.append("KEY FINDINGS")
    output.append("="*80)
    
    if set(broken_artsizes) != set(working_artsizes):
        output.append(f"\n⚠️ POTENTIAL PATTERN: ArtSize difference detected!")
        output.append(f"  Broken vehicles have ArtSize: {set(broken_artsizes)}")
        output.append(f"  Working vehicles have ArtSize: {set(working_artsizes)}")
    
    if set(broken_sets).isdisjoint(set(working_sets)):
        output.append(f"\n⚠️ POTENTIAL PATTERN: No overlapping sets!")
        output.append(f"  Broken sets: {set(broken_sets)}")
        output.append(f"  Working sets: {set(working_sets)}")
    
    # Write to file
    output_file = Path(__file__).parent / "vehicle_comparison.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print('\n'.join(output))
    print(f"\n\nComparison saved to: {output_file}")
    
    connection.close()

if __name__ == "__main__":
    compare_vehicles()
