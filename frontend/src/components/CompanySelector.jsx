import "./CompanySelector.css";

export default function CompanySelector({ documents, selected, onChange }) {

  return (
    <label className="company-selector-wrap">
      <span className="company-selector-label">Active filing</span>
      <select
        className="company-selector"
        value={selected?.content_hash || ""}
        onChange={(e) => onChange(e.target.value)}
      >
        {documents.map((document) => (
          <option key={document.content_hash} value={document.content_hash}>
            {document.company} — FY{document.fiscal_year} · {document.source_file}
          </option>
        ))}
      </select>
    </label>
  );
}
