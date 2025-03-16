"""
Unit tests for the website crawler service.
Tests crawling functionality with the OpenAI Agents SDK documentation page.
"""
import os
import asyncio
import unittest
from pathlib import Path
import re
import pytest

from src.crawler import WebsiteCrawlerService, crawl_single_url


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


if __name__ == "__main__":
    pytest.main() 