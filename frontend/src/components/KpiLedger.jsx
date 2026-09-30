import "./KpiLedger.css";

const ROWS = [
  { key: "revenue", label: "Revenue" },
  { key: "net_income", label: "Net income" },
  { key: "operating_income", label: "Operating income" },
  { key: "operating_cash_flow", label: "Operating cash flow" },
  { key: "total_assets", label: "Total assets" },
  { key: "total_liabilities", label: "Total liabilities" },
];

export default function KpiLedger({ metric }) {
  if (!metric) {
    return (
      <section className="kpi-ledger">
        <h2 className="panel-heading">Key figures</h2>
        <p className="empty-note">Ingest a report to populate this ledger.</p>
      </section>
    );
  }

  return (
    <section className="kpi-ledger">
      <div className="kpi-ledger-header">
        <div className="kpi-ledger-title">
          <h2 className="panel-heading">Key figures</h2>
          <p>Key financial metrics from the ingested filing.</p>
        </div>
        <span className="kpi-ledger-scope">
          {metric.company} · FY{metric.fiscal_year}
        </span>
      </div>

      <table className="ledger-table">
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.key}>
              <td className="ledger-table-label">{row.label}</td>
              <td className="ledger-table-value tabular">{metric[row.key] ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}