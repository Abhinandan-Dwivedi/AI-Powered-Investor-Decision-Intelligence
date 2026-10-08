import "./Masthead.css";

export default function Masthead() {
  return (
    <header className="masthead">
      <div className="masthead-mark" aria-hidden="true">§</div>
      <div>
        <h1 className="masthead-title">Investor Ledger</h1>
        <p className="masthead-tagline">Corporate filings, read and reasoned over.</p>
      </div>
    </header>
  );
}
