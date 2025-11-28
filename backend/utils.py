"""Utility functions for parsing markdown results."""
import re
from typing import Dict, Tuple, Optional


def split_manager_and_analysts(markdown_text: str) -> Tuple[str, Optional[str]]:
    """Split markdown into manager report and analyst reports."""
    if not markdown_text:
        return "", None
    
    text = markdown_text.strip()
    marker = "# 📊 Individual Analyst Reports"
    
    if marker in text:
        head, tail = text.split(marker, 1)
        analyst_block = f"{marker}{tail}".strip()
        return head.strip(), analyst_block
    
    # Fallback: look for first analyst-style heading
    analyst_markers = [
        "## 1️⃣ Fundamental Analyst Report",
        "## Fundamental Analyst Report",
        "## Fundamental Analyst",
        "## 2️⃣ Technical Analyst Report",
        "## Technical Analyst Report",
        "## Technical Analyst",
        "## 3️⃣ News & Sentiment Analyst Report",
        "## News & Sentiment Analyst Report",
        "## News & Sentiment Analyst",
    ]
    
    first_idx = len(text)
    found = False
    for m in analyst_markers:
        pos = text.find(m)
        if pos != -1:
            first_idx = min(first_idx, pos)
            found = True
    
    if found:
        manager_md = text[:first_idx].strip()
        analysts_md = text[first_idx:].strip()
        return manager_md, analysts_md
    
    return text, None


def parse_analyst_reports(analysts_markdown: str) -> Dict[str, str]:
    """Parse the analyst reports section into individual reports."""
    if not analysts_markdown:
        return {
            "fundamental": "",
            "technical": "",
            "news": "",
        }
    
    reports = {
        "fundamental": "",
        "technical": "",
        "news": "",
    }
    
    # Debug: show what we're looking for
    if "News" in analysts_markdown:
        news_section_start = analysts_markdown.find("News")
        if news_section_start != -1:
            preview = analysts_markdown[news_section_start:news_section_start+200]
            print(f"[DEBUG] News section preview: {preview}")
    
    patterns = {
        "fundamental": [
            r"##\s*1️⃣\s*Fundamental Analyst Report\s*\n(.*?)(?=---|##\s*[23]|$)",
            r"##\s*1\s*Fundamental Analyst Report\s*\n(.*?)(?=---|##\s*[23]|$)",
            r"##\s*Fundamental Analyst Report\s*\n(.*?)(?=---|##\s*[23]|$)",
            r"##\s*Fundamental Analyst\s*\n(.*?)(?=---|##\s*[23]|$)",
        ],
        "technical": [
            r"##\s*2️⃣\s*Technical Analyst Report\s*\n(.*?)(?=---|##\s*[13]|$)",
            r"##\s*2\s*Technical Analyst Report\s*\n(.*?)(?=---|##\s*[13]|$)",
            r"##\s*Technical Analyst Report\s*\n(.*?)(?=---|##\s*[13]|$)",
            r"##\s*Technical Analyst\s*\n(.*?)(?=---|##\s*[13]|$)",
        ],
        "news": [
            # Match content after "## 3️⃣ News & Sentiment Analyst Report" heading
            # The content starts with "## News Analysis" so we need to capture everything after the heading
            r"##\s*3️⃣\s*News\s*&\s*Sentiment\s*Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*3\s*News\s*&\s*Sentiment\s*Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*3️⃣\s*News.*?Sentiment.*?Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*3\s*News.*?Sentiment.*?Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*News\s*&\s*Sentiment\s*Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*News.*?Sentiment.*?Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*News.*?Analyst\s*Report\s*\n+(.*?)(?=---|##\s*[12]|$)",
            r"##\s*News.*?Analyst\s*\n+(.*?)(?=---|##\s*[12]|$)",
        ],
    }
    
    for report_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, analysts_markdown, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Remove any trailing separators
                content = re.sub(r'\n*---\s*$', '', content)
                # Remove leading/trailing whitespace and newlines
                content = content.strip()
                if content and content != "_No output_":
                    reports[report_type] = content
                    break
    
    # Debug: if news is still empty, try a more lenient pattern
    if not reports["news"]:
        # Try to find anything after "News" heading - capture everything until end or next section
        news_match = re.search(
            r"##\s*3[️⃣\s]*News[^\n]*\n+(.*?)(?=---|##\s*[12]|$)",
            analysts_markdown,
            re.DOTALL | re.IGNORECASE
        )
        if news_match:
            content = news_match.group(1).strip()
            content = re.sub(r'\n*---\s*$', '', content)
            # Remove leading newlines but keep the content structure
            content = content.lstrip('\n').strip()
            if content and content != "_No output_":
                reports["news"] = content
                print(f"[DEBUG] Fallback pattern matched news: {len(content)} chars")
        
        # If still empty, try to find "## News Analysis" directly (it's the actual report content)
        if not reports["news"]:
            news_analysis_match = re.search(
                r"##\s*News\s*Analysis\s*\n(.*?)(?=---|##|$)",
                analysts_markdown,
                re.DOTALL | re.IGNORECASE
            )
            if news_analysis_match:
                content = news_analysis_match.group(1).strip()
                content = re.sub(r'\n*---\s*$', '', content)
                if content and content != "_No output_":
                    reports["news"] = content
                    print(f"[DEBUG] News Analysis pattern matched: {len(content)} chars")
    
    return reports


def extract_final_rating(markdown_text: str) -> Optional[str]:
    """Extract the final rating from recommender output."""
    if not markdown_text:
        return None
    
    patterns = [
        r"Model Rating[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"Final Rating[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"\*\*Model Rating\*\*[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
        r"\*\*Final Rating\*\*[:\s]+(StrongBuy|Buy|Hold|UnderPerform|Sell)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, markdown_text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

