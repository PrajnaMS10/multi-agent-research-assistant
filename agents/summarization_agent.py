from transformers import pipeline
import re

summarizer = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

def clean_text(text):
    # remove copyright and repeated boilerplate
    text = re.sub(r"All rights reserved.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)  # remove extra spaces
    return text.strip()

def summarize_paper(abstract):

    prompt = f"""
    Read the following research paper abstract and generate a detailed structured summary.

    Include the following sections:

    Research Problem:
    Explain what problem the paper addresses.

    Methodology:
    Describe the approach or model used.

    Key Contributions:
    List the main innovations or contributions.

    Results and Findings:
    Explain the outcomes or improvements reported.

    Write at least 6–8 sentences.

    Abstract:
    {abstract}
    """

    result = summarizer(
        prompt,
        max_length=400,
        min_length=150,
        truncation=True
    )

    return result[0]["generated_text"]