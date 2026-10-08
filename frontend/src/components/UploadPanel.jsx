import { useRef, useState } from "react";
import { ingestReport } from "../api/client";
import "./UploadPanel.css";

export default function UploadPanel({ onIngested }) {
  const [company, setCompany] = useState("");
  const [fiscalYear, setFiscalYear] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState(null); // { kind: "success"|"error"|"pending", message }
  const inputRef = useRef(null);

  async function handleFile(file) {
    if (!file) return;
    if (!company.trim() || !fiscalYear) {
      setStatus({ kind: "error", message: "Enter company and fiscal year first." });
      return;
    }
    setStatus({ kind: "pending", message: `Reading ${file.name}…` });
    try {
      const result = await ingestReport({ file, company, fiscalYear });
      setStatus({
        kind: result.status === "duplicate" ? "info" : "success",
        message:
          result.status === "duplicate"
            ? "Already ingested — skipped re-processing."
            : `Ingested ${result.chunk_count} sections from ${result.company} FY${result.fiscal_year}.`,
      });
      onIngested?.(result);
    } catch (err) {
      setStatus({ kind: "error", message: err.message });
    }
  }

  return (
    <section className="upload-panel panel-card">
      <div className="upload-copy">
        <p className="panel-eyebrow">01 · Source</p>
        <h2 className="panel-heading">Ingest a report</h2>
        <p className="panel-subtitle">Upload a company’s financial report to extract key insights.</p>
      </div>

      <div className="upload-fields">
        <label className="ledger-field">
          <span className="ledger-field-label">Company</span>
          <input
            className="ledger-input"
            placeholder="Company (e.g. Apple)"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </label>
        <label className="ledger-field ledger-field-year">
          <span className="ledger-field-label">Fiscal year</span>
          <input
            className="ledger-input"
            placeholder="Fiscal year"
            type="number"
            value={fiscalYear}
            onChange={(e) => setFiscalYear(e.target.value)}
          />
        </label>
      </div>

      <div
        className={`dropzone ${isDragging ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
      >
        <span className="dropzone-icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 16V4" />
            <path d="m7 9 5-5 5 5" />
            <path d="M20 16v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-3" />
          </svg>
        </span>
        <p className="dropzone-label">
          Drag &amp; drop a PDF here
          <span>or click to browse · PDF only</span>
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {status && (
        <p className={`upload-status status-${status.kind}`} role="status">
          <span className="upload-status-dot" aria-hidden="true" />
          {status.message}
        </p>
      )}
    </section>
  );
}