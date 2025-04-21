# sentinelforge/__main__.py

# Comment out Typer CLI imports/setup
# import typer
# from sentinelforge.cli.dashboard import app as dashboard_app
# app = typer.Typer()
# app.add_typer(dashboard_app, name="dashboard")

# Add Uvicorn import
import uvicorn

if __name__ == "__main__":
    # Run the FastAPI app using uvicorn
    uvicorn.run(
        "sentinelforge.api.taxii:app",  # Point to the FastAPI app instance
        host="0.0.0.0",  # Listen on all interfaces
        port=8080,  # Use port 8080
        reload=True,  # Enable auto-reload for development
    )
