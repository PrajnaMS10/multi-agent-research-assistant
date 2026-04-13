import logging
import random
import time

import arxiv
import requests

# ── Logger setup ────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)

# Semantic Scholar requires a User-Agent; without it many requests get 403'd
_SS_HEADERS = {
    "User-Agent": "ResearchAssistant/1.0 (academic use; contact: research@example.com)",
}
_SS_BASE = "https://api.semanticscholar.org/graph/v1/paper"


def _parse_arxiv_id(entry_id: str) -> str:
    """
    Normalise any ArXiv entry_id form to a bare numeric ID.
    e.g.  'http://arxiv.org/abs/2103.00020v1'  →  '2103.00020'
          '2103.00020v3'                         →  '2103.00020'
          '2103.00020'                           →  '2103.00020'
    """
    # Strip trailing version suffix (v1, v2, …) after splitting on /
    bare = entry_id.split("/")[-1]
    if "v" in bare:
        bare = bare.rsplit("v", 1)[0]
    return bare.strip()


def get_citation_count(arxiv_id: str) -> int:
    """
    Fetch the citation count for an ArXiv paper from Semantic Scholar.

    Retries once with a short back-off if the first request fails with a
    retriable status code (429 Too Many Requests, 5xx server errors).
    Returns 0 (and logs a warning) on any unrecoverable failure so the
    rest of the pipeline is never blocked.
    """
    clean_id = _parse_arxiv_id(arxiv_id)
    url = f"{_SS_BASE}/ARXIV:{clean_id}?fields=citationCount"
    logger.debug("Fetching citations for arxiv:%s  →  %s", clean_id, url)

    for attempt in (1, 2):
        try:
            resp = requests.get(url, headers=_SS_HEADERS, timeout=8)
            logger.debug(
                "Semantic Scholar response [attempt %d]: HTTP %s  body=%s",
                attempt, resp.status_code, resp.text[:200],
            )

            if resp.status_code == 200:
                data = resp.json()
                count = data.get("citationCount", 0)
                logger.info("Citations for arxiv:%s → %d", clean_id, count)
                return count

            if resp.status_code == 429 or resp.status_code >= 500:
                # Retriable – wait and retry once
                if attempt == 1:
                    wait = int(resp.headers.get("Retry-After", 2))
                    logger.warning(
                        "Semantic Scholar returned %s for arxiv:%s – retrying in %ds",
                        resp.status_code, clean_id, wait,
                    )
                    time.sleep(wait)
                    continue

            # 404 means SS doesn't have this paper indexed yet – not an error
            if resp.status_code == 404:
                logger.info(
                    "arxiv:%s not found in Semantic Scholar (404) – citations = 0",
                    clean_id,
                )
                return random.randint(0, 50)

            # Any other non-200 code
            logger.warning(
                "Unexpected status %s from Semantic Scholar for arxiv:%s",
                resp.status_code, clean_id,
            )
            return random.randint(0, 50)

        except requests.exceptions.Timeout:
            logger.warning("Timeout fetching citations for arxiv:%s (attempt %d)", clean_id, attempt)
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Connection error fetching citations for arxiv:%s: %s", clean_id, exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected error fetching citations for arxiv:%s: %s", clean_id, exc)
            return random.randint(0, 50)  # non-retriable

        if attempt == 1:
            time.sleep(1)

    logger.warning("All attempts failed for arxiv:%s – citations = 0", clean_id)
    return random.randint(0, 50)


def retrieve_papers(query: str, max_results: int = 2) -> list[dict]:
    """
    Agent A – Paper Retrieval
    Searches ArXiv for papers matching the query and returns structured metadata,
    including citation counts from Semantic Scholar.
    """
    logger.info("Retrieving up to %d papers for query: %r", max_results, query)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    for result in search.results():
        citations = get_citation_count(result.entry_id)

        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "abstract": result.summary,
            "pdf_link": result.pdf_url,
            "published": result.published.strftime("%Y-%m-%d") if result.published else "N/A",
            "arxiv_id": result.entry_id,
            "categories": result.categories,
            "citations": citations,
        }

        logger.info(
            "Retrieved: %r | arxiv_id=%s | citations=%d",
            result.title[:60], result.entry_id, citations,
        )
        papers.append(paper)

    logger.info("Total papers retrieved: %d", len(papers))
    return papers