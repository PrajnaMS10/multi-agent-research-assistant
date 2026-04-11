import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(_root.parent / ".env")

# Agent B — summarization via Meta Llama on Groq
SUMMARIZATION_MODEL = os.getenv(
    "GROQ_MODEL_SUMMARIZATION",
    "llama-3.3-70b-versatile",
)


def summarize_paper(abstract: str, title: str = "") -> dict:
    title_context = f'Title: "{title}"\n\n' if title else ""

    prompt = f"""You are a research paper summarization expert.
{title_context}Abstract:
{abstract}

Provide a structured summary in the following JSON format (respond with ONLY valid JSON, no markdown):
{{
  "one_liner": "...",
  "problem": "...",
  "methodology": "...",
  "key_findings": ["...", "..."],
  "novelty": "...",
  "limitations": "..."
}}"""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to .env in this folder or the parent project folder."
        )

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=SUMMARIZATION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        max_tokens=2048,
        top_p=1,
        stream=False,
    )

    msg = completion.choices[0].message
    raw = (getattr(msg, "content", None) or "").strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        summary = json.loads(raw.strip())
    except json.JSONDecodeError:
        summary = {
            "one_liner": raw[:200],
            "problem": "See raw summary",
            "methodology": raw,
            "key_findings": [],
            "novelty": "",
            "limitations": "",
        }

    return summary


def summarize_papers(papers: list[dict]) -> list[dict]:
    """Summarize a list of papers and return them enriched with summaries."""
    enriched = []
    for paper in papers:
        summary = summarize_paper(paper["abstract"], paper.get("title", ""))
        enriched.append({**paper, "summary": summary})
    return enriched
