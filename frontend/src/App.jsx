import { useEffect, useState } from "react";
import Masthead from "./components/Masthead";
import UploadPanel from "./components/UploadPanel";
import CompanySelector from "./components/CompanySelector";
import KpiLedger from "./components/KpiLedger";
import InsightColumns from "./components/InsightColumns";
import ChatPanel from "./components/ChatPanel";
import { fetchMetrics } from "./api/client";
import "./App.css";

export default function App() {
  const [metrics, setMetrics] = useState([]);
  const [selectedScope, setSelectedScope] = useState(null);
  const [loadError, setLoadError] = useState(null);

  async function reloadMetrics() {
    try {
      const data = await fetchMetrics();
      setMetrics(data);
      if (!selectedScope && data.length > 0) {
        setSelectedScope({ company: data[0].company, fiscal_year: data[0].fiscal_year });
      }
    } catch (err) {
      setLoadError(err.message);
    }
  }

  useEffect(() => {
    reloadMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeMetric = metrics.find(
    (m) => m.company === selectedScope?.company && m.fiscal_year === selectedScope?.fiscal_year
  );

  return (
    <div className="app-shell">
      <main className="app-main">
        <div className="app-main-inner">
          <div className="app-header">
            <Masthead />
            {metrics.length > 0 && (
              <CompanySelector metrics={metrics} selected={selectedScope} onChange={setSelectedScope} />
            )}
          </div>

          {loadError && <p className="app-load-error">Could not reach the backend: {loadError}</p>}

          <UploadPanel onIngested={reloadMetrics} />
          <KpiLedger metric={activeMetric} />
          <InsightColumns metric={activeMetric} />
        </div>
      </main>

      <ChatPanel scope={selectedScope} />
    </div>
  );
}