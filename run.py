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

def wait_for_server(url, name, max_wait=60):
    """Wait for a server to be ready by checking if it responds to HTTP requests"""
    print(f"⏳ Waiting for {name} to start...", end="", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code < 500:  # Any response < 500 means server is up
                print(f" ✅")
                return True
        except (requests.exceptions.RequestException, ConnectionError):
            pass
        
        print(".", end="", flush=True)
        time.sleep(1)
    
    print(f" ⚠️  (timeout after {max_wait}s, but continuing anyway)")
    return False

def main():
    print("=" * 60)
    print("🚀 Starting Agentic Recommendation System")
    print("=" * 60)
    print()
    
    # Get project root directory
    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend" / "insight-agent"
    
    # Check if frontend directory exists
    if not frontend_dir.exists():
        print("❌ Error: Frontend directory not found!")
        print(f"   Expected: {frontend_dir}")
        sys.exit(1)
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("⚠️  Warning: node_modules not found!")
        print("   Installing frontend dependencies...")
        print()
        install_process = subprocess.Popen(
            ["npm", "install"],
            cwd=frontend_dir,
            shell=True if sys.platform == "win32" else False
        )
        install_process.wait()
        if install_process.returncode != 0:
            print("❌ Error: Failed to install frontend dependencies")
            sys.exit(1)
        print("✅ Frontend dependencies installed")
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
    print("⏳ Waiting for backend to finish loading datasets and start...")
    backend_ready = wait_for_server("http://localhost:8000/health", "Backend Server", max_wait=90)
    
    if not backend_ready:
        print("⚠️  Backend may still be loading datasets. It will be ready shortly.")
    else:
        print("✅ Backend is ready!")
    
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
    print("⏳ Waiting for frontend to compile and start...")
    frontend_ready = wait_for_server("http://localhost:5173", "Frontend Server", max_wait=30)
    
    if frontend_ready:
        print("✅ Frontend is ready!")
    
    print()
    print("=" * 60)
    print("✅ All servers are ready!")
    print()
    print("📊 Backend API: http://localhost:8000")
    print("📚 API Docs:    http://localhost:8000/docs")
    print("🌐 Frontend:    http://localhost:5173")
    print()
    print("💡 Tip: Open http://localhost:5173 in your browser to use the app")
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
                    print(f"\n⚠️  Process {i+1} exited with code {process.returncode}")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        cleanup()

