"""
Convenience script to start the FastAPI backend server
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Agentic Recommendation API Backend")
    print("=" * 60)
    print()
    print("API will be available at: http://localhost:8000")
    print("API docs will be at: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

