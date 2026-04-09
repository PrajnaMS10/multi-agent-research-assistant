import json
# from openai import OpenAI
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

def generate_related_work(query: str, papers: list[dict]) -> dict:
    """
    Agent C – Related Work Generator
    Synthesizes summaries of retrieved papers into a structured literature review
    with thematic groupings, research gaps, and future directions.
    """
    # client = OpenAI()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

    # Build a structured representation of the papers for the prompt
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

Write a comprehensive Related Work section in the following JSON format (respond with ONLY valid JSON):
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

    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     max_tokens=2048,
    #     messages=[{"role": "user", "content": prompt}]
    # )

    # raw = response.choices[0].message.content.strip()
    response = model.generate_content(prompt)
    raw = (response.text or "").strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError:
        result = {
            "overview": raw[:500],
            "themes": [],
            "evolution": "",
            "consensus": "",
            "debates": "",
            "gaps": [],
            "future_directions": [],
            "literature_review_paragraph": raw,
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
        lines.append(f"### {theme['name']}")
        lines.append(f"{theme['description']}\n")
        lines.append(f"**Papers:** {', '.join(theme['papers'])}")
        lines.append(f"\n{theme['synthesis']}\n")

    if related_work.get("evolution"):
        lines.append("\n## Evolution of the Field\n")
        lines.append(related_work["evolution"] + "\n")

    if related_work.get("consensus"):
        lines.append("\n## Points of Consensus\n")
        lines.append(related_work["consensus"] + "\n")

    if related_work.get("debates"):
        lines.append("\n## Open Debates\n")
        lines.append(related_work["debates"] + "\n")

    if related_work.get("gaps"):
        lines.append("\n## Research Gaps\n")
        for gap in related_work["gaps"]:
            lines.append(f"- {gap}")
        lines.append("")

    if related_work.get("future_directions"):
        lines.append("\n## Future Directions\n")
        for direction in related_work["future_directions"]:
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