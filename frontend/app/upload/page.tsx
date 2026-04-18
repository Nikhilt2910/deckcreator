"use client";

import { FormEvent, useState } from "react";

import { uploadFiles } from "@/lib/api";

export default function UploadPage() {
  const [message, setMessage] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    const formData = new FormData(event.currentTarget);
    const excelFile = formData.get("excel_file");
    const referenceFile = formData.get("reference_file");

    if (!(excelFile instanceof File) || !(referenceFile instanceof File)) {
      setMessage("Select both an Excel file and a PPT or PDF reference file.");
      return;
    }

    try {
      setIsSubmitting(true);
      const result = await uploadFiles(excelFile, referenceFile);
      setMessage(JSON.stringify(result, null, 2));
      event.currentTarget.reset();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h1>Upload source files</h1>
      <p className="status-text">
        This page sends files directly to the FastAPI backend at
        {" "}
        <code>{process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}</code>.
      </p>
      <form className="stack" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="excel_file">Excel file</label>
          <input id="excel_file" name="excel_file" type="file" accept=".xlsx,.xls,.xlsm" required />
        </div>
        <div className="field">
          <label htmlFor="reference_file">PPT template or reference file</label>
          <input id="reference_file" name="reference_file" type="file" accept=".pptx,.potx,.pdf" required />
        </div>
        <div className="actions">
          <button className="button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Uploading..." : "Upload files"}
          </button>
        </div>
      </form>
      {message ? <pre className="result">{message}</pre> : null}
    </div>
  );
}
