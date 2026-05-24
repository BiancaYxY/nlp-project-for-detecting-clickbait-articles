import React, { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import logo from "./assets/logo.png";

const VERDICT_CONFIG = {
  reliable: { emoji: "✅", label: "Reliable", className: "verdict-reliable" },
  misleading: { emoji: "🚨", label: "Misleading", className: "verdict-misleading" },
  clickbait: { emoji: "🎣", label: "Clickbait", className: "verdict-clickbait" },
  unverifiable: { emoji: "🔍", label: "Unverifiable", className: "verdict-unverifiable" },
};

function ResultCard({ data, summary }) {
  const title =
    data?.scraping?.cleaned?.title ||
    data?.scraping?.raw?.title ||
    "Title unavailable";
  const language = data?.language || "N/A";
  const verdict = data?.verdict?.verdict || "unverifiable";
  const confidence =
    typeof data?.verdict?.confidence === "number" ? data.verdict.confidence : 0;
  const flags = Array.isArray(data?.verdict?.flags) ? data.verdict.flags : [];

  const signals = data?.verdict?.signals || {};
  const similarity =
    typeof signals.similarity_score === "number"
      ? signals.similarity_score.toFixed(3)
      : "N/A";
  const entailment = signals.entailment_label || "N/A";
  const clickbait =
    typeof signals.clickbait_score === "number"
      ? signals.clickbait_score.toFixed(3)
      : "N/A";

  const llmExplanation = data?.llm_explanation?.explanation || "";
  const llmEmoji = data?.llm_explanation?.emoji || "";

  const vConfig = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.unverifiable;
  const pct = Math.round(confidence * 100);

  return (
    <div className={`result-card ${vConfig.className}`}>
      <div className="result-verdict-banner">
        <div className="verdict-emoji-wrap">{vConfig.emoji}</div>
        <div className="verdict-info">
          <span className="verdict-label-text">Verdict</span>
          <span className="verdict-name-text">{vConfig.label}</span>
        </div>
        <div className="confidence-wrap">
          <div className="confidence-bar-track">
            <div className="confidence-bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <span className="confidence-pct">{pct}%</span>
        </div>
      </div>

      <div className="result-body">
        <div className="result-section">
          <span className="result-section-label">Article</span>
          <p className="result-title-text">"{title}"</p>
          <span className="result-lang-badge">{language.toUpperCase()}</span>
        </div>

        <div className="result-section">
          <span className="result-section-label">NLP Signals</span>
          <div className="signals-grid">
            <div className="signal-item">
              <span className="signal-name">Similarity</span>
              <span className="signal-val">{similarity}</span>
            </div>
            <div className="signal-item">
              <span className="signal-name">Entailment</span>
              <span className={`signal-val ent-${entailment}`}>{entailment}</span>
            </div>
            <div className="signal-item">
              <span className="signal-name">Clickbait</span>
              <span className="signal-val">{clickbait}</span>
            </div>
          </div>
        </div>

        {flags.length > 0 && (
          <div className="result-section">
            <span className="result-section-label">Flags</span>
            <div className="flags-list">
              {flags.map((flag, i) => (
                <div key={i} className="flag-item">
                  <span className="flag-icon">⚠</span>
                  <span>{flag}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {llmExplanation && (
          <div className="explanation-box">
            <span className="explanation-header-text">
              {llmEmoji} Detective's Report
            </span>
            <p className="explanation-text">{llmExplanation}</p>
          </div>
        )}

        {summary && (
          <div className="summary-box">
            <span className="result-section-label">Article Summary</span>
            <p className="summary-text">{summary}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message-row bot-row">
      <div className="message-bubble typing">
        <div className="typing-dots">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
        <span className="typing-label">Analizez articolul...</span>
      </div>
    </div>
  );
}

function BowAnimation() {
  const items = useMemo(
    () =>
      Array.from({ length: 22 }, (_, i) => ({
        symbol: ["🎀", "💖", "✨"][i % 3],
        left: `${Math.random() * 100}%`,
        delay: `${Math.random() * 0.9}s`,
        duration: `${2.4 + Math.random() * 1.6}s`,
        size: `${18 + Math.random() * 18}px`,
      })),
    []
  );

  return (
    <div className="bow-container">
      {items.map((item, i) => (
        <div
          key={i}
          className="bow"
          style={{
            left: item.left,
            animationDelay: item.delay,
            animationDuration: item.duration,
            fontSize: item.size,
          }}
        >
          {item.symbol}
        </div>
      ))}
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showBows, setShowBows] = useState(false);
  const [wantSummary, setWantSummary] = useState(false);
  const chatEndRef = useRef(null);
  const msgId = useRef(0);

  useEffect(() => {
    setMessages([
      {
        id: 0,
        sender: "bot",
        type: "text",
        text: "Buna! Sunt Gossip Police... yap yap yap! Da-mi un link si hai sa barfim! 🎀",
      },
    ]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addTextMessage = (sender, text) => {
    const id = ++msgId.current;
    setMessages((prev) => [...prev, { id, sender, type: "text", text }]);
  };

  const addResultMessage = (data, summary = null) => {
    const id = ++msgId.current;
    setMessages((prev) => [
      ...prev,
      { id, sender: "bot", type: "result", data, summary },
    ]);
  };

  const isValidUrl = (value) => /^https?:\/\/.+/i.test(value.trim());

  const triggerBowAnimation = () => {
    setShowBows(false);
    setTimeout(() => {
      setShowBows(true);
      setTimeout(() => setShowBows(false), 3500);
    }, 50);
  };

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || loading) return;

    addTextMessage("user", trimmedInput);
    setInput("");

    if (!isValidUrl(trimmedInput)) {
      addTextMessage(
        "bot",
        "Te rog trimite un link valid care incepe cu http:// sau https://."
      );
      return;
    }

    setLoading(true);
    triggerBowAnimation();

    try {
      const response = await fetch("http://localhost:8080/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmedInput }),
      });

      const data = await response.json();

      if (!response.ok) {
        addTextMessage(
          "bot",
          data?.error || data?.message || "A aparut o eroare la analiza."
        );
        return;
      }

      let summary = null;

      if (wantSummary) {
        const articleText = data?.scraping?.cleaned?.text || "";
        const headline = data?.scraping?.cleaned?.title || "";
        const language = data?.language || "en";

        try {
          const explainResp = await fetch("http://localhost:8080/explain", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ headline, article_text: articleText, language }),
          });
          const explainData = await explainResp.json();
          summary = explainData?.summary || null;
        } catch {
          summary = null;
        }
      }

      addResultMessage(data, summary);
    } catch {
      addTextMessage(
        "bot",
        "Nu ma pot conecta la backend. Verifica daca Flask ruleaza pe http://localhost:8080."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="app">
      {showBows && <BowAnimation />}

      <div className="chat-card">
        <header className="chat-header">
          <div className="logo-wrapper">
            <img src={logo} alt="Gossip Police" className="logo" />
          </div>
          <div className="header-text">
            <h1>Gossip Police</h1>
            <p className="subtitle">
              Detectam daca un titlu spune adevarul sau cauta scandal.
            </p>
          </div>
        </header>

        <main className="chat-window">
          {messages.map((message) =>
            message.type === "result" ? (
              <div key={message.id} className="message-row bot-row">
                <div className="result-card-wrap">
                  <ResultCard data={message.data} summary={message.summary} />
                </div>
              </div>
            ) : (
              <div
                key={message.id}
                className={`message-row ${
                  message.sender === "user" ? "user-row" : "bot-row"
                }`}
              >
                <div
                  className={`message-bubble ${
                    message.sender === "user" ? "user" : "bot"
                  }`}
                >
                  {message.text.split("\n").map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>
            )
          )}

          {loading && <TypingIndicator />}
          <div ref={chatEndRef} />
        </main>

        <footer className="chat-input-area">
          <div className="input-options">
            <label className="summary-toggle">
              <input
                type="checkbox"
                checked={wantSummary}
                onChange={(e) => setWantSummary(e.target.checked)}
                disabled={loading}
              />
              Vreau rezumat
            </label>
          </div>

          <div className="input-row">
            <input
              type="text"
              placeholder="Lipeste linkul articolului..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              {loading ? "Se analizeaza..." : "Analizeaza"}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
