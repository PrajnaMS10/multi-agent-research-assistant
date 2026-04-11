import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(_root.parent / ".env")

# Agent C — related work via Qwen on Groq
RELATED_WORK_MODEL = os.getenv(
    "GROQ_MODEL_RELATED_WORK",
    "qwen/qwen3-32b",
)


def generate_related_work(query: str, papers: list[dict]) -> dict:
    """
    Agent C – Related Work Generator
    Synthesizes summaries of retrieved papers into a structured literature review
    with thematic groupings, research gaps, and future directions.
    """
    papers_text = ""
    for i, paper in enumerate(papers, 1):
        summary = paper.get("summary", {})
        papers_text += f"""
Paper {i}: {paper['title']}
Authors: {', '.join(paper['authors'][:3])}{'et al.' if len(paper['authors']) > 3 else ''}
Published: {paper.get('published', 'N/A')}
One-liner: {summary.get('one_liner', paper['abstract'][:150])}
Problem: {summary.get('problem', '')}
Methodology: {summary.get('methodology', '')}
Key Findings: {'; '.join(summary.get('key_findings', []))}
Novelty: {summary.get('novelty', '')}
---"""

    prompt = f"""You are an expert academic researcher writing a literature review section.

Research Topic: "{query}"

Here are {len(papers)} retrieved papers with their summaries:
{papers_text}

Write a comprehensive Related Work section in the following JSON format.
CRITICAL: Respond with ONLY valid JSON. Do NOT include any introductory text, any conversational commentary, and absolutely NO internal thinking/reasoning blocks (e.g., no <thought> tags). Your entire response must be a single JSON object.

JSON Format:
{{
  "overview": "2-3 sentence high-level overview of the research landscape for this topic",
  "themes": [
    {{
      "name": "Theme name",
      "description": "What this cluster of work focuses on",
      "papers": ["Paper title 1", "Paper title 2"],
      "synthesis": "2-3 sentences synthesizing what these papers collectively show"
    }}
  ],
  "evolution": "How has this research area evolved based on publication dates and methodologies?",
  "consensus": "What do most/all papers agree on?",
  "debates": "Any contradictions, competing approaches, or open debates across papers?",
  "gaps": ["research gap 1", "research gap 2", "research gap 3"],
  "future_directions": ["direction 1", "direction 2", "direction 3"],
  "literature_review_paragraph": "A single cohesive academic paragraph (200-300 words) suitable for inclusion in a paper, written in third person, past tense, with in-text citations like [1], [2], etc. referencing the paper numbers above."
}}"""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to .env in this folder or the parent project folder."
        )

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=RELATED_WORK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # Lower temperature for more consistent JSON
        max_tokens=4096,
        top_p=1,
        stream=False,
    )

    msg = completion.choices[0].message
    raw = (getattr(msg, "content", None) or "").strip()

    # Post-process to remove potential reasoning blocks or thought tags
    import re
    # Remove <thought>...</thought> tags and content
    raw = re.sub(r'<thought>.*?</thought>', '', raw, flags=re.DOTALL).strip()
    # Remove thinking: ... sections if they appear
    raw = re.sub(r'^thinking:.*?\n', '', raw, flags=re.IGNORECASE | re.MULTILINE).strip()

    try:
        # Try to find the first '{' and last '}' to extract the JSON object
        start_idx = raw.find('{')
        end_idx = raw.rfind('}')
        if start_idx != -1 and end_idx != -1:
            raw = raw[start_idx:end_idx + 1]
        
        result = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        result = {
            "overview": raw[:500] if raw else "Error parsing response.",
            "themes": [],
            "evolution": "",
            "consensus": "",
            "debates": "",
            "gaps": [],
            "future_directions": [],
            "literature_review_paragraph": raw if raw else "Error parsing response.",
        }

    return result


def format_literature_review(query: str, papers: list[dict], related_work: dict) -> str:
    """
    Formats the full literature review as a readable markdown document.
    """
    lines = []
    lines.append(f"# Literature Review: {query}\n")
    lines.append(f"*Generated from {len(papers)} papers retrieved from ArXiv*\n")
    lines.append("---\n")

    lines.append("## Overview\n")
    lines.append(related_work.get("overview", "") + "\n")

    lines.append("\n## Research Themes\n")
    for theme in related_work.get("themes", []):
        if not isinstance(theme, dict):
            continue
        name = theme.get("name", "Theme")
        desc = theme.get("description", "")
        synth = theme.get("synthesis", "")
        papers_field = theme.get("papers", [])
        if isinstance(papers_field, str):
            papers_field = [papers_field]
        elif not isinstance(papers_field, list):
            papers_field = [str(papers_field)] if papers_field else []
        papers_line = ", ".join(str(p) for p in papers_field)
        lines.append(f"### {name}")
        lines.append(f"{desc}\n")
        lines.append(f"**Papers:** {papers_line}")
        lines.append(f"\n{synth}\n")

    if related_work.get("evolution"):
        lines.append("\n## Evolution of the Field\n")
        lines.append(related_work["evolution"] + "\n")

    if related_work.get("consensus"):
        lines.append("\n## Points of Consensus\n")
        lines.append(related_work["consensus"] + "\n")

    if related_work.get("debates"):
        lines.append("\n## Open Debates\n")
        lines.append(related_work["debates"] + "\n")

    gaps = related_work.get("gaps") or []
    if isinstance(gaps, str):
        gaps = [gaps]
    if gaps:
        lines.append("\n## Research Gaps\n")
        for gap in gaps:
            lines.append(f"- {gap}")
        lines.append("")

    directions = related_work.get("future_directions") or []
    if isinstance(directions, str):
        directions = [directions]
    if directions:
        lines.append("\n## Future Directions\n")
        for direction in directions:
            lines.append(f"- {direction}")
        lines.append("")

    lines.append("\n## Literature Review Paragraph\n")
    lines.append(related_work.get("literature_review_paragraph", "") + "\n")

    lines.append("\n---\n## References\n")
    for i, paper in enumerate(papers, 1):
        authors = paper["authors"]
        author_str = (
            f"{authors[0]} et al." if len(authors) > 1 else authors[0]
        ) if authors else "Unknown"
        lines.append(
            f"[{i}] {author_str}. *{paper['title']}*. {paper.get('published', 'N/A')}. "
            f"[ArXiv]({paper.get('pdf_link', '')})"
        )

    return "\n".join(lines)
