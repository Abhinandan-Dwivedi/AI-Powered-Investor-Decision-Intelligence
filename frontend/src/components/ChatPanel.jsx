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
        <h2 className="panel-heading">Analyst</h2>
        {scope && (
          <span className="chat-scope">
            {scope.company} · FY{scope.fiscal_year}
          </span>
        )}
      </div>

      <div className="chat-transcript" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-line chat-line-${m.role} ${m.isError ? "chat-line-error" : ""}`}>
            <span className="chat-prompt">{m.role === "user" ? ">" : "·"}</span>
            <div>
              <p className="chat-text">{m.text}</p>
              {m.sources?.length > 0 && (
                <p className="chat-sources">
                  Sources: {m.sources.map((s) => `${s.company} FY${s.fiscal_year}`).join(", ")}
                </p>
              )}
            </div>
          </div>
        ))}
        {isThinking && (
          <div className="chat-line chat-line-assistant">
            <span className="chat-prompt">·</span>
            <p className="chat-text chat-thinking">reading the filing…</p>
          </div>
        )}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <span className="chat-caret">{">"}</span>
        <input
          className="chat-input"
          placeholder="Ask about revenue, risk, growth…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
      </form>
    </aside>
  );
}