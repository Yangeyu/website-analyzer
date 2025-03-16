"""
FastAPI interface for website crawler service.
"""
import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field

from .crawler import WebsiteCrawlerService, crawl_url_sync, crawl_multiple_urls_sync

# Initialize FastAPI app
app = FastAPI(
    title="Website Analyzer API",
    description="API for crawling websites and generating markdown content",
    version="0.2.0",
)

# Initialize crawler service with default settings
crawler_service = WebsiteCrawlerService()


class CrawlRequest(BaseModel):
    """Model for a crawl request."""
    url: HttpUrl
    max_pages: Optional[int] = 1
    depth: Optional[int] = 1
    follow_links: Optional[bool] = False
    save_html: Optional[bool] = False
    save_links: Optional[bool] = True
    crawl_delay: Optional[float] = 0.0
    user_agent: Optional[str] = None
    extract_metadata: Optional[bool] = True


class BatchCrawlRequest(BaseModel):
    """Model for a batch crawl request."""
    urls: List[HttpUrl]
    max_pages_per_url: Optional[int] = 1
    crawl_delay: Optional[float] = 1.0
    save_html: Optional[bool] = False
    save_links: Optional[bool] = True
    user_agent: Optional[str] = None
    extract_metadata: Optional[bool] = True


class LinkInfo(BaseModel):
    """Model for link information."""
    url: str
    text: Optional[str] = None
    is_internal: bool
    domain: str
    path: Optional[str] = None


class CrawlResponse(BaseModel):
    """Model for a crawl response."""
    success: bool
    url: str
    file_path: Optional[str] = None
    html_path: Optional[str] = None
    title: Optional[str] = None
    content_length: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None
    links_count: Optional[int] = None
    internal_links_count: Optional[int] = None
    external_links_count: Optional[int] = None
    error: Optional[str] = None


