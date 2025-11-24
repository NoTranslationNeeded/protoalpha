import webbrowser
import subprocess
import sys
import time
import os
import signal

def run_servers():
    print("Starting MTGA Swapper Web UI...")
    
    # Determine python executable
    python_exe = sys.executable
    if ".venv" in str(os.getcwd()) or os.path.exists(".venv"):
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_exe = venv_python

    # Start Backend
    print(f"Starting Backend with {python_exe}...")
    backend_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=os.getcwd()
    )
    
    # Start Frontend
    print("Starting Frontend...")
    if not os.path.exists("frontend/node_modules"):
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd="frontend", shell=True)

    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"], 
        cwd="frontend", 
        shell=True
    )

    print("\nServers are running!")
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:5173 (or similar)")
    print("Press Ctrl+C to stop.\n")

    # Open browser after a short delay
    def open_browser():
        time.sleep(3)
        print("Opening browser...")
        webbrowser.open("http://localhost:5173")
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        while True:
            time.sleep(1)
            if backend_process.poll() is not None:
                print("Backend process ended unexpectedly!")
                break
            if frontend_process.poll() is not None:
                print("Frontend process ended unexpectedly!")
                break
    except KeyboardInterrupt:
        print("\nStopping servers...")
    finally:
        backend_process.terminate()
        # Frontend shell process might need stronger kill
        if sys.platform == 'win32':
            subprocess.run(f"taskkill /F /T /PID {frontend_process.pid}", shell=True)
        else:
            frontend_process.terminate()
            
if __name__ == "__main__":
    run_servers()
