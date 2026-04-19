"use client";

import { FormEvent, useState } from "react";

import { generateReport } from "@/lib/api";

export default function UploadPage() {
  const [message, setMessage] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    const form = event.currentTarget;

    const formData = new FormData(form);
    const excelFile = formData.get("excel_file");
    const referenceFile = formData.get("reference_file");

    if (!(excelFile instanceof File) || !(referenceFile instanceof File)) {
      setMessage("Select both an Excel file and a PPT or PDF reference file.");
      return;
    }

    try {
      setIsSubmitting(true);
      const { blob, filename } = await generateReport(excelFile, referenceFile);
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);
      setMessage(`Presentation generated successfully. Downloaded ${filename}.`);
      form.reset();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Report generation failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="stack">
      <section className="page-hero">
        <div className="eyebrow">Create a deck</div>
        <h1>Upload the data source and the visual reference.</h1>
        <p>
          Excel drives the content. PPTX, POTX, or PDF shape the tone. The backend
          keeps the orchestration and the output remains editable.
        </p>
      </section>

      <section className="workspace">
        <form className="studio-form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="excel_file">Excel workbook</label>
            <input id="excel_file" name="excel_file" type="file" accept=".xlsx,.xls,.xlsm" required />
            <span className="field-note">Upload the business data source used for analysis and slide content.</span>
          </div>
          <div className="field">
            <label htmlFor="reference_file">PPT, POTX, or PDF reference</label>
            <input id="reference_file" name="reference_file" type="file" accept=".pptx,.potx,.pdf" required />
            <span className="field-note">Use PPTX for the best layout and theme transfer. PDF works as a style cue.</span>
          </div>
          <div className="actions">
            <button className="button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit"}
            </button>
          </div>
        </form>

        <aside className="side-rail">
          <div className="console-card">
            <div className="console-label">Recommended reference order</div>
            <ul className="signal-list">
              <li>1. PPTX or POTX template</li>
              <li>2. Google Slides exported to PPTX</li>
              <li>3. PDF for visual direction only</li>
            </ul>
          </div>
          <div className="console-card accent">
            <div className="console-label">Connected backend</div>
            <p>
              Requests are sent to
              {" "}
              <code>{process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}</code>.
            </p>
          </div>
        </aside>
      </section>

      {message ? <pre className="result">{message}</pre> : null}
    </div>
  );
}
