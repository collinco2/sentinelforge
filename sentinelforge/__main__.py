# sentinelforge/__main__.py
import typer
from sentinelforge.cli.dashboard import app as dashboard_app

# Create the main application instance
app = typer.Typer()

# Add the dashboard commands under the name "dashboard"
app.add_typer(dashboard_app, name="dashboard")

# TODO: Add other command groups here (e.g., ingestion, enrichment)
# app.add_typer(ingestion_app, name="ingest")

if __name__ == "__main__":
    app()
