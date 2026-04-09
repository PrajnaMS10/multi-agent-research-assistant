from agents.retrieval_agent import retrieve_papers
from agents.summarization_agent import summarize_paper


def run_pipeline():

    query = input("Enter research topic: ")

    print("\nRetrieving papers...\n")

    papers = retrieve_papers(query)

    summaries = []

    for paper in papers:

        print("Paper:", paper["title"])
        print("Authors:", paper["authors"])
        print()

        summary = summarize_paper(paper["abstract"])

        print("Summary:")
        print(summary)
        print("--------------------------------------------------")

        summaries.append(summary)

if __name__ == "__main__":
    run_pipeline()