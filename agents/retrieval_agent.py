import arxiv

def retrieve_papers(query, max_results=3):

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    papers = []

    for result in search.results():
        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "abstract": result.summary,
            "pdf_link": result.pdf_url
        }

        papers.append(paper)

    return papers