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
    <section className="upload-panel">
      <div className="upload-copy">
        <h2 className="panel-heading">Ingest a report</h2>
        <p>Upload a company’s financial report to extract key insights.</p>
      </div>

      <div className="upload-fields">
        <input
          className="ledger-input"
          placeholder="Company (e.g. Apple)"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
        />
        <input
          className="ledger-input"
          placeholder="Fiscal year"
          type="number"
          value={fiscalYear}
          onChange={(e) => setFiscalYear(e.target.value)}
        />
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
        <p className="dropzone-label">Drag &amp; drop a PDF here<br /><span>or click to browse</span></p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      {status && <p className={`upload-status status-${status.kind}`}>{status.message}</p>}
    </section>
  );
}