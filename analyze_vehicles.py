import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))
from src.sql_editor import create_database_connection, find_mtga_db_path

def analyze_vehicle_differences():
    """
    Analyze differences between vehicles with and without parallax
    to understand why some work and others don't.
    """
    db_path = find_mtga_db_path()
    cursor, connection, _ = create_database_connection(db_path)
    
    output = []
    output.append("="*80)
    output.append("Vehicle Card Parallax Analysis")
    output.append("="*80)
    
    # Get all vehicles
    query = """
        SELECT 
            GrpId,
            Order_Title,
            ArtId,
            ExpansionCode,
            SubTypes,
            tags,
            ArtSize,
            Rarity
        FROM Cards
        WHERE SubTypes LIKE '%331%'
        ORDER BY tags DESC, Order_Title
    """
    
    cursor.execute(query)
    vehicles = cursor.fetchall()
    
    output.append(f"\nTotal Vehicle cards found: {len(vehicles)}\n")
    
    # Separate vehicles by parallax status
    with_parallax = []
    without_parallax = []
    
    for vehicle in vehicles:
        grp_id, name, art_id, set_code, subtypes, tags, art_size, rarity = vehicle
        if tags and '1696804317' in tags:
            with_parallax.append(vehicle)
        else:
            without_parallax.append(vehicle)
    
    output.append(f"Vehicles WITH parallax: {len(with_parallax)}")
    output.append(f"Vehicles WITHOUT parallax: {len(without_parallax)}\n")
    
    # Analyze vehicles with parallax
    output.append("="*80)
    output.append("VEHICLES WITH PARALLAX (First 20)")
    output.append("="*80)
    
    for vehicle in with_parallax[:20]:
        grp_id, name, art_id, set_code, subtypes, tags, art_size, rarity = vehicle
        
        # Parse tags
        tag_list = tags.split(',') if tags else []
        other_tags = [t for t in tag_list if t.strip() != '1696804317']
        
        output.append(f"\n{name}")
        output.append(f"  GrpId: {grp_id}")
        output.append(f"  Set: {set_code}")
        output.append(f"  ArtId: {art_id}")
        output.append(f"  ArtSize: {art_size}")
        output.append(f"  Rarity: {rarity}")
        output.append(f"  Total tags: {len(tag_list)}")
        output.append(f"  Other styles: {', '.join(other_tags) if other_tags else 'None'}")
    
    # Group by characteristics
    output.append("\n" + "="*80)
    output.append("PATTERN ANALYSIS - Vehicles with Parallax")
    output.append("="*80)
    
    # By set
    sets_count = {}
    for vehicle in with_parallax:
        set_code = vehicle[3]
        sets_count[set_code] = sets_count.get(set_code, 0) + 1
    
    output.append("\nBy Set:")
    for set_code, count in sorted(sets_count.items(), key=lambda x: x[1], reverse=True):
        output.append(f"  {set_code}: {count} cards")
    
    # By number of tags
    tag_counts = {}
    parallax_only = 0
    parallax_plus_others = 0
    
    for vehicle in with_parallax:
        tags = vehicle[5]
        tag_list = tags.split(',') if tags else []
        count = len(tag_list)
        tag_counts[count] = tag_counts.get(count, 0) + 1
        
        if count == 1:
            parallax_only += 1
        else:
            parallax_plus_others += 1
    
    output.append(f"\nTag Count Distribution:")
    for count, num_cards in sorted(tag_counts.items()):
        output.append(f"  {count} tag(s): {num_cards} cards")
    
    output.append(f"\nParallax only: {parallax_only}")
    output.append(f"Parallax + other styles: {parallax_plus_others}")
    
    # Sample cards with multiple styles
    output.append("\n" + "="*80)
    output.append("VEHICLES WITH MULTIPLE STYLES (First 10)")
    output.append("="*80)
    
    multi_style = [v for v in with_parallax if v[5] and len(v[5].split(',')) > 1]
    for vehicle in multi_style[:10]:
        grp_id, name, art_id, set_code, subtypes, tags, art_size, rarity = vehicle
        output.append(f"\n{name} ({set_code})")
        output.append(f"  Tags: {tags}")
    
    # By ArtSize
    output.append("\n" + "="*80)
    output.append("By ArtSize:")
    artsize_counts = {}
    for vehicle in with_parallax:
        art_size = vehicle[6]
        artsize_counts[art_size] = artsize_counts.get(art_size, 0) + 1
    
    for size, count in sorted(artsize_counts.items()):
        output.append(f"  ArtSize {size}: {count} cards")
    
    # Write to file
    output_file = Path(__file__).parent / "vehicle_detailed_analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print('\n'.join(output))
    print(f"\n\nDetailed analysis saved to: {output_file}")
    
    connection.close()

if __name__ == "__main__":
    analyze_vehicle_differences()
