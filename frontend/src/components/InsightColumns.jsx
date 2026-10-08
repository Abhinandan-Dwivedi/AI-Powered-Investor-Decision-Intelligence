import "./InsightColumns.css";

export default function InsightColumns({ metric }) {
  if (!metric) return null;

  const hasInsights = metric.growth_drivers?.length || metric.risk_factors?.length;
  if (!hasInsights) return null;

  return (
    <section className="insight-section">
      <p className="panel-eyebrow">03 · Analysis</p>
      <div className="insight-columns">
        <div className="insight-column insight-column-gain panel-card">
          <div className="insight-header">
            <span className="insight-glyph" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m3 17 6-6 4 4 8-8" />
                <path d="M15 7h6v6" />
              </svg>
            </span>
            <div className="insight-titles">
              <h3 className="insight-heading">Growth drivers</h3>
              <p className="insight-description">Key factors that may drive future growth.</p>
            </div>
            <span className="insight-count tabular">{metric.growth_drivers.length}</span>
          </div>
          <ol className="insight-list">
            {metric.growth_drivers.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ol>
        </div>

        <div className="insight-column insight-column-loss panel-card">
          <div className="insight-header">
            <span className="insight-glyph" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3 2 20h20L12 3z" />
                <path d="M12 10v4" />
                <path d="M12 17h.01" />
              </svg>
            </span>
            <div className="insight-titles">
              <h3 className="insight-heading">Risk factors</h3>
              <p className="insight-description">Key risks and potential headwinds.</p>
            </div>
            <span className="insight-count tabular">{metric.risk_factors.length}</span>
          </div>
          <ol className="insight-list">
            {metric.risk_factors.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
