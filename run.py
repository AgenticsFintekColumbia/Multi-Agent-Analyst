"""
Single command launcher for the Agentic Recommendation System
Starts both backend and frontend servers
"""

import subprocess
import sys
import os
import signal
import time
import socket
import requests
from pathlib import Path

# Fix encoding issues on Windows
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding for Windows console
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# Store process references for cleanup
processes = []

def cleanup():
    """Kill all child processes"""
    print("\n" + "=" * 60)
    print("Shutting down servers...")
    for process in processes:
        try:
            if sys.platform == "win32":
                process.terminate()
                # On Windows, we need to kill the process tree
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], 
                            capture_output=True, check=False)
            else:
                process.terminate()
                process.wait(timeout=5)
        except Exception as e:
            print(f"Error stopping process: {e}")
    print("All servers stopped.")
    sys.exit(0)

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    cleanup()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def is_port_open(host, port, timeout=1):
    """Check if a port is open and accepting connections"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_node_installed():
    """Check if Node.js and npm are installed"""
    # On Windows, use shell=True to ensure PATH is searched
    use_shell = sys.platform == "win32"
    
    # On Windows, also try common installation paths
    node_paths = []
    if sys.platform == "win32":
        # Common Node.js installation paths on Windows
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        node_paths = [
            os.path.join(program_files, "nodejs", "node.exe"),
            os.path.join(program_files_x86, "nodejs", "node.exe"),
            "C:\\Program Files\\nodejs\\node.exe",
        ]
    
    node_installed = False
    npm_installed = False
    
    # Try direct command first
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=use_shell
        )
        node_installed = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        # Try common paths on Windows
        if sys.platform == "win32":
            for node_path in node_paths:
                if os.path.exists(node_path):
                    try:
                        result = subprocess.run(
                            [node_path, "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            node_installed = True
                            # Add to PATH for this session
                            node_dir = os.path.dirname(node_path)
                            os.environ["PATH"] = node_dir + os.pathsep + os.environ.get("PATH", "")
                            break
                    except Exception:
                        continue
    
    # Check npm
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=use_shell
        )
        npm_installed = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        # If node was found, npm should be in the same directory
        if node_installed and sys.platform == "win32":
            for node_path in node_paths:
                if os.path.exists(node_path):
                    npm_path = os.path.join(os.path.dirname(node_path), "npm.cmd")
                    if os.path.exists(npm_path):
                        try:
                            result = subprocess.run(
                                [npm_path, "--version"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if result.returncode == 0:
                                npm_installed = True
                                break
                        except Exception:
                            continue
    
    return node_installed, npm_installed

def wait_for_server(url, name, max_wait=60):
    """Wait for a server to be ready by checking if it responds to HTTP requests"""
    print(f"Waiting for {name} to start...", end="", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code < 500:  # Any response < 500 means server is up
                print(f" [OK]")
                return True
        except (requests.exceptions.RequestException, ConnectionError):
            pass
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print(f" [TIMEOUT after {max_wait}s, but continuing anyway]")
    return False

def main():
    print("=" * 60)
    print("Starting Agentic Recommendation System")
    print("=" * 60)
    print()
    
    # Check if Node.js and npm are installed
    node_installed, npm_installed = check_node_installed()
    if not node_installed or not npm_installed:
        print("ERROR: Node.js and/or npm are not found in PATH!")
        print()
        
        # On Windows, check if Node.js might be installed but not in PATH
        if sys.platform == "win32":
            print("Node.js might be installed but not in your PATH.")
            print()
            print("Quick fixes:")
            print("  1. Close this terminal and open a NEW terminal window")
            print("  2. Or restart your computer (if you just installed Node.js)")
            print("  3. Or manually add Node.js to PATH:")
            print("     - Usually: C:\\Program Files\\nodejs")
            print()
        
        print("If Node.js is not installed:")
        print()
        print("Windows:")
        print("  1. Download Node.js from: https://nodejs.org/")
        print("  2. Choose the LTS (Long Term Support) version")
        print("  3. Run the installer and follow the prompts")
        print("  4. IMPORTANT: Close and reopen your terminal after installation")
        print()
        print("Mac:")
        print("  1. Download Node.js from: https://nodejs.org/")
        print("  2. Or use Homebrew: brew install node")
        print()
        print("Linux (Ubuntu/Debian):")
        print("  sudo apt update")
        print("  sudo apt install nodejs npm")
        print()
        print("After installing, verify with:")
        print("  node --version")
        print("  npm --version")
        print()
        print("Then run this script again.")
        print("=" * 60)
        sys.exit(1)
    
    # Get project root directory
    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend" / "insight-agent"
    
    # Check if frontend directory exists
    if not frontend_dir.exists():
        print("ERROR: Frontend directory not found!")
        print(f"   Expected: {frontend_dir}")
        sys.exit(1)
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("WARNING: node_modules not found!")
        print("   Installing frontend dependencies...")
        print("   (This may take a few minutes on first run)")
        print()
        install_process = subprocess.Popen(
            ["npm", "install"],
            cwd=frontend_dir,
            shell=True if sys.platform == "win32" else False
        )
        install_process.wait()
        if install_process.returncode != 0:
            print()
            print("ERROR: Failed to install frontend dependencies")
            print("   Try running manually: cd frontend/insight-agent && npm install")
            sys.exit(1)
        print()
        print("SUCCESS: Frontend dependencies installed")
        print()
    
    print("Starting Backend Server...")
    
    # Start backend (don't redirect output so user can see startup messages)
    backend_process = subprocess.Popen(
        [sys.executable, "start_backend.py"],
        cwd=project_root,
        shell=False
    )
    processes.append(backend_process)
    
    # Wait for backend to be ready (check health endpoint)
    print("Waiting for backend to finish loading datasets and start...")
    backend_ready = wait_for_server("http://localhost:8000/health", "Backend Server", max_wait=90)
    
    if not backend_ready:
        print("WARNING: Backend may still be loading datasets. It will be ready shortly.")
    else:
        print("SUCCESS: Backend is ready!")
    
    print()
    print("Starting Frontend Server...")
    
    # Start frontend (don't redirect output so user can see startup messages)
    if sys.platform == "win32":
        # Windows
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            shell=True
        )
    else:
        # Unix/Mac
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            shell=False
        )
    processes.append(frontend_process)
    
    # Wait for frontend to be ready
    print("Waiting for frontend to compile and start...")
    frontend_ready = wait_for_server("http://localhost:5173", "Frontend Server", max_wait=30)
    
    if frontend_ready:
        print("SUCCESS: Frontend is ready!")
    
    print()
    print("=" * 60)
    print("SUCCESS: All servers are ready!")
    print()
    print("Backend API: http://localhost:8000")
    print("API Docs:    http://localhost:8000/docs")
    print("Frontend:   http://localhost:5173")
    print()
    print("TIP: Open http://localhost:5173 in your browser to use the app")
    print()
    print("Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()
    
    # Wait for processes (they should run indefinitely)
    try:
        # Monitor processes
        while True:
            # Check if processes are still alive
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"\nWARNING: Process {i+1} exited with code {process.returncode}")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        cleanup()

