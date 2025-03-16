"""
Unit tests for the website crawler service.
Tests crawling functionality with the OpenAI Agents SDK documentation page.
"""
import os
import asyncio
import unittest
import json
from pathlib import Path
import re
import pytest

from src.crawler import WebsiteCrawlerService, crawl_single_url, crawl_url_sync


@pytest.fixture
def test_output_dir():
    """Create a test output directory."""
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    # Cleanup is handled separately to keep generated files for inspection


@pytest.fixture
def crawler(test_output_dir):
    """Create a crawler service with test output directory."""
    return WebsiteCrawlerService(output_dir=test_output_dir)


@pytest.fixture
def advanced_crawler(test_output_dir):
    """Create a crawler service with advanced features enabled."""
    return WebsiteCrawlerService(
        output_dir=test_output_dir,
        save_html=True,
        crawl_delay=0.5,
        extract_metadata=True
    )


@pytest.mark.crawler
class TestWebsiteCrawler:
    """Test cases for website crawler functionality."""
    
    openai_agents_url = "https://openai.github.io/openai-agents-python/"
    
    def test_extract_title_from_markdown(self, crawler):
        """Test the title extraction functionality."""
        # Test with H1 heading
        markdown_with_h1 = "# This is an H1 Title\nSome content"
        title = crawler._extract_title_from_markdown(markdown_with_h1)
        assert title == "This is an H1 Title"
        
        # Test with no heading
        markdown_no_heading = "Just some content without a heading"
        title = crawler._extract_title_from_markdown(markdown_no_heading)
        assert title == "Website Content"
    
    def test_extract_metadata(self, crawler):
        """Test metadata extraction functionality."""
        html = """
        <html>
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="This is a test description">
                <meta name="keywords" content="test, metadata, crawler">
                <meta property="og:title" content="OG Test Title">
                <meta property="og:description" content="OG test description">
                <meta property="og:image" content="https://example.com/image.jpg">
            </head>
            <body>
                <h1>Test Page</h1>
                <p>This is a test page</p>
            </body>
        </html>
        """
        
        metadata = crawler._extract_metadata(html)
        
        assert "title" in metadata
        assert metadata["title"] == "Test Page Title"
        assert "description" in metadata
        assert metadata["description"] == "This is a test description"
        assert "keywords" in metadata
        assert metadata["keywords"] == "test, metadata, crawler"
        assert "og:title" in metadata
        assert metadata["og:title"] == "OG Test Title"
        assert "og:description" in metadata
        assert metadata["og:description"] == "OG test description"
        assert "og:image" in metadata
        assert metadata["og:image"] == "https://example.com/image.jpg"
    
    def test_extract_links(self, crawler):
        """Test link extraction functionality."""
        base_url = "https://example.com/page"
        html = """
        <html>
            <body>
                <a href="https://example.com/internal1">Internal Link 1</a>
                <a href="/internal2">Internal Link 2</a>
                <a href="#section">Anchor Link</a>
                <a href="https://external.com/page">External Link</a>
                <a href="javascript:void(0)">JavaScript Link</a>
                <a href="">Empty Link</a>
                <a href="relative/path">Relative Link</a>
            </body>
        </html>
        """
        
        links = crawler._extract_links(html, base_url)
        
        # Should extract 4 valid links (excluding javascript, anchor, and empty links)
        assert len(links) == 4
        
        # Check internal links
        internal_links = [l for l in links if l["is_internal"]]
        assert len(internal_links) == 3
        
        # Check external links
        external_links = [l for l in links if not l["is_internal"]]
        assert len(external_links) == 1
        assert external_links[0]["domain"] == "external.com"
        
        # Check relative link resolution
        relative_link = next(l for l in links if l["text"] == "Relative Link")
        assert relative_link["url"] == "https://example.com/relative/path"
    
    @pytest.mark.slow
    def test_crawl_url_sync(self, test_output_dir):
        """Test synchronous crawling of a URL."""
        # Crawl the OpenAI Agents SDK docs
        result = asyncio.run(crawl_single_url(
            self.openai_agents_url, 
            output_dir=test_output_dir
        ))
        
        # Verify the result
        assert result["success"] is True
        assert "openai-github-io" in result["file_path"]
        assert result["content_length"] > 0
        
        # Verify the file exists
        assert os.path.exists(result["file_path"])
        
        # Verify the content of the file
        with open(result["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
            
            # Check for expected content from the OpenAI Agents SDK docs
            assert "OpenAI" in content
            assert "Agents" in content
            assert "SDK" in content
            
            # Check for specific content
            expressions = [
                r"agent",
                r"openai",
                r"documentation"
            ]
            
            for expression in expressions:
                assert re.search(expression, content, re.IGNORECASE) is not None, \
                    f"Expected to find '{expression}' in content"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_crawl_url_async(self, crawler):
        """Test asynchronous crawling of a URL."""
        # Crawl the OpenAI Agents SDK docs
        result = await crawler.crawl_url(self.openai_agents_url)
        
        # Verify the result
        assert result["success"] is True
        assert "openai-github-io" in result["file_path"]
        assert result["content_length"] > 0
        
        # Verify the file exists
        assert os.path.exists(result["file_path"])
        
        # Check the content
        with open(result["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
            assert "OpenAI" in content
            assert "Agents" in content
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_advanced_crawl_features(self, advanced_crawler, test_output_dir):
        """Test advanced crawling features."""
        # Crawl with advanced features enabled
        result = await advanced_crawler.crawl_url(
            self.openai_agents_url,
            save_links=True
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["content_length"] > 0
        
        # Verify HTML was saved
        assert result["html_path"] is not None
        assert os.path.exists(result["html_path"])
        
        # Verify metadata was extracted
        assert "metadata" in result
        assert len(result["metadata"]) > 0
        
        # Verify links were extracted and counts are available
        assert "links_count" in result
        assert result["links_count"] > 0
        assert "internal_links_count" in result
        assert "external_links_count" in result
        
        # Check for links JSON file
        links_files = list(test_output_dir.glob("*_links.json"))
        assert len(links_files) > 0
        
        # Verify the links JSON content
        with open(links_files[0], "r", encoding="utf-8") as f:
            links_data = json.load(f)
            assert "url" in links_data
            assert "total_links" in links_data
            assert "links" in links_data
            assert len(links_data["links"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_crawl_multiple_urls(self, advanced_crawler):
        """Test crawling multiple URLs."""
        # Define multiple URLs to crawl
        urls = [
            "https://openai.github.io/openai-agents-python/",
            "https://docs.python.org/3/"
        ]
        
        # Crawl multiple URLs
        results = await advanced_crawler.crawl_multiple_urls(
            urls,
            max_pages_per_url=1,
            crawl_delay=1.0  # Use a longer delay for the test
        )
        
        # Verify the results
        assert len(results) == 2
        assert all(result["success"] for result in results)
        
        # Verify each result has the expected data
        for i, result in enumerate(results):
            assert urls[i] == result["url"]
            assert result["content_length"] > 0
            assert result["html_path"] is not None
            assert os.path.exists(result["html_path"])


if __name__ == "__main__":
    pytest.main() 