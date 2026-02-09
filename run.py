"""
Entry point for the Smart Waste IoT Dashboard web application.
Run with: python run.py
"""
import uvicorn


def main():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
