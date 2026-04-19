const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type TicketType = "bug" | "feature";
export type AssistantSource = {
  title: string;
  url: string;
};

export type AssistantResponse = {
  answer: string;
  sources: AssistantSource[];
};

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

export type GeneratedDeckResult = {
  blob: Blob;
  filename: string;
};

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

export async function generateReport(
  excelFile?: File,
  referenceFile?: File,
  prompt?: string,
): Promise<GeneratedDeckResult> {
  const formData = new FormData();
  if (excelFile) {
    formData.append("excel_file", excelFile);
  }
  if (referenceFile) {
    formData.append("reference_file", referenceFile);
  }
  if (prompt?.trim()) {
    formData.append("prompt", prompt.trim());
  }

  const response = await fetch(`${API_BASE_URL}/reports/generate`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  const disposition = response.headers.get("content-disposition") ?? "";
  const fileNameMatch = disposition.match(/filename="?([^"]+)"?/i);
  const filename = fileNameMatch?.[1] ?? "generated-report.pptx";
  const blob = await response.blob();

  return { blob, filename };
}

export async function askAssistant(prompt: string): Promise<AssistantResponse> {
  const response = await fetch(`${API_BASE_URL}/api/assistant/respond`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
  });

  return parseResponse<AssistantResponse>(response);
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
