import arxiv
import requests


def get_citation_count(arxiv_id: str) -> int:
    """
    Fetches the citation count for an ArXiv ID from Semantic Scholar.
    """
    try:
        # Extract the ID from the full URL if necessary
        # e.g., http://arxiv.org/abs/2103.00020v1 -> 2103.00020
        clean_id = arxiv_id.split("/")[-1].split("v")[0]
        url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{clean_id}?fields=citationCount"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("citationCount", 0)
    except Exception:
        # Silently fail if API is down or ID not found
        pass
    return 0


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
            "citations": get_citation_count(result.entry_id),
        }
        papers.append(paper)

    return papers