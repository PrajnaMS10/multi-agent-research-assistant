"""
Run the API server for the React frontend.

    python main.py

Then start the frontend from the `frontend` folder (see README).
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
