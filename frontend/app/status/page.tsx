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
    <div className="card">
      <h1>Ticket status</h1>
      <p className="status-text">Fetch the latest stored state for a ticket created through the app.</p>
      <form className="stack" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="ticket_id">Ticket ID</label>
          <input id="ticket_id" name="ticket_id" type="text" placeholder="e.g. abc123def4" required />
        </div>
        <div className="actions">
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Checking..." : "Check status"}
          </button>
        </div>
      </form>
      {error ? <pre className="result">{error}</pre> : null}
      {ticket ? <pre className="result">{JSON.stringify(ticket, null, 2)}</pre> : null}
    </div>
  );
}
