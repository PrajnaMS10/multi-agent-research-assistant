"""
FastAPI backend for the Research Assistant (used by the React frontend).
"""
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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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

    papers = retrieve_papers(query, max_results=body.max_papers)
    if not papers:
        raise HTTPException(status_code=404, detail="No papers found. Try a different query.")

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
