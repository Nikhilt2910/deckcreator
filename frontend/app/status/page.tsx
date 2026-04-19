"use client";

import { FormEvent, useState } from "react";

import { getTicketStatus, TicketResponse } from "@/lib/api";

export default function StatusPage() {
  const [ticket, setTicket] = useState<TicketResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const formData = new FormData(event.currentTarget);
    const ticketId = String(formData.get("ticket_id") ?? "").trim();
    if (!ticketId) {
      setError("Ticket ID is required.");
      return;
    }

    try {
      setLoading(true);
      setTicket(await getTicketStatus(ticketId));
    } catch (statusError) {
      setTicket(null);
      setError(statusError instanceof Error ? statusError.message : "Unable to load ticket status.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <section className="page-hero">
        <div className="eyebrow">Run tracking</div>
        <h1>Check whether a ticket is waiting, approved, or resolved.</h1>
        <p>
          Use the generated ticket ID to inspect the latest state stored by the backend.
        </p>
      </section>

      <section className="workspace">
        <form className="studio-form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="ticket_id">Ticket ID</label>
            <input id="ticket_id" name="ticket_id" type="text" placeholder="e.g. abc123def4" required />
            <span className="field-note">This returns the latest local state for a ticket created inside the app.</span>
          </div>
          <div className="actions">
            <button className="button" type="submit" disabled={loading}>
              {loading ? "Checking..." : "Load status"}
            </button>
          </div>
        </form>

        <aside className="side-rail">
          <div className="console-card">
            <div className="console-label">Tracked states</div>
            <ul className="signal-list">
              <li>Pending</li>
              <li>Approved</li>
              <li>Rejected</li>
            </ul>
          </div>
        </aside>
      </section>

      {error ? <pre className="result">{error}</pre> : null}
      {ticket ? <pre className="result">{JSON.stringify(ticket, null, 2)}</pre> : null}
    </div>
  );
}
