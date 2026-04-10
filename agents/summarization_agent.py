# from openai import OpenAI
# from google import genai
# import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()

def summarize_paper(abstract: str, title: str = "") -> dict:
    # client = OpenAI() 
    # genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # model = genai.GenerativeModel("gemini-2.5-flash-lite")
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

    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     max_tokens=1024,
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # response = model.generate_content(prompt)
    # raw = response.text.strip()
    # raw = (response.text or "").strip()

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
        {
            "role": "user",
            "content": prompt
            # temperature=0.2
            # max_tokens=1024
        }
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None
    )

    # for chunk in completion:
    #     print(chunk.choices[0].delta.content or "", end="")
    raw = (completion.choices[0].message.content or "").strip()


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