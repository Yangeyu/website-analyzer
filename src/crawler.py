"""
Website content crawler service using Crawl4AI.
"""
import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse

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

# Default User-Agent strings
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:123.0) Gecko/20100101 Firefox/123.0"
]


class WebsiteCrawlerService:
    """Service for crawling websites and extracting content as markdown."""
    
    def __init__(
        self, 
        output_dir: Optional[Path] = None,
        save_html: bool = False,
        user_agent: Optional[str] = None,
        crawl_delay: float = 0.0,
        extract_metadata: bool = True,
    ):
        """Initialize the crawler service.
        
        Args:
            output_dir: Directory to save markdown files. Defaults to data/temp.
            save_html: Whether to save raw HTML content. Defaults to False.
            user_agent: Custom user agent string. If None, a random one is selected.
            crawl_delay: Delay between requests in seconds. Defaults to 0.0.
            extract_metadata: Whether to extract metadata from pages. Defaults to True.
        """
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.save_html = save_html
        self.crawl_delay = crawl_delay
        self.extract_metadata = extract_metadata
        
        # Create html directory if saving HTML
        if self.save_html:
            (self.output_dir / "html").mkdir(exist_ok=True)
        
        # Set up user agent
        if user_agent:
            self.user_agent = user_agent
        else:
            import random
            self.user_agent = random.choice(DEFAULT_USER_AGENTS)
        
        # Configure browser options
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            user_agent=self.user_agent
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
    
    def _extract_metadata(self, html: str) -> Dict[str, str]:
        """Extract metadata from HTML content.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Extract title from meta tags
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Extract description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if desc_match:
            metadata["description"] = desc_match.group(1).strip()
        
        # Extract keywords
        keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if keywords_match:
            metadata["keywords"] = keywords_match.group(1).strip()
        
        # Extract Open Graph metadata
        og_matches = re.finditer(r'<meta[^>]*property=["\']og:([^"\']+)["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for match in og_matches:
            og_property = match.group(1).strip()
            og_content = match.group(2).strip()
            metadata[f"og:{og_property}"] = og_content
        
        return metadata
    
    def _extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract and analyze links from HTML content.
        
        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dictionaries with link information
        """
        links = []
        link_matches = re.finditer(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html)
        
        parsed_base_url = urlparse(base_url)
        base_domain = parsed_base_url.netloc
        
        for match in link_matches:
            href = match.group(1).strip()
            text = match.group(2).strip()
            
            # Skip empty, javascript, and anchor links
            if not href or href.startswith("javascript:") or href.startswith("#"):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)
            
            # Determine if internal or external
            is_internal = parsed_url.netloc == base_domain or not parsed_url.netloc
            
            links.append({
                "url": absolute_url,
                "text": text,
                "is_internal": is_internal,
                "domain": parsed_url.netloc or base_domain,
                "path": parsed_url.path
            })
        
        return links
        
    async def crawl_url(
        self, 
        url: str, 
        max_pages: int = 1,
        depth: int = 1,
        follow_links: bool = False,
        save_links: bool = True
    ) -> Dict[str, Union[bool, str, Path, Dict]]:
        """Crawl a URL and save its content as markdown.
        
        Args:
            url: The website URL to crawl
            max_pages: Maximum number of pages to crawl (for deep crawling)
            depth: Maximum depth to crawl (for deep crawling)
            follow_links: Whether to follow links on the page
            save_links: Whether to save extracted links
        
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
        
        # Create HTML filename if saving HTML
        html_path = None
        if self.save_html:
            html_filename = f"{slug}_{timestamp}.html"
            html_path = self.output_dir / "html" / html_filename
        
        # Setup crawler config
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            pdf=False,
            screenshot=True,
        )
        
        # Add deep crawl config if needed
        if max_pages > 1 and follow_links:
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED,
                pdf=False,
                screenshot=True,
                deep_crawl_strategy=DeepCrawlStrategy.BFS,
                max_pages=max_pages,
                max_depth=depth,
                same_domain_only=True,
            )
        
        try:
            # Add delay if configured
            if self.crawl_delay > 0:
                logger.info(f"Waiting {self.crawl_delay} seconds before crawling...")
                await asyncio.sleep(self.crawl_delay)
            
            # Initialize and run crawler
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success:
                    # Extract title from markdown or use domain as fallback
                    page_title = self._extract_title_from_markdown(result.markdown)
                    
                    # Extract metadata and links if needed
                    metadata = {}
                    links = []
                    
                    if result.html:
                        if self.extract_metadata:
                            metadata = self._extract_metadata(result.html)
                        
                        if save_links:
                            links = self._extract_links(result.html, url)
                    
                    # Save HTML if requested
                    if self.save_html and result.html and html_path:
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(result.html)
                        logger.info(f"Saved HTML to {html_path}")
                    
                    # Save markdown to file
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(f"# {page_title}\n\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"Crawled: {datetime.now().isoformat()}\n\n")
                        
                        # Add metadata section if available
                        if metadata:
                            f.write("## Metadata\n\n")
                            for key, value in metadata.items():
                                f.write(f"- **{key}**: {value}\n")
                            f.write("\n---\n\n")
                        
                        # Add links section if available and requested
                        if links and save_links:
                            f.write("## Links\n\n")
                            
                            # Internal links
                            internal_links = [l for l in links if l["is_internal"]]
                            if internal_links:
                                f.write("### Internal Links\n\n")
                                for link in internal_links:
                                    f.write(f"- [{link['text'] or link['url']}]({link['url']})\n")
                                f.write("\n")
                            
                            # External links
                            external_links = [l for l in links if not l["is_internal"]]
                            if external_links:
                                f.write("### External Links\n\n")
                                for link in external_links:
                                    f.write(f"- [{link['text'] or link['url']}]({link['url']}) - {link['domain']}\n")
                                f.write("\n")
                            
                            f.write("---\n\n")
                        
                        # Add main content
                        f.write("## Content\n\n")
                        f.write(result.markdown)
                    
                    logger.info(f"Successfully crawled {url}, saved to {output_path}")
                    
                    # Save links to JSON file if requested
                    if links and save_links:
                        links_filename = f"{slug}_{timestamp}_links.json"
                        links_path = self.output_dir / links_filename
                        with open(links_path, "w", encoding="utf-8") as f:
                            json.dump({
                                "url": url,
                                "total_links": len(links),
                                "internal_links": len([l for l in links if l["is_internal"]]),
                                "external_links": len([l for l in links if not l["is_internal"]]),
                                "links": links
                            }, f, indent=2)
                        logger.info(f"Saved links to {links_path}")
                    
                    return {
                        "success": True,
                        "url": url,
                        "file_path": str(output_path),
                        "html_path": str(html_path) if html_path else None,
                        "title": page_title,
                        "content_length": len(result.markdown),
                        "metadata": metadata,
                        "links_count": len(links),
                        "internal_links_count": len([l for l in links if l["is_internal"]]),
                        "external_links_count": len([l for l in links if not l["is_internal"]])
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
    
    async def crawl_multiple_urls(
        self, 
        urls: List[str], 
        max_pages_per_url: int = 1,
        crawl_delay: Optional[float] = None
    ) -> List[Dict]:
        """Crawl multiple URLs with delay between requests.
        
        Args:
            urls: List of URLs to crawl
            max_pages_per_url: Maximum pages to crawl per URL
            crawl_delay: Override the instance crawl delay
            
        Returns:
            List of dictionaries with crawl results
        """
        results = []
        delay = crawl_delay if crawl_delay is not None else self.crawl_delay
        
        for url in urls:
            result = await self.crawl_url(url, max_pages=max_pages_per_url)
            results.append(result)
            
            # Apply delay between requests
            if delay > 0 and url != urls[-1]:  # Don't delay after the last URL
                logger.info(f"Waiting {delay} seconds before next crawl...")
                await asyncio.sleep(delay)
        
        return results


async def crawl_single_url(url: str, output_dir: Optional[Path] = None, **kwargs) -> Dict:
    """Utility function to crawl a single URL."""
    service = WebsiteCrawlerService(output_dir=output_dir, **kwargs)
    return await service.crawl_url(url, **kwargs)


def crawl_url_sync(url: str, output_dir: Optional[Path] = None, **kwargs) -> Dict:
    """Synchronous wrapper for crawl_single_url."""
    return asyncio.run(crawl_single_url(url, output_dir=output_dir, **kwargs))


async def crawl_multiple_urls_sync(urls: List[str], output_dir: Optional[Path] = None, **kwargs) -> List[Dict]:
    """Synchronous wrapper for crawling multiple URLs."""
    service = WebsiteCrawlerService(output_dir=output_dir, **kwargs)
    return await service.crawl_multiple_urls(urls, **kwargs)
