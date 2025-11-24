import os
import subprocess
import sys
import shutil

def run_command(command, cwd=None):
    print(f"Running: {command}")
    try:
        subprocess.check_call(command, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    # 1. Build Frontend
    print("--- Building Frontend ---")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    
    print("Running npm run build...")
    run_command("npm run build", cwd=frontend_dir)
    
    # Verify dist exists
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.exists(dist_dir):
        print("Error: frontend/dist not found after build!")
        sys.exit(1)

    # 2. Install PyInstaller if needed
    print("\n--- Checking PyInstaller ---")
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        run_command(f"{sys.executable} -m pip install pyinstaller")

    # 3. Run PyInstaller
    print("\n--- Creating Executable ---")
    
    # Clean previous build
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        
    # PyInstaller arguments
    # --onefile: Create a single executable
    # --name: Name of the executable
    # --add-data: Include frontend/dist
    # --hidden-import: uvicorn and other dynamic imports
    
    sep = ";" if os.name == 'nt' else ":"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "app_entry.py",
        "--name", "MTGA_Swapper",
        "--onefile",
        "--clean",
        f"--add-data", f"frontend/dist{sep}frontend/dist",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "engineio.async_drivers.asgi", # often needed for socketio/fastapi
        "--collect-all", "uvicorn",
        "--collect-all", "fastapi",
    ]
    
    # Convert list to string for shell execution
    cmd_str = " ".join(cmd)
    run_command(cmd_str)
    
    print("\n--- Build Complete ---")
    print(f"Executable created at: {os.path.join(os.getcwd(), 'dist', 'MTGA_Swapper.exe')}")

if __name__ == "__main__":
    main()
