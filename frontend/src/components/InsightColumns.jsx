import "./InsightColumns.css";

export default function InsightColumns({ metric }) {
  if (!metric) return null;

  const hasInsights = metric.growth_drivers?.length || metric.risk_factors?.length;
  if (!hasInsights) return null;

  return (
    <section className="insight-columns">
      <div className="insight-column">
        <h3 className="insight-heading insight-heading-gain">
          <span className="insight-glyph">▲</span> Growth drivers
        </h3>
        <p className="insight-description">Key factors that may drive future growth.</p>
        <ul className="insight-list">
          {metric.growth_drivers.map((point, i) => (
            <li key={i}>{point}</li>
          ))}
        </ul>
      </div>

      <div className="insight-column">
        <h3 className="insight-heading insight-heading-loss">
          <span className="insight-glyph">▼</span> Risk factors
        </h3>
        <p className="insight-description">Key risks and potential headwinds.</p>
        <ul className="insight-list">
          {metric.risk_factors.map((point, i) => (
            <li key={i}>{point}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}