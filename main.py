import os
import subprocess
import time
import sys
from pathlib import Path

def print_header():
    print("="*60)
    print("🚀 Starting Obsidian RAG System")
    print("="*60)

def main():
    print_header()
    
    # 1. Start the FastAPI backend
    print("[1/2] Starting Backend API (pydantic/FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.api:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL, # Ocultamos los logs para que la consola quede limpia
        stderr=subprocess.STDOUT
    )
    
    # Give a few seconds for the API to load the models locally into the GPU
    print("      Loading LanceDB and Embedding Models into GPU (this may take a moment)...")
    time.sleep(4)
    
    # 2. Start Open WebUI
    print("[2/2] Starting Open WebUI Frontend...")
    
    # Prepare the necessary environment variables for Open WebUI
    env = os.environ.copy()
    env["OPENAI_API_BASE_URL"] = "http://127.0.0.1:8000/v1"
    env["OPENAI_API_KEY"] = "nada"
    env["WEBUI_PORT"] = "8080"
    
    try:
        frontend_process = subprocess.Popen(
            ["open-webui", "serve"],
            env=env
        )
        
        print("\n" + "="*60)
        print("✨ SYSTEM READY ✨")
        print("👉 Frontend: http://localhost:8080")
        print("👉 API Docs: http://localhost:8000/docs")
        print("Press Ctrl+C to stop all services.")
        print("="*60 + "\n")
        
        # Keep the script alive waiting for the user to press Ctrl+C
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
    finally:
        # Kill orphan processes before closing
        print("Killing backend server...")
        backend_process.terminate()
        try:
            frontend_process.terminate()
            print("Killing frontend server...")
        except:
            pass
        print("Goodbye! 👋")

if __name__ == "__main__":
    main()
