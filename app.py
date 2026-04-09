import streamlit as st
import time
from agents.retrieval_agent import retrieve_papers
from agents.summarization_agent import summarize_paper
from agents.related_work_agent import generate_related_work, format_literature_review
from dotenv import load_dotenv
load_dotenv()

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
  }

  /* Dark scholarly theme */
  .stApp {
    background-color: #0f1117;
    color: #e8e4d9;
  }

  h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: #e8e4d9 !important;
  }

  .main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem;
    color: #e8e4d9;
    letter-spacing: -0.02em;
    line-height: 1.1;
  }

  .subtitle {
    font-family: 'DM Sans', sans-serif;
    font-weight: 300;
    color: #8a8578;
    font-size: 1.05rem;
    margin-top: 0.5rem;
  }

  .agent-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    padding: 2px 10px;
    border-radius: 20px;
    margin-bottom: 8px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .badge-a { background: #1a2a1a; color: #5dbb5d; border: 1px solid #2d4a2d; }
  .badge-b { background: #1a1a2a; color: #6b8cff; border: 1px solid #2d2d4a; }
  .badge-c { background: #2a1a1a; color: #ff8c6b; border: 1px solid #4a2d2d; }

  .paper-card {
    background: #161820;
    border: 1px solid #252830;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
  }

  .paper-card:hover {
    border-color: #3a3d50;
  }

  .paper-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.1rem;
    color: #e8e4d9;
    margin-bottom: 4px;
  }

  .paper-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #5a5850;
    margin-bottom: 12px;
  }

  .one-liner {
    font-size: 0.9rem;
    color: #a8a49a;
    font-style: italic;
    border-left: 3px solid #2d4a2d;
    padding-left: 12px;
    margin: 10px 0;
  }

  .finding-chip {
    display: inline-block;
    background: #1a1f2e;
    border: 1px solid #252b3d;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.78rem;
    color: #7a8fc0;
    margin: 3px 3px 3px 0;
  }

  .review-box {
    background: #12141a;
    border: 1px solid #252830;
    border-radius: 12px;
    padding: 28px 32px;
    font-size: 0.95rem;
    line-height: 1.75;
    color: #c8c4ba;
  }

  .gap-item {
    background: #1a1510;
    border-left: 3px solid #c07a3a;
    padding: 8px 14px;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    font-size: 0.88rem;
    color: #c8a07a;
  }

  .direction-item {
    background: #101a1a;
    border-left: 3px solid #3a9090;
    padding: 8px 14px;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    font-size: 0.88rem;
    color: #7ac8c8;
  }

  .stButton > button {
    background: #e8e4d9;
    color: #0f1117;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    width: 100%;
    transition: all 0.2s;
  }

  .stButton > button:hover {
    background: #d4cfc0;
    transform: translateY(-1px);
  }

  .stSelectbox label, .stSlider label, .stTextInput label {
    color: #8a8578 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
  }

  div[data-testid="stSidebar"] {
    background-color: #0c0e14 !important;
    border-right: 1px solid #1a1d25 !important;
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 0 8px;
    border-bottom: 1px solid #1e2028;
    margin-bottom: 20px;
  }

  .step-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #4a4d5a;
    font-weight: 500;
  }

  .lit-review-paragraph {
    background: #0c1020;
    border: 1px solid #1e2535;
    border-radius: 8px;
    padding: 24px;
    font-size: 0.93rem;
    line-height: 1.8;
    color: #b8c8e8;
    font-style: italic;
  }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Pipeline Settings")
    max_papers = st.slider("Papers to retrieve", min_value=2, max_value=10, value=2)
    st.markdown("---")
    st.markdown("### 🤖 Agents")
    st.markdown("""
    <div style='font-size:0.82rem; color:#5a5850; line-height:1.8;'>
    <b style='color:#5dbb5d;'>Agent A</b> — ArXiv Retrieval<br>
    <b style='color:#6b8cff;'>Agent B</b> — Paper Summarization<br>
    <b style='color:#ff8c6b;'>Agent C</b> — Related Work Generator
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; color:#3a3830;'>
    Powered by Claude Sonnet<br>& ArXiv Open API
    </div>
    """, unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 2rem 0 1.5rem;'>
  <div class='main-title'>Research Assistant</div>
  <div class='subtitle'>Multi-agent pipeline · Retrieval → Summarization → Synthesis</div>
</div>
""", unsafe_allow_html=True)

query = st.text_input(
    "Research topic",
    placeholder="e.g. 'diffusion models for image generation'",
    label_visibility="collapsed",
)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    run_btn = st.button("🔬 Run Pipeline", use_container_width=True)

st.markdown("---")

# ── Pipeline Execution ─────────────────────────────────────────
if run_btn and query.strip():

    # ── Agent A ────────────────────────────────────────────────
    st.markdown("""
    <div class='step-header'>
      <span class='agent-badge badge-a'>Agent A</span>
      <span style='font-family:DM Serif Display,serif;font-size:1.3rem;'>Paper Retrieval</span>
      <span class='step-number'>01 / 03</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Searching ArXiv..."):
        papers = retrieve_papers(query, max_results=max_papers)

    if not papers:
        st.error("No papers found. Try a different query.")
        st.stop()

    st.success(f"Retrieved **{len(papers)}** papers")

    for p in papers:
        st.markdown(f"""
        <div class='paper-card'>
          <div class='paper-title'>{p['title']}</div>
          <div class='paper-meta'>{' · '.join(p['authors'][:3])}{'...' if len(p['authors']) > 3 else ''} &nbsp;|&nbsp; {p.get('published','')} &nbsp;|&nbsp; <a href='{p.get("pdf_link","")}' style='color:#3a6aaa;'>PDF ↗</a></div>
          <div style='font-size:0.85rem;color:#6a6860;'>{p['abstract'][:200]}…</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Agent B ────────────────────────────────────────────────
    st.markdown("""
    <div class='step-header'>
      <span class='agent-badge badge-b'>Agent B</span>
      <span style='font-family:DM Serif Display,serif;font-size:1.3rem;'>Paper Summarization</span>
      <span class='step-number'>02 / 03</span>
    </div>
    """, unsafe_allow_html=True)

    enriched_papers = []
    progress = st.progress(0, text="Summarizing papers...")

    for i, paper in enumerate(papers):
        with st.spinner(f"Summarizing: {paper['title'][:60]}..."):
            summary = summarize_paper(paper["abstract"], paper["title"])
            enriched = {**paper, "summary": summary}
            enriched_papers.append(enriched)

        findings_html = "".join(
            f"<span class='finding-chip'>{f}</span>"
            for f in summary.get("key_findings", [])[:3]
        )

        st.markdown(f"""
        <div class='paper-card'>
          <div class='paper-title'>{paper['title']}</div>
          <div class='one-liner'>{summary.get('one_liner','')}</div>
          <div style='font-size:0.82rem;color:#7a7870;margin:8px 0 4px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;'>Key Findings</div>
          <div>{findings_html}</div>
          {"<div style='margin-top:10px;font-size:0.82rem;color:#6a6860;'><b style='color:#5a5850;'>Novelty:</b> " + summary.get('novelty','') + "</div>" if summary.get('novelty') else ""}
        </div>
        """, unsafe_allow_html=True)

        progress.progress((i + 1) / len(papers), text=f"Summarized {i+1}/{len(papers)} papers")
        time.sleep(0.1)

    progress.empty()

    # ── Agent C ────────────────────────────────────────────────
    st.markdown("""
    <div class='step-header'>
      <span class='agent-badge badge-c'>Agent C</span>
      <span style='font-family:DM Serif Display,serif;font-size:1.3rem;'>Related Work Generator</span>
      <span class='step-number'>03 / 03</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Synthesizing literature review..."):
        related_work = generate_related_work(query, enriched_papers)
        review_md = format_literature_review(query, enriched_papers, related_work)

    # Overview
    st.markdown(f"""
    <div class='review-box'>
      <div style='font-size:0.75rem;color:#5a5850;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;font-family:JetBrains Mono,monospace;'>Overview</div>
      {related_work.get('overview','')}
    </div>
    """, unsafe_allow_html=True)

    # Themes
    if related_work.get("themes"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Research Themes")
        cols = st.columns(min(len(related_work["themes"]), 2))
        for i, theme in enumerate(related_work["themes"]):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='paper-card'>
                  <div style='font-family:DM Serif Display,serif;font-size:1rem;color:#e8e4d9;margin-bottom:6px;'>{theme['name']}</div>
                  <div style='font-size:0.82rem;color:#6a6860;margin-bottom:8px;'>{theme['description']}</div>
                  <div style='font-size:0.8rem;color:#3a6aaa;margin-bottom:8px;'>{'  ·  '.join(theme.get('papers',[]))}</div>
                  <div style='font-size:0.85rem;color:#9a9890;'>{theme.get('synthesis','')}</div>
                </div>
                """, unsafe_allow_html=True)

    # Gaps & Directions side-by-side
    g_col, d_col = st.columns(2)
    with g_col:
        st.markdown("#### Research Gaps")
        for gap in related_work.get("gaps", []):
            st.markdown(f"<div class='gap-item'>⚠ {gap}</div>", unsafe_allow_html=True)

    with d_col:
        st.markdown("#### Future Directions")
        for direction in related_work.get("future_directions", []):
            st.markdown(f"<div class='direction-item'>→ {direction}</div>", unsafe_allow_html=True)

    # Literature Review Paragraph
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📝 Literature Review Paragraph")
    st.markdown(f"""
    <div class='lit-review-paragraph'>
      {related_work.get('literature_review_paragraph','')}
    </div>
    """, unsafe_allow_html=True)

    # Download
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
      label="⬇ Download Full Review (.md)",
      data=review_md,
      file_name=f"literature_review_{'_'.join(query.split()[:4])}.md",
      mime="text/markdown",
    )

elif run_btn and not query.strip():
    st.warning("Please enter a research topic.")

else:
    st.markdown("""
    <div style='text-align:center;padding:4rem 0;color:#3a3830;'>
      <div style='font-size:3rem;margin-bottom:1rem;'>🔬</div>
      <div style='font-family:DM Serif Display,serif;font-size:1.4rem;color:#4a4840;'>Enter a topic to begin</div>
      <div style='font-size:0.85rem;margin-top:0.5rem;'>The pipeline will retrieve, summarize, and synthesize papers from ArXiv</div>
    </div>
    """, unsafe_allow_html=True)