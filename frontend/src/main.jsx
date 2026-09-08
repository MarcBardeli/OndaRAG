import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const newId = () => crypto.randomUUID();

function App() {
  const [conversationId, setConversationId] = useState(() => localStorage.getItem('omni_conversation') || newId());
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState('');
  const [sources, setSources] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => localStorage.setItem('omni_conversation', conversationId), [conversationId]);

  const startNewChat = () => {
    setConversationId(newId());
    setMessages([]);
    setNotice('New conversation ready');
    inputRef.current?.focus();
  };

  const sendMessage = async (event) => {
    event?.preventDefault();
    const message = draft.trim();
    if (!message || busy) return;
    setDraft('');
    setMessages((current) => [...current, { role: 'user', content: message }]);
    setBusy(true);
    setNotice('OmniCar is thinking...');
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      });
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
      const data = await response.json();
      setMessages((current) => [...current, { role: 'assistant', content: data.text, audio: data.audio }]);
      setNotice('Ready');
    } catch (error) {
      setMessages((current) => [...current, { role: 'error', content: error.message }]);
      setNotice('Could not reach the local model');
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    setNotice('Indexing document...');
    try {
      const response = await fetch('/upload', { method: 'POST', body: form });
      if (!response.ok) throw new Error('Upload failed');
      setNotice(`${file.name} added to knowledge`);
      setFile(null);
    } catch (error) {
      setNotice(error.message);
    }
  };

  const inspectKnowledge = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    try {
      const response = await fetch(`/debug/retrieve?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSources(data.results || []);
    } catch {
      setSources([]);
    }
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">O</span><span>OMNICAR</span><span className="brand-dot" /></div>
        <div className="sidebar-section">
          <div className="section-label">Workspace</div>
          <button className="nav-item active"><span className="nav-icon">✦</span> Assistant <span className="nav-count">1</span></button>
          <button className="nav-item" onClick={startNewChat}><span className="nav-icon">＋</span> New conversation</button>
        </div>
        <div className="sidebar-section knowledge-section">
          <div className="section-label">Knowledge base</div>
          <label className="upload-drop">
            <input type="file" accept=".txt,.md" onChange={(event) => setFile(event.target.files?.[0] || null)} />
            <span className="upload-icon">↑</span>
            <strong>{file ? file.name : 'Add a document'}</strong>
            <small>{file ? 'Ready to index' : 'TXT or Markdown'}</small>
          </label>
          {file && <button className="index-button" onClick={uploadFile}>Index document <span>→</span></button>}
        </div>
        <div className="sidebar-footer"><span className="status-dot" /> Local model online <span className="version">v1.0</span></div>
      </aside>

      <section className="workspace">
        <header className="topbar"><div><span className="eyebrow">LOCAL INTELLIGENCE</span><h1>OmniCar assistant</h1></div><button className="new-chat" onClick={startNewChat}>＋ <span>New chat</span></button></header>
        <div className="chat-stage">
          {messages.length === 0 ? <div className="welcome"><div className="welcome-symbol">✦</div><p className="eyebrow">YOUR PRIVATE COPILOT</p><h2>What can I help you<br /><em>understand?</em></h2><p className="welcome-copy">Ask about your indexed knowledge, explore a topic, or bring in a new document to give OmniCar more context.</p><div className="prompt-grid"><button onClick={() => setDraft('Summarize the key points in my knowledge base')}>Summarize my knowledge base <span>↗</span></button><button onClick={() => setDraft('What documents are available?')}>What is in my workspace? <span>↗</span></button></div></div> : <div className="messages">{messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} />)}{busy && <div className="message assistant"><div className="avatar">O</div><div className="bubble thinking"><span /><span /><span /></div></div>}</div>}
        </div>
        <div className="composer-wrap"><form className="composer" onSubmit={sendMessage}><textarea ref={inputRef} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(event); } }} placeholder="Ask OmniCar anything..." rows="1" disabled={busy} /><button className="send-button" type="submit" aria-label="Send message" disabled={!draft.trim() || busy}>↑</button></form><div className="composer-meta"><span>{notice || 'Enter to send · Shift + Enter for a new line'}</span><span>Responses use your local knowledge</span></div></div>
      </section>

      <aside className="inspector"><div className="inspector-heading"><div><span className="eyebrow">CONTEXT</span><h2>Knowledge inspector</h2></div><span className="live-pill"><span /> LIVE</span></div><p className="inspector-copy">Search the indexed documents directly and see the context available to your assistant.</p><form className="search-box" onSubmit={inspectKnowledge}><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search knowledge..." /><button type="submit">↵</button></form><div className="source-list">{sources.length ? sources.map((source, index) => <article className="source-card" key={`${source.source}-${index}`}><div className="source-top"><span className="file-badge">TXT</span><strong>{source.source}</strong><span className="score">{Math.round((source.score || 0) * 100)}%</span></div><p>{source.content}</p></article>) : <div className="empty-sources"><div>⌁</div><strong>No context loaded</strong><span>Search above to inspect relevant passages.</span></div>}</div><div className="inspector-note"><span>i</span><p>OmniCar runs locally. Your documents stay on this machine.</p></div></aside>
    </main>
  );
}

function Message({ message }) {
  if (message.role === 'error') return <div className="error-message">{message.content}</div>;
  const assistant = message.role === 'assistant';
  return <div className={`message ${assistant ? 'assistant' : 'user'}`}><div className="avatar">{assistant ? 'O' : 'Y'}</div><div className="message-body"><span className="message-label">{assistant ? 'OMNICAR' : 'YOU'}</span><div className="bubble">{message.content}</div>{assistant && message.audio && <audio controls src={message.audio} />}</div></div>;
}

createRoot(document.getElementById('root')).render(<App />);