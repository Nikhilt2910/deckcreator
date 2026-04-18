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
    <div className="card">
      <h1>Submit a ticket</h1>
      <p className="status-text">Feature requests and bug reports are sent to FastAPI and synced to Jira.</p>
      <form className="stack" onSubmit={handleSubmit}>
        <div className="grid two">
          <div className="field">
            <label htmlFor="type">Type</label>
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
            placeholder="Describe the requested change or the bug clearly."
            required
          />
        </div>
        <div className="actions">
          <button className="button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Create ticket"}
          </button>
        </div>
      </form>
      {error ? <pre className="result">{error}</pre> : null}
      {result ? <pre className="result">{JSON.stringify(result, null, 2)}</pre> : null}
    </div>
  );
}
