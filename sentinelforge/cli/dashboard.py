import typer
from rich.table import Table
from rich.console import Console
from datetime import datetime
from typing import Optional
import logging

# Use correct import path and model name
from sentinelforge.storage import SessionLocal, IOC

# Import rules to use defined tiers
from sentinelforge.scoring import _rules as scoring_rules


app = typer.Typer()
console = Console()
logger = logging.getLogger(__name__)

# Get tier thresholds from loaded rules (provide safe defaults)
default_tiers = {"high": 50, "medium": 20, "low": 0}
tiers = scoring_rules.get("tiers", default_tiers)
high_threshold = tiers.get("high", default_tiers["high"])
medium_threshold = tiers.get("medium", default_tiers["medium"])


@app.command()
def top(
    limit: int = typer.Option(20, "--limit", "-n", help="How many IOCs to show"),
    ioc_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by IOC type: ip, domain, hash, etc."
    ),
    since: Optional[str] = typer.Option(None, "--since", "-s", help="Start date (YYYY-MM-DD)"),
    until: Optional[str] = typer.Option(None, "--until", "-u", help="End date (YYYY-MM-DD)"),
):
    """
    Show top-scoring IOCs from the database.
    """
    db = None
    try:
        db = SessionLocal()
        logger.info("Database session created for dashboard.")

        # Use correct model name (IOC)
        q = db.query(IOC)

        # Use correct column name (ioc_type)
        if ioc_type:
            q = q.filter(IOC.ioc_type == ioc_type)

        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                q = q.filter(IOC.first_seen >= since_dt)
            except ValueError:
                console.print(
                    f"[bold red]Error:[/bold red] Invalid format for --since '{since}'. Use YYYY-MM-DD."
                )
                raise typer.Exit(code=1)

        if until:
            try:
                # Add time component to make it inclusive of the end date
                until_dt = datetime.fromisoformat(until + "T23:59:59")
                q = q.filter(IOC.first_seen <= until_dt)
            except ValueError:
                console.print(
                    f"[bold red]Error:[/bold red] Invalid format for --until '{until}'. Use YYYY-MM-DD."
                )
                raise typer.Exit(code=1)

        # Basic stats using thresholds from scoring_rules
        total = q.count()
        high = q.filter(IOC.score >= high_threshold).count()
        medium = q.filter(IOC.score.between(medium_threshold, high_threshold - 1)).count()
        low = q.filter(IOC.score < medium_threshold).count()

        console.print(
            f"[bold]Total IOCs:[/] {total}   "
            f"[bold green]High ({high_threshold}+):[/] {high}   "
            f"[bold yellow]Med ({medium_threshold}-{high_threshold - 1}):[/] {medium}   "
            f"[bold blue]Low (<{medium_threshold}):[/] {low}"
        )

        # Top N by score (use correct model IOC)
        top_n = q.order_by(IOC.score.desc()).limit(limit).all()

        if not top_n:
            console.print("No IOCs found matching the criteria.")
            return

        table = Table("Score", "Category", "Type", "Value", "Source Feed", "First Seen")
        for i in top_n:
            # Use correct model (IOC) and column names (ioc_type, ioc_value)
            table.add_row(
                str(i.score),
                i.category,
                i.ioc_type,
                i.ioc_value,
                i.source_feed,
                i.first_seen.date().isoformat(),
            )

        console.print(table)

    except Exception as e:
        logger.error(f"Dashboard command failed: {e}", exc_info=True)
        console.print(f"[bold red]An error occurred:[/bold red] {e}")
        raise typer.Exit(code=1)
    finally:
        if db:
            db.close()
            logger.info("Database session closed for dashboard.")


if __name__ == "__main__":
    app()
