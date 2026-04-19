"use client";

import { useEffect, useState, useTransition } from "react";
import { useParams, useSearchParams } from "next/navigation";

import {
  approveTicket,
  getTicketStatus,
  rejectTicket,
  TicketResponse,
} from "@/lib/api";

export default function ReviewPage() {
  const params = useParams<{ ticketId: string }>();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const ticketId = String(params.ticketId ?? "");

  const [ticket, setTicket] = useState<TicketResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;

    async function loadTicket() {
      if (!ticketId) {
        setError("Ticket ID is missing.");
        return;
      }

      try {
        const response = await getTicketStatus(ticketId);
        if (!cancelled) {
          setTicket(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load ticket.");
        }
      }
    }

    loadTicket();
    return () => {
      cancelled = true;
    };
  }, [ticketId]);

  function handleDecision(action: "approve" | "reject") {
    if (!ticketId || !token) {
      setError("The review link is missing a valid token.");
      return;
    }

    setError("");
    setStatusMessage("");

    startTransition(async () => {
      try {
        const response =
          action === "approve"
            ? await approveTicket(ticketId, token)
            : await rejectTicket(ticketId, token);
        setTicket(response);
        setStatusMessage(
          action === "approve"
            ? "Approval processed. The backend attempted patch apply, test, and push automation."
            : "Ticket rejected.",
        );
      } catch (decisionError) {
        setError(
          decisionError instanceof Error ? decisionError.message : "Unable to process the review action.",
        );
      }
    });
  }

  return (
    <div className="stack">
      <section className="page-hero">
        <div className="eyebrow">Developer review</div>
        <h1>Review the proposed code change before it touches the repository.</h1>
        <p>
          This page is designed for the developer email flow. Approval triggers the backend
          patch, test, and git automation chain.
        </p>
      </section>

      <section className="review-shell">
        <div className="review-main">
          <div className="review-card">
            <div className="console-label">Ticket</div>
            <h2>{ticket?.jira_issue_key ?? ticket?.id ?? ticketId}</h2>
            <p className="review-description">{ticket?.description ?? "Loading ticket details..."}</p>
            <div className="result-grid">
              <article>
                <span className="result-label">Status</span>
                <strong>{ticket?.status ?? "loading"}</strong>
              </article>
              <article>
                <span className="result-label">Email</span>
                <strong>{ticket?.email_sent ? "Sent" : "Not sent"}</strong>
              </article>
              <article>
                <span className="result-label">Review URL</span>
                <strong>{token ? "Token valid" : "Missing token"}</strong>
              </article>
            </div>

            <div className="actions">
              <button className="button" type="button" disabled={isPending} onClick={() => handleDecision("approve")}>
                {isPending ? "Processing..." : "Approve"}
              </button>
              <button
                className="button secondary"
                type="button"
                disabled={isPending}
                onClick={() => handleDecision("reject")}
              >
                Reject
              </button>
            </div>
          </div>

          {ticket?.resolution ? (
            <div className="review-card">
              <div className="console-label">Proposed change</div>
              <p className="review-description">{ticket.resolution.explanation}</p>
              <pre className="result">{ticket.resolution.patch}</pre>
            </div>
          ) : null}

          {ticket?.review_outcome ? (
            <div className="review-card">
              <div className="console-label">Apply outcome</div>
              <pre className="result">{ticket.review_outcome.message}</pre>
            </div>
          ) : null}

          {ticket?.automation_result ? (
            <div className="review-card">
              <div className="console-label">Automation</div>
              <pre className="result">{ticket.automation_result.message}</pre>
            </div>
          ) : null}

          {statusMessage ? <div className="result-card"><p className="result-copy">{statusMessage}</p></div> : null}
          {error ? <pre className="result result-error">{error}</pre> : null}
        </div>
      </section>
    </div>
  );
}
