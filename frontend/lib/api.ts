const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type TicketType = "bug" | "feature";

export type TicketResponse = {
  id: string;
  type: TicketType;
  description: string;
  created_at: string;
  jira_synced: boolean;
  jira_issue_key?: string | null;
  resolution?: {
    files: string[];
    patch: string;
    explanation: string;
    generated_at: string;
  } | null;
  status: "pending" | "approved" | "rejected";
  developer_email?: string | null;
  review_url?: string | null;
  email_sent: boolean;
  email_error?: string | null;
  review_outcome?: {
    applied: boolean;
    message: string;
    applied_at?: string | null;
  } | null;
  automation_result?: {
    patch_applied: boolean;
    tests_passed: boolean;
    pushed: boolean;
    branch?: string | null;
    commit_sha?: string | null;
    message: string;
    completed_at?: string | null;
  } | null;
};

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function uploadFiles(excelFile: File, referenceFile: File): Promise<unknown> {
  const formData = new FormData();
  formData.append("excel_file", excelFile);
  formData.append("reference_file", referenceFile);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(response);
}

export async function createTicket(type: TicketType, description: string): Promise<TicketResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ticket`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ type, description }),
  });

  return parseResponse<TicketResponse>(response);
}

export async function getTicketStatus(ticketId: string): Promise<TicketResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ticket/${ticketId}`, {
    method: "GET",
    cache: "no-store",
  });

  return parseResponse<TicketResponse>(response);
}

export async function approveTicket(ticketId: string, token: string): Promise<TicketResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/approve?ticket_id=${encodeURIComponent(ticketId)}&token=${encodeURIComponent(token)}`,
    {
      method: "GET",
      cache: "no-store",
    },
  );

  return parseResponse<TicketResponse>(response);
}

export async function rejectTicket(ticketId: string, token: string): Promise<TicketResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/reject?ticket_id=${encodeURIComponent(ticketId)}&token=${encodeURIComponent(token)}`,
    {
      method: "GET",
      cache: "no-store",
    },
  );

  return parseResponse<TicketResponse>(response);
}
