/**
 * Utility functions for cleaning and formatting markdown from LLM outputs
 */

/**
 * Remove LLM planning/reasoning text that appears before the actual report.
 * Looks for common patterns like "Here's my plan:", "I need to...", etc.
 */
export function cleanMarkdown(markdown: string): string {
  if (!markdown) return "";
  
  let cleaned = markdown;
  
  // Remove common planning phrases at the start
  const planningPatterns = [
    /^I need to .+?\.\s*\n\n/gi,
    /^Here's my plan:.*?\n\n/gi,
    /^Here's a plan:.*?\n\n/gi,
    /^Let's break down .+?\.\s*\n\n/gi,
    /^Now I will .+?\.\s*\n\n/gi,
    /^Let's .+?\.\s*\n\n/gi,
    /^Your job:.*?\n\n/gi,
    /^1\.\s*Analyze.*?\n/gi,
    /^2\.\s*Identify.*?\n/gi,
    /^3\.\s*Analyze.*?\n/gi,
    /^4\.\s*Interpret.*?\n/gi,
    /^5\.\s*Explain.*?\n/gi,
  ];
  
  for (const pattern of planningPatterns) {
    cleaned = cleaned.replace(pattern, "");
  }
  
  // Remove sections that are clearly planning (contain "plan", "strategy", etc.)
  // but keep actual content sections
  const lines = cleaned.split("\n");
  const filteredLines: string[] = [];
  let skipUntilHeader = false;
  let inPlanningSection = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineLower = line.toLowerCase();
    
    // If we hit a real header (##), stop skipping
    if (line.match(/^##\s+/)) {
      skipUntilHeader = false;
      inPlanningSection = false;
      filteredLines.push(line);
    }
    // Skip planning paragraphs
    else if (skipUntilHeader || inPlanningSection) {
      if (lineLower.includes("plan") || lineLower.includes("strategy") || 
          lineLower.includes("i will") || lineLower.includes("let's break down") ||
          lineLower.includes("synthesizing for") || lineLower.match(/^\d+\.\s*[a-z]/)) {
        continue;
      } else if (line.trim() === "" || line.match(/^[#\-\*]/)) {
        // Empty line or new section - stop skipping
        skipUntilHeader = false;
        inPlanningSection = false;
        filteredLines.push(line);
      } else {
        // Regular content after planning
        skipUntilHeader = false;
        inPlanningSection = false;
        filteredLines.push(line);
      }
    }
    // Start of planning section
    else if (lineLower.includes("here's my plan") || lineLower.includes("here's a plan") ||
             lineLower.includes("synthesis strategy") || lineLower.includes("let's break down")) {
      skipUntilHeader = true;
      inPlanningSection = true;
      continue;
    }
    else {
      filteredLines.push(line);
    }
  }
  
  cleaned = filteredLines.join("\n");
  
  // Remove multiple consecutive blank lines
  cleaned = cleaned.replace(/\n{3,}/g, "\n\n");
  
  // Remove standalone planning sentences
  cleaned = cleaned.replace(/^Price Momentum:.*?\n\n/gi, "### Price Momentum\n\n");
  cleaned = cleaned.replace(/^Volume Analysis:.*?\n\n/gi, "### Volume Analysis\n\n");
  cleaned = cleaned.replace(/^Technical Indicators:.*?\n\n/gi, "### Technical Indicators\n\n");
  
  // Trim whitespace
  cleaned = cleaned.trim();
  
  return cleaned;
}

/**
 * Extract just the formatted report section, removing any planning text
 */
export function extractFormattedReport(markdown: string): string {
  if (!markdown) return "";
  
  // Look for the first major header (##) which usually starts the actual report
  const headerMatch = markdown.match(/^(##\s+.+)$/m);
  if (headerMatch) {
    const headerIndex = markdown.indexOf(headerMatch[0]);
    return markdown.substring(headerIndex).trim();
  }
  
  // Fallback: just clean the markdown
  return cleanMarkdown(markdown);
}

/**
 * Truncate manager report to be more concise for display
 * Keeps the first few key sections and truncates the rest
 */
export function truncateManagerReport(markdown: string, maxSections: number = 4): string {
  if (!markdown) return "";
  
  const lines = markdown.split("\n");
  const sections: string[] = [];
  let currentSection: string[] = [];
  let sectionCount = 0;
  
  for (const line of lines) {
    // Check if this is a header (## or ###)
    if (line.match(/^#{2,3}\s+/)) {
      if (currentSection.length > 0) {
        sections.push(currentSection.join("\n"));
        currentSection = [];
        sectionCount++;
        
        // Stop after maxSections
        if (sectionCount >= maxSections) {
          break;
        }
      }
      currentSection.push(line);
    } else {
      currentSection.push(line);
    }
  }
  
  // Add the last section if we haven't exceeded max
  if (currentSection.length > 0 && sectionCount < maxSections) {
    sections.push(currentSection.join("\n"));
  }
  
  return sections.join("\n\n").trim();
}

