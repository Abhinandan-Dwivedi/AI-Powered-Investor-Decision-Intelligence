import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api/client";
import "./ChatPanel.css";

const WELCOME = {
  role: "assistant",
  text: "Ask about revenue trends, risk factors, or growth drivers from any ingested filing.",
};

export default function ChatPanel({ scope }) {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isThinking]);

  async function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isThinking) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsThinking(true);

    try {
      const result = await sendChatMessage({
        question,
        company: scope?.company,
        fiscalYear: scope?.fiscal_year,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Could not complete that query: ${err.message}`, isError: true },
      ]);
    } finally {
      setIsThinking(false);
    }
  }

  return (
    <aside className="chat-panel">
      <div className="chat-panel-header">
        <div className="chat-identity">
          <span className="chat-avatar" aria-hidden="true">✦</span>
          <div>
            <h2 className="chat-title">Analyst</h2>
            <p className="chat-subtitle">Grounded in your filings</p>
          </div>
        </div>
        {scope && (
          <span className="chat-scope">
            {scope.company} · FY{scope.fiscal_year}
          </span>
        )}
      </div>

      <div className="chat-transcript" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-line chat-line-${m.role} ${m.isError ? "chat-line-error" : ""}`}>
            <div className="chat-bubble">
              <p className="chat-text">{m.text}</p>
              {m.sources?.length > 0 && (
                <div className="chat-sources">
                  <span className="chat-sources-label">Sources</span>
                  {/* Display-only de-dupe: several chunks often come from the same filing. */}
                  {[...new Set(m.sources.map((s) => `${s.company} FY${s.fiscal_year}`))].map((label) => (
                    <span key={label} className="chat-source-chip">{label}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isThinking && (
          <div className="chat-line chat-line-assistant">
            <div className="chat-bubble chat-thinking">
              <span className="chat-dots" aria-hidden="true"><i /><i /><i /></span>
              reading the filing…
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          placeholder="Ask about revenue, risk, growth…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          className="chat-send"
          aria-label="Send question"
          disabled={!input.trim() || isThinking}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14" />
            <path d="m13 6 6 6-6 6" />
          </svg>
        </button>
      </form>
    </aside>
  );
}