import React, { useEffect, useRef, useState } from "react";
import "./App.css";
import logo from "./assets/logo.png";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showBows, setShowBows] = useState(false);
  const [wantSummary, setWantSummary] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    setMessages([
      {
        sender: "bot",
        text: "Buna! Sunt Gossip Police... yap yap yap! Da-mi un link si hai sa barfim!"
      }
    ]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addMessage = (sender, text) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  const isValidUrl = (value) => {
    return /^https?:\/\/.+/i.test(value.trim());
  };

  const formatBotReply = (data) => {
    const title =
      data?.scraping?.cleaned?.title ||
      data?.scraping?.raw?.title ||
      "Titlu indisponibil";

    const language = data?.language || "N/A";

    const verdict = data?.verdict?.verdict || "unknown";
    const confidence =
      typeof data?.verdict?.confidence === "number"
        ? `${(data.verdict.confidence * 100).toFixed(1)}%`
        : "N/A";

    const similarityRaw = data?.semantic_similarity?.similarity_score;
    const similarity = typeof similarityRaw === "number"
      ? similarityRaw.toFixed(4)
      : "N/A";

    const entailment =
      data?.entailment?.label ??
      data?.entailment?.prediction ??
      "N/A";

    const clickbaitRaw = data?.clickbait?.final_score;
    const clickbait = typeof clickbaitRaw === "number"
      ? clickbaitRaw.toFixed(4)
      : "N/A";

    const flags = Array.isArray(data?.verdict?.flags) ? data.verdict.flags : [];

    let response = "";
    response += "Am terminat analiza.\n\n";
    response += `Titlu: ${title}\n`;
    response += `Limba detectata: ${language}\n`;
    response += `Verdict: ${verdict}\n`;
    response += `Confidence: ${confidence}\n`;
    response += `Semantic similarity: ${similarity}\n`;
    response += `Entailment: ${entailment}\n`;
    response += `Clickbait score: ${clickbait}\n`;

    if (flags.length > 0) {
      response += `Flags: ${flags.join(", ")}\n`;
    }

    return response;
  };

  const triggerBowAnimation = () => {
    setShowBows(false);

    setTimeout(() => {
      setShowBows(true);

      setTimeout(() => {
        setShowBows(false);
      }, 3000);
    }, 50);
  };

  const handleSend = async () => {
    const trimmedInput = input.trim();

    if (!trimmedInput || loading) return;

    addMessage("user", trimmedInput);
    setInput("");
    triggerBowAnimation();

    if (!isValidUrl(trimmedInput)) {
      addMessage(
        "bot",
        "Te rog trimite un link valid care incepe cu http:// sau https://."
      );
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmedInput })
      });

      const data = await response.json();

      if (!response.ok) {
        addMessage("bot", data?.error || data?.message || "A aparut o eroare la analiza.");
      } else {
        addMessage("bot", formatBotReply(data));

        if (wantSummary) {
          const articleText = data?.scraping?.cleaned?.text || "";
          const headline = data?.scraping?.cleaned?.title || "";
          const language = data?.language || "en";

          try {
            const explainResp = await fetch("http://localhost:5000/explain", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ headline, article_text: articleText, language })
            });
            const explainData = await explainResp.json();
            if (explainData?.summary) {
              addMessage("bot", `📝 Rezumat:\n${explainData.summary}`);
            }
          } catch {
            addMessage("bot", "Nu am putut genera rezumatul.");
          }
        }
      }
    } catch (error) {
      addMessage(
        "bot",
        "Nu ma pot conecta la backend. Verifica daca Flask ruleaza pe http://localhost:5000."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  return (
    <div className="app">
      {showBows && <BowAnimation />}

      {loading && <LoadingAnimation />}

      <div className="chat-card">
        <header className="chat-header">
          <div className="logo-wrapper">
            <img src={logo} alt="Gossip Police" className="logo" />
          </div>

          <div className="header-text">
            <h1>Gossip Police</h1>
            <p className="subtitle">
              Detectam daca un titlu spune adevarul sau doar cauta scandal.
            </p>
          </div>
        </header>

        <main className="chat-window">
          {messages.map((message, index) => (
            <div
              key={index}
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
          ))}

          {loading && (
            <div className="message-row bot-row">
              <div className="message-bubble bot typing">
                <p>Analizez articolul...</p>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </main>

        <footer className="chat-input-area">
          <label className="summary-toggle">
            <input
              type="checkbox"
              checked={wantSummary}
              onChange={(e) => setWantSummary(e.target.checked)}
              disabled={loading}
            />
            Vreau rezumat
          </label>

          <div className="input-row">
            <input
              type="text"
              placeholder="Lipeste aici linkul articolului..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />

            <button onClick={handleSend} disabled={loading || !input.trim()}>
              {loading ? "Se analizeaza..." : "Trimite"}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

function LoadingAnimation() {
  const symbols = ["🎀", "🔍", "🪪"];
  const items = Array.from({ length: 21 }, (_, i) => {
    const tx = (Math.random() - 0.5) * 160;
    const ty = (Math.random() - 0.5) * 160;
    const rot = Math.random() * 720 - 360;
    return { symbol: symbols[i % 3], tx, ty, rot };
  });

  return (
    <div className="loading-overlay">
      {items.map((item, i) => (
        <div
          key={i}
          className="loading-particle"
          style={{
            "--tx": `${item.tx}vw`,
            "--ty": `${item.ty}vh`,
            "--rot": `${item.rot}deg`,
            animationDelay: `${(i / 21) * 1.8}s`,
            animationDuration: `${1.6 + Math.random() * 0.6}s`,
            fontSize: `${22 + Math.random() * 18}px`,
          }}
        >
          {item.symbol}
        </div>
      ))}
    </div>
  );
}

function BowAnimation() {
  const items = Array.from({ length: 24 });

  return (
    <div className="bow-container">
      {items.map((_, i) => {
        const symbols = ["🎀", "💖", "✨"];
        const symbol = symbols[Math.floor(Math.random() * symbols.length)];

        return (
          <div
            key={i}
            className="bow"
            style={{
              left: `${Math.random() * 100}vw`,
              animationDelay: `${Math.random() * 0.8}s`,
              animationDuration: `${2.4 + Math.random() * 1.8}s`,
              fontSize: `${18 + Math.random() * 20}px`
            }}
          >
            {symbol}
          </div>
        );
      })}
    </div>
  );
}

export default App;