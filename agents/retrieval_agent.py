import arxiv


def retrieve_papers(query: str, max_results: int = 2) -> list[dict]:
    """
    Agent A – Paper Retrieval
    Searches ArXiv for papers matching the query and returns structured metadata.
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    for result in search.results():
        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "abstract": result.summary,
            "pdf_link": result.pdf_url,
            "published": result.published.strftime("%Y-%m-%d") if result.published else "N/A",
            "arxiv_id": result.entry_id,
            "categories": result.categories,
        }
        papers.append(paper)

    return papers