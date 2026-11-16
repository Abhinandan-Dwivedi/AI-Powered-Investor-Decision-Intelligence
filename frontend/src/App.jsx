import { useEffect, useState } from "react";
import Masthead from "./components/Masthead";
import UploadPanel from "./components/UploadPanel";
import CompanySelector from "./components/CompanySelector";
import KpiLedger from "./components/KpiLedger";
import InsightColumns from "./components/InsightColumns";
import ChatPanel from "./components/ChatPanel";
import { fetchDocuments, fetchMetrics } from "./api/client";
import "./App.css";

export default function App() {
  const [metrics, setMetrics] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedContentHash, setSelectedContentHash] = useState("");
  const [loadError, setLoadError] = useState(null);

  async function reloadData() {
    try {
      const [metricsData, documentsData] = await Promise.all([
        fetchMetrics(),
        fetchDocuments(),
      ]);
      setMetrics(metricsData);
      setDocuments(documentsData);
      setSelectedContentHash((current) =>
        documentsData.some((document) => document.content_hash === current)
          ? current
          : documentsData[0]?.content_hash || ""
      );
      setLoadError(null);
    } catch (err) {
      setLoadError(err.message);
    }
  }

  useEffect(() => {
    reloadData();
  }, []);

  const selectedDocument =
    documents.find((document) => document.content_hash === selectedContentHash) || null;

  const activeMetric = metrics.find(
    (m) =>
      m.company === selectedDocument?.company &&
      m.fiscal_year === selectedDocument?.fiscal_year
  );

  return (
    <div className="app-shell">
      <main className="app-main">
        <div className="app-main-inner">
          <div className="app-header">
            <Masthead />
            {documents.length > 0 && (
              <CompanySelector
                documents={documents}
                selected={selectedDocument}
                onChange={setSelectedContentHash}
              />
            )}
          </div>

          {loadError && <p className="app-load-error">Could not reach the backend: {loadError}</p>}

          <UploadPanel onIngested={reloadData} />
          <KpiLedger metric={activeMetric} />
          <InsightColumns metric={activeMetric} />
        </div>
      </main>

      <ChatPanel scope={selectedDocument} />
    </div>
  );
}
