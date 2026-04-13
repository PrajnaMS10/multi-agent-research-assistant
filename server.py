"""
FastAPI backend for the Research Assistant (used by the React frontend).
"""
from pathlib import Path

from dotenv import load_dotenv

# Load .env from app folder and parent workspace (common OneDrive layout)
_base = Path(__file__).resolve().parent
load_dotenv(_base / ".env")
load_dotenv(_base.parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from agents.retrieval_agent import retrieve_papers
from agents.summarization_agent import summarize_paper
from agents.related_work_agent import generate_related_work, format_literature_review

app = FastAPI(title="Research Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
"*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PipelineRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_papers: int = Field(default=5, ge=2, le=10)

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/pipeline")
def run_pipeline(body: PipelineRequest):
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        papers = retrieve_papers(query, max_results=body.max_papers)
        if not papers:
            raise HTTPException(
                status_code=404, detail="No papers found. Try a different query."
            )

        enriched_papers = []
        for paper in papers:
            summary = summarize_paper(paper["abstract"], paper["title"])
            enriched_papers.append({**paper, "summary": summary})

        related_work = generate_related_work(query, enriched_papers)
        review_md = format_literature_review(query, enriched_papers, related_work)

        return {
            "query": query,
            "papers": papers,
            "enriched_papers": enriched_papers,
            "related_work": related_work,
            "review_md": review_md,
        }
    except HTTPException:
        raise
    except Exception as e:
        # Surface provider / config errors instead of a bare 500
        msg = str(e).strip() or repr(e)
        raise HTTPException(
            status_code=502,
            detail=f"Pipeline failed: {msg}",
        ) from e
