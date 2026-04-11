import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";

function StepHeader({ badge, badgeClass, title, step }) {
  return (
    <div className="step-header">
      <span className={`agent-badge ${badgeClass}`}>{badge}</span>
      <span className="step-title">{title}</span>
      <span className="step-number">{step}</span>
    </div>
  );
}

function PaperMeta({ paper }) {
  const authors = paper.authors || [];
  const head = authors.slice(0, 3).join(" · ");
  const more = authors.length > 3 ? "…" : "";
  return (
    <div className="paper-meta">
      <span className="paper-meta-text">
        {head}
        {more}
      </span>
      <span className="paper-meta-sep" aria-hidden>
        ·
      </span>
      <span>{paper.published || "—"}</span>
      {paper.pdf_link ? (
        <>
          <span className="paper-meta-sep" aria-hidden>
            ·
          </span>
          <a href={paper.pdf_link} target="_blank" rel="noopener noreferrer">
            Open PDF
          </a>
        </>
      ) : null}
      {paper.citations !== undefined && (
        <>
          <span className="paper-meta-sep" aria-hidden>
            ·
          </span>
          <span className="citation-count">
            <svg
              className="citation-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ width: "12px", height: "12px", marginRight: "4px" }}
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            {paper.citations} {paper.citations === 1 ? "citation" : "citations"}
          </span>
        </>
      )}
    </div>
  );
}

