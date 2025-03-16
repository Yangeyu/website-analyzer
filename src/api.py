"""
FastAPI interface for website crawler service.
"""
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from .crawler import WebsiteCrawlerService, crawl_url_sync

# Initialize FastAPI app
app = FastAPI(
    title="Website Analyzer API",
    description="API for crawling websites and generating markdown content",
    version="0.1.0",
)

# Initialize crawler service
crawler_service = WebsiteCrawlerService()


class CrawlRequest(BaseModel):
    """Model for a crawl request."""
    url: HttpUrl
    max_pages: Optional[int] = 1


class CrawlResponse(BaseModel):
    """Model for a crawl response."""
    success: bool
    url: str
    file_path: Optional[str] = None
    title: Optional[str] = None
    content_length: Optional[int] = None
    error: Optional[str] = None


class FileInfo(BaseModel):
    """Model for file information."""
    filename: str
    file_path: str
    size_bytes: int
    created_at: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Website Analyzer API is running"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """Crawl a website and generate markdown content.
    
    Args:
        request: CrawlRequest containing the URL to crawl
        
    Returns:
        CrawlResponse with results and file info
    """
    try:
        result = await crawler_service.crawl_url(
            url=str(request.url), 
            max_pages=request.max_pages
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
        request: CrawlRequest containing the URL to crawl
        background_tasks: FastAPI background tasks
        
    Returns:
        Confirmation that the task has been scheduled
    """
    background_tasks.add_task(
        crawl_url_sync, 
        url=str(request.url), 
        output_dir=None
    )
    return {
        "message": f"Crawling of {request.url} started in background",
        "status": "processing"
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
        for file_path in output_dir.glob("*.md"):
            stats = file_path.stat()
            created_time = datetime.fromtimestamp(stats.st_ctime).isoformat()
            
            files.append(
                FileInfo(
                    filename=file_path.name,
                    file_path=str(file_path),
                    size_bytes=stats.st_size,
                    created_at=created_time
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
    """Get the content of a specific markdown file.
    
    Args:
        filename: Name of the file to retrieve
        
    Returns:
        File content as text
    """
    file_path = crawler_service.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"File {filename} not found"
        )
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading file: {str(e)}"
        )
