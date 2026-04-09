from openai import OpenAI

def summarize_paper(abstract: str, title: str = "") -> dict:
    client = OpenAI()  # reads OPENAI_API_KEY from env automatically

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

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON response
    import json
    try:
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        summary = json.loads(raw.strip())
    except json.JSONDecodeError:
        # Fallback: return raw text in a structured dict
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
    """
    Summarize a list of papers and return them enriched with summaries.
    """
    enriched = []
    for paper in papers:
        summary = summarize_paper(paper["abstract"], paper.get("title", ""))
        enriched.append({**paper, "summary": summary})
    return enriched