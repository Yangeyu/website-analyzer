"""
Advanced tests for crawling the OpenAI Agents SDK documentation.
These tests validate specific content and structure from the documentation.
"""
import os
import asyncio
import pytest
from pathlib import Path
import re
import json

from src.crawler import WebsiteCrawlerService


@pytest.fixture
def test_output_dir():
    """Create a test output directory."""
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    # Cleanup is not performed to keep analysis files


@pytest.fixture
def crawler(test_output_dir):
    """Create a crawler service with test output directory."""
    return WebsiteCrawlerService(output_dir=test_output_dir)


@pytest.fixture
def openai_agents_url():
    """URL for OpenAI Agents SDK docs."""
    return "https://openai.github.io/openai-agents-python/"


@pytest.fixture
def expected_patterns():
    """Expected content patterns."""
    return {
        "title": r"OpenAI\s+Agents",
        "sdk": r"SDK",  # Simplified to just look for SDK
        "agent_concepts": r"agent|assistant|function|tool",
        "api_references": r"API\s+Reference|method|function|class",
    }


@pytest.mark.slow
@pytest.mark.content
class TestOpenAIAgentsSDK:
    """Test cases specifically for the OpenAI Agents SDK documentation."""
    
    async def crawl_and_analyze(self, crawler, openai_agents_url, expected_patterns, test_output_dir):
        """Crawl the OpenAI Agents documentation and analyze the content."""
        # Crawl the OpenAI Agents SDK docs
        result = await crawler.crawl_url(openai_agents_url)
        
        if not result["success"]:
            pytest.fail(f"Failed to crawl {openai_agents_url}: {result.get('error')}")
        
        # Load the generated markdown file
        with open(result["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        
        # Save analysis results
        analysis = {}
        
        # Check for expected patterns
        for pattern_name, pattern in expected_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            match_texts = [m.group(0) for m in matches]
            
            analysis[pattern_name] = {
                "found": bool(match_texts),
                "count": len(match_texts),
                "examples": match_texts[:5]  # Limit to first 5 examples
            }
        
        # Extract all headings to analyze document structure
        headings = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)
        
        analysis["document_structure"] = {
            "heading_count": len(headings),
            "top_level_headings": [h[1] for h in headings if len(h[0]) == 1][:10],
            "has_clear_structure": len(headings) > 3  # Simple heuristic
        }
        
        # Extract code blocks with improved regex that matches more patterns
        code_blocks = re.findall(r'```(?:python|bash|json)?\n?(.*?)```', content, re.DOTALL)
        
        # Also look for inline code
        inline_code = re.findall(r'`([^`]+)`', content)
        
        analysis["code_analysis"] = {
            "code_block_count": len(code_blocks),
            "inline_code_count": len(inline_code),
            "has_code_examples": len(code_blocks) > 0 or len(inline_code) > 0,
            "inline_code_examples": inline_code[:5] if inline_code else []
        }
        
        # Save analysis to file for manual review
        analysis_path = test_output_dir / "analysis.json"
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        
        # Save the content for debugging
        content_path = test_output_dir / "content.md"
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return result, analysis
    
    @pytest.mark.asyncio
    async def test_openai_agents_content(self, crawler, openai_agents_url, expected_patterns, test_output_dir):
        """Test extraction of OpenAI Agents SDK documentation content."""
        result, analysis = await self.crawl_and_analyze(
            crawler, openai_agents_url, expected_patterns, test_output_dir)
        
        # Basic verification
        assert result["success"] is True
        assert "openai-github-io" in result["file_path"]
        
        # Content verification based on analysis
        assert analysis["title"]["found"] is True, "Expected to find title patterns in content"
        assert analysis["sdk"]["found"] is True, "Expected to find SDK in content"
        assert analysis["agent_concepts"]["found"] is True, "Expected to find agent concepts in content"
        
        # Document structure checks
        structure = analysis["document_structure"]
        assert structure["has_clear_structure"] is True, "Document should have a clear heading structure"
        
        # Code example checks - based on actual content structure
        code_analysis = analysis["code_analysis"]
        assert code_analysis["has_code_examples"] is True, "Documentation should contain code examples"
    
    @pytest.mark.asyncio
    async def test_openai_agents_relevance(self, crawler, openai_agents_url, expected_patterns, test_output_dir):
        """Test the relevance of extracted content to OpenAI Agents."""
        result, analysis = await self.crawl_and_analyze(
            crawler, openai_agents_url, expected_patterns, test_output_dir)
        
        # Check for agent-related content
        assert analysis["agent_concepts"]["found"] is True, "Content should contain agent-related concepts"
        assert analysis["agent_concepts"]["count"] > 5, "Content should have multiple mentions of agent concepts"
        
        # Check for code examples - using the code_analysis field
        assert analysis["code_analysis"]["has_code_examples"] is True, "Content should contain code examples"
        
        # For a real content check, let's examine whether there are headings
        assert analysis["document_structure"]["heading_count"] > 3, "Content should have a reasonable document structure"


if __name__ == "__main__":
    pytest.main() 