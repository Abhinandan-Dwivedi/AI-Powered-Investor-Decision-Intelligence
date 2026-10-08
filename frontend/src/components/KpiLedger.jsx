import "./KpiLedger.css";

const ROWS = [
  { key: "revenue", label: "Revenue" },
  { key: "net_income", label: "Net income" },
  { key: "operating_income", label: "Operating income" },
  { key: "operating_cash_flow", label: "Operating cash flow" },
  { key: "total_assets", label: "Total assets" },
  { key: "total_liabilities", label: "Total liabilities" },
];

// Display-only: split "$97,690 million" into a bold figure and a muted
// unit so the number reads first. Anything that doesn't match the
// pattern is rendered exactly as the backend sent it.
const UNIT_PATTERN = /^(.*\d)\s+(thousand|million|billion|trillion|lakh|crore|mn|bn|m|b)$/i;

function KpiValue({ value }) {
  if (value == null) return <span className="ledger-value-empty">—</span>;
  const match = String(value).match(UNIT_PATTERN);
  if (!match) return value;
  return (
    <>
      {match[1]}
      <span className="ledger-value-unit">{match[2]}</span>
    </>
  );
}

export default function KpiLedger({ metric }) {
  if (!metric) {
    return (
      <section className="kpi-ledger panel-card">
        <p className="panel-eyebrow">02 · Financials</p>
        <h2 className="panel-heading">Key figures</h2>
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3v18h18" />
              <path d="m7 15 4-4 3 3 5-6" />
            </svg>
          </span>
          <p className="empty-note">Ingest a report to populate this ledger.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="kpi-ledger panel-card">
      <div className="kpi-ledger-header">
        <div className="kpi-ledger-title">
          <p className="panel-eyebrow">02 · Financials</p>
          <h2 className="panel-heading">Key figures</h2>
          <p className="panel-subtitle">Key financial metrics from the ingested filing.</p>
        </div>
        <span className="scope-chip kpi-ledger-scope">
          {metric.company} · FY{metric.fiscal_year}
        </span>
      </div>

      <div className="ledger-grid">
        {ROWS.map((row) => (
          <div key={row.key} className="ledger-card">
            <span className="ledger-card-label">{row.label}</span>
            <span className="ledger-card-value tabular">
              <KpiValue value={metric[row.key]} />
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
