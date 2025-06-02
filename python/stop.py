# stop.py
import subprocess

def stop_services():
    print("🛑 Stopping PostgreSQL and services via Assemble.py...")
    subprocess.run(["python3", "Assemble.py", "stop"], check=True)
    print("✅ Shutdown complete.")

if __name__ == "__main__":
    try:
        stop_services()
    except subprocess.CalledProcessError as e:
        print("❌ Error stopping services:", e)