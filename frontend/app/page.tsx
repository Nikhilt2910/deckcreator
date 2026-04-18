import Link from "next/link";

export default function HomePage() {
  return (
    <div className="stack">
      <section className="hero">
        <h1>Full-stack deck generation workflow</h1>
        <p>
          Upload business data, generate presentation-ready decks, and manage developer
          tickets through the same application.
        </p>
        <div className="actions">
          <Link className="button" href="/upload">
            Open upload
          </Link>
          <Link className="button secondary" href="/tickets">
            Submit ticket
          </Link>
        </div>
      </section>
      <section className="grid two">
        <article className="card">
          <h2>Upload</h2>
          <p>Send an Excel workbook and a PPTX reference file to the FastAPI backend.</p>
        </article>
        <article className="card">
          <h2>Track</h2>
          <p>Look up ticket state and review the latest Jira-sync and approval status.</p>
        </article>
      </section>
    </div>
  );
}
