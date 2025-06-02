# start.py
import subprocess
import time
import os

def run_assemble():
    print("🔧 Initializing PostgreSQL via Assemble.py...")
    subprocess.run(["python3", "Assemble.py"], check=True)

def start_php_server():
    print("🚀 Starting PHP server at http://localhost:8000 ...")
    # Run PHP server in background
    return subprocess.Popen(["php", "-S", "0.0.0.0:8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    try:
        run_assemble()
        time.sleep(1)  # small buffer to ensure DB starts up
        php_process = start_php_server()
        print("✅ Server is running. Press Ctrl+C to exit.\n")
        php_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except subprocess.CalledProcessError as e:
        print("❌ Error:", e)