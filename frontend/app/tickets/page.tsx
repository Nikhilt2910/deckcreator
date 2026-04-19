"use client";

import { FormEvent, useState } from "react";

import { createTicket, TicketResponse, TicketType } from "@/lib/api";

export default function TicketsPage() {
  const [result, setResult] = useState<TicketResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    const form = event.currentTarget;

    const formData = new FormData(form);
    const type = formData.get("type") as TicketType;
    const description = String(formData.get("description") ?? "").trim();

    if (!description) {
      setError("Description is required.");
      return;
    }

    try {
      setIsSubmitting(true);
      const ticket = await createTicket(type, description);
      setResult(ticket);
      form.reset();
    } catch (submitError) {
      setResult(null);
      setError(submitError instanceof Error ? submitError.message : "Ticket creation failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="stack">
      <section className="page-hero">
        <div className="eyebrow">Support lane</div>
        <h1>Report a product issue without leaving the studio.</h1>
        <p>
          Feature requests and bugs go through the backend, sync to Jira, and can
          trigger the developer approval workflow behind the scenes.
        </p>
      </section>

      <section className="workspace">
        <form className="studio-form" onSubmit={handleSubmit}>
          <div className="grid two">
            <div className="field">
              <label htmlFor="type">Request type</label>
              <select id="type" name="type" defaultValue="feature">
                <option value="feature">Feature</option>
                <option value="bug">Bug</option>
              </select>
            </div>
          </div>
          <div className="field">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              placeholder="Describe what should change in the product, or what is broken."
              required
            />
            <span className="field-note">Clear, direct requests create better engineering resolutions.</span>
          </div>
          <div className="actions">
            <button className="button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Sending..." : "Submit request"}
            </button>
          </div>
        </form>

        <aside className="side-rail">
          <div className="console-card">
            <div className="console-label"></div>
            <ul className="signal-list">
              <li>1. Ticket stored locally</li>
              <li>2. Jira issue created</li>
              <li>3. Resolution drafted</li>
              <li>4. Developer review email sent when valid</li>
            </ul>
          </div>
        </aside>
      </section>

      {error ? <pre className="result result-error">{error}</pre> : null}
      {result ? (
        <section className="result-card">
          <div className="result-head">
            <div>
              <div className="console-label">Ticket created</div>
              <h2>{result.jira_issue_key ?? result.id}</h2>
            </div>
            <span className={`status-pill status-${result.status}`}>{result.status}</span>
          </div>

          <div className="result-grid">
            <article>
              <span className="result-label">Type</span>
              <strong>{result.type}</strong>
            </article>
            <article>
              <span className="result-label">Created</span>
              <strong>{formatDate(result.created_at)}</strong>
            </article>
            <article>
              <span className="result-label">Jira sync</span>
              <strong>{result.jira_synced ? `Linked to ${result.jira_issue_key}` : "Stored locally only"}</strong>
            </article>
            <article>
              <span className="result-label">Developer email</span>
              <strong>{result.email_sent ? "Sent" : "Not sent"}</strong>
            </article>
          </div>

          <div className="result-copy">
            <p>{result.description}</p>
            {result.email_sent ? (
              <p className="result-note">
                Review email sent to {result.developer_email ?? "the configured developer"}.
              </p>
            ) : result.email_error ? (
              <p className="result-note">
                Ticket creation succeeded. No review email was sent because: {result.email_error}
              </p>
            ) : null}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}