class FileInfo(BaseModel):
    """Model for file information."""
    filename: str
    file_path: str
    size_bytes: int
    created_at: str
    type: str = "markdown"


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Website Analyzer API is running"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """Crawl a website and generate markdown content.
    
    Args:
        request: CrawlRequest containing the URL to crawl and options
        
    Returns:
        CrawlResponse with results and file info
    """
    try:
        # Create custom crawler if specialized parameters are provided
        if any([
            request.save_html, 
            request.crawl_delay > 0,
            request.user_agent,
            request.extract_metadata is not True  # Default is True
        ]):
            custom_crawler = WebsiteCrawlerService(
                save_html=request.save_html,
                crawl_delay=request.crawl_delay,
                user_agent=request.user_agent,
                extract_metadata=request.extract_metadata
            )
            result = await custom_crawler.crawl_url(
                url=str(request.url), 
                max_pages=request.max_pages,
                depth=request.depth,
                follow_links=request.follow_links,
                save_links=request.save_links
            )
        else:
            # Use default crawler service
            result = await crawler_service.crawl_url(
                url=str(request.url), 
                max_pages=request.max_pages,
                depth=request.depth,
                follow_links=request.follow_links,
                save_links=request.save_links
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawl/background")
async def crawl_website_background(
    request: CrawlRequest, background_tasks: BackgroundTasks
):
    """Crawl a website in the background.
    
    Args:
        request: CrawlRequest containing the URL to crawl and options
        background_tasks: FastAPI background tasks
        
    Returns:
        Confirmation that the task has been scheduled
    """
    # Convert to dict to handle HttpUrl type
    request_dict = request.model_dump()
    url = str(request_dict.pop("url"))
    
    background_tasks.add_task(
        crawl_url_sync, 
        url=url, 
        output_dir=None,
        **request_dict
    )
    return {
        "message": f"Crawling of {url} started in background",
        "status": "processing",
        "options": request_dict
    }


@app.post("/crawl-batch", response_model=List[CrawlResponse])
async def crawl_multiple_websites(request: BatchCrawlRequest):
    """Crawl multiple websites and generate markdown content.
    
    Args:
        request: BatchCrawlRequest containing the URLs to crawl and options
        
    Returns:
        List of CrawlResponse with results for each URL
    """
    try:
        # Create custom crawler with batch settings
        custom_crawler = WebsiteCrawlerService(
            save_html=request.save_html,
            crawl_delay=request.crawl_delay,
            user_agent=request.user_agent,
            extract_metadata=request.extract_metadata
        )
        
        # Convert URLs to strings
        url_strings = [str(url) for url in request.urls]
        
        # Execute batch crawl
        results = await custom_crawler.crawl_multiple_urls(
            urls=url_strings,
            max_pages_per_url=request.max_pages_per_url,
            crawl_delay=request.crawl_delay
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawl-batch/background")
async def crawl_multiple_websites_background(
    request: BatchCrawlRequest, background_tasks: BackgroundTasks
):
    """Crawl multiple websites in the background.
    
    Args:
        request: BatchCrawlRequest containing the URLs to crawl and options
        background_tasks: FastAPI background tasks
        
    Returns:
        Confirmation that the task has been scheduled
    """
    # Convert to dict to handle HttpUrl type
    request_dict = request.model_dump()
    urls = [str(url) for url in request_dict.pop("urls")]
    
    background_tasks.add_task(
        crawl_multiple_urls_sync,
        urls=urls,
        output_dir=None,
        **request_dict
    )
    
    return {
        "message": f"Batch crawling of {len(urls)} URLs started in background",
        "status": "processing",
        "url_count": len(urls),
        "options": request_dict
    }


@app.get("/files", response_model=List[FileInfo])
async def list_files():
    """List all saved markdown files.
    
    Returns:
        List of FileInfo objects
    """
    output_dir = crawler_service.output_dir
    files = []
    
    try:
        # Get markdown files
        for file_path in output_dir.glob("*.md"):
            stats = file_path.stat()
            created_time = datetime.fromtimestamp(stats.st_ctime).isoformat()
            
            files.append(
                FileInfo(
                    filename=file_path.name,
                    file_path=str(file_path),
                    size_bytes=stats.st_size,
                    created_at=created_time,
                    type="markdown"
                )
            )
        
        # Get HTML files if they exist
        html_dir = output_dir / "html"
        if html_dir.exists():
            for file_path in html_dir.glob("*.html"):
                stats = file_path.stat()
                created_time = datetime.fromtimestamp(stats.st_ctime).isoformat()
                
                files.append(
                    FileInfo(
                        filename=file_path.name,
                        file_path=str(file_path),
                        size_bytes=stats.st_size,
                        created_at=created_time,
                        type="html"
                    )
                )
        
        # Get JSON files (for links)
        for file_path in output_dir.glob("*_links.json"):
            stats = file_path.stat()
            created_time = datetime.fromtimestamp(stats.st_ctime).isoformat()
            
            files.append(
                FileInfo(
                    filename=file_path.name,
                    file_path=str(file_path),
                    size_bytes=stats.st_size,
                    created_at=created_time,
                    type="json"
                )
            )
        
        return files
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )


@app.get("/files/{filename}")
async def get_file_content(filename: str):
    """Get the content of a specific file.
    
    Args:
        filename: Name of the file to retrieve
        
    Returns:
        File content as text
    """
    # Determine the file path based on extension
    if filename.endswith(".html"):
        file_path = crawler_service.output_dir / "html" / filename
    else:
        file_path = crawler_service.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"File {filename} not found"
        )
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Determine content type
        if filename.endswith(".md"):
            content_type = "markdown"
        elif filename.endswith(".html"):
            content_type = "html"
        elif filename.endswith(".json"):
            content_type = "json"
        else:
            content_type = "text"
            
        return {
            "filename": filename,
            "content": content,
            "content_type": content_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading file: {str(e)}"
        )


@app.get("/healthcheck")
async def healthcheck():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }
