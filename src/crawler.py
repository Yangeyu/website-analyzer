"""
Website content crawler service using Crawl4AI.
"""
import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import DeepCrawlStrategy
from slugify import slugify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("website-analyzer")

# Set default paths
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "temp"


class WebsiteCrawlerService:
    """Service for crawling websites and extracting content as markdown."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the crawler service.
        
        Args:
            output_dir: Directory to save markdown files. Defaults to data/temp.
        """
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure browser options
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )
    
    def _extract_title_from_markdown(self, markdown: str) -> str:
        """Extract title from markdown content.
        
        Args:
            markdown: Markdown content
            
        Returns:
            Extracted title or default title
        """
        # Try to find the first H1 heading
        h1_match = re.search(r'^# (.+)$', markdown, re.MULTILINE)
        if h1_match:
            return h1_match.group(1)
        
        # Try to find any heading if no H1
        heading_match = re.search(r'^#+\s+(.+)$', markdown, re.MULTILINE)
        if heading_match:
            return heading_match.group(1)
        
        # Default title
        return "Website Content"
        
    async def crawl_url(self, url: str, max_pages: int = 1) -> Dict[str, Union[bool, str, Path]]:
        """Crawl a URL and save its content as markdown.
        
        Args:
            url: The website URL to crawl
            max_pages: Maximum number of pages to crawl (for deep crawling)
        
        Returns:
            Dictionary with crawl results and file locations
        """
        logger.info(f"Crawling URL: {url}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(url).netloc
        slug = slugify(domain)
        
        # Create a unique filename based on domain and timestamp
        filename = f"{slug}_{timestamp}.md"
        output_path = self.output_dir / filename
        
        # Setup crawler config
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            pdf=False,
            screenshot=True,
        )
        
        # Add deep crawl config if needed
        if max_pages > 1:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED,
                pdf=False,
                screenshot=True,
                deep_crawl_strategy=DeepCrawlStrategy.BFS,
                max_pages=max_pages,
                same_domain_only=True,
            )
        
        try:
            # Initialize and run crawler
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success:
                    # Extract title from markdown or use domain as fallback
                    page_title = self._extract_title_from_markdown(result.markdown)
                    
                    # Save markdown to file
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(f"# {page_title}\n\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"Crawled: {datetime.now().isoformat()}\n\n")
                        f.write("---\n\n")
                        f.write(result.markdown)
                    
                    logger.info(f"Successfully crawled {url}, saved to {output_path}")
                    
                    return {
                        "success": True,
                        "url": url,
                        "file_path": str(output_path),
                        "title": page_title,
                        "content_length": len(result.markdown)
                    }
                else:
                    logger.error(f"Failed to crawl {url}: {result.error_message}")
                    return {
                        "success": False,
                        "url": url,
                        "error": result.error_message
                    }
                    
        except Exception as e:
            logger.exception(f"Error crawling {url}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }


async def crawl_single_url(url: str, output_dir: Optional[Path] = None) -> Dict:
    """Utility function to crawl a single URL."""
    service = WebsiteCrawlerService(output_dir=output_dir)
    return await service.crawl_url(url)


def crawl_url_sync(url: str, output_dir: Optional[Path] = None) -> Dict:
    """Synchronous wrapper for crawl_single_url."""
    return asyncio.run(crawl_single_url(url, output_dir=output_dir))
