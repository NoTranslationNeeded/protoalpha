from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import asyncio
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os
import json
from pathlib import Path
import sqlite3

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import sql_editor, card_models
from src.sql_editor import find_mtga_db_path

router = APIRouter()

@router.get("/system/browse")
async def browse_path(type: str = "file"):
    """
    Opens a native file dialog to select a file or folder using PowerShell.
    type: "file" or "folder"
    """
    import subprocess
    
    try:
        cmd = ""
        if type == "file":
            # Use a more robust PowerShell script that forces the dialog to the front
            cmd = """
            Add-Type -AssemblyName System.Windows.Forms
            $FileBrowser = New-Object System.Windows.Forms.OpenFileDialog
            $FileBrowser.Title = "Select MTGA Database File"
            $FileBrowser.Filter = "MTGA Database (*.mtga)|*.mtga|All Files (*.*)|*.*"
            $FileBrowser.InitialDirectory = [Environment]::GetFolderPath("MyDocuments")
            
            # Hack to ensure dialog shows on top
            $Form = New-Object System.Windows.Forms.Form
            $Form.TopMost = $true
            $Form.StartPosition = "Manual"
            $Form.ShowInTaskbar = $false
            $Form.Opacity = 0
            $Form.Show()
            $Form.Focus()
            
            $result = $FileBrowser.ShowDialog($Form)
            if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Output $FileBrowser.FileName
            }
            $Form.Close()
            $Form.Dispose()
            """
        else:
            cmd = """
            Add-Type -AssemblyName System.Windows.Forms
            $FolderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
            $FolderBrowser.Description = "Select Image Save Folder"
            
            # Hack to ensure dialog shows on top
            $Form = New-Object System.Windows.Forms.Form
            $Form.TopMost = $true
            $Form.StartPosition = "Manual"
            $Form.ShowInTaskbar = $false
            $Form.Opacity = 0
            $Form.Show()
            $Form.Focus()
            
            $result = $FolderBrowser.ShowDialog($Form)
            if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Output $FolderBrowser.SelectedPath
            }
            $Form.Close()
            $Form.Dispose()
            """
            
        # Run PowerShell command with timeout
        result = subprocess.run(
            ["powershell", "-Command", cmd], 
            capture_output=True, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=60 # 60 second timeout to prevent hanging
        )
        
        path = result.stdout.strip()
        
        if path:
            return {"path": path}
        return {"path": None}
        
    except subprocess.TimeoutExpired:
        print("File dialog timed out")
        return {"path": None}
    except Exception as e:
        print(f"Error opening file dialog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Paths
USER_CONFIG_DIR = Path.home() / ".mtga_swapper"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.json"
USER_CONFIG_DIR.mkdir(exist_ok=True)

# Database State
db_connection = None
db_cursor = None
current_db_path = None

def get_db_connection():
    global db_connection, db_cursor, current_db_path
    if db_connection is None and current_db_path:
        print(f"Attempting to connect to DB at: '{current_db_path}'") # DEBUG LOG
        if not os.path.exists(current_db_path):
             print(f"Error: Database file does not exist at: '{current_db_path}'")
             return None
             
        try:
            # Create connection
            db_cursor, db_connection, _ = sql_editor.create_database_connection(current_db_path)
            
            # Validate connection by querying Cards table
            try:
                db_cursor.execute("SELECT 1 FROM Cards LIMIT 1")
                print("Database connection successful and validated")
            except sqlite3.Error as e:
                print(f"Database validation failed: {e}")
                db_connection.close()
                db_connection = None
                db_cursor = None
                return None
                
        except Exception as e:
            print(f"Error connecting to DB: {e}")
            return None
    return db_cursor

def init_config():
    global current_db_path
    if not USER_CONFIG_FILE.exists():
        # Create default config
        default_config = {"SavePath": "", "DatabasePath": ""}
        # Try to find DB automatically
        found_path = find_mtga_db_path()
        if found_path:
            default_config["DatabasePath"] = found_path
        
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
    
    # Load config
    try:
        with open(USER_CONFIG_FILE, "r") as f:
            config = json.load(f)
            db_path = config.get("DatabasePath")
            if db_path:
                # Sanitize path: remove "True" prefix if present (from previous bug) and whitespace
                db_path = db_path.replace("True", "").strip()
                current_db_path = db_path
                # Attempt connection on init
                get_db_connection()
    except Exception as e:
        print(f"Error loading config: {e}")

# Initialize config on startup
init_config()

@router.get("/config")
async def get_config():
    global current_db_path
    
    # Check connection status
    is_connected = get_db_connection() is not None
    
    return {
        "database_path": current_db_path,
        "is_db_connected": is_connected
    }

class ConfigModel(BaseModel):
    database_path: Optional[str]
    save_path: Optional[str]

@router.post("/config")
async def update_config(config: ConfigModel):
    global current_db_path
    
    current_data = {}
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r") as f:
                content = f.read()
                if content.strip():
                    current_data = json.loads(content)
        except Exception as e:
            print(f"Warning: Could not read existing config: {e}")
            # Continue with empty current_data
    
    if config.database_path is not None:
        # Sanitize path: remove quotes, whitespace, and fix common typos like '>'
        # Also remove "True" prefix if present (from previous bug)
        clean_path = config.database_path.strip().strip('"').strip("'")
        clean_path = clean_path.replace("True", "").strip()
        clean_path = clean_path.replace(">", os.sep)
        
        current_data["DatabasePath"] = clean_path
        current_db_path = clean_path
        # Reset connection to force reconnect
        global db_connection, db_cursor
        if db_connection:
            try:
                db_connection.close()
            except:
                pass
        db_connection = None
        db_cursor = None
        
    if config.save_path is not None:
        current_data["SavePath"] = config.save_path
        
    try:
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(current_data, f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config file: {str(e)}")
        
    return {"status": "success", "config": current_data}

@router.get("/cards")
async def get_cards(
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "Name"
):
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    # DEBUG: Print table info
    try:
        print("Cards Table Columns:", [row[1] for row in cursor.execute("PRAGMA table_info(Cards)").fetchall()])
    except:
        pass
        
    query = """
        SELECT 
            CASE 
                WHEN NULLIF(c1.Order_Title, '') IS NOT NULL THEN c1.Order_Title
                WHEN NULLIF(c1.Order_Title, '') IS NULL 
                    AND NULLIF(c2.Order_Title, '') IS NOT NULL THEN c2.Order_Title || '-flip-side'
            END AS Order_Title,
            c1.ExpansionCode,
            c1.ArtSize,
            c1.GrpId,
            c1.ArtId,
            MAX(lko.Loc) AS KoreanName,
            c1.IsDigitalOnly,
            c1.IsRebalanced
        FROM Cards c1
        LEFT JOIN Cards c2
            ON c1.LinkedFaceGrpIds = c2.GrpId
        AND NULLIF(c2.Order_Title, '') IS NOT NULL
        LEFT JOIN Localizations_koKR lko ON c1.TitleId = lko.LocId
        WHERE (NULLIF(c1.Order_Title, '') IS NOT NULL
        OR NULLIF(c2.Order_Title, '') IS NOT NULL)
    """
    
    params = []
    if search:
        query += """
            AND (
                c1.Order_Title LIKE ? OR 
                c2.Order_Title LIKE ? OR
                c1.ExpansionCode LIKE ? OR 
                c1.GrpId LIKE ? OR 
                c1.ArtId LIKE ? OR
                lko.Loc LIKE ?
            )
        """
        search_term = f"%{search}%"
        # We now have 6 placeholders (added Korean localization)
        params.extend([search_term, search_term, search_term, search_term, search_term, search_term])
        
    # Add grouping to ensure unique cards
    query += " GROUP BY c1.GrpId, c1.ArtId"
        
    # Add sorting
    # "Name", "Set", "ArtType", "GrpID", "ArtID"
    if sort_by == "Name":
        # Use the alias for sorting, which is allowed in ORDER BY
        query += " ORDER BY Order_Title"
    elif sort_by == "Set":
        query += " ORDER BY c1.ExpansionCode"
    elif sort_by == "GrpID":
        query += " ORDER BY c1.GrpId"
    elif sort_by == "ArtID":
        query += " ORDER BY c1.ArtId"
        
    # Add pagination
    query += f" LIMIT {limit} OFFSET {offset}"
    
    print(f"Executing query with params: {params}") # DEBUG LOG
    
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows") # DEBUG LOG
        
        cards = []
        for row in rows:
            name = row[0]
            set_code = row[1]
            # Identify Alchemy cards using IsDigitalOnly or IsRebalanced columns
            # row[6] is IsDigitalOnly, row[7] is IsRebalanced (1 or 0)
            is_alchemy = bool(row[6]) or bool(row[7])
            
            cards.append({
                "name": name,
                "set_code": set_code,
                "art_type": str(row[2]),
                "grp_id": str(row[3]),
                "art_id": str(row[4]),
                "korean_name": row[5] if len(row) > 5 and row[5] else None,
                "is_alchemy": is_alchemy
            })
            
        return {"cards": cards, "count": len(cards)}
        
    except Exception as e:
        print(f"Database error in get_cards: {e}") # DEBUG LOG
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/cards/{art_id}/image")
async def get_card_image(art_id: str):
    # Create a dummy card object for the utility function
    class DummyCard:
        def __init__(self, art_id):
            self.art_id = art_id
            
    card = DummyCard(art_id)
    
    # Use existing logic to get texture
    # We need the DB path from config
    global current_db_path
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    try:
        from src.unity_bundle import get_card_texture_data, convert_texture_to_bytes
        from fastapi.responses import Response
        
        result = get_card_texture_data(card, current_db_path)
        if result:
            processed_images, _ = result
            if processed_images:
                # Convert to bytes
                img_bytes = convert_texture_to_bytes(processed_images[0])
                return Response(content=img_bytes, media_type="image/png")
                
        return Response(status_code=404)
    except Exception as e:
        print(f"Error getting image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File
import shutil

@router.post("/cards/{art_id}/swap")
async def swap_card_art(
    art_id: str, 
    file: UploadFile = File(...)
):
    global current_db_path
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")

    # Save uploaded file temporarily
    temp_path = f"temp_{art_id}.png"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Use existing logic
        from src.unity_bundle import get_card_texture_data, load_unity_bundle, extract_textures_from_bundle, replace_texture_in_bundle
        
        class DummyCard:
            def __init__(self, art_id):
                self.art_id = art_id
        
        card = DummyCard(art_id)
        
        # Get matching bundle file
        # get_card_texture_data returns (images, textures, filename) if ret_matching=True
        result = get_card_texture_data(card, current_db_path, ret_matching=True)
        
        if not result:
             raise HTTPException(status_code=404, detail="Card assets not found")
             
        _, _, matching_file = result
        
        # Construct paths
        db_parent = Path(current_db_path).parent
        game_root = db_parent.parent
        asset_bundle_dir = game_root / "AssetBundle"
        bundle_path = asset_bundle_dir / matching_file
        
        # Load bundle
        unity_env = load_unity_bundle(str(bundle_path))
        
        # Get texture to replace (first one)
        textures = extract_textures_from_bundle(unity_env)
        if not textures:
            raise HTTPException(status_code=404, detail="No textures found in bundle")
            
        target_texture = textures[0]
        
        # Create backup
        backup_dir = Path.home() / "MTGA_Swapper_Backups"
        backup_dir.mkdir(exist_ok=True)
        shutil.copy(bundle_path, backup_dir / f"BACKUP_{matching_file}")
        
        # Replace
        replace_texture_in_bundle(target_texture, temp_path, str(bundle_path), unity_env)
        
        return {"status": "success", "message": "Art swapped successfully"}
        
    except Exception as e:
        print(f"Swap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/cards/{grp_id}/style/unlock")
async def unlock_card_style(grp_id: str):
    global current_db_path, db_connection, db_cursor
    
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        # We need user_save_changes_path for logging changes
        # In main.py it was: user_save_changes_path = user_config_directory / "changes.json"
        user_save_changes_path = USER_CONFIG_DIR / "changes.json"
        
        # Ensure changes.json exists
        if not user_save_changes_path.exists():
            with open(user_save_changes_path, "w") as f:
                json.dump({}, f)
        
        # We also need asset_bundle_path for logging
        asset_bundle_path = str(Path(current_db_path).parent.parent / "AssetBundle")
        
        # Ensure backup directory exists (required by save_grp_id_info called within unlock_parallax_style)
        backup_dir = Path.home() / "MTGA_Swapper_Backups"
        backup_dir.mkdir(exist_ok=True)
        
        success = sql_editor.unlock_parallax_style(
            [grp_id], 
            cursor, 
            db_connection, 
            str(user_save_changes_path),
            asset_bundle_path
        )
        
        if success:
            return {"status": "success", "message": "Parallax style unlocked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to unlock style")
            
    except Exception as e:
        print(f"Unlock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cards/style/unlock-batch")
async def unlock_batch_card_style(search: Optional[str] = None):
    global current_db_path, db_connection, db_cursor
    
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    # 1. Find cards matching search criteria (reuse get_cards logic)
    query = """
        SELECT c1.GrpId, c1.Order_Title
        FROM Cards c1
        LEFT JOIN Cards c2
            ON c1.LinkedFaceGrpIds = c2.GrpId
        AND NULLIF(c2.Order_Title, '') IS NOT NULL
        WHERE (NULLIF(c1.Order_Title, '') IS NOT NULL
        OR NULLIF(c2.Order_Title, '') IS NOT NULL)
    """
    
    params = []
    if search:
        query += """
            AND (
                c1.Order_Title LIKE ? OR 
                c2.Order_Title LIKE ? OR
                c1.ExpansionCode LIKE ? OR 
                c1.GrpId LIKE ? OR 
                c1.ArtId LIKE ?
            )
        """
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term, search_term, search_term])
    
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Filter out basic lands
        basic_lands = ["island", "forest", "mountain", "plains", "wastes", "swamp"]
        target_grp_ids = []
        
        for row in rows:
            grp_id = str(row[0])
            name = str(row[1]).lower()
            
            # Check if name starts with any basic land name
            is_basic_land = any(name.startswith(land) for land in basic_lands)
            
            if not is_basic_land:
                target_grp_ids.append(grp_id)
                
        if not target_grp_ids:
             return {"status": "success", "message": "No eligible cards found to unlock", "count": 0}

        # 2. Unlock styles for filtered cards
        user_save_changes_path = USER_CONFIG_DIR / "changes.json"
        if not user_save_changes_path.exists():
            with open(user_save_changes_path, "w") as f:
                json.dump({}, f)
                
        asset_bundle_path = str(Path(current_db_path).parent.parent / "AssetBundle")
        
        backup_dir = Path.home() / "MTGA_Swapper_Backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Process in chunks to avoid SQLite variable limit (usually 999)
        # and to prevent massive print outputs from unlock_parallax_style
        chunk_size = 900
        total_processed = 0
        failed_chunks = 0
        
        for i in range(0, len(target_grp_ids), chunk_size):
            chunk = target_grp_ids[i:i + chunk_size]
            try:
                success = sql_editor.unlock_parallax_style(
                    chunk, 
                    cursor, 
                    db_connection, 
                    str(user_save_changes_path),
                    asset_bundle_path
                )
                if success:
                    total_processed += len(chunk)
                else:
                    print(f"Failed to unlock chunk {i//chunk_size}")
                    failed_chunks += 1
            except Exception as e:
                print(f"Error unlocking chunk {i//chunk_size}: {e}")
                failed_chunks += 1
        
        if total_processed > 0:
            msg = f"Unlocked styles for {total_processed} cards."
            if failed_chunks > 0:
                msg += f" (Failed to process {failed_chunks} batches)"
            return {
                "status": "success", 
                "message": msg, 
                "count": total_processed
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to unlock styles (all batches failed)")
            
    except Exception as e:
        print(f"Batch unlock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cards/style/unlock-batch-stream")
async def unlock_batch_card_style_stream(search: Optional[str] = None):
    """
    SSE endpoint for batch unlock with real-time progress updates
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def generate_progress():
        global current_db_path, db_connection, db_cursor
        
        try:
            if not current_db_path:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Database not configured'})}\n\n"
                return
                
            cursor = get_db_connection()
            if not cursor:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Database not connected'})}\n\n"
                return
            
            # Find cards matching search criteria
            query = """
                SELECT c1.GrpId, c1.Order_Title
                FROM Cards c1
                LEFT JOIN Cards c2
                    ON c1.LinkedFaceGrpIds = c2.GrpId
                AND NULLIF(c2.Order_Title, '') IS NOT NULL
                WHERE (NULLIF(c1.Order_Title, '') IS NOT NULL
                OR NULLIF(c2.Order_Title, '') IS NOT NULL)
            """
            
            params = []
            if search:
                query += """
                    AND (
                        c1.Order_Title LIKE ? OR 
                        c2.Order_Title LIKE ? OR
                        c1.ExpansionCode LIKE ? OR 
                        c1.GrpId LIKE ? OR 
                        c1.ArtId LIKE ?
                    )
                """
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term, search_term, search_term])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Filter out basic lands
            basic_lands = ["island", "forest", "mountain", "plains", "wastes", "swamp"]
            target_grp_ids = []
            
            for row in rows:
                grp_id = str(row[0])
                name = str(row[1]).lower()
                is_basic_land = any(name.startswith(land) for land in basic_lands)
                if not is_basic_land:
                    target_grp_ids.append(grp_id)
            
            total_cards = len(target_grp_ids)
            
            if total_cards == 0:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No eligible cards found to unlock'})}\n\n"
                return
            
            # Send initial progress
            yield f"data: {json.dumps({'type': 'progress', 'current': 0, 'total': total_cards, 'message': 'Starting...'})}\n\n"
            await asyncio.sleep(0)  # Allow event to be sent
            
            # Setup paths
            user_save_changes_path = USER_CONFIG_DIR / "changes.json"
            if not user_save_changes_path.exists():
                with open(user_save_changes_path, "w") as f:
                    json.dump({}, f)
            
            asset_bundle_path = str(Path(current_db_path).parent.parent / "AssetBundle")
            backup_dir = Path.home() / "MTGA_Swapper_Backups"
            backup_dir.mkdir(exist_ok=True)
            
            # Process in chunks
            chunk_size = 100
            total_processed = 0
            failed_chunks = 0
            
            for i in range(0, len(target_grp_ids), chunk_size):
                chunk = target_grp_ids[i:i + chunk_size]
                try:
                    success = sql_editor.unlock_parallax_style(
                        chunk, 
                        cursor, 
                        db_connection, 
                        str(user_save_changes_path),
                        asset_bundle_path
                    )
                    if success:
                        total_processed += len(chunk)
                    else:
                        failed_chunks += 1
                    
                    # Send progress update
                    progress_pct = int((total_processed / total_cards) * 100)
                    yield f"data: {json.dumps({'type': 'progress', 'current': total_processed, 'total': total_cards, 'percentage': progress_pct, 'message': f'Processing... {total_processed}/{total_cards}'})}\n\n"
                    await asyncio.sleep(0)  # Allow event to be sent
                    
                except Exception as e:
                    print(f"Error unlocking chunk {i//chunk_size}: {e}")
                    failed_chunks += 1
            
            # Send completion
            if total_processed > 0:
                msg = f"Unlocked styles for {total_processed} cards."
                if failed_chunks > 0:
                    msg += f" (Failed to process {failed_chunks} batches)"
                yield f"data: {json.dumps({'type': 'complete', 'total': total_processed, 'message': msg})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to unlock styles (all batches failed)'})}\n\n"
                
        except Exception as e:
            print(f"SSE Batch unlock error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")


@router.get("/cards/style/reset-tokens-stream")
async def reset_token_styles_stream():
    """SSE endpoint for resetting token card styles with progress"""
    global current_db_path, db_connection, db_cursor
    
    async def generate_progress():
        try:
            if not current_db_path:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Database not configured'})}\n\n"
                return
                
            cursor = get_db_connection()
            if not cursor:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to connect to database'})}\n\n"
                return
            
            # Get all token cards
            cursor.execute("SELECT GrpId FROM Cards WHERE IsToken = 1")
            target_grp_ids = [row[0] for row in cursor.fetchall()]
            total_cards = len(target_grp_ids)
            
            if total_cards == 0:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No token cards found'})}\n\n"
                return
            
            # Process in chunks
            chunk_size = 100
            total_processed = 0
            failed_chunks = 0
            
            for i in range(0, len(target_grp_ids), chunk_size):
                chunk = target_grp_ids[i:i + chunk_size]
                try:
                    placeholders = ','.join('?' * len(chunk))
                    update_query = f"""
                        UPDATE Cards
                        SET tags = CASE
                            WHEN tags = ',1696804317,' THEN ',,'
                            WHEN tags LIKE ',1696804317,%' THEN REPLACE(tags, ',1696804317,', ',')
                            WHEN tags LIKE '%,1696804317,' THEN REPLACE(tags, ',1696804317,', ',')
                            ELSE tags
                        END
                        WHERE GrpId IN ({placeholders})
                        AND tags LIKE '%1696804317%'
                    """
                    cursor.execute(update_query, chunk)
                    db_connection.commit()
                    rows_affected = cursor.rowcount
                    total_processed += rows_affected
                    
                    # Send progress update
                    progress_pct = round((total_processed / total_cards) * 100, 1)
                    yield f"data: {json.dumps({'type': 'progress', 'current': total_processed, 'total': total_cards, 'percentage': progress_pct, 'message': f'Processing... {total_processed}/{total_cards}'})}\n\n"
                    await asyncio.sleep(0)
                    
                except Exception as e:
                    print(f"Chunk processing error: {e}")
                    failed_chunks += 1
            
            # Send completion
            if total_processed > 0:
                msg = f"Reset styles for {total_processed} token cards."
                if failed_chunks > 0:
                    msg += f" (Failed to process {failed_chunks} batches)"
                yield f"data: {json.dumps({'type': 'complete', 'total': total_processed, 'message': msg})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No token cards needed resetting (already clean).'})}\n\n"
                
        except Exception as e:
            print(f"SSE Reset tokens error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")



@router.post("/cards/style/unlock-tokens")
async def unlock_token_styles():
    global current_db_path, db_connection, db_cursor
    
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    # Find all token cards (IsToken = 1)
    query = """
        SELECT GrpId
        FROM Cards
        WHERE IsToken = 1
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        target_grp_ids = [str(row[0]) for row in rows]
                
        if not target_grp_ids:
             return {"status": "success", "message": "No token cards found", "count": 0}

        # Unlock styles for token cards
        user_save_changes_path = USER_CONFIG_DIR / "changes.json"
        if not user_save_changes_path.exists():
            with open(user_save_changes_path, "w") as f:
                json.dump({}, f)
                
        asset_bundle_path = str(Path(current_db_path).parent.parent / "AssetBundle")
        
        backup_dir = Path.home() / "MTGA_Swapper_Backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Process in chunks to avoid SQLite variable limit (usually 999)
        # and to prevent massive print outputs from unlock_parallax_style
        chunk_size = 900
        total_processed = 0
        failed_chunks = 0
        
        for i in range(0, len(target_grp_ids), chunk_size):
            chunk = target_grp_ids[i:i + chunk_size]
            try:
                success = sql_editor.unlock_parallax_style(
                    chunk, 
                    cursor, 
                    db_connection, 
                    str(user_save_changes_path),
                    asset_bundle_path
                )
                if success:
                    total_processed += len(chunk)
                else:
                    print(f"Failed to unlock token chunk {i//chunk_size}")
                    failed_chunks += 1
            except Exception as e:
                print(f"Error unlocking token chunk {i//chunk_size}: {e}")
                failed_chunks += 1
        
        if total_processed > 0:
            msg = f"Unlocked Parallax for {total_processed} token cards."
            if failed_chunks > 0:
                msg += f" (Failed to process {failed_chunks} batches)"
            return {
                "status": "success", 
                "message": msg, 
                "count": total_processed
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to unlock token styles (all batches failed)")
            
    except Exception as e:
        print(f"Token unlock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cards/style/reset-tokens")
async def reset_token_styles():
    global current_db_path, db_connection, db_cursor
    
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        # First, get total count of all tokens for debugging
        cursor.execute("SELECT COUNT(*) FROM Cards WHERE IsToken = 1")
        total_tokens = cursor.fetchone()[0]
        print(f"Total tokens in database: {total_tokens}")
        
        # Find all token cards with parallax style (IsToken = 1 AND tags contains '1696804317')
        query = """
            SELECT GrpId, tags
            FROM Cards
            WHERE IsToken = 1 
            AND tags LIKE '%1696804317%'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} tokens with parallax style")
        
        if not rows:
            return {
                "status": "success", 
                "message": f"No token cards with parallax style found. (Total tokens in DB: {total_tokens})", 
                "count": 0
            }
        
        target_grp_ids = [str(row[0]) for row in rows]
        
        # Reset the parallax style tag for token cards
        # Remove '1696804317' tag from the tags field
        chunk_size = 900
        total_processed = 0
        failed_chunks = 0
        
        for i in range(0, len(target_grp_ids), chunk_size):
            chunk = target_grp_ids[i:i + chunk_size]
            try:
                # Build SQL to remove the parallax tag
                placeholders = ','.join(['?'] * len(chunk))
                update_query = f"""
                    UPDATE Cards
                    SET tags = CASE
                        WHEN tags = '1696804317' THEN ''
                        WHEN tags LIKE '1696804317,%' THEN SUBSTR(tags, LENGTH('1696804317,') + 1)
                        WHEN tags LIKE '%,1696804317' THEN SUBSTR(tags, 1, LENGTH(tags) - LENGTH(',1696804317'))
                        WHEN tags LIKE '%,1696804317,%' THEN REPLACE(tags, ',1696804317,', ',')
                        ELSE tags
                    END
                    WHERE GrpId IN ({placeholders})
                    AND tags LIKE '%1696804317%'
                """
                
                cursor.execute(update_query, chunk)
                db_connection.commit()
                
                rows_affected = cursor.rowcount
                print(f"Chunk {i//chunk_size}: {rows_affected} rows updated")
                total_processed += rows_affected
                
            except Exception as e:
                print(f"Error resetting token chunk {i//chunk_size}: {e}")
                failed_chunks += 1
        
        if total_processed > 0:
            msg = f"Reset Parallax for {total_processed} token cards."
            if failed_chunks > 0:
                msg += f" (Failed to process {failed_chunks} batches)"
            return {
                "status": "success", 
                "message": msg, 
                "count": total_processed
            }
        else:
            return {
                "status": "success", 
                "message": f"No changes made. Found {len(target_grp_ids)} tokens with parallax but none were updated.", 
                "count": 0
            }
            
    except Exception as e:
        print(f"Token reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cards/style/reset-all-parallax")
async def reset_all_parallax_styles():
    """
    Reset parallax style for ALL cards in the database.
    This removes the parallax tag (1696804317) from every card.
    """
    global current_db_path, db_connection, db_cursor
    
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        # Find all cards with parallax style
        query = """
            SELECT GrpId, tags
            FROM Cards
            WHERE tags LIKE '%1696804317%'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} cards with parallax style")
        
        if not rows:
            return {
                "status": "success", 
                "message": "No cards with parallax style found.", 
                "count": 0
            }
        
        target_grp_ids = [str(row[0]) for row in rows]
        
        # Reset the parallax style tag for all cards
        chunk_size = 900
        total_processed = 0
        failed_chunks = 0
        
        for i in range(0, len(target_grp_ids), chunk_size):
            chunk = target_grp_ids[i:i + chunk_size]
            try:
                placeholders = ','.join(['?'] * len(chunk))
                update_query = f"""
                    UPDATE Cards
                    SET tags = CASE
                        WHEN tags = '1696804317' THEN ''
                        WHEN tags LIKE '1696804317,%' THEN SUBSTR(tags, LENGTH('1696804317,') + 1)
                        WHEN tags LIKE '%,1696804317' THEN SUBSTR(tags, 1, LENGTH(tags) - LENGTH(',1696804317'))
                        ELSE REPLACE(tags, ',1696804317,', ',')
                    END
                    WHERE GrpId IN ({placeholders})
                """
                
                cursor.execute(update_query, chunk)
                db_connection.commit()
                total_processed += len(chunk)
                print(f"Processed chunk {i//chunk_size + 1}: {len(chunk)} cards")
            except Exception as chunk_error:
                print(f"Error processing chunk {i//chunk_size + 1}: {chunk_error}")
                failed_chunks += 1
                continue
        
        if total_processed > 0:
            return {
                "status": "success",
                "message": f"Successfully reset parallax style for {total_processed} cards. Failed chunks: {failed_chunks}",
                "count": total_processed
            }
        else:
            return {
                "status": "success", 
                "message": f"No changes made. Found {len(target_grp_ids)} cards with parallax but none were updated.", 
                "count": 0
            }
            
    except Exception as e:
        print(f"Reset all parallax error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/style/reset-colored-vehicles")
async def reset_colored_vehicle_styles():
    """
    Reset parallax style for colored mono-colored vehicles.
    
    Colored mono-colored vehicles with parallax have a rendering bug
    where rules text displays in black instead of white.
    
    Criteria:
    - SubTypes contains '331' (Vehicle)
    - Colors is not empty (has color)
    - Colors doesn't contain comma (mono-colored, not multicolor)
    - tags contains '1696804317' (has parallax)
    """
    global current_db_path, db_connection, db_cursor
    
    if not current_db_path:
        raise HTTPException(status_code=400, detail="Database not configured")
        
    cursor = get_db_connection()
    if not cursor:
        raise HTTPException(status_code=500, detail="Database not connected")
        
    try:
        # First, get total count of all vehicles for debugging
        cursor.execute("""
            SELECT COUNT(*) FROM Cards 
            WHERE SubTypes LIKE '%331%'
        """)
        total_vehicles = cursor.fetchone()[0]
        print(f"Total vehicles in database: {total_vehicles}")
        
        # Find colored mono-colored vehicles with parallax
        # Colorless vehicles have Colors = NULL or ''
        # Multicolor vehicles have ',' in Colors (e.g., "3,4")
        query = """
            SELECT GrpId, Order_Title, Colors, tags
            FROM Cards
            WHERE SubTypes LIKE '%331%'
            AND tags LIKE '%1696804317%'
            AND Colors IS NOT NULL
            AND Colors != ''
            AND Colors NOT LIKE '%,%'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} colored mono-colored vehicles with parallax")
        
        if not rows:
            return {
                "status": "success", 
                "message": f"No colored mono-colored vehicles with parallax found. (Total vehicles: {total_vehicles})", 
                "count": 0
            }
        
        target_grp_ids = [str(row[0]) for row in rows]
        
        # Reset the parallax style tag
        chunk_size = 900
        total_processed = 0
        failed_chunks = 0
        
        for i in range(0, len(target_grp_ids), chunk_size):
            chunk = target_grp_ids[i:i + chunk_size]
            try:
                # Build SQL to remove the parallax tag
                placeholders = ','.join(['?'] * len(chunk))
                update_query = f"""
                    UPDATE Cards
                    SET tags = CASE
                        WHEN tags = '1696804317' THEN ''
                        WHEN tags LIKE '1696804317,%' THEN SUBSTR(tags, LENGTH('1696804317,') + 1)
                        WHEN tags LIKE '%,1696804317' THEN SUBSTR(tags, 1, LENGTH(tags) - LENGTH(',1696804317'))
                        WHEN tags LIKE '%,1696804317,%' THEN REPLACE(tags, ',1696804317,', ',')
                        ELSE tags
                    END
                    WHERE GrpId IN ({placeholders})
                    AND tags LIKE '%1696804317%'
                """
                
                cursor.execute(update_query, chunk)
                db_connection.commit()
                
                rows_affected = cursor.rowcount
                print(f"Chunk {i//chunk_size}: {rows_affected} rows updated")
                total_processed += rows_affected
                
            except Exception as e:
                print(f"Error resetting colored vehicle chunk {i//chunk_size}: {e}")
                failed_chunks += 1
        
        if total_processed > 0:
            msg = f"Reset Parallax for {total_processed} colored mono-colored vehicle cards (fixes black text bug)."
            if failed_chunks > 0:
                msg += f" (Failed to process {failed_chunks} batches)"
            return {
                "status": "success", 
                "message": msg, 
                "count": total_processed
            }
        else:
            return {
                "status": "success", 
                "message": f"No changes made. Found {len(target_grp_ids)} colored vehicles with parallax but none were updated.", 
                "count": 0
            }
            
    except Exception as e:
        print(f"Colored vehicle reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/style/reset-colored-vehicles-stream")
async def reset_colored_vehicle_styles_stream():
    """SSE endpoint for resetting colored vehicle card styles with progress"""
    global current_db_path, db_connection, db_cursor
    
    async def generate_progress():
        try:
            if not current_db_path:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Database not configured'})}\n\n"
                return
                
            cursor = get_db_connection()
            if not cursor:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to connect to database'})}\n\n"
                return
            
            # Get all mono-colored vehicles with parallax style
            query = """
                SELECT GrpId
                FROM Cards
                WHERE SubTypes LIKE '%331%'
                AND tags LIKE '%1696804317%'
                AND Colors IS NOT NULL
                AND Colors != ''
                AND Colors NOT LIKE '%,%'
            """
            cursor.execute(query)
            target_grp_ids = [str(row[0]) for row in cursor.fetchall()]
            total_cards = len(target_grp_ids)
            
            if total_cards == 0:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No colored vehicles with parallax found'})}\n\n"
                return
            
            # Process in chunks
            chunk_size = 100
            total_processed = 0
            failed_chunks = 0
            
            for i in range(0, len(target_grp_ids), chunk_size):
                chunk = target_grp_ids[i:i + chunk_size]
                try:
                    placeholders = ','.join('?' * len(chunk))
                    update_query = f"""
                        UPDATE Cards
                        SET tags = CASE
                            WHEN tags = ',1696804317,' THEN ',,'
                            WHEN tags LIKE ',1696804317,%' THEN REPLACE(tags, ',1696804317,', ',')
                            WHEN tags LIKE '%,1696804317,' THEN REPLACE(tags, ',1696804317,', ',')
                            ELSE tags
                        END
                        WHERE GrpId IN ({placeholders})
                        AND tags LIKE '%1696804317%'
                    """
                    cursor.execute(update_query, chunk)
                    db_connection.commit()
                    rows_affected = cursor.rowcount
                    total_processed += rows_affected
                    
                    # Send progress update
                    progress_pct = round((total_processed / total_cards) * 100, 1)
                    yield f"data: {json.dumps({'type': 'progress', 'current': total_processed, 'total': total_cards, 'percentage': progress_pct, 'message': f'Processing... {total_processed}/{total_cards}'})}\n\n"
                    await asyncio.sleep(0)
                    
                except Exception as e:
                    print(f"Chunk processing error: {e}")
                    failed_chunks += 1
            
            # Send completion
            if total_processed > 0:
                msg = f"Reset Parallax for {total_processed} colored mono-colored vehicle cards."
                if failed_chunks > 0:
                    msg += f" (Failed to process {failed_chunks} batches)"
                yield f"data: {json.dumps({'type': 'complete', 'total': total_processed, 'message': msg})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No colored vehicles needed resetting (already clean).'})}\n\n"
                
        except Exception as e:
            print(f"SSE Reset colored vehicles error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")


@router.get("/cards/style/reset-all-parallax-stream")
async def reset_all_parallax_stream():
    """SSE endpoint for resetting all parallax styles with progress"""
    global current_db_path, db_connection, db_cursor
    
    async def generate_progress():
        try:
            if not current_db_path:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Database not configured'})}\n\n"
                return
                
            cursor = get_db_connection()
            if not cursor:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to connect to database'})}\n\n"
                return
            
            # Get all cards with parallax style
            query = "SELECT DISTINCT GrpId FROM Cards WHERE tags LIKE '%1696804317%'"
            cursor.execute(query)
            target_grp_ids = [str(row[0]) for row in cursor.fetchall()]
            total_cards = len(target_grp_ids)
            
            if total_cards == 0:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No cards with parallax style found'})}\n\n"
                return
            
            # Process in chunks
            chunk_size = 100
            total_processed = 0
            failed_chunks = 0
            
            for i in range(0, len(target_grp_ids), chunk_size):
                chunk = target_grp_ids[i:i + chunk_size]
                try:
                    placeholders = ','.join('?' * len(chunk))
                    update_query = f"""
                        UPDATE Cards
                        SET tags = CASE
                            WHEN tags = ',1696804317,' THEN ',,'
                            WHEN tags LIKE ',1696804317,%' THEN REPLACE(tags, ',1696804317,', ',')
                            WHEN tags LIKE '%,1696804317,' THEN REPLACE(tags, ',1696804317,', ',')
                            ELSE tags
                        END
                        WHERE GrpId IN ({placeholders})
                        AND tags LIKE '%1696804317%'
                    """
                    cursor.execute(update_query, chunk)
                    db_connection.commit()
                    rows_affected = cursor.rowcount
                    total_processed += rows_affected
                    
                    # Send progress update
                    progress_pct = round((total_processed / total_cards) * 100, 1)
                    yield f"data: {json.dumps({'type': 'progress', 'current': total_processed, 'total': total_cards, 'percentage': progress_pct, 'message': f'Processing... {total_processed}/{total_cards}'})}\n\n"
                    await asyncio.sleep(0)
                    
                except Exception as e:
                    print(f"Chunk processing error: {e}")
                    failed_chunks += 1
            
            # Send completion
            if total_processed > 0:
                msg = f"Reset Parallax for {total_processed} cards."
                if failed_chunks > 0:
                    msg += f" (Failed to process {failed_chunks} batches)"
                yield f"data: {json.dumps({'type': 'complete', 'total': total_processed, 'message': msg})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'complete', 'total': 0, 'message': 'No cards needed resetting (already clean).'})}\n\n"
                
        except Exception as e:
            print(f"SSE Reset all parallax error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")