function PipelineProgress() {
  const steps = [
    { id: "a", label: "Retrieve", short: "ArXiv" },
    { id: "b", label: "Summarize", short: "LLM" },
    { id: "c", label: "Synthesize", short: "Review" },
  ];
  return (
    <div className="pipeline-progress">
      <p className="pipeline-progress-title">Pipeline</p>
      <ol className="pipeline-steps">
        {steps.map((s) => (
          <li key={s.id} className="pipeline-step">
            <span className="pipeline-step-dot" />
            <span className="pipeline-step-label">{s.label}</span>
            <span className="pipeline-step-short">{s.short}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ── Copy button with transient feedback ────────────────────────
function CopyButton({ getText, label = "Copy", className = "copy-btn" }) {
  const [state, setState] = useState("idle"); // idle | copied | error

  const handleCopy = async () => {
    try {
      const text = typeof getText === "function" ? getText() : getText;
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("error");
    } finally {
      setTimeout(() => setState("idle"), 2000);
    }
  };

  return (
    <button type="button" className={className} onClick={handleCopy}>
      {state === "copied" ? "✓ Copied!" : state === "error" ? "✗ Failed" : label}
    </button>
  );
}

// ── Related Work Table ─────────────────────────────────────────
function RelatedWorkTable({ rows }) {
  if (!rows || rows.length === 0) return null;

  const buildTsv = () => {
    const header = "Paper Info\tObjective\tMethodology\tKey Results\tLimitations";
    const body = rows
      .map(
        (r) =>
          `${r.name || ""} (${r.year || ""}) — ${r.authors || ""}\t${r.objective || ""}\t${r.methodology || ""}\t${r.key_results || ""}\t${r.limitations || ""}`
      )
      .join("\n");
    return `${header}\n${body}`;
  };

  return (
    <section className="table-section" aria-labelledby="rw-table-heading">
      <div className="section-title-row">
        <h3 id="rw-table-heading" className="section-title">
          Literature Review
        </h3>
        <CopyButton getText={buildTsv} label="Copy table" className="copy-btn" />
      </div>
      <div className="table-scroll">
        <table className="rw-table">
          <thead>
            <tr>
              <th>Paper Info</th>
              <th>Objective</th>
              <th>Methodology</th>
              <th>Key Results</th>
              <th>Limitations</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td className="rw-table-paper-info">
                  <span className="rw-table-paper-name">{r.name}</span>
                  <span className="rw-table-paper-meta">
                    {r.year} {r.authors ? `· ${r.authors}` : ""}
                  </span>
                </td>
                <td>{r.objective}</td>
                <td>{r.methodology}</td>
                <td>{r.key_results}</td>
                <td>{r.limitations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function App() {
  const [theme, setTheme] = useState(() =>
    typeof window !== "undefined" && localStorage.getItem("theme") === "light"
      ? "light"
      : "dark"
  );
  const [maxPapers, setMaxPapers] = useState(5);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [warn, setWarn] = useState("");
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState("a");
  const resultsRef = useRef(null);

  useEffect(() => {
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  useEffect(() => {
    if (result && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  const runPipeline = useCallback(async () => {
    setWarn("");
    setErr("");
    setResult(null);
    const q = query.trim();
    if (!q) {
      setWarn("Enter a topic above, then run the pipeline.");
      return;
    }
    setLoading(true);
    setActiveTab("a");
    try {
      const res = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, max_papers: maxPapers }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.detail || res.statusText || "Request failed";
        setErr(typeof msg === "string" ? msg : JSON.stringify(msg));
        return;
      }
      setResult(data);
    } catch (e) {
      setErr(
        e.message ||
          "Could not reach the API. Start the backend with `python main.py` (port 8000)."
      );
    } finally {
      setLoading(false);
    }
  }, [query, maxPapers]);

  const clearResults = useCallback(() => {
    setResult(null);
    setWarn("");
    setErr("");
  }, []);

  // ── PDF download (client-side via print) ──────────────────────
  const downloadPdf = useCallback(() => {
    if (!result?.related_work) return;
    const rw = result.related_work;
    const q = result.query || query;

    const tableRows = (rw.papers_table || [])
      .map(
        (r) => `
        <tr>
          <td><strong>${r.name || ""}</strong><br/><small>${r.year || ""} · ${r.authors || ""}</small></td>
          <td>${r.objective || ""}</td>
          <td>${r.methodology || ""}</td>
          <td>${r.key_results || ""}</td>
          <td>${r.limitations || ""}</td>
        </tr>`
      )
      .join("");

    const tableHtml =
      rw.papers_table?.length > 0
        ? `
        <h2>Related Work Table</h2>
        <table>
          <thead>
            <tr>
              <th>Paper Info</th><th>Objective</th><th>Methodology</th><th>Key Results</th><th>Limitations</th>
            </tr>
          </thead>
          <tbody>${tableRows}</tbody>
        </table>`
        : "";

    const gapsHtml = (rw.gaps || []).map((g) => `<li>${g}</li>`).join("");
    const dirsHtml = (rw.future_directions || [])
      .map((d) => `<li>${d}</li>`)
      .join("");

    const themesHtml = (rw.themes || [])
      .map(
        (t) => `
      <div class="theme">
        <h4>${t.name || ""}</h4>
        <p>${t.description || ""}</p>
        <p><em>${(t.papers || []).join(", ")}</em></p>
        <p>${t.synthesis || ""}</p>
      </div>`
      )
      .join("");

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Research Review — ${q}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Georgia, serif; font-size: 11pt; color: #111; padding: 2cm; line-height: 1.6; }
    h1 { font-size: 18pt; margin-bottom: 4pt; }
    h2 { font-size: 13pt; margin: 22pt 0 6pt; border-bottom: 1px solid #ccc; padding-bottom: 3pt; color: #222; }
    h3, h4 { font-size: 11pt; margin: 12pt 0 4pt; }
    p { margin-bottom: 8pt; }
    .meta { font-size: 9pt; color: #555; margin-bottom: 16pt; }
    table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 10pt 0; page-break-inside: auto; }
    th { background: #2a2a3a; color: #fff; padding: 6pt 8pt; text-align: left; }
    td { padding: 5pt 8pt; border: 1px solid #ccc; vertical-align: top; }
    tr:nth-child(even) td { background: #f7f7fa; }
    ul, ol { margin: 6pt 0 10pt 18pt; }
    li { margin-bottom: 4pt; }
    .rw-para { font-style: italic; background: #f5f5f0; border-left: 3px solid #888; padding: 10pt 14pt; margin: 8pt 0; }
    .theme { margin-bottom: 10pt; padding-left: 10pt; border-left: 2px solid #ddd; }
    @media print { body { padding: 1.5cm; } }
  </style>
</head>
<body>
  <h1>Research Review</h1>
  <p class="meta">Topic: <strong>${q}</strong> · Generated ${new Date().toLocaleDateString()}</p>

  <h2>Overview</h2>
  <p>${rw.overview || ""}</p>

  ${themesHtml ? `<h2>Research Themes</h2>${themesHtml}` : ""}

  ${tableHtml}

  ${gapsHtml ? `<h2>Research Gaps</h2><ul>${gapsHtml}</ul>` : ""}
  ${dirsHtml ? `<h2>Future Directions</h2><ul>${dirsHtml}</ul>` : ""}

  <h2>Related Work Section</h2>
  <div class="rw-para">${rw.literature_review_paragraph || ""}</div>
</body>
</html>`;

    const win = window.open("", "_blank");
    if (!win) {
      alert("Please allow popups for this site to download the PDF.");
      return;
    }
    win.document.write(html);
    win.document.close();
    win.focus();
    // slight delay so styles render before print dialog
    setTimeout(() => {
      win.print();
      win.close();
    }, 400);
  }, [result, query]);

  const showEmpty = !loading && !result && !warn && !err;

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <div className="app-root">
      <header className="top-bar">
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={
            theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
          }
        >
          {theme === "dark" ? (
            <>
              <svg
                className="theme-toggle-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                aria-hidden
              >
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 6.34L4.93 4.93M19.07 19.07l-1.41-1.41M19.07 4.93 17.66 6.34M6.34 17.66 4.93 19.07" />
              </svg>
              Light mode
            </>
          ) : (
            <>
              <svg
                className="theme-toggle-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                aria-hidden
              >
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
              Dark mode
            </>
          )}
        </button>
      </header>

      <div className="app">
        <aside className="sidebar" aria-label="Settings">
          <div className="sidebar-brand">
            <span className="sidebar-brand-mark" aria-hidden />
            <div>
              <p className="sidebar-brand-name">Research Assistant</p>
              <p className="sidebar-brand-tag">3-agent pipeline</p>
            </div>
          </div>

          <div className="sidebar-card">
            <h3 className="sidebar-heading">Pipeline</h3>
            <label className="sidebar-label" htmlFor="max-papers">
              Papers to retrieve
            </label>
            <div className="slider-block">
              <div className="slider-row">
                <input
                  id="max-papers"
                  type="range"
                  min={2}
                  max={10}
                  value={maxPapers}
                  onChange={(e) => setMaxPapers(Number(e.target.value))}
                  disabled={loading}
                  aria-valuemin={2}
                  aria-valuemax={10}
                  aria-valuenow={maxPapers}
                  aria-valuetext={`${maxPapers} papers`}
                />
                <output className="slider-value" htmlFor="max-papers">
                  {maxPapers}
                </output>
              </div>
              <p className="slider-hint">
                More papers mean richer synthesis and longer wait times.
              </p>
            </div>
          </div>

          <div className="sidebar-card">
            <h3 className="sidebar-heading">Agents</h3>
            <ul className="agent-list">
              <li>
                <span className="agent-dot agent-dot--a" aria-hidden />
                <div>
                  <strong>Retrieval</strong>
                  <span>ArXiv search &amp; metadata</span>
                </div>
              </li>
              <li>
                <span className="agent-dot agent-dot--b" aria-hidden />
                <div>
                  <strong>Summarization</strong>
                  <span>Structured paper summaries</span>
                </div>
              </li>
              <li>
                <span className="agent-dot agent-dot--c" aria-hidden />
                <div>
                  <strong>Related work</strong>
                  <span>Themes, gaps, and paragraph</span>
                </div>
              </li>
            </ul>
          </div>

          <p className="footer-note">
            Summaries (Llama) · Synthesis (Qwen) via Groq · Data from ArXiv
          </p>
        </aside>

        <div className="main-wrap">
          <main className="main" id="main-content">
            <header className="header-block">
              <h1 className="main-title"> AI-Powered Literature Review Assistant</h1>
              <p className="subtitle">
                Search ArXiv, summarize each paper, then generate themes, gaps,
                and a citation-ready paragraph—all in one run.
              </p>
            </header>

            <section className="search-panel" aria-labelledby="search-heading">
              <h2 id="search-heading" className="visually-hidden">
                Search
              </h2>
              <div className="search-panel-inner">
                <label className="field-label" htmlFor="topic">
                  Research topic
                </label>
                <div className="search-row">
                  <input
                    id="topic"
                    type="search"
                    className="topic-input"
                    placeholder="e.g. diffusion models for medical imaging"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={loading}
                    autoComplete="off"
                    enterKeyHint="search"
                    onKeyDown={(e) =>
                      e.key === "Enter" && !loading && runPipeline()
                    }
                  />
                  <button
                    type="button"
                    className="run-btn"
                    onClick={runPipeline}
                    disabled={loading}
                  >
                    {loading ? "Running…" : "Run"}
                  </button>
                </div>
                <p className="search-hint">
                  <kbd>Enter</kbd> also starts a run. Typical runtime: 1–5+
                  minutes depending on paper count and APIs.
                </p>
              </div>
            </section>

            {result && (
              <div className="results-toolbar">
                <p className="results-toolbar-text">
                  Results for <strong>{result.query}</strong>
                </p>
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={clearResults}
                >
                  New search
                </button>
              </div>
            )}

            <div className="content-flow">
              {warn && (
                <div className="alert alert--warn" role="status">
                  {warn}
                </div>
              )}
              {err && (
                <div className="alert alert--err" role="alert">
                  {err}
                </div>
              )}

              {loading && (
                <div
                  className="loading-card"
                  role="status"
                  aria-live="polite"
                  aria-busy="true"
                >
                  <div className="loading-card-top">
                    <div className="spinner" aria-hidden />
                    <div>
                      <p className="loading-title">
                        Working through the pipeline
                      </p>
                      <p className="loading-desc">
                        Retrieving papers, generating summaries, then building
                        your related-work section. Safe to wait—do not refresh
                        the page.
                      </p>
                    </div>
                  </div>
                  <PipelineProgress />
                </div>
              )}

              {showEmpty && (
                <div className="empty-state">
                  <div className="empty-visual" aria-hidden>
                    <div className="empty-orbit" />
                    <div className="empty-core" />
                  </div>
                  <h2 className="empty-title">Ready when you are</h2>
                  <p className="empty-lead">
                    Describe your research angle in plain language. We will pull
                    relevant preprints and draft a structured review you can
                    refine.
                  </p>
                  <ul className="empty-tips">
                    <li>
                      Use specific methods or datasets for tighter retrieval
                    </li>
                    <li>
                      Start with 3–5 papers, then increase if you need breadth
                    </li>
                    <li>Export the full review as a PDF for your manuscript</li>
                  </ul>
                </div>
              )}

              {result && (
                <div ref={resultsRef} className="results" tabIndex={-1}>
                  <div className="tabs-nav">
                    <button
                      className={`tab-btn ${activeTab === "a" ? "active" : ""}`}
                      onClick={() => setActiveTab("a")}
                    >
                      <span className="tab-badge badge-a">A</span>
                      Retrieval
                    </button>
                    <button
                      className={`tab-btn ${activeTab === "b" ? "active" : ""}`}
                      onClick={() => setActiveTab("b")}
                    >
                      <span className="tab-badge badge-b">B</span>
                      Summaries
                    </button>
                    <button
                      className={`tab-btn ${activeTab === "c" ? "active" : ""}`}
                      onClick={() => setActiveTab("c")}
                    >
                      <span className="tab-badge badge-c">C</span>
                      Synthesis
                    </button>
                  </div>

                  {/* ── Tab A: Retrieval ── */}
                  {activeTab === "a" && (
                    <div className="tab-content">
                      <StepHeader
                        badge="Agent A"
                        badgeClass="badge-a"
                        title="Paper retrieval"
                        step="01 / 03"
                      />
                      <div className="alert alert--ok" role="status">
                        Found{" "}
                        <strong>{result.papers?.length ?? 0}</strong> papers on
                        ArXiv
                      </div>
                      <div className="card-stack">
                        {(result.papers || []).map((p, idx) => (
                          <article key={idx} className="paper-card">
                            <span className="paper-index">{idx + 1}</span>
                            <h3 className="paper-title">{p.title}</h3>
                            <PaperMeta paper={p} />
                            <p className="abstract-snippet">
                              {(p.abstract || "").slice(0, 220)}
                              {(p.abstract || "").length > 220 ? "…" : ""}
                            </p>
                          </article>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* ── Tab B: Summaries ── */}
                  {activeTab === "b" && (
                    <div className="tab-content">
                      <StepHeader
                        badge="Agent B"
                        badgeClass="badge-b"
                        title="Summarization"
                        step="02 / 03"
                      />
                      <div className="card-stack">
                        {(result.enriched_papers || []).map((paper, idx) => {
                          const s = paper.summary || {};
                          const findings = (s.key_findings || []).slice(0, 4);
                          return (
                            <article
                              key={idx}
                              className="paper-card paper-card--summary"
                            >
                              <span className="paper-index paper-index--b">
                                {idx + 1}
                              </span>
                              <h3 className="paper-title">{paper.title}</h3>
                              {s.one_liner && (
                                <blockquote className="one-liner">
                                  {s.one_liner}
                                </blockquote>
                              )}
                              <div className="findings-label">Key findings</div>
                              <div className="chips">
                                {findings.length === 0 ? (
                                  <span className="finding-chip finding-chip--muted">
                                    No bullets returned
                                  </span>
                                ) : (
                                  findings.map((f, i) => (
                                    <span key={i} className="finding-chip">
                                      {f}
                                    </span>
                                  ))
                                )}
                              </div>
                              {s.novelty && (
                                <div className="novelty">
                                  <span className="novelty-label">Novelty</span>
                                  {s.novelty}
                                </div>
                              )}
                            </article>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* ── Tab C: Synthesis ── */}
                  {activeTab === "c" && result.related_work && (
                    <div className="tab-content">
                      <StepHeader
                        badge="Agent C"
                        badgeClass="badge-c"
                        title="Related work & synthesis"
                        step="03 / 03"
                      />

                      {/* Overview */}
                      <div className="review-box">
                        <div className="overline">Overview</div>
                        <div className="review-body">
                          {result.related_work.overview}
                        </div>
                      </div>

                      {/* Research Themes */}
                      {(result.related_work.themes || []).length > 0 && (
                        <section
                          className="themes-section"
                          aria-labelledby="themes-heading"
                        >
                          <h3 id="themes-heading" className="section-title">
                            Research themes
                          </h3>
                          <div className="themes-grid">
                            {(result.related_work.themes || []).map(
                              (theme, i) => (
                                <div key={i} className="theme-card">
                                  <h4 className="theme-name">{theme.name}</h4>
                                  <p className="theme-desc">
                                    {theme.description}
                                  </p>
                                  <div className="theme-papers">
                                    {(theme.papers || []).join(" · ")}
                                  </div>
                                  <p className="theme-synth">
                                    {theme.synthesis}
                                  </p>
                                </div>
                              )
                            )}
                          </div>
                        </section>
                      )}

                      {/* Gaps & Directions */}
                      <div className="two-col">
                        <section
                          className="insight-column"
                          aria-labelledby="gaps-h"
                        >
                          <h3 id="gaps-h" className="section-title">
                            Research gaps
                          </h3>
                          {(result.related_work.gaps || []).map((gap, i) => (
                            <div key={i} className="gap-item">
                              <span className="insight-icon" aria-hidden>
                                ◆
                              </span>
                              {gap}
                            </div>
                          ))}
                        </section>
                        <section
                          className="insight-column"
                          aria-labelledby="dir-h"
                        >
                          <h3 id="dir-h" className="section-title">
                            Future directions
                          </h3>
                          {(result.related_work.future_directions || []).map(
                            (d, i) => (
                              <div key={i} className="direction-item">
                                <span
                                  className="insight-icon insight-icon--dir"
                                  aria-hidden
                                >
                                  →
                                </span>
                                {d}
                              </div>
                            )
                          )}
                        </section>
                      </div>

                      {/* ── Feature 1: Related Work Table ── */}
                      <RelatedWorkTable
                        rows={result.related_work.papers_table}
                      />

                      {/* ── Feature 2: Related Work Section (renamed) + copy ── */}
                      <div className="section-title-row">
                        <h3 className="section-title">Related work section</h3>
                        <CopyButton
                          getText={() =>
                            result.related_work.literature_review_paragraph ||
                            ""
                          }
                          label="Copy section"
                          className="copy-btn"
                        />
                      </div>
                      <div className="lit-review-paragraph">
                        {result.related_work.literature_review_paragraph}
                      </div>

                      {/* ── Feature 3: Download as PDF ── */}
                      <div className="download-row">
                        <button
                          type="button"
                          className="download-btn"
                          onClick={downloadPdf}
                        >
                          Download full review (.pdf)
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}