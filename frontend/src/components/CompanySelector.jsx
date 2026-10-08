import "./CompanySelector.css";

export default function CompanySelector({ metrics, selected, onChange }) {
  const options = metrics.map((m) => ({
    value: `${m.company}::${m.fiscal_year}`,
    label: `${m.company} — FY${m.fiscal_year}`,
  }));

  return (
    <label className="company-selector-wrap">
      <span className="company-selector-label">Active filing</span>
      <select
        className="company-selector"
        value={selected ? `${selected.company}::${selected.fiscal_year}` : ""}
        onChange={(e) => {
          const [company, fiscalYear] = e.target.value.split("::");
          onChange({ company, fiscal_year: Number(fiscalYear) });
        }}
      >
        <option value="" disabled>
          Select a filing
        </option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  );
}
