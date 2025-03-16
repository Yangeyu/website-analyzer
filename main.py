#!/usr/bin/env python3
"""
Website Analyzer - Main entry point.
Run as API server or CLI tool to analyze websites and generate markdown content.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from pydantic import HttpUrl
from typing_extensions import Annotated

from src.crawler import WebsiteCrawlerService, crawl_url_sync
from src.api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("website-analyzer")

# Create CLI app
cli = typer.Typer(
    name="website-analyzer",
    help="Analyze websites and generate markdown content"
)


@cli.command("crawl")
def crawl_website(
    url: Annotated[str, typer.Argument(help="URL to crawl")],
    output_dir: Annotated[Optional[Path], typer.Option(help="Output directory")] = None,
    max_pages: Annotated[int, typer.Option(help="Maximum pages to crawl")] = 1,
):
    """Crawl a website and save its content as markdown."""
    try:
        result = crawl_url_sync(url, output_dir=output_dir)
        if result["success"]:
            typer.echo(f"✅ Successfully crawled {url}")
            typer.echo(f"📄 Saved to: {result['file_path']}")
            typer.echo(f"📊 Content length: {result['content_length']} characters")
        else:
            typer.echo(f"❌ Failed to crawl {url}: {result['error']}", err=True)
            sys.exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("serve")
def serve_api(
    host: Annotated[str, typer.Option(help="Host to bind")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind")] = 8000,
    reload: Annotated[bool, typer.Option(help="Enable auto-reload")] = False,
):
    """Run the Website Analyzer API server."""
    typer.echo(f"🚀 Starting Website Analyzer API on http://{host}:{port}")
    uvicorn.run("src.api:app", host=host, port=port, reload=reload)


@cli.command("list")
def list_files(
    output_dir: Annotated[Optional[Path], typer.Option(help="Output directory")] = None,
):
    """List all saved markdown files."""
    service = WebsiteCrawlerService(output_dir=output_dir)
    files = list(service.output_dir.glob("*.md"))
    
    if not files:
        typer.echo("No files found.")
        return
    
    typer.echo(f"Found {len(files)} files:")
    for file_path in files:
        stats = file_path.stat()
        size_kb = stats.st_size / 1024
        typer.echo(f"- {file_path.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    cli()
