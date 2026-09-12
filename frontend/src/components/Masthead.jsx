import "./Masthead.css";

export default function Masthead() {
  return (
    <header className="masthead">
      <div>
        <h1 className="masthead-title">Investor Ledger</h1>
        <p className="masthead-tagline">Corporate filings, read and reasoned over.</p>
      </div>
      <div className="masthead-mark">§</div>
    </header>
  );
}