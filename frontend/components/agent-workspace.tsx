"use client";

import { ChangeEvent, FormEvent, useRef, useState } from "react";

import { askAssistant, AssistantSource, generateReport } from "@/lib/api";


type AttachmentKind = "excel" | "reference" | "unsupported";

type PendingAttachment = {
  id: string;
  name: string;
  kind: AttachmentKind;
  file: File;
};

type RenderAttachment = {
  id: string;
  name: string;
  kind: AttachmentKind;
};

type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  kind: "text" | "status" | "download";
  content: string;
  attachments?: RenderAttachment[];
  sources?: AssistantSource[];
  steps?: string[];
  activeStep?: number;
  downloadName?: string;
  downloadUrl?: string;
};

const EXCEL_EXTENSIONS = [".xlsx", ".xls", ".xlsm"];
const REFERENCE_EXTENSIONS = [".pptx", ".potx", ".pdf"];
const SUGGESTIONS = [
  "What are the latest retail media trends this quarter?",
  "Summarize current AI presentation design tools and cite sources.",
  "Generate an executive deck from my workbook and template with a sharper McKinsey tone.",
  "Explain how to improve ROI storytelling in a board presentation.",
];


export function AgentWorkspace() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [prompt, setPrompt] = useState("");
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: createId(),
      role: "assistant",
      kind: "text",
      content:
        "Ask a question for live web research, or attach one Excel workbook and one PPT/POTX/PDF reference to generate an editable deck.",
    },
  ]);

  function handleSuggestionClick(value: string) {
    setPrompt(value);
  }

  function handleAttachClick() {
    fileInputRef.current?.click();
  }

  function handleFileSelection(event: ChangeEvent<HTMLInputElement>) {
    const incomingFiles = Array.from(event.target.files ?? []);
    if (!incomingFiles.length) {
      return;
    }

    const nextAttachments = incomingFiles.map((file) => ({
      id: createId(),
      name: file.name,
      kind: detectAttachmentKind(file.name),
      file,
    }));

    setAttachments((current) => [...current, ...nextAttachments]);
    event.target.value = "";
  }

  function removeAttachment(attachmentId: string) {
    setAttachments((current) => current.filter((item) => item.id !== attachmentId));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) {
      return;
    }

    const trimmedPrompt = prompt.trim();
    const currentAttachments = [...attachments];
    if (!trimmedPrompt && currentAttachments.length === 0) {
      return;
    }

    const userMessageContent =
      trimmedPrompt ||
      "Generate a presentation from the attached workbook and style reference.";
    const renderedAttachments = currentAttachments.map(renderAttachment);
    setMessages((current) => [
      ...current,
      {
        id: createId(),
        role: "user",
        kind: "text",
        content: userMessageContent,
        attachments: renderedAttachments,
      },
    ]);
    setPrompt("");
    setAttachments([]);

    const classified = classifyAttachments(currentAttachments);
    if (classified.errors.length > 0) {
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: "assistant",
          kind: "text",
          content: classified.errors[0],
        },
      ]);
      return;
    }

    setIsSubmitting(true);
    try {
      if (classified.excel && classified.reference) {
        await runDeckGeneration(trimmedPrompt, classified.excel.file, classified.reference.file);
      } else {
        if (currentAttachments.length > 0) {
          setMessages((current) => [
            ...current,
            {
              id: createId(),
              role: "assistant",
              kind: "text",
              content:
                "For deck generation, attach exactly one Excel workbook and one PPT, POTX, or PDF reference file. For research questions, send just the prompt.",
            },
          ]);
          return;
        }

        if (!trimmedPrompt) {
          setMessages((current) => [
            ...current,
            {
              id: createId(),
              role: "assistant",
              kind: "text",
              content: "Type a prompt to search the web or attach the required files for deck generation.",
            },
          ]);
          return;
        }

        await runResearchAnswer(trimmedPrompt);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function runResearchAnswer(question: string) {
    const statusId = createId();
    setMessages((current) => [
      ...current,
      {
        id: statusId,
        role: "assistant",
        kind: "status",
        content: "Searching the web and preparing a grounded answer.",
        steps: ["Search current sources", "Compare signals", "Write reply"],
        activeStep: 0,
      },
    ]);

    try {
      const pendingAnswer = askAssistant(question);
      await advanceStatus(statusId, 1);
      const response = await pendingAnswer;
      await advanceStatus(statusId, 2);

      setMessages((current) =>
        current.map((message) =>
          message.id === statusId
            ? {
                ...message,
                kind: "text",
                content: response.answer,
                sources: response.sources,
                steps: undefined,
                activeStep: undefined,
              }
            : message,
        ),
      );
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === statusId
            ? {
                ...message,
                kind: "text",
                content: error instanceof Error ? error.message : "The assistant request failed.",
                steps: undefined,
                activeStep: undefined,
              }
            : message,
        ),
      );
    }
  }

  async function runDeckGeneration(userPrompt: string, excelFile: File, referenceFile: File) {
    const statusId = createId();
    const steps = [
      "Validate workbook and reference",
      "Build the narrative from the data",
      "Render the editable deck",
    ];
    setMessages((current) => [
      ...current,
      {
        id: statusId,
        role: "assistant",
        kind: "status",
        content: "Building your presentation.",
        steps,
        activeStep: 0,
      },
    ]);

    try {
      const generationPromise = generateReport(excelFile, referenceFile, userPrompt);
      await advanceStatus(statusId, 1);
      const result = await generationPromise;
      await advanceStatus(statusId, 2);

      const downloadUrl = URL.createObjectURL(result.blob);
      triggerDownload(downloadUrl, result.filename);

      setMessages((current) =>
        current.map((message) =>
          message.id === statusId
            ? {
                ...message,
                kind: "download",
                content:
                  "Your deck is ready. I used the uploaded workbook, reference file, and prompt to generate an editable presentation.",
                downloadName: result.filename,
                downloadUrl,
                steps: undefined,
                activeStep: undefined,
              }
            : message,
        ),
      );
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === statusId
            ? {
                ...message,
                kind: "text",
                content: error instanceof Error ? error.message : "Deck generation failed.",
                steps: undefined,
                activeStep: undefined,
              }
            : message,
        ),
      );
    }
  }

  async function advanceStatus(messageId: string, stepIndex: number) {
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId
          ? {
              ...message,
              activeStep: stepIndex,
            }
          : message,
      ),
    );
    await new Promise((resolve) => setTimeout(resolve, 220));
  }

  return (
    <section className="agent-shell">
      <div className="agent-header">
        <div>
          <div className="agent-eyebrow">DeckCreator agent</div>
          <h1>Ask, attach, and generate in one conversation.</h1>
          <p>
            Use live web search for questions. Attach an Excel workbook and a style reference to
            generate a deck with progress and a downloadable PPTX.
          </p>
        </div>
        <div className="agent-capabilities">
          <span>Web research</span>
          <span>Excel ingestion</span>
          <span>PPTX generation</span>
        </div>
      </div>

      <div className="suggestion-row">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            className="suggestion-chip"
            type="button"
            onClick={() => handleSuggestionClick(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>

      <div className="agent-thread">
        {messages.map((message) => (
          <article
            key={message.id}
            className={`chat-message ${message.role === "assistant" ? "assistant" : "user"}`}
          >
            <div className="chat-avatar">{message.role === "assistant" ? "DC" : "You"}</div>
            <div className="chat-bubble">
              <p>{message.content}</p>

              {message.attachments?.length ? (
                <div className="message-attachments">
                  {message.attachments.map((attachment) => (
                    <span key={attachment.id} className={`attachment-pill ${attachment.kind}`}>
                      {attachment.name}
                    </span>
                  ))}
                </div>
              ) : null}

              {message.kind === "status" && message.steps ? (
                <div className="status-steps">
                  {message.steps.map((step, index) => (
                    <div
                      key={step}
                      className={`status-step ${
                        index < (message.activeStep ?? 0)
                          ? "complete"
                          : index === (message.activeStep ?? 0)
                            ? "active"
                            : ""
                      }`}
                    >
                      <span>{index + 1}</span>
                      <strong>{step}</strong>
                    </div>
                  ))}
                </div>
              ) : null}

              {message.sources?.length ? (
                <div className="source-list">
                  <div className="source-label">Sources</div>
                  {message.sources.map((source) => (
                    <a key={source.url} href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                  ))}
                </div>
              ) : null}

              {message.kind === "download" && message.downloadName && message.downloadUrl ? (
                <div className="download-card">
                  <div>
                    <div className="source-label">Generated deck</div>
                    <strong>{message.downloadName}</strong>
                  </div>
                  <a href={message.downloadUrl} download={message.downloadName} className="button">
                    Download PPTX
                  </a>
                </div>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <div className="composer-top">
          <button className="attach-button" type="button" onClick={handleAttachClick} aria-label="Attach files">
            +
          </button>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Ask a question, or describe the deck you want to generate..."
            rows={1}
          />
          <button className="button composer-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Working..." : "Send"}
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          className="hidden-input"
          multiple
          accept=".xlsx,.xls,.xlsm,.pptx,.potx,.pdf"
          onChange={handleFileSelection}
        />

        {attachments.length ? (
          <div className="composer-attachments">
            {attachments.map((attachment) => (
              <button
                key={attachment.id}
                type="button"
                className={`attachment-pill ${attachment.kind}`}
                onClick={() => removeAttachment(attachment.id)}
              >
                {attachment.name}
              </button>
            ))}
          </div>
        ) : (
          <div className="composer-hint">
            Attach one Excel workbook and one PPT/POTX/PDF reference for deck generation.
          </div>
        )}
      </form>
    </section>
  );
}


function classifyAttachments(attachments: PendingAttachment[]) {
  const errors: string[] = [];
  const excelFiles = attachments.filter((item) => item.kind === "excel");
  const referenceFiles = attachments.filter((item) => item.kind === "reference");
  const unsupported = attachments.filter((item) => item.kind === "unsupported");

  if (unsupported.length > 0) {
    errors.push("Unsupported files were attached. Use Excel plus PPT, POTX, or PDF files only.");
  }
  if (excelFiles.length > 1) {
    errors.push("Attach only one Excel workbook per generation run.");
  }
  if (referenceFiles.length > 1) {
    errors.push("Attach only one PPT, POTX, or PDF reference per generation run.");
  }

  return {
    excel: excelFiles[0],
    reference: referenceFiles[0],
    errors,
  };
}


function detectAttachmentKind(fileName: string): AttachmentKind {
  const normalized = fileName.toLowerCase();
  if (EXCEL_EXTENSIONS.some((extension) => normalized.endsWith(extension))) {
    return "excel";
  }
  if (REFERENCE_EXTENSIONS.some((extension) => normalized.endsWith(extension))) {
    return "reference";
  }
  return "unsupported";
}


function renderAttachment(attachment: PendingAttachment): RenderAttachment {
  return {
    id: attachment.id,
    name: attachment.name,
    kind: attachment.kind,
  };
}


function triggerDownload(downloadUrl: string, fileName: string) {
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
}


function createId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

