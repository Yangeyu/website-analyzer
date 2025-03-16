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
from typing import Optional, List

import typer
import uvicorn
from pydantic import HttpUrl
from typing_extensions import Annotated

from src.crawler import WebsiteCrawlerService, crawl_url_sync, crawl_multiple_urls_sync
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
    depth: Annotated[int, typer.Option(help="Maximum depth to crawl")] = 1,
    follow_links: Annotated[bool, typer.Option(help="Follow links on the page")] = False,
    save_html: Annotated[bool, typer.Option(help="Save raw HTML content")] = False,
    save_links: Annotated[bool, typer.Option(help="Save extracted links")] = True,
    crawl_delay: Annotated[float, typer.Option(help="Delay between requests in seconds")] = 0.0,
    user_agent: Annotated[Optional[str], typer.Option(help="Custom user agent string")] = None,
    extract_metadata: Annotated[bool, typer.Option(help="Extract metadata from pages")] = True,
):
    """Crawl a website and save its content as markdown."""
    try:
        result = crawl_url_sync(
            url, 
            output_dir=output_dir,
            max_pages=max_pages,
            depth=depth,
            follow_links=follow_links,
            save_html=save_html,
            save_links=save_links,
            crawl_delay=crawl_delay,
            user_agent=user_agent,
            extract_metadata=extract_metadata
        )
        if result["success"]:
            typer.echo(f"✅ Successfully crawled {url}")
            typer.echo(f"📄 Saved to: {result['file_path']}")
            
            if result["html_path"]:
                typer.echo(f"🌐 HTML saved to: {result['html_path']}")
                
            typer.echo(f"📊 Content length: {result['content_length']} characters")
            
            if result.get("links_count"):
                typer.echo(f"🔗 Links found: {result['links_count']} total " +
                          f"({result['internal_links_count']} internal, " +
                          f"{result['external_links_count']} external)")
        else:
            typer.echo(f"❌ Failed to crawl {url}: {result['error']}", err=True)
            sys.exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command("crawl-batch")
def crawl_batch(
    urls_file: Annotated[Path, typer.Argument(help="File containing URLs to crawl, one per line")],
    output_dir: Annotated[Optional[Path], typer.Option(help="Output directory")] = None,
    max_pages: Annotated[int, typer.Option(help="Maximum pages to crawl per URL")] = 1,
    save_html: Annotated[bool, typer.Option(help="Save raw HTML content")] = False,
    save_links: Annotated[bool, typer.Option(help="Save extracted links")] = True,
    crawl_delay: Annotated[float, typer.Option(help="Delay between requests in seconds")] = 1.0,
    user_agent: Annotated[Optional[str], typer.Option(help="Custom user agent string")] = None,
    extract_metadata: Annotated[bool, typer.Option(help="Extract metadata from pages")] = True,
):
    """Crawl multiple websites from a file and save their content as markdown."""
    if not urls_file.exists():
        typer.echo(f"❌ File not found: {urls_file}", err=True)
        sys.exit(1)
        
    try:
        # Read URLs from file
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        if not urls:
            typer.echo("❌ No valid URLs found in the file", err=True)
            sys.exit(1)
            
        typer.echo(f"🔍 Found {len(urls)} URLs to crawl")
        
        # Create crawler service
        service = WebsiteCrawlerService(
            output_dir=output_dir,
            save_html=save_html,
            user_agent=user_agent,
            crawl_delay=crawl_delay,
            extract_metadata=extract_metadata
        )
        
        # Run batch crawl
        results = asyncio.run(service.crawl_multiple_urls(
            urls=urls,
            max_pages_per_url=max_pages,
            crawl_delay=crawl_delay
        ))
        
        # Report results
        success_count = sum(1 for r in results if r["success"])
        typer.echo(f"✅ Successfully crawled {success_count} of {len(urls)} URLs")
        
        for result in results:
            if result["success"]:
                typer.echo(f"  ✓ {result['url']} -> {result['file_path']}")
            else:
                typer.echo(f"  ✗ {result['url']}: {result['error']}")
                
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
    typer.echo(f"📚 API documentation available at http://{host}:{port}/docs")
    uvicorn.run("src.api:app", host=host, port=port, reload=reload)


@cli.command("list")
def list_files(
    output_dir: Annotated[Optional[Path], typer.Option(help="Output directory")] = None,
    show_all: Annotated[bool, typer.Option(help="Show all file types")] = False,
):
    """List all saved files."""
    service = WebsiteCrawlerService(output_dir=output_dir)
    
    # Get markdown files
    md_files = list(service.output_dir.glob("*.md"))
    
    # Get HTML files if they exist
    html_dir = service.output_dir / "html"
    html_files = list(html_dir.glob("*.html")) if html_dir.exists() else []
    
    # Get JSON files
    json_files = list(service.output_dir.glob("*_links.json"))
    
    if not md_files and not html_files and not json_files:
        typer.echo("No files found.")
        return
    
    # Show markdown files
    if md_files:
        typer.echo(f"Found {len(md_files)} markdown files:")
        for file_path in md_files:
            stats = file_path.stat()
            size_kb = stats.st_size / 1024
            typer.echo(f"- {file_path.name} ({size_kb:.1f} KB)")
    
    # Show HTML files if requested
    if show_all and html_files:
        typer.echo(f"\nFound {len(html_files)} HTML files:")
        for file_path in html_files:
            stats = file_path.stat()
            size_kb = stats.st_size / 1024
            typer.echo(f"- {file_path.name} ({size_kb:.1f} KB)")
    
    # Show JSON files if requested
    if show_all and json_files:
        typer.echo(f"\nFound {len(json_files)} JSON files:")
        for file_path in json_files:
            stats = file_path.stat()
            size_kb = stats.st_size / 1024
            typer.echo(f"- {file_path.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    cli()
