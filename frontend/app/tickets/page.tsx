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

    const formData = new FormData(event.currentTarget);
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
      event.currentTarget.reset();
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
            <div className="console-label">What happens next</div>
            <ul className="signal-list">
              <li>1. Ticket stored locally</li>
              <li>2. Jira issue created</li>
              <li>3. Resolution drafted</li>
              <li>4. Developer review email sent when valid</li>
            </ul>
          </div>
        </aside>
      </section>

      {error ? <pre className="result">{error}</pre> : null}
      {result ? <pre className="result">{JSON.stringify(result, null, 2)}</pre> : null}
    </div>
  );
}
