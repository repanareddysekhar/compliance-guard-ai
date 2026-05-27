import typer
import asyncio
import uuid
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from backend.agent.scan_agent import run_scan
from backend.db.database import async_session
from backend.db.models import ScanRun, Violation
from sqlalchemy import select

app = typer.Typer(help="ComplianceGuard AI CLI - Autonomous Security Compliance Scanner")
console = Console()

async def run_scan_cli(service_name: str, repo_path: str, standards: List[str]):
    scan_id = uuid.uuid4()
    
    async with async_session() as session:
        new_scan = ScanRun(
            id=scan_id,
            service_name=service_name,
            repo_path=repo_path,
            status="RUNNING",
            standards=standards
        )
        session.add(new_scan)
        await session.commit()

    console.print(f"[bold blue]Starting scan for {service_name} at {repo_path}...[/bold blue]")
    console.print(f"Scan ID: [bold]{scan_id}[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description="Scanning...", total=None)
        
        async def on_event(event):
            if event["type"] == "TOOL_CALLED":
                progress.update(task, description=f"Tool: {event['tool']} - {event['intent'][:50]}...")
            elif event["type"] == "VIOLATION_FOUND":
                console.print(f"[bold red]⚠️ Found {event['violation']['severity']} violation: {event['violation']['description']}[/bold red]")

        await run_scan(
            str(scan_id), 
            repo_path, 
            service_name, 
            standards,
            on_event=on_event
        )
        
        progress.update(task, description="Scan Completed!", completed=True)

    console.print("\n[bold green]Scan Completed Successfully![/bold green]")
    await show_results(scan_id)

async def show_results(scan_id: uuid.UUID):
    async with async_session() as session:
        v_query = select(Violation).where(Violation.scan_run_id == scan_id)
        v_result = await session.execute(v_query)
        violations = v_result.scalars().all()

    if not violations:
        console.print("[bold green]No violations found! Your service is compliant.[/bold green]")
        return

    table = Table(title=f"Violations for Scan {scan_id}")
    table.add_column("Severity", justify="center")
    table.add_column("Category", justify="center")
    table.add_column("Description", justify="left")
    table.add_column("File:Line", justify="left")

    for v in violations:
        severity_style = "bold red" if v.severity == "HIGH" else "bold yellow" if v.severity == "MED" else "blue"
        table.add_row(
            f"[{severity_style}]{v.severity}[/{severity_style}]",
            v.category,
            v.description,
            f"{v.file_path}:{v.line_number}"
        )

    console.print(table)

@app.command()
def scan(
    service_name: str = typer.Argument(..., help="Name of the service to scan"),
    repo_path: str = typer.Argument(..., help="Path to the repository to scan"),
    standards: List[str] = typer.Option(["FIPS-140-3", "CIS-Docker", "OWASP-Dependency"], "--standard", "-s", help="Compliance standards to check against")
):
    """Trigger a new compliance scan"""
    asyncio.run(run_scan_cli(service_name, repo_path, standards))

@app.command()
def list_scans():
    """List all previous scan runs"""
    async def _list():
        async with async_session() as session:
            query = select(ScanRun).order_by(ScanRun.started_at.desc())
            result = await session.execute(query)
            scans = result.scalars().all()

        table = Table(title="ComplianceGuard Scan History")
        table.add_column("ID", justify="center")
        table.add_column("Service", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Violations", justify="center")
        table.add_column("Started At", justify="center")

        for s in scans:
            status_style = "green" if s.status == "COMPLETED" else "yellow" if s.status == "RUNNING" else "red"
            table.add_row(
                str(s.id)[:8],
                s.service_name,
                f"[{status_style}]{s.status}[/{status_style}]",
                str(s.violations_found),
                s.started_at.strftime("%Y-%m-%d %H:%M") if s.started_at else "N/A"
            )
        console.print(table)

    asyncio.run(_list())

if __name__ == "__main__":
    app()
