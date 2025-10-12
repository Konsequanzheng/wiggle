#!/usr/bin/env python3
"""
Startup script for the Direct Wiggle API
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set environment variables if not already set
if not os.getenv("WEAVIATE_GRPC_ENDPOINT"):
    os.environ["WEAVIATE_GRPC_ENDPOINT"] = "grpc-aoj6v69aspmruwn6zlgma.c0.europe-west3.gcp.weaviate.cloud"

if not os.getenv("WEAVIATE_API_KEY"):
    os.environ["WEAVIATE_API_KEY"] = "N08rcE1Ua0pJTlB1RVh0cF9XeEJjMVRGZE5MdjF1YkpqanZKc1RHaTV3ajc4c3BaOEZiOTA5ZXBlay9nPV92MjAw"

def main():
    """Run the FastAPI application"""
    print("🚀 Starting Wiggle Direct API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
    print("🔍 Health check at: http://localhost:8000/health")
    print()
    
    try:
        uvicorn.run(
            "direct_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Wiggle Direct API...")
    except Exception as e:
        print(f"❌ Error starting API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()