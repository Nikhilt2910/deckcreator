import Link from "next/link";

export default function HomePage() {
  return (
    <div className="stack studio-stack">
      <section className="hero-panel">
        <div className="eyebrow">Deck creation studio</div>
        <div className="hero-grid">
          <div className="hero-copy">
            <h1>
              Turn raw data into a boardroom deck with the right tone, structure, and
              visual system.
            </h1>
            <p>
              Upload Excel data, point the engine to a PPT, PDF, or preset template,
              and generate a polished presentation workflow that stays editable.
            </p>
            <div className="actions">
              <Link className="button" href="/upload">
                Start a deck
              </Link>
            </div>
          </div>
          <div className="hero-console">
            <div className="console-card">
              <div className="console-label">Live workflow</div>
              <ul className="signal-list">
                <li>1. Upload Excel workbook</li>
                <li>2. Choose a preset or style reference</li>
                <li>3. Generate structured insights</li>
                <li>4. Export downloadable PPTX</li>
              </ul>
            </div>
            <div className="console-card accent">
              <div className="console-label">Reference modes</div>
              <p>
                Preset templates for stability. Uploaded PPTX for brand fidelity. PDF
                for visual direction.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid three">
        <article className="feature-panel">
          <span className="feature-kicker">Preset gallery</span>
          <h2>Start from a business-ready deck structure</h2>
          <p>
            Use curated templates for marketing reviews, case studies, and story-led
            decks when consistency matters more than style inference.
          </p>
        </article>
        <article className="feature-panel">
          <span className="feature-kicker">Reference-aware generation</span>
          <h2>Use uploaded style guides without rebuilding the workflow manually</h2>
          <p>
            The app accepts PPTX and PDF reference files and keeps the generation path
            connected to the backend orchestration you already have.
          </p>
        </article>
        <article className="feature-panel">
          <span className="feature-kicker">Support lane</span>
          <h2>Keep product feedback and bug reporting close to the output</h2>
          <p>
            Tickets remain part of the app, but they now sit behind the main deck
            creation journey instead of dominating it.
          </p>
        </article>
      </section>

      <section className="showcase-panel">
        <div className="showcase-copy">
          <div className="eyebrow">Template directions</div>
          <h2>Choose the deck language before you upload the data.</h2>
          <p>
            A deck creator should feel like choosing a narrative system, not filling in
            a utility form. These modes mirror the actual use case behind the product.
          </p>
        </div>
        <div className="template-rack">
          <article className="template-card template-card-a">
            <span>Marketing review</span>
            <strong>Dense KPI narrative</strong>
          </article>
          <article className="template-card template-card-b">
            <span>Case study</span>
            <strong>Client story structure</strong>
          </article>
          <article className="template-card template-card-c">
            <span>Photo-led deck</span>
            <strong>Editorial composition</strong>
          </article>
        </div>
      </section>
    </div>
  );
}
